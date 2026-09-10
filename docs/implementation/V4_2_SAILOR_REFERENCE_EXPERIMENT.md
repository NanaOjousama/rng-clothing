# V4.2 Sailor Technical-Reference Experiment

Status: one fixed-seed controlled experiment.

- Current V4.2 Sailor automated QC: **PASS**
- Technical-reference Sailor automated QC: **PASS**
- **HUMAN VISUAL QC: PENDING**

No visual-success claim is made here. The Farmer comparison is the human review authority.

## Controlled inputs

Both sides of the comparison use the same canonical garment and projections:

- Family: `SAILOR_TOP`
- Intent: `SAILOR_DECK_CLASSIC`
- Fit: `UNISEX_REGULAR`
- Seed: `420205`
- Material: `WOVEN_SHIRT`
- Palette story: `SAILOR_NAVY`
- Farmer/body/hair fixture: identical
- Runtime and native sleeve contract: identical
- Frozen V5/HD carrier, polish, and palette resolution: identical

The only route difference is `V4_2_SHAPE_PROOF` versus the Sailor-only `V4_2_SAILOR_TECHNICAL_EXPERIMENT` component-variant profile.

## Reference-derived architecture

The construction study is in `docs/research/SAILOR_TECHNICAL_REFERENCE_STUDY.md`. Its physical architecture is recorded under `familyArchitectures.SAILOR_TOP` in `architecture_grammar_v4.json`.

The technical profile executes:

- `SAILOR_COLLAR_FRONT_TECHNICAL_V1`
- `SAILOR_COLLAR_SIDE_TECHNICAL_V1`
- `SAILOR_REAR_FLAP_TECHNICAL_V1`
- `SAILOR_COLLAR_BORDER_TECHNICAL_V1`
- Existing subordinate `SAILOR_FRONT_OPENING_OR_INSERT_V1`

No separate technical tie variant was added. The references support a tie, but the selected architecture keeps the existing compact four-cell insert so the experiment isolates collar/flap/border geometry.

## Geometry and ownership change

### Current V4.2

- Front collar: 18 owned collar cells.
- Side collar: 6 owned cells per side.
- Rear panel: 28 owned back cells and 4 side cells per side.
- Border system: absent.
- Topology: ADD at right `(14,2)` and left `(1,2)`.

### Technical-reference profile

- Front: 12 collar-fill cells plus 8 disjoint perimeter-border cells.
- Side: 5 collar-depth cells, 2 border/handoff cells, and 4 rear-handoff cells per side.
- Back: 14 interior flap cells nested inside 20 perimeter-border cells.
- Topology: ADD at the higher shoulder attachment cells right `(12,1)` and left `(3,1)`.
- Component ownership conflicts: 0.
- Safe-envelope, connectivity, topology-survival, protected-cell, and visual-change-contract failures: 0.

The border owns only enumerated component-perimeter cells. It does not outline the torso or garment silhouette.

## Questions answered

### 1. What did the technical references provide that the previous grammar lacked?

They provided a stable physical sequence: compact rear neck, high attachment, broad shoulder-spanning flap, shallow upper-back depth, and a controlled lower edge. They also showed that trim should run parallel to the collar/flap perimeter and that front, side, and rear are one wrapped construction. The previous grammar encoded a filled rear patch and a sparse side cue, but it did not explicitly separate flap fill, perimeter, lower termination, or high shoulder handoff.

### 2. Did the back flap become more physically coherent?

**Architecturally, yes.** It is now a broad shallow trapezoid constructed from a distinct 14-cell fill and 20-cell supported perimeter, attached at the high rear neckline with a named lower termination. It can no longer degrade into a tiny central rectangle under the technical variant contract. Whether this construction reads more coherently at Farmer scale remains a human visual decision.

### 3. Did the side transition improve?

**Structurally, yes.** The silhouette addition moved from a lower/farther side projection to the upper shoulder attachment, and the view now allocates separate collar-depth, border-handoff, and rear-handoff clusters. The contract forbids a floating patch, long stripe, diagonal slash, and vertical rail. Human review must decide whether the resulting pixels communicate that improvement.

### 4. Did a small outline/border improve readability?

It created measurable component separation without changing the garment-wide outline: the back has a one-cell perimeter around a contrasting interior fill, and the front/side borders remain sparse. The logical and ownership overlays show that separation clearly. Farmer-scale readability is **PENDING** rather than self-approved.

### 5. What can become permanent Sailor grammar?

- High rear-neck attachment as a mandatory anchor.
- Broad, shallow rear-flap proportions.
- Square, tapered-square, and shallow-trapezoid row profiles.
- Separate fill and one-cell perimeter ownership.
- Named lower-flap termination.
- Compact shoulder-local side depth with an explicit rear handoff.
- A degradation order that preserves shoulder mass and lower termination before secondary fill/highlight cells.
- Tie/insert subordination to the collar.

### 6. What was not useful?

- The button-front shirt flat contained no Sailor collar/flap evidence.
- Exact colors, stripe counts, fabric rendering, sleeve shapes, dress length, cuff decoration, and tie silhouettes were not useful to this architecture proof.
- Front-only imagery could not establish rear proportions.
- No reference supplied a true orthographic side view, so side depth remains a conservative reconstruction rather than copied geometry.

### 7. Should technical flats become a standard architecture-authoring input?

**Yes, as a construction input with constraints—not as a pixel, palette, or decoration source.** Matched front/back flats are particularly useful for attachment, proportion, perimeter, and termination rules. They should be converted first into a coordinate-free physical study, then into declarative variants, and finally checked at Farmer scale. A missing side flat must remain an explicit inference limit. This recommendation does not authorize applying the technique to other families before this experiment receives human review.

## Automated evidence

- Both compilers loaded `4.2.0-shape-proof` and executed non-empty fail-closed expected variant sets.
- Current topology displacement: 2 cells.
- Technical topology displacement: 2 cells.
- Final logical pixel differences: front 10, right 16, left 16, back 13.
- Final alpha differences: front 0, right 2, left 2, back 0.
- Current guarded-polish rejections: 5.
- Technical guarded-polish rejections: 6.
- Unit/integration tests: 6 passed.

## Outputs

- `output/v4-sailor-reference-experiment/SAILOR_REFERENCE_BEFORE_AFTER_FARMER.png`
- `output/v4-sailor-reference-experiment/SAILOR_REFERENCE_BEFORE_AFTER_ISOLATED_8X.png`
- `output/v4-sailor-reference-experiment/SAILOR_REFERENCE_ARCHITECTURE_OVERLAY.png`

Shared canonical/projection records are at the experiment root. `current-v4.2/` and `technical-refined/` each contain their final logical atlas, topology map, ownership ledger, semantic regions, metrics, validation, and stage trace.

Final status: **HUMAN VISUAL QC: PENDING**.
