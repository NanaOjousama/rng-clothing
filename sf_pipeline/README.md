# SF-assisted Generator Pipeline

This package is the AI-assisted visual-production layer for RNG Clothing.

## Phase mapping
- Phase 1 / preserve: existing template contracts, source catalogs, roll matrices, exclusions, view semantics, ESM runtime, and trusted source-backed render paths stay authoritative.
- Phase 2 / quarantine: deprecated_visual_paths.json marks failed procedural SF-backed render experiments as support/research only.
- Phase 3 / SF candidate path: reference_bundle.py + client.py + tools/sf_run_request.py create role-aware requests and preserve local provenance.
- Phase 4 / QC: qc.py blocks oversize/empty output, requires eight direction-set outputs, and forces semantic human review for contamination/design consistency.
- Phase 5 / promotion: promotion.py + registry.json + tools/sf_pipeline_cli.py enforce lifecycle and fail-closed production admission.

## Production rule
Only PRODUCTION_APPROVED assets may enter a live production pool, and that status requires:
- candidate mechanical QC;
- direction mechanical QC;
- human art approval;
- ESM wear approval;
- a recorded direction manifest.

See docs/SPRITE_FUSION_WORKFLOW.md before changing this pipeline.
