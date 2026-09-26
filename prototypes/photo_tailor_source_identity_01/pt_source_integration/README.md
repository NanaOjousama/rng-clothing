# Photo Tailor source-backed integration v1

This isolated layer implements only the Photo Tailor subsystems approved by the
audit. It surrounds the source-preserving renderer; it does not replace it.

## Implemented stages

1. `contracts.py` — immutable semantic/evidence DTOs adapted from Photo Tailor,
   with explicit source binding, provenance, and review status.
2. `render.py` and `audit.py` — immutable prepared pixels, exact diff auditing,
   and export of the same pixels used by preview.
3. `semantic.py` — typed integration of the previously parity-tested Photo
   Tailor semantic retriever. Rankings remain advisory and cannot select source
   geometry.
4. `analysis.py` — exact source palette candidates and local texture statistics.
   It performs no clustering, cleanup, color merging, or pattern generation.
5. `pipeline.py` — render-first orchestration. Advisory work runs only after the
   prepared pixels pass the source/output audit.

## Hard boundary

Final pixels are owned only by:

`explicit source authority + reviewed source-space masks + source-relative transforms`

An unreviewed mask cannot authorize a transform. Every reviewed mask is bound
to the exact source ID and decoded-pixel SHA-256. Region transforms must be one
injective RGB translation, must preserve alpha/occupancy, and may not collide
with untouched colors. Evidence bundles reject all automatic pixel operations.

The following Photo Tailor systems are absent by design: generic hat rendering,
recolor/harmonize/shade ramps, canonical canvas/UV projection, generic whole-hat
region authority, procedural bands/patterns/motifs, runtime, menus, and migration
rerendering.

## Connected proof

`prove_integration.py` binds the accepted
`source_traced_trucker_template_02_native_front` frames and runs an identity-only
integration audit. No transform is allowed because that trace does not yet have
reviewed component masks. It creates one JSON audit report and no styled art.
