# Autonomous Generator Recovery Report

Status: **PASS_STATIC_DIRECT_VISUAL_REVIEW**. Pack: **PASS_STATIC_RUNTIME_NOT_TESTED**. Runtime: **NOT TESTED**.

## Active architecture

Normal recovery generation now follows `garment family -> coherent autonomous design concept -> structural validation and anti-convergence -> existing V5 carrier -> render_fs_hd_v2 -> V3 surface -> V4 -> V5B -> V5D when required -> reset named surface to permanent HD planes -> article construction adapter -> polish_upper_frames -> soften_shared_rear_neck -> semantic material/palette adapter -> Farmer composite`.

The frozen renderer and runtime contracts were not replaced. The flat `reference_grammar.render_controlled_garment` route and both premium-cardigan experimental profiles are absent from every stage trace. Native Farmer sleeves, `SleeveColors`, 16x16 logical directional frames, 16x64 atlases, Scale 2 and BodyPosition `(0,32)` remain intact.

## Autonomous design layer

`generator/autonomous_recovery/concept_engine.py` generates concrete, coordinate-free specifications from compatible family bundles. It chooses silhouette, fit, neckline/collar, opening, layering, hem, pockets/panels, sleeve relationship, side carrier, back carrier, color-block topology, restrained secondary construction, material and palette. Palette selection occurs after construction. Designs with vague axes, incompatible opening/layering, custom sleeves, or insufficient structural distance are rejected before raster work.

The anti-convergence gate requires at least three differing structural axes from every accepted item, including silhouette or opening/layering. Palette, name, buttons, motif and shading do not count. Each slot allows five concepts; failed render/static candidates are discarded rather than polished indefinitely.

## Accepted garments

| # | Garment | Family | Carrier | Material | Palette story |
|---:|---|---|---|---|---|
| 1 | Orchardline Tee | `FITTED_TEE` | `V5B_PLAIN_TEE` | `COTTON_TEE` | `WARM_EVERYDAY` |
| 2 | Ambergrain Pullover | `TEXTURED_KNIT` | `V5D_KNIT` | `KNIT` | `FOREST_LIBRARY` |
| 3 | Pollenridge Sweater Vest | `SWEATER_VEST` | `V5B_VEST` | `KNIT` | `EARTH_MOSS` |
| 4 | Lilac Crossing Cardigan | `OPEN_CARDIGAN` | `V5D_CARDIGAN` | `CARDIGAN` | `ROSEWOOD_PASTEL` |
| 5 | Coastlane Open Shirt | `OPEN_CASUAL_SHIRT` | `V5B_STRUCTURED_SHIRT` | `WOVEN_SHIRT` | `EVERYDAY_NEUTRAL` |
| 6 | Berrycloud Crew | `CREWNECK_SWEATSHIRT` | `V5B_SWEATER` | `SWEATSHIRT` | `SEA_GLASS` |
| 7 | Frostline Chore Jacket | `WORK_JACKET` | `V5D_WORK_SHELL` | `DENIM_WORKWEAR` | `WINTER_FROST` |
| 8 | Pearlwick Waistcoat | `FORMAL_WAISTCOAT` | `V5D_WAISTCOAT` | `BLAZER_FORMAL` | `FORMAL_PEARL` |
| 9 | Retroflare Zip Top | `TRACK_JACKET` | `V5D_FIELD_SHELL` | `SPORT_SHELL` | `BRIGHT_SPORT` |
| 10 | Silverleaf Salon Jacket | `FITTED_BLAZER` | `V5D_BLAZER` | `BLAZER_FORMAL` | `CEREMONIAL_IVORY` |
| 11 | Berryharbor Sailor Shirt | `SAILOR_TOP` | `V5B_SAILOR` | `WOVEN_SHIRT` | `COASTAL_MIST` |
| 12 | Seafig Polo Knit | `POLO_KNIT` | `V5B_STRUCTURED_SHIRT` | `WOVEN_SHIRT` | `SEA_GLASS` |

Every accepted recipe is saved both under `/run/media/deck/USD00/RNG_clothing/output/fashionsense/autonomous-generator-recovery` and beside its Fashion Sense Shirt. Front/right/back/left text is authored in each recipe. The adapters use family-specific carriers instead of forcing all designs through `STANDARD_JACKET`.

## Rejected concepts

- None. All first concepts passed semantic and static machine gates; direct image review remains the authoritative gate.

Machine rejection logs are at `/run/media/deck/USD00/RNG_clothing/output/fashionsense/autonomous-generator-recovery/rejected-concepts.json`. Direct visual inspection may still reject garments despite passing metrics; the Farmer sprite outranks JSON.

## Diversity and palette analysis

The batch spans closed cotton, continuous knit, sleeveless layered knit, open knit, open woven layering, ribbed sweatwear, heavy work shell, tailored waistcoat, athletic shell, tailored blazer, sailor collar, and partial-placket polo. Pairwise semantic checks: **66/66 PASS**. Palette stories include light, pastel, coastal, academic, denim, bright sport, formal, sailor and natural families; masculinity/unisex construction is not mapped to dark military color.

## Quality comparison and limitations

Alderwick remains the recovery anchor for specific construction, clean large shapes, side/back ownership and restrained decoration. Sunfield Pathfinder, Juniper Vale and Orchard Reserve remain prior V5E/V6 quality anchors on the comparison sheet. The new batch uses the same HD plane/polish backend rather than copying their designs.

Static Farmer composites do not simulate native `SleeveColors`, live arm animation, tool poses or Fashion Sense draw behavior. Therefore this work is **EXPERIMENTAL**, not `RUNTIME_PASS`. Remaining weak/unfilled carrier families: none among the twelve bounded recovery families; hoodies, long coats, pants and custom-sleeve families remain intentionally excluded.

## Recovery conclusion

Autonomous procedural generation is **RECOVERED AT THE STATIC DESIGN/RENDER LEVEL**. Direct inspection of the Farmer front and four-direction sheets found twelve identifiable reads rather than one repeated short jacket: the strongest are the sweater vest, open cardigan, chore jacket, waistcoat, track shell and blazer; the deliberately quiet tee is the weakest but remains a clean fitted tee rather than a flat role-grid prototype. Live Fashion Sense review is still required before runtime or production promotion.

## Outputs

- Pack: `/run/media/deck/USD00/RNG_clothing/test-packs/fashionsense/RNG-Clothing-Autonomous-Recovery`
- Accepted recipes: `/run/media/deck/USD00/RNG_clothing/output/fashionsense/autonomous-generator-recovery/accepted-recipes.json`
- Rejections: `/run/media/deck/USD00/RNG_clothing/output/fashionsense/autonomous-generator-recovery/rejected-concepts.json`
- Validation: `/run/media/deck/USD00/RNG_clothing/output/fashionsense/autonomous-generator-recovery/validation.json`
- Farmer fronts: `/run/media/deck/USD00/RNG_clothing/output/comparisons/AUTONOMOUS_RECOVERY_FARMER_FRONTS.png`
- Farmer four directions: `/run/media/deck/USD00/RNG_clothing/output/comparisons/AUTONOMOUS_RECOVERY_FARMER_DIRECTIONS.png`
- Gameplay sheet: `/run/media/deck/USD00/RNG_clothing/output/comparisons/AUTONOMOUS_RECOVERY_GAMEPLAY.png`
- Nearest-neighbor inspection: `/run/media/deck/USD00/RNG_clothing/output/comparisons/AUTONOMOUS_RECOVERY_NEAREST.png`
- Quality anchors: `/run/media/deck/USD00/RNG_clothing/output/comparisons/AUTONOMOUS_RECOVERY_QUALITY_COMPARISON.png`
