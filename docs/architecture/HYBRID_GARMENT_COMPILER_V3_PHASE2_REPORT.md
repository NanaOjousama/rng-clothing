# Hybrid Garment Compiler V3 — Phase 2 Report

Status: **PASS — CONTROLLED COMPILER/STATIC FARMER PROOF**  
Production feature flag: **OFF**  
Live Fashion Sense runtime status: **EXPERIMENTAL / NOT YET VERIFIED**

## 1. Frozen backend hash verification

All eight protected Phase 1 hashes matched before implementation and again after final validation:

| Protected contract | Result |
|---|---|
| `render_fs_hd_v2` | PASS |
| `render_fs_v3_surface` | PASS |
| `render_fs_v4` | PASS |
| `render_fs_v5b` | PASS |
| `render_fs_v5d` | PASS |
| `polish_upper_frames` / `soften_shared_rear_neck` | PASS |
| native sleeve contract | PASS |
| rarity renderer architecture | PASS |

No frozen V5/HD or runtime-contract file was modified. `HYBRID_GARMENT_COMPILER_V3_ENABLED` remains `false` and evaluates false without an explicit environment override.

## 2. Compiler files added or changed

Added:

- `specs/hybrid_garment_compiler/v3/carrier_capabilities.json`
- `generator/hybrid_v3/compiler/__init__.py`
- `generator/hybrid_v3/compiler/carrier_registry.py`
- `generator/hybrid_v3/compiler/component_compilers.py`
- `generator/hybrid_v3/compiler/semantic_regions.py`
- `generator/hybrid_v3/compiler/pixel_grammar.py`
- `generator/hybrid_v3/compiler/compiler_validation.py`
- `generator/hybrid_v3/compiler/stage_trace.py`
- `tools/generate_hybrid_v3_phase2.py`
- `tools/validate_hybrid_v3_phase2.py`

Changed:

- `generator/hybrid_v3/data.py` now loads the versioned carrier-capability document.

Generated output and test-pack files are isolated under `output/hybrid-v3-phase2`, `output/comparisons/HYBRID_V3_PHASE2_*`, and `test-packs/fashionsense/RNG-Clothing-Hybrid-V3-Phase2`.

## 3. Carrier-capability registry

There is no universal or `STANDARD_JACKET` fallback.

| Carrier | Accepted family | Native sleeve policy | Backend |
|---|---|---|---|
| `V5B_TEE_HD_V1` | `T_SHIRT` | required | V5B over V4/V3/HD |
| `V5B_POLO_HD_V1` | `POLO_SHIRT` | required | V5B over V4/V3/HD |
| `V5B_SWEATER_VEST_HD_V1` | `SWEATER_VEST` | inner-shirt/native color only | V5B over V4/V3/HD |
| `V5B_SAILOR_HD_V1` | `SAILOR_TOP` | required | V5B over V4/V3/HD |

The registry records supported components, direction operations, silhouette operations, runtime envelope, unsupported features, and exact backend route. Unsupported component/family combinations fail carrier selection.

## 4. Four connected families

- `T_SHIRT`: closed knit body, bound crew, native short sleeves, normal hem.
- `POLO_SHIRT`: inherited knit body plus folded collar and short front-only placket. Material remains `KNIT`, never `WOVEN_SHIRT`.
- `SWEATER_VEST`: sleeveless knit body, bound cut-in armholes, inner shirt, V binding, ribbed waist/hem.
- `SAILOR_TOP`: woven body, broad sailor front collar, compressed side continuation, mandatory full rear panel.

`CARDIGAN` and `BLAZER` were not connected.

## 5. Component compiler handlers

Handlers exist for the bounded Phase 2 component set:

`BODY`, `COLLAR`, `SLEEVE`, `ARMHOLE`, `OPENING`, `PLACKET`, `HEM`, `WAISTBAND`, `RIBBING`, `INNER_LAYER`, and `REAR_PANEL`.

Handlers receive existing canonical instances and Phase 1 projections. They do not decide whether anatomy exists. Native `SLEEVE` instances emit the proven `NATIVE_ANIMATED_SLEEVES_V1` contract, not a custom atlas.

## 6. Pixel-priority behavior

Mandatory identity is compiled ahead of secondary finishing:

- Polo: folded collar and short placket before hem/button accents.
- Vest: torso-connected body, cut-in armholes and V binding before inner exposure/rib rhythm.
- Sailor: broad collar and mandatory rear panel before hem finishing.
- Tee: coherent body and bound crew before restrained fit-plane articulation.

The compiler fails when a mandatory visible component produces neither pixels nor an approved native runtime component. It also fails if a component emits pixels in a `FORBIDDEN` direction.

## 7. Semantic pixel-region generation

Every result saves a region ledger containing:

- construction-system cells;
- per-cell fabric-role assignments;
- per-component emitted cells;
- architecture cells deliberately excluded by the compiler;
- native runtime component contracts.

This ledger is independent from the Phase 1 semantic flat. The flat remains debug-only and is never renderer input.

## 8. Palette and material reconnection

Palette stories are applied only after semantic pixel regions and HD polish exist. Primary, secondary, trim, and accent roles retain the proven shade ramps rather than becoming flat RGB regions.

Controlled proof assignments:

| Family specimens | Material | Palette stories |
|---|---|---|
| Tee | `COTTON_TEE` | `SPRING_ORCHARD`, `ROSEWOOD_PASTEL` |
| Polo | `KNIT` | `COASTAL_MIST`, `SEA_GLASS` |
| Sweater vest | `KNIT` | `CREAM_ACADEMIC`, `LAVENDER_DAY` |
| Sailor top | `WOVEN_SHIRT` | `SAILOR_NAVY`, `SNOWBERRY` |

No rarity-polish expansion was added.

## 9. Sweater-vest regression fixture

The inherited V5B vest carrier had six invalid side cells per direction:

- Right: `(2,0)`, `(3,0)`, `(4,0)`, `(0,1)`, `(1,1)`, `(0,2)`
- Left: `(11,0)`, `(12,0)`, `(13,0)`, `(14,1)`, `(15,1)`, `(15,2)`

These are excluded during canonical `BODY_KNIT_VEST` side topology compilation, before construction, polish, palette, or final validation. The rule keeps only torso-connected body mass and requires direct row-1 cloth support for top-row shoulder cells. This is not a post-render stray-pixel deletion.

Final vest result in every direction:

- exactly one connected alpha component;
- zero unsupported row-zero cells;
- no sleeve component;
- compiled side armhole signal present;
- no floating band, alpha island, or fake sleeve slab.

## 10. Sprite-integrity validation

Hard checks cover:

- canonical and projection validity;
- exact one-component final alpha;
- binary alpha;
- unsupported top-row cells;
- runtime coverage after only compiler-approved exclusions;
- mandatory identity emission;
- forbidden-direction emission;
- vest armhole signal and sleeve prohibition;
- 16×64 final atlas;
- Scale 2, BodyPosition `(0,32)`, correct direction offsets;
- native sleeves and no custom `SleevesId`;
- deterministic canonical model, projections, and final texture.

Final validator: `output/hybrid-v3-phase2/phase2-validation.json` — **PASS**, zero errors.

## 11. Farmer-fit results

All eight static Farmer composites passed the binary visual review:

- Tee: closed, simple tee read; no false opening.
- Polo: folded collar and localized short placket; sides show collar depth; back is uninterrupted.
- Vest: sleeveless knit layer with a clean side shoulder/armhole transition and no top artifact.
- Sailor: broad front collar, compressed side continuation, and clearly authored rear panel.

The two within-family Tee variations remain intentionally subtle. Vest inner-shirt exposure is compact at side scale but remains legible. These are limitations, not integrity failures.

Static Farmer composites do not prove live animation/runtime success. The pack remains experimental until in-game front/right/back/left and movement checks are completed.

## 12. Eight-garment QC table

| # | Garment | Intent / fit | Static QC | Farmer QC |
|---:|---|---|---|---|
| 1 | Orchard Essential Tee | `TEE_CLEAN_ESSENTIAL` / `UNISEX_REGULAR` | PASS | PASS |
| 2 | Rosewater Weekend Tee | `TEE_RELAXED_WEEKEND` / `UNISEX_BOXY` | PASS | PASS |
| 3 | Coastal Knit Polo | `POLO_CLASSIC` / `MASC_TAILORED` | PASS | PASS |
| 4 | Sea Glass Sport Polo | `POLO_COASTAL_SPORT` / `UNISEX_BOXY` | PASS | PASS |
| 5 | Ivory Academic Vest | `VEST_ACADEMIC` / `MASC_TAILORED` | PASS | PASS |
| 6 | Lavender Relaxed Vest | `VEST_RELAXED_KNIT` / `FEM_RELAXED` | PASS | PASS |
| 7 | Harbor Deck Sailor | `SAILOR_DECK_CLASSIC` / `UNISEX_REGULAR` | PASS | PASS |
| 8 | Snowberry Maritime Sailor | `SAILOR_SOFT_MARITIME` / `FEM_RELAXED` | PASS | PASS |

There are no final failed garments.

## 13. Stage diagnosis for failures found during implementation

Two development candidates were correctly rejected before final export:

1. **Vest side top cells** — canonical model and projection were correct; inherited carrier alpha did not match the compiled armhole topology. Cause stage: carrier-to-pixel-grammar mapping. Fix: bounded BODY/ARMHOLE carrier normalization before polish.
2. **Full dark center plane across closed families and Polo** — canonical model and semantic flat were correct; the reset carrier retained its permanent legacy `PLACKET` plane. Cause stage: pixel-grammar preparation, not renderer or palette. Fix: reuse `_remove_closed_opening_from_hd_regions` before V3 component compilation, then let only Polo emit its short placket.

No V5/HD renderer defect was found or modified.

## 14. Frozen backend confirmation

The post-build validation re-hashed all protected files and reproduced every Phase 1 digest exactly. The compiler does not call `reference_grammar.render_controlled_garment`, `PREMIUM_CARDIGAN_V1`, or `PREMIUM_CONSTRUCTION_CARDIGAN_V1`. It does not import custom sleeve generation.

## 15. Expansion readiness boundary

The Phase 2 boundary is technically ready to be reviewed for a later `CARDIGAN` + `BLAZER` expansion because:

- canonical/projected anatomy remains authoritative;
- unsupported carriers fail closed;
- inherited carrier anatomy can be explicitly neutralized before compilation;
- debug artifacts locate defects by stage;
- final sprites pass integrity, directional, deterministic, and static Farmer gates.

Expansion should not begin until human visual and live Fashion Sense testing of this eight-item pack is accepted. A future Phase 2 expansion would need new capability records and component handlers for cardigan opening/inner-layer topology and blazer collar/lapel/opening/rear-seam behavior; it must not fall back to the current four carriers.

## Artifact paths

- Experimental pack: `test-packs/fashionsense/RNG-Clothing-Hybrid-V3-Phase2/`
- Per-garment debug chains: `output/hybrid-v3-phase2/`
- Validator: `output/hybrid-v3-phase2/phase2-validation.json`
- All Farmer fronts: `output/comparisons/HYBRID_V3_PHASE2_ALL_FARMER_FRONTS.png`
- All directions: `output/comparisons/HYBRID_V3_PHASE2_ALL_DIRECTIONS.png`
- Isolated 8×: `output/comparisons/HYBRID_V3_PHASE2_ISOLATED_8X.png`
- Vest side QC: `output/comparisons/HYBRID_V3_PHASE2_SWEATER_VEST_SIDE_QC.png`
- Polo QC: `output/comparisons/HYBRID_V3_PHASE2_POLO_QC.png`
- Sailor QC: `output/comparisons/HYBRID_V3_PHASE2_SAILOR_QC.png`
