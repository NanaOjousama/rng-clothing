# Clothing V5 — CLOTHING_MEMORY

> Compact persistent memory for Clothing V5.
> Read after `PROJECT_MEMORY.md` only when working on clothing.

## Status
Clothing V5 architecture is established.
The Sailor family is **frozen / good enough** and should not be reopened unless a real new bug or regression is demonstrated.

## Canonical Design Model
- `Slot -> Garment Family -> Design Architecture -> scoped variables`
- one roll resolves one coherent garment
- Architecture owns topology, closure, aperture, seams, layering changes
- independent dimensions/modifiers remain scoped parameters
- lower passes do not reopen structural decisions
- authored closed silhouette/construction vocabularies are preferred over arbitrary carving
- projection is deterministic and adds zero design entropy
- validity is enforced during generation
- diversity is measured afterward

## Resolution / Fashion Sense Findings
Fashion Sense source audit established:
- 8x8 shirts with Scale 4 are a convention, not a hard engine requirement
- `ShirtSize` controls source rectangle width/height
- per-direction ShirtModels may have different frame sizes and BodyPosition
- Scale is real; alternate resolutions are possible
- BodyPosition is the origin offset
- animation Offset is additive
- shirts do not receive armOffset; sleeves do
- SleeveColors recolor Farmer sleeves only
- masks are exact RGB recolor, not clipping/deformation masks

Practical policy:
- keep native 8x8 / Scale 4 as the clothing default
- per-direction envelopes are a flexibility capability, not a quality button
- do not change resolution casually just to fix weak authoring

## Corpus Lessons
Large Fashion Sense garment study:
- majority use 8x8 / Scale 4
- richness comes primarily from color roles, region partitioning, accents, and authored construction
- not from simply increasing pixel density
- universal near-black outlines are not the clothing norm
- region partitioning is a dominant construction strategy

## Sailor — Frozen State
Architectures:
- CLASSIC_SQUARE_FLAP
- MIDDY_YOKE

Retain:
- hybrid procedural design + authored motifs/stencils/silhouettes
- shared Sailor motif vocabulary including tie styles
- IdentityRetention
- IdentitySeparation
- composite cue QC

Shared decorative-line rule:
`grammar.terminate_inboard(cells, run_axis, min_run=LINE_MIN_RUN)`

Apply to decorative stripes and hem/cuff bands.
Do not apply to panels, seams, or outlines.

Periodic Surface:
- unresolved period = absent
- do not silently default an unresolved period

Previously fixed:
- `check_continuity` KeyError
- INV-04 entropy leak

## Visual Lessons
In-game testing exposed issues metrics alone did not:
- neck holes
- armpit gaps
- straps on arms
- flat flaps/bands
- side-view weaknesses
- value-structure problems where a bright tie dominated while rear structure disappeared

Normal-scale wearability/readability remains the gate.

## Per-Direction Envelopes
Fashion Sense supports per-direction frame sizes/BodyPosition.
This is a future family capability when evidence requires it.

Do not assume:
- every family needs it
- larger envelopes automatically improve quality
- it would have fixed Sailor's authored defects

## Deep Reference
Use when detailed clothing work resumes:
- `V5_Clothing_Generator_Canonical_Merged_Architecture_Claude_Handoff.md`
