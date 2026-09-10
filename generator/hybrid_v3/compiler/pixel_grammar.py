"""Hybrid V3 canonical garment -> frozen V5/HD backend compiler."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from generator.controlled_test.hd_adapter import _remove_closed_opening_from_hd_regions
from generator.controlled_test.reference_guided import _copy_frames, _reset_to_proven_hd_planes, _resolve
from generator.hybrid_v3.validator import PhysicalValidator
from generator.renderers.fashionsense.art_polish_v5e import polish_upper_frames, soften_shared_rear_neck
from generator.renderers.fashionsense.upper_v5b import _coverage_missing, _stack

from .carrier_registry import CarrierRegistry
from .compiler_validation import validate_compiled
from .component_compilers import compile_components
from .semantic_regions import SemanticRegionLedger
from .stage_trace import phase2_trace


@dataclass(frozen=True)
class CompiledGarment:
    canonical: dict[str, Any]
    projections: dict[str, list[dict[str, Any]]]
    palette_story: str
    carrier: dict[str, Any]
    backend_recipe: dict[str, Any]
    pixel_grammar_map: dict[str, Any]
    semantic_regions: dict[str, Any]
    mask_frames: dict
    frames: dict
    role_frames: dict
    texture: list
    sleeve_colors: tuple
    validation: dict[str, Any]
    material_evidence: dict[str, Any]
    stage_trace: list[str]


class PixelGrammarCompiler:
    def __init__(self):
        self.registry = CarrierRegistry()
        self.validator = PhysicalValidator()

    def compile(self, canonical: dict[str, Any], projections: dict[str, list[dict[str, Any]]], *, palette_story: str) -> CompiledGarment:
        canonical_check = self.validator.validate(canonical)
        projection_check = self.validator.validate_projections(canonical, projections)
        if canonical_check["status"] != "PASS" or projection_check["status"] != "PASS":
            raise ValueError({"canonical": canonical_check, "projections": projection_check})
        capability, recipe, raw = self.registry.select(canonical)
        base = raw
        frames = _copy_frames(raw.frames); defaults = _copy_frames(raw.default_frames)
        _reset_to_proven_hd_planes(base, frames, defaults)
        # Every Phase 2 carrier may contain a permanent legacy PLACKET plane.
        # V3 anatomy owns opening topology, so erase that inherited semantic
        # signal before component compilation. POLO then emits only its
        # canonical short upper-chest placket; other families emit none.
        inherited_placket_cells = _remove_closed_opening_from_hd_regions(base, frames, defaults)
        ledger = SemanticRegionLedger()
        component_map, _shape_events = compile_components(canonical, projections, base, frames, defaults, ledger)

        # Compiler-cleared cells are approved architecture exclusions, not
        # post-render repairs. All remaining missing body cells remain fatal.
        allow_exposure = canonical["identity"]["family"] == "SWEATER_VEST"
        coverage = _coverage_missing(base, frames, allow_sleeve_exposure=allow_exposure)
        approved = {d:set() for d in frames}
        for views in ledger.cleared_cells.values():
            for direction, cells in views.items(): approved[direction].update(cells)
        coverage = {d:tuple(cell for cell in cells if cell not in approved[d]) for d,cells in coverage.items()}

        polished = polish_upper_frames(base, frames, defaults, article_family=canonical["identity"]["family"])
        protected_back = frozenset(cell for system in ledger.systems.values() for cell in system["back"])
        polished = soften_shared_rear_neck(base, polished, protected_cells=protected_back)
        design = {"material": canonical["material"]["id"], "paletteStory": palette_story}
        resolved, role_frames, ramps, evidence = _resolve(design, polished, ledger.fabrics)
        sleeve_fabric = "SecondaryFabric" if allow_exposure else "PrimaryFabric"
        sleeve_ramp = ramps[sleeve_fabric]
        sleeve_colors = tuple(color[:3] for color in (sleeve_ramp["DEEP_CREASE"], sleeve_ramp["BASE"], sleeve_ramp["LIGHT"]))
        validation = validate_compiled(canonical, projections, resolved, ledger, coverage)
        pixel_map = {
            "schemaVersion": "3.0.0-phase2", "carrierId": capability["id"],
            "compilerRule": "components realized only from validated canonical instances and Phase 1 visibility",
            "inheritedCarrierPlacketCellsReset": inherited_placket_cells,
            "components": component_map,
            "mandatoryPriority": sorted([{"instance": c["instanceId"], "priority": c["pixelPriority"]} for c in canonical["components"]], key=lambda x:x["priority"]),
        }
        return CompiledGarment(
            canonical, projections, palette_story, capability, recipe, pixel_map, ledger.as_json(),
            polished.frames, resolved, role_frames, _stack(resolved), sleeve_colors,
            validation, evidence, phase2_trace(capability["id"]),
        )
