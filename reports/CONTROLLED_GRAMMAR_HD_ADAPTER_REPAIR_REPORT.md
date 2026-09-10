# Controlled Grammar HD Adapter Repair Report

Status: **PASS_STATIC_RUNTIME_NOT_TESTED**. Pack: **PASS_STATIC_RUNTIME_NOT_TESTED**. Runtime remains **NOT TESTED**.

## 1. Adapter and modules

- `generator/controlled_test/hd_adapter.py` is the bounded semantic adapter. It supports exactly `FITTED_TEE`, `OPEN_CARDIGAN`, and `WORK_JACKET`.
- `generator/controlled_test/hd_validation.py` adds finished-art gates and V5E/V6 anchor measurements.
- `tools/generate_controlled_grammar_hd_adapter_repair.py` exports only the three repaired specimens, previews, validation, and isolated test pack.
- `generator/renderers/fashionsense/reference_grammar.py` is marked `STRUCTURE_DEBUG_ONLY` / `FINAL_ART_ELIGIBLE = False`.
- The old twelve-item export command is hard-disabled. Its existing files remain archived but are not valid quality candidates.

No production renderer was rewritten.

## 2. Reused renderer stages

All three routes begin at `render_fs_hd_v2`, retaining HD region construction, edge exposure, gesture hierarchy, broad upper-left light planes, lower-right shadow masses, termination/cuff rules, binary alpha, and the body-coverage envelope. They then pass through V4/V5B article translation. Cardigan and work jacket additionally use existing V5D construction programs. Every item finally passes through `polish_upper_frames` before palette resolution.

- Tee: `render_fs_hd_v2 -> V3 surface/V4 -> V5B plain tee -> existing reset_v3_surface -> polish_upper_frames`.
- Cardigan: `render_fs_hd_v2 -> V4/V5B STANDARD_JACKET -> V5D CARDIGAN -> polish_upper_frames`.
- Work jacket: `render_fs_hd_v2 -> V4 SHORT_OUTERWEAR -> V5B utility_jacket -> V5D WORK_SHIRT construction -> polish_upper_frames`.

No custom Sleeves appearance is exported. Native Farmer arms remain authoritative.

## 3. Disabled regressed path

`reference_grammar.render_controlled_garment` remains available only for topology/debug visualization. `generate_controlled_grammar_palette_test.py` now exits immediately instead of exporting its flat role grid as final art.

## 4. Semantic mapping

- `FITTED_TEE` maps to the existing fitted Shirt/plain-tee translator, crew binding, closed single layer, short native sleeves, and clean normal termination. Inherited V3 decoration is removed with the existing reset helper; no replacement motif or center stripe is added.
- `OPEN_CARDIGAN` maps to the existing soft STANDARD_JACKET base plus V5D's broad inner field, two knit edges, lower pockets, side hanging edge, coherent rear neck band, and ribbed termination.
- `WORK_JACKET` maps to the existing boxy SHORT_OUTERWEAR/utility-jacket base plus V5D's work collar, firm placket, paired practical pockets, straight termination, side pocket carrier, and broad rear yoke.

## 5–6. Palette and material behavior

The adapter does not paint one RGB across a semantic fabric region. Existing HD mask roles map as follows: exterior contour → `DeepShadow`; deep crease/structural edge → the `DeepShadow`/`StructuralDark` ramp; shadow/base/light/highlight → material-spaced `PrimaryFabric` ramps. Fixed layer fields map into `SecondaryFabric`, `Trim`, or `Accent`, with their own positional light/base/shadow treatment.

Material policy changes actual shade pixels: cotton uses moderate spacing, cardigan compresses its fabric ramp for softer knit transitions, and denim expands shadow/light separation for a firmer shell. Every specimen records the chosen policy, affected shade-cell count, and proven mask-role counts in its summary and validation. The material gate requires both a non-generic policy and at least 24 affected pixels; all three pass.

## 7. Quality metrics

| Grammar | Material | Palette | Dominant front fill | Light plane | Shadow plane | Structural dark | Front/back difference | Result |
|---|---|---|---:|---:|---:|---:|---:|---|
| `FITTED_TEE` | `COTTON_TEE` | `SPRING_ORCHARD` | 48.6% | 25 | 48 | 41 | 11.5% | PASS |
| `OPEN_CARDIGAN` | `CARDIGAN` | `LAVENDER_DAY` | 29.4% | 15 | 29 | 75 | 42.1% | PASS |
| `WORK_JACKET` | `DENIM_WORKWEAR` | `DENIM_BLUE` | 29.0% | 19 | 43 | 82 | 40.1% | PASS |

The regressed Orchard front was 91.5% one fill. The repaired tee is below the 65% simple-garment ceiling and carries full light, shadow, crease, and contour planes without adding decoration.

## 8. V5E/V6 anchor comparison

| Prior anchor | Active front colors | Dominant front fill | Luminance range |
|---|---:|---:|---:|
| Sunfield Pathfinder Jacket | 11 | 27.3% | 189.96 |
| Juniper Vale Cardigan | 8 | 29.4% | 181.59 |
| Orchard Reserve Workshirt | 10 | 25.2% | 182.15 |

The anchor comparison is contextual rather than a demand that a minimal tee match Rare feature count. All repaired garments reuse the same underlying HD shade-role and polish logic. Cardigan/work jacket meet the richer construction gates; the tee meets a stricter simplicity-aware dominant-fill ceiling while retaining meaningful form planes.

## 9. Farmer composites

Static worn review shows three distinct reads: a fitted closed tee; a soft open cardigan with a broad inner shirt; and a boxy work shell with pockets/placket/yoke. Front/right/back/left reconstructions are exported. The Farmer composite is still a static idle approximation; native SleeveColors and motion require live Fashion Sense testing.

## 10. Unresolved issues

- Static previews cannot prove walk, tools, sitting, horse, or multiplayer behavior.
- Native Farmer geometry limits visible cardigan sleeve volume; no unsafe custom atlas was introduced.
- The work jacket uses the proven workwear construction program over a heavier outerwear base. Live review must confirm that shell weight survives animation.
- The palette output is fixed-color (`DisableGrayscale: true`) for this adapter proof; dye/customization integration is intentionally deferred.

## 11. Expansion decision

The adapter is structurally safe to review for expansion because it leaves production renderers untouched and explicitly allowlists three grammars. It should **not** expand until live Farmer review confirms these three. Future grammars should add semantic mappings into existing article/construction programs, not new rasterizers.

## Outputs

- Test pack: `/run/media/deck/USD00/RNG_clothing/test-packs/fashionsense/RNG-Clothing-Controlled-Grammar-HD-Adapter-Repair`
- Per-garment output: `/run/media/deck/USD00/RNG_clothing/output/fashionsense/controlled-grammar-hd-adapter-repair`
- Isolated directions: `/run/media/deck/USD00/RNG_clothing/output/comparisons/CONTROLLED_GRAMMAR_HD_ADAPTER_DIRECTIONS.png`
- Farmer directions: `/run/media/deck/USD00/RNG_clothing/output/comparisons/CONTROLLED_GRAMMAR_HD_ADAPTER_FARMER_DIRECTIONS.png`
- Gameplay fronts: `/run/media/deck/USD00/RNG_clothing/output/comparisons/CONTROLLED_GRAMMAR_HD_ADAPTER_GAMEPLAY.png`
- Old/debug versus repaired: `/run/media/deck/USD00/RNG_clothing/output/comparisons/CONTROLLED_GRAMMAR_HD_ADAPTER_OLD_VS_REPAIRED.png`
- Validation: `/run/media/deck/USD00/RNG_clothing/output/fashionsense/controlled-grammar-hd-adapter-repair/static-validation.json`

Stop state: exactly three repaired garments; no rarity, additional grammar, custom sleeve, or production-batch work was performed.
