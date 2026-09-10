"""Semantic pixel-region ledger produced by component compilation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from .ownership_v4 import OwnershipLedgerV4


@dataclass
class SemanticRegionLedger:
    systems: dict[str, dict[str, set[tuple[int, int]]]] = field(default_factory=lambda: {
        system: {direction: set() for direction in DIRECTION_ORDER}
        for system in ("silhouette", "collar", "collar_border", "tie", "sleeves", "armholes", "opening", "placket", "hem", "waistband", "ribbing", "inner_layer", "rear_panel")
    })
    fabrics: dict[str, dict[tuple[int, int], str]] = field(default_factory=lambda: {direction: {} for direction in DIRECTION_ORDER})
    component_cells: dict[str, dict[str, set[tuple[int, int]]]] = field(default_factory=dict)
    cleared_cells: dict[str, dict[str, set[tuple[int, int]]]] = field(default_factory=dict)
    runtime_components: dict[str, dict[str, str]] = field(default_factory=dict)
    ownership: OwnershipLedgerV4 = field(default_factory=OwnershipLedgerV4)

    def record(self, instance: str, system: str, direction: str, cell: tuple[int, int], fabric: str) -> None:
        self.systems[system][direction].add(cell)
        self.fabrics[direction][cell] = fabric
        self.component_cells.setdefault(instance, {}).setdefault(direction, set()).add(cell)
        is_body_plane = system == "silhouette"
        existing = self.ownership.cells[direction].get(cell)
        # A topology claim already captures the stronger reason the cell was
        # added. Keep that LOCKED claim while still recording semantic/fabric
        # membership for palette resolution and identity QC.
        if existing is not None and existing.topology_role == "ALPHA_ADDITION":
            return
        self.ownership.claim(
            direction, cell, component_owner=instance, system=system,
            topology_role="BODY_FORM" if is_body_plane else "COMPONENT_IDENTITY",
            semantic_region=system,
            shade_authority="MATERIAL_FORM" if is_body_plane else "COMPONENT",
            protection_level="FORM" if is_body_plane else "STRUCTURAL",
            allowed_later_mutations=("LEGACY_POLISH", "MATERIAL_FORM", "PALETTE_RESOLVE") if is_body_plane else ("PALETTE_RESOLVE",),
            originating_stage="V4_BODY_FORM" if is_body_plane else "V4_COMPONENT_COMPILER",
        )

    def record_clear(self, instance: str, direction: str, cell: tuple[int, int]) -> None:
        self.cleared_cells.setdefault(instance, {}).setdefault(direction, set()).add(cell)

    def record_runtime(self, instance: str, direction: str, contract: str) -> None:
        self.runtime_components.setdefault(instance, {})[direction] = contract

    def as_json(self) -> dict[str, Any]:
        cells = lambda values: [[x, y] for x, y in sorted(values, key=lambda p: (p[1], p[0]))]
        return {
            "systems": {s: {d: cells(v) for d, v in views.items()} for s, views in self.systems.items()},
            "fabrics": {d: [{"cell": [x, y], "role": role} for (x, y), role in sorted(values.items(), key=lambda p: (p[0][1], p[0][0]))] for d, values in self.fabrics.items()},
            "components": {i: {d: cells(v) for d, v in views.items()} for i, views in self.component_cells.items()},
            "clearedByCompiler": {i: {d: cells(v) for d, v in views.items()} for i, views in self.cleared_cells.items()},
            "runtimeComponents": self.runtime_components,
            "ownership": self.ownership.as_json(),
        }
