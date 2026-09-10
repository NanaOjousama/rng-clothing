# V4.2 Shape-Library Proof — Polo / Sweater Vest / Sailor

Status: experimental three-family proof; production remains disabled.

- **AUTOMATED QC: PASS** for all three fixed-seed garments.
- **HUMAN VISUAL QC: PENDING.** Automated results do not approve garment identity or visual quality.
- Frozen V5/HD renderer/runtime files remain unchanged and the V3 canonical model remains the garment source of truth.

## Routing correction

The V4.1 comparison generator and V4.2 proof generator previously shared the same compiler class with an `enable_v42_shapes` boolean. `tools/generate_v4_art_grammar_pass2.py` intentionally disabled that switch, so its `output/v4-art-grammar-pass2/*/metrics.json` files correctly reported `4.1-inline-baseline`, but those files could be mistaken for V4.2 proof output.

Routing is now explicit:

- `V4_1_INLINE_BASELINE` selects the inline comparison route and does not claim to be a V4.2 proof.
- `V4_2_SHAPE_PROOF` loads `4.2.0-shape-proof` and is the only profile used by `generate_v42_shape_library_proof.py`.
- The proof compiler call requires `required_shape_library_version="4.2.0-shape-proof"`.
- Validation fails closed on a version mismatch, an empty expected-variant set, missing variants, or missing topology displacement.
- The proof generator verifies the exact family variant set and exact ADD/REMOVE coordinates before writing any routing-fixed artifact.

The post-fix human-review sheets are `V4_2_ROUTING_FIXED_FARMER.png` and `V4_2_ROUTING_FIXED_ISOLATED_8X.png`. Each garment directory also contains `routing-trace.json` plus freshly written `metrics.json` and `validation.json`.

## Scope and deterministic cases

| Garment | Family | Intent | Fit | Seed | Palette story |
|---|---|---|---|---:|---|
| Polo | `POLO_SHIRT` | `POLO_CLASSIC` | `MASC_TAILORED` | 420201 | `COASTAL_MIST` |
| Sweater Vest | `SWEATER_VEST` | `VEST_ACADEMIC` | `MASC_TAILORED` | 420203 | `CREAM_ACADEMIC` |
| Sailor Top | `SAILOR_TOP` | `SAILOR_DECK_CLASSIC` | `UNISEX_REGULAR` | 420205 | `SAILOR_NAVY` |

No rerolls, rarity work, palette modernization, custom sleeves, new garment families, or runtime changes were made.

## Exact shape variants implemented

The executable library is `specs/garment_grammar_v4/component_shape_variants.json`, schema `4.2.0-shape-proof`. Every entry defines a stable ID, compatible family/component IDs, allowed directions, attachment anchor, local footprint bounds, alpha operations, support/adjacency, semantic roles, minimum identity cells, protected cells, degradation order, connectivity, safe-envelope requirements, and direction-local geometry.

### Polo

- `FOLDED_POLO_COLLAR_FRONT_V1`: two separate 2x2 folded leaf masses around the neckline.
- `FOLDED_POLO_COLLAR_SIDE_V1`: compact attached fold depth with one bounded silhouette projection per side.
- `FOLDED_POLO_COLLAR_BACK_V1`: shallow four-cell rear band plus two controlled under-collar shadow cells.
- `SHORT_POLO_PLACKET_FRONT_V1`: front-only 2x2 short placket with one localized button accent; it ends at logical row 4.

The opening component delegates its front identity to the placket variant through `V4_2_SHORT_POLO_PLACKET_PARENT`; no side or rear placket pixels are emitted.

### Sweater Vest

- `V_BINDING_FRONT_V1`: six-cell bounded V binding ending at logical row 3.
- `V_BINDING_SIDE_V1`: three-cell compressed binding in each side view.
- `V_BINDING_BACK_V1`: one-row compact rear binding.
- `CUTIN_ARMHOLE_SIDE_V1`: two-cell topology notch per side plus a four-cell adjacent binding.
- `INNER_SHIRT_EXPOSURE_SIDE_V1`: three-cell inner-shirt handoff per side, allocated beside rather than over the armhole binding.
- `KNIT_HEM_TERMINATION_V1`: one-row, primary-fabric knit termination with sparse shadow beats.

Waistband and surface-rib cells now occupy separate rows, preventing structural ownership competition and avoiding a giant dark band.

### Sailor Top

- `SAILOR_COLLAR_FRONT_V1`: broad paired collar leaves spanning the shoulder/neck area with an 18-cell minimum.
- `SAILOR_COLLAR_SIDE_V1`: connected side depth and a bounded one-cell silhouette projection on each side.
- `SAILOR_REAR_PANEL_V1`: parameterized square/tapered-square back row profiles plus independently reconstructed diagonal side handoffs.
- `SAILOR_FRONT_OPENING_OR_INSERT_V1`: compact four-cell front insert nested between the collar leaves.

The rear-facing collar projection delegates to the mandatory rear-panel construction through `V4_2_SAILOR_REAR_PANEL_COLLAR_HANDOFF`; the rear panel is forbidden and empty in front.

## Exact topology API operations

All operations were applied by `TopologyEditorV4`, inside family-specific masks in `safe_envelopes.json`. Additions require adjacent parent alpha. Removals require an opaque target and are rolled back if the root garment mass disconnects. A final four-direction connectivity check rejects unsupported islands.

| Family | Operation | Direction | Logical cell | Owner / variant |
|---|---|---|---|---|
| Polo | ADD | right | (12, 1) | collar / `FOLDED_POLO_COLLAR_SIDE_V1` |
| Polo | ADD | left | (3, 1) | collar / `FOLDED_POLO_COLLAR_SIDE_V1` |
| Sweater Vest | REMOVE | right | (13, 2) | armholes / `CUTIN_ARMHOLE_SIDE_V1` |
| Sweater Vest | REMOVE | right | (13, 3) | armholes / `CUTIN_ARMHOLE_SIDE_V1` |
| Sweater Vest | REMOVE | left | (2, 2) | armholes / `CUTIN_ARMHOLE_SIDE_V1` |
| Sweater Vest | REMOVE | left | (2, 3) | armholes / `CUTIN_ARMHOLE_SIDE_V1` |
| Sailor Top | ADD | right | (14, 2) | collar / `SAILOR_COLLAR_SIDE_V1` |
| Sailor Top | ADD | left | (1, 2) | collar / `SAILOR_COLLAR_SIDE_V1` |

Every operation reports `alphaDisplacement: 1`. Role-only recolors are explicitly reported as non-geometry and do not satisfy the topology contract.

## Ownership and guarded legacy polish

Component allocation finishes with **zero ownership-claim conflicts** in each final proof garment. Equal-strength incoming structural claims are now rejected by policy rather than winning through pass order; the existing owner is preserved and the rejected claim is diagnostic.

Frozen legacy polish runs on a clone and merges through the V4.1 ownership boundary. Illegal changes rejected from the final proof were:

| Family | Rejected legacy-polish mutations | By direction (front/right/back/left) |
|---|---:|---|
| Polo | 4 | 2 / 0 / 2 / 0 |
| Sweater Vest | 16 | 8 / 1 / 6 / 1 |
| Sailor Top | 5 | 2 / 0 / 2 / 1 |
| **Total** | **25** | |

Coordinates, owners, reasons, and stages are retained in each garment's `ownership-ledger.json` and `stage-trace.json`.

## Structural survival and visual-change contract

- Polo: both side collar additions remain opaque in the final logical frames; the folded front leaves, shallow rear band, and front-only short placket remain owned after polish.
- Sweater Vest: all four cut-in cells remain transparent; side armhole bindings and side inner-shirt exposure remain present; the garment remains one connected alpha mass in every direction.
- Sailor Top: both side collar additions remain opaque; the mandatory rear panel retains at least 24 owned back cells and remains connected semantically to the collar/side handoff.
- Safe-envelope failures: 0.
- Structural survival failures: 0.
- Visual-change-contract failures: 0.
- Detached islands: 0.
- Unsupported row-zero cells: 0.
- Accidental long dark bands/rails: 0.
- Forbidden-direction component emissions: 0.

## Automated QC versus visual authority

Automated QC covers canonical/projection validation, binary alpha, one connected garment mass, parent-supported topology, safe envelopes, top-edge support, dark-band scanning, mandatory variant execution/minimums, forbidden directions, ownership rejection, protected-cell survival, and real final-frame alpha displacement.

It does **not** approve the visual result. The three supplied Farmer-scale rows are the review authority, so the final state is:

| Family | Automated QC | Human visual QC |
|---|---|---|
| Polo | PASS | PENDING |
| Sweater Vest | PASS | PENDING |
| Sailor Top | PASS | PENDING |

## Remaining literal coordinate logic

The V4.2 target variants keep their fixed logical offsets in versioned data. Their procedural code resolves anchors, row profiles, bounds, and topology operations generically.

Literal carrier-aligned coordinate logic still exists in the preserved V4.1/V3 fallback handlers, including the baseline collar mappings, the generic woven inner-shirt front exposure, and generic front/back armhole-binding sampling. Those paths were intentionally not rewritten in this proof. They are not named cleanup hacks, and the V4.2 target side shapes do not depend on them for topology.

## What should be generalized next

After human review of these three garments:

1. Move the remaining generic woven inner-front exposure and front/back armhole sampling into the same declarative variant schema.
2. Add a JSON Schema for shape/envelope documents and validate anchors, footprint containment, degradation tokens, and row profiles before compilation.
3. Generalize collision-free component cell allocation so intentional occlusion is declared in data rather than inferred from compiler order.
4. Add Farmer-fixture snapshot tests for anchor attachment and left/right reconstruction, while keeping human visual authority.
5. Only after this proof is accepted, consider a separate next family; do not combine that work with palette or rarity changes.

## Artifacts

The review sheets are:

- `output/v4-shape-proof/V4_2_SHAPE_LIBRARY_FARMER.png`
- `output/v4-shape-proof/V4_2_SHAPE_LIBRARY_ISOLATED_8X.png`
- `output/v4-shape-proof/V4_2_SHAPE_LIBRARY_BEFORE_AFTER.png`

Each garment directory contains the canonical model, projections, topology map, ownership ledger, semantic regions, pre-polish frame, post-polish merge result, final logical atlas/frames, Farmer composites, metrics, validation, and stage trace. `proof-summary.json` records the exact seeds and final two-part QC state.
