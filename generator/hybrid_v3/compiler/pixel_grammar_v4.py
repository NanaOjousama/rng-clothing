"""Hybrid V4 proof compiler: legacy carrier for safe silhouette, V4 owns art form + components."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from generator.controlled_test.hd_adapter import _remove_closed_opening_from_hd_regions
from generator.controlled_test.reference_guided import _copy_frames, _reset_to_proven_hd_planes, _resolve
from generator.hybrid_v3.validator import PhysicalValidator
from generator.renderers.fashionsense.art_polish_v5e import PolishedUpperFrames, polish_upper_frames, soften_shared_rear_neck
from generator.renderers.fashionsense.upper_v5b import _coverage_missing, _stack
from .carrier_registry import CarrierRegistry
from .compiler_validation import validate_compiled
from .component_compilers import compile_components
from .semantic_regions import SemanticRegionLedger
from .art_grammar_v4 import normalize_body_form, normalize_vanilla_plus_body_form
from .non_destructive_polish_v4 import merge_legacy_polish_non_destructive
from .shape_library_v42 import ShapeLibraryV42, VANILLA_PLUS_SHAPES
from .topology_v4 import TopologyEditorV4
from generator.renderers.fashionsense.upper_v5b import _default_value, _mask_value

V42_SHAPE_LIBRARY_VERSION = "4.2.0-shape-proof"
V42_PROOF_PROFILE = "V4_2_SHAPE_PROOF"
V42_SAILOR_TECHNICAL_PROFILE = "V4_2_SAILOR_TECHNICAL_EXPERIMENT"
V42_SAILOR_OUTLINE_PROFILE = "V4_2_SAILOR_OUTLINE_REFINEMENT"
V4_VANILLA_PLUS_PROFILE = "V4_VANILLA_PLUS_PROOF"
V4_VANILLA_PLUS_LIBRARY_VERSION = "4.2.1-vanilla-plus-proof"
V41_BASELINE_PROFILE = "V4_1_INLINE_BASELINE"

@dataclass(frozen=True)
class CompiledGarmentV4:
    canonical: dict[str,Any]; projections: dict[str,list[dict[str,Any]]]; palette_story:str
    carrier:dict[str,Any]; backend_recipe:dict[str,Any]; mask_frames:dict; frames:dict; role_frames:dict; texture:list
    sleeve_colors:tuple; validation:dict[str,Any]; semantic_regions:dict[str,Any]; stage_trace:list[str]
    metrics:dict[str,Any]; topology_map:list[dict[str,Any]]; pre_polish_frames:dict; post_polish_frames:dict

class PixelGrammarCompilerV4:
    """Proof architecture.

    Ownership order:
      carrier alpha -> legacy polish (body optics only) -> V4 body form ->
      component identity -> rear-neck cleanup respecting components -> palette.
    No legacy global polish is allowed after component identity is emitted.
    """
    def __init__(self, *, execution_profile=V42_PROOF_PROFILE):
        if execution_profile not in {V42_PROOF_PROFILE,V42_SAILOR_TECHNICAL_PROFILE,V42_SAILOR_OUTLINE_PROFILE,V4_VANILLA_PLUS_PROFILE,V41_BASELINE_PROFILE}:
            raise ValueError(f"unknown V4 compiler execution profile: {execution_profile}")
        self.registry=CarrierRegistry(); self.validator=PhysicalValidator()
        self.execution_profile=execution_profile
        self.shape_library=(
            ShapeLibraryV42(document_path=VANILLA_PLUS_SHAPES)
            if execution_profile==V4_VANILLA_PLUS_PROFILE else
            ShapeLibraryV42() if execution_profile!=V41_BASELINE_PROFILE else None
        )

    def compile(self, canonical, projections, *, palette_story, required_shape_library_version=None, expected_shape_variants=None):
        c=self.validator.validate(canonical); p=self.validator.validate_projections(canonical,projections)
        if c['status']!='PASS' or p['status']!='PASS': raise ValueError({'canonical':c,'projections':p})
        if self.execution_profile in {V42_SAILOR_TECHNICAL_PROFILE,V42_SAILOR_OUTLINE_PROFILE} and canonical['identity']['family']!='SAILOR_TOP':
            raise ValueError('V4.2 Sailor experiment profiles are restricted to SAILOR_TOP')
        capability, recipe, raw=self.registry.select(canonical); base=raw
        frames=_copy_frames(raw.frames); defaults=_copy_frames(raw.default_frames)
        _reset_to_proven_hd_planes(base,frames,defaults)
        inherited=_remove_closed_opening_from_hd_regions(base,frames,defaults)

        # Legacy polish is demoted to BODY OPTICS and runs before identity.
        polished=polish_upper_frames(base,frames,defaults,article_family=canonical['identity']['family'])
        frames,defaults,form_changed=normalize_body_form(base,polished.frames,polished.default_frames,
                                                        family=canonical['identity']['family'],
                                                        break_dark_rails=self.shape_library is not None)

        ledger=SemanticRegionLedger()
        topology=TopologyEditorV4(
            frames,defaults,safe_envelopes=self.shape_library.safe_envelope(canonical['identity']['family']) if self.shape_library else {d:set() for d in frames},
            ownership=ledger.ownership,opaque_value=lambda shade:_mask_value(base,shade),
            default_value=lambda shade:_default_value(base,shade),
        )
        component_map,shape_events=compile_components(canonical,projections,base,frames,defaults,ledger,
                                                      shape_library=self.shape_library,topology=topology,shape_profile=self.execution_profile)
        topology.validate_final_connectivity()
        pre_polish_frames=_copy_frames(frames)

        # Codex/V4.1 contract: run frozen legacy polish through an ownership-aware
        # clone/merge boundary.  Component-owned structural cells are never
        # silently rewritten.  Rejected mutations are preserved in the trace.
        wrapped_polish=merge_legacy_polish_non_destructive(
            base, frames, defaults, article_family=canonical['identity']['family'], ownership=ledger.ownership
        )
        vanilla_changed=None
        if self.execution_profile==V4_VANILLA_PLUS_PROFILE:
            protected={d:ledger.ownership.protected_cells(d) for d in wrapped_polish.frames}
            vanilla_frames,vanilla_defaults,vanilla_changed=normalize_vanilla_plus_body_form(
                base,wrapped_polish.frames,wrapped_polish.default_frames,protected_cells=protected
            )
            wrapped_polish=PolishedUpperFrames(vanilla_frames,vanilla_defaults,{
                **wrapped_polish.metrics,
                'vanillaPlusBodyAbstractionChangedCells':vanilla_changed,
                'vanillaPlusBodyAbstractionAlphaPreserved':True,
            })
        post_polish_frames=_copy_frames(wrapped_polish.frames)

        # Rear-neck cleanup is also constrained by the ownership ledger.
        protected_back=ledger.ownership.protected_cells('back')
        softened=soften_shared_rear_neck(base,wrapped_polish,protected_cells=protected_back)

        allow_exposure=canonical['identity']['family']=='SWEATER_VEST'
        coverage=_coverage_missing(base,softened.frames,allow_sleeve_exposure=allow_exposure)
        approved={d:set() for d in softened.frames}
        for views in ledger.cleared_cells.values():
            for d,cells in views.items(): approved[d].update(cells)
        for operation in topology.operations:
            if operation['op']=='REMOVE': approved[operation['direction']].add(tuple(operation['cell']))
        coverage={d:tuple(cell for cell in cells if cell not in approved[d]) for d,cells in coverage.items()}

        design={'material':canonical['material']['id'],'paletteStory':palette_story}
        resolved,role_frames,ramps,evidence=_resolve(design,softened,ledger.fabrics)
        sleeve_fabric='SecondaryFabric' if allow_exposure else 'PrimaryFabric'
        sr=ramps[sleeve_fabric]
        sleeve_colors=tuple(color[:3] for color in (sr['DEEP_CREASE'],sr['BASE'],sr['LIGHT']))
        validation=validate_compiled(canonical,projections,resolved,ledger,coverage,
                                     topology_operations=topology.operations,
                                     safe_envelopes=topology.safe_envelopes,
                                     shape_events=shape_events,
                                     shape_contract_enabled=self.shape_library is not None,
                                     shape_library_version=self.shape_library.schema_version if self.shape_library else '4.1-inline-baseline',
                                     required_shape_library_version=required_shape_library_version,
                                     expected_shape_variants=expected_shape_variants)
        expected_variants=validation['shapeVariantExecution']['expected']
        metrics={'bodyFormChanged':form_changed,'inheritedCarrierPlacketCellsReset':inherited,'componentMap':component_map,
                 'ownership':'per-cell V4 ownership ledger; frozen legacy polish clone/merge rejects structural overwrites',
                 'legacyPolishMerge': wrapped_polish.metrics.get('ownershipAwareMerge'),
                 'legacyPolishRejected': wrapped_polish.metrics.get('rejectedCells'),
                 'ownershipConflictCount': len(ledger.ownership.conflicts),
                 'ownershipRejectedMutationCount': len(ledger.ownership.rejected_mutations),
                 'vanillaPlusBodyAbstractionChangedCells':vanilla_changed,
                 'executionProfile':self.execution_profile,
                 'shapeLibraryVersion':self.shape_library.schema_version if self.shape_library else '4.1-inline-baseline',
                 'expectedShapeVariants':expected_variants,
                 'shapeVariants':[event['variantId'] for event in shape_events],
                 'topologyOperationCount':len(topology.operations),
                 'topologyAlphaDisplacement':sum(op['alphaDisplacement'] for op in topology.operations),
                 'routing':{
                     'canonicalFamily':canonical['identity']['family'],
                     'canonicalId':canonical['identity']['id'],
                     'projectionDirections':sorted(projections),
                     'compiler':'PixelGrammarCompilerV4',
                     'executionProfile':self.execution_profile,
                     'requiredShapeLibraryVersion':required_shape_library_version,
                     'loadedShapeLibraryVersion':self.shape_library.schema_version if self.shape_library else None,
                     'expectedShapeVariants':expected_variants,
                     'resolvedShapeVariants':[event['variantId'] for event in shape_events],
                     'topologyOperations':len(topology.operations),
                     'ownershipLedgerCells':sum(len(cells) for cells in ledger.ownership.cells.values()),
                 }}
        trace=['select_existing_V5_carrier','reset_named_surface_to_proven_hd_planes','legacy_polish_as_body_optics','v4_normalize_body_form']
        if self.shape_library:
            trace += ['v4_2_load_required_shape_library']
            if self.execution_profile==V42_SAILOR_TECHNICAL_PROFILE:
                trace += ['v4_2_select_sailor_technical_reference_profile']
            elif self.execution_profile==V42_SAILOR_OUTLINE_PROFILE:
                trace += ['v4_2_select_sailor_outline_refinement_profile']
            elif self.execution_profile==V4_VANILLA_PLUS_PROFILE:
                trace += ['v4_select_vanilla_plus_micro_shape_library']
            trace += ['v4_2_resolve_component_variants','v4_2_apply_versioned_directional_shape_variants','v4_2_validated_safe_envelope_topology']
        else:
            trace += ['v4_1_inline_baseline_component_route']
        trace += ['v4_compile_component_identity','legacy_polish_clone_merge_ownership_guard']
        if self.execution_profile==V4_VANILLA_PLUS_PROFILE:
            trace += ['v4_vanilla_plus_protected_body_abstraction']
        trace += ['soften_shared_rear_neck_ownership_guard','semantic_palette_material_adapter']
        return CompiledGarmentV4(canonical,projections,palette_story,capability,recipe,softened.frames,resolved,role_frames,
                                 _stack(resolved),sleeve_colors,validation,ledger.as_json(),trace,metrics,
                                 topology.operations,pre_polish_frames,post_polish_frames)
