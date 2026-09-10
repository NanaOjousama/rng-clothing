# Controlled Grammar + Palette Implementation Test

Status: **PASS_STATIC_RUNTIME_NOT_TESTED**. Runtime status: **NOT TESTED**. These twelve appearances remain **EXPERIMENTAL**.

## Shared implementation

This phase adds a bounded semantic recipe assembler, a direct-logical-pixel Fashion Sense renderer for only the approved twelve grammars, structural/directional validation, pairwise diversity validation, Farmer compositing, and an isolated test-pack exporter. It does not alter rarity or enable open-ended generation.

Every appearance uses the proven Fashion Sense 7.5 Shirt contract: 16×16 logical frames, Scale 2, BodyPosition `(0,32)`, native animated Farmer sleeves through three `SleeveColors`, `HideSleeves: false`, and no custom Sleeves atlas. The renderer first authors silhouette, collar, opening/layering, hem, and directional carriers, then resolves semantic palette roles and applies restrained material finishing.

## Specimens

| # | Garment | Grammar | Material | Palette story | Farmer-composite review |
|---:|---|---|---|---|---|
| 01 | Orchard Bound Tee | `FITTED_TEE` | `COTTON_TEE` | `SPRING_ORCHARD` | Clear fitted basic; quiet side/back are appropriate. |
| 02 | Mistshore Open Shirt | `OPEN_CASUAL_SHIRT` | `WOVEN_SHIRT` | `COASTAL_MIST` | Two leaves and broad inner tee survive front; side keeps one open edge. |
| 03 | Lavender Hearth Cardigan | `OPEN_CARDIGAN` | `CARDIGAN` | `LAVENDER_DAY` | Soft open knit and pockets read; loose sleeve volume remains runtime-limited. |
| 04 | Cream Ledger Sweater Vest | `SWEATER_VEST` | `KNIT` | `CREAM_ACADEMIC` | Bound armhole/V and inner shirt separate it from a plain knit. |
| 05 | Pearl Line Waistcoat | `FORMAL_WAISTCOAT` | `BLAZER_FORMAL` | `FORMAL_PEARL` | Deep formal V, button rhythm, welt cues, and pointed hem read distinctly. |
| 06 | Rosewood Sunday Crew | `CREWNECK_SWEATSHIRT` | `SWEATSHIRT` | `ROSEWOOD_PASTEL` | Boxy mass and ribbed terminations separate it from the fitted tee. |
| 07 | Bluebolt Cropped Bomber | `CROPPED_BOMBER` | `BOMBER_OUTERWEAR` | `BRIGHT_SPORT` | Rounded crop, shoulder block, zip, pocket cue, and gathered band read strongly. |
| 08 | Indigo Foundry Work Jacket | `WORK_JACKET` | `DENIM_WORKWEAR` | `DENIM_BLUE` | Firm box, large pockets, side pocket depth, and rear yoke read as workwear. |
| 09 | Midnight Column Blazer | `FITTED_BLAZER` | `BLAZER_FORMAL` | `FORMAL_MIDNIGHT` | Lapel hierarchy and tailored rear carrier read; side remains deliberately restrained. |
| 10 | Seaglass Crosswrap Top | `WRAP_TOP` | `WOVEN_SHIRT` | `SEA_GLASS` | Diagonal overlap is geometry-first and survives front/right reconstruction. |
| 11 | Harbor Sail Collar Top | `SAILOR_TOP` | `WOVEN_SHIRT` | `SAILOR_NAVY` | Large rear collar is the strongest non-front carrier in the set. |
| 12 | Emberpath Belted Tunic | `BELTED_TUNIC` | `WOVEN_SHIRT` | `SUN_EMBER` | Belt and split fall read, but safe Shirt bounds limit apparent length. |

## Structural separation

Neighboring garments do not use color as their primary distinction. The tee is a fitted closed single mass; the open shirt has two woven leaves and a broad inner tee; the cardigan has soft knit edges and pockets; the sweater vest uses bound armholes over native shirt sleeves; the waistcoat uses a tailored deep V, buttons, welt pockets, and shaped points. The sweatshirt is soft and boxy; the bomber is short and rounded with a gathered band; the work jacket is a firm box with large patch pockets and rear yoke; the blazer uses lapel masses, tailored waist, and rear vent. The wrap is diagonally overlapped, the sailor top is carried by its front/rear collar, and the tunic uses a belt, longer-looking upper-safe fall, and split termination.

The automatic 66-pair gate passed. Maximum shared semantic dimensions: **2/10**. No pair shares seven dimensions, and no pair shares silhouette + opening + layering. Numeric checks are guardrails; the exported worn Farmer sheet was also reviewed at native gameplay scale.

## Runtime risk and limitations

No custom sleeve workaround was used. BELTED_TUNIC stays entirely inside the known-safe Shirt frame and implies length with belt/termination topology; it does not draw rigid geometry over moving legs. Static Farmer composites cannot prove walking, tools, sitting, horse, recolor UI, or multiplayer behavior. Side silhouettes are constrained by the same safe upper-body footprint, so runtime review should focus on whether soft/boxy/cropped/tailored differences survive animation.

No grammar was declared impossible in this bounded proof. The most constrained are BELTED_TUNIC (safe bounds limit apparent length) and OPEN_CARDIGAN (native arm geometry limits loose sleeve volume). Neither was expanded with an unsafe layer.

The closest worn comparisons are FITTED_TEE versus CREWNECK_SWEATSHIRT (both closed single-fabric tops, separated by fitted versus boxy mass and clean versus ribbed hem) and SWEATER_VEST versus FORMAL_WAISTCOAT (both layered sleeveless outer frames, separated by knit binding versus tailored opening, buttons, pockets, and shaped points). These are acceptable in the static Farmer sheet but deserve explicit live review. The matrix uses exact semantic-axis equality and therefore does not replace this visual judgment.

## Outputs

- Test pack: `/run/media/deck/USD00/RNG_clothing/test-packs/fashionsense/RNG-Clothing-Controlled-Grammar-Palette-Test`
- Per-specimen assets and recipes: `/run/media/deck/USD00/RNG_clothing/output/fashionsense/controlled-grammar-palette-test`
- Gameplay fronts: `/run/media/deck/USD00/RNG_clothing/output/comparisons/CONTROLLED_GRAMMAR_PALETTE_FARMER_FRONTS.png`
- Four-direction Farmer composites: `/run/media/deck/USD00/RNG_clothing/output/comparisons/CONTROLLED_GRAMMAR_PALETTE_FARMER_DIRECTIONS.png`
- Enlarged isolated art: `/run/media/deck/USD00/RNG_clothing/output/comparisons/CONTROLLED_GRAMMAR_PALETTE_ISOLATED_4X.png`
- Pairwise matrix: `/run/media/deck/USD00/RNG_clothing/output/comparisons/CONTROLLED_GRAMMAR_PALETTE_DIVERSITY_MATRIX.png`
- Validation: `/run/media/deck/USD00/RNG_clothing/output/fashionsense/controlled-grammar-palette-test/static-validation.json`
- Pack validation: `/run/media/deck/USD00/RNG_clothing/test-packs/fashionsense/RNG-Clothing-Controlled-Grammar-Palette-Test/static-validation.json`

## Live review

Install only the dedicated pack, then test each numbered preset front/right/back/left, walk, run, and use a tool. Confirm native arms remain attached, nothing appears near the feet, side/back carriers stay readable, and each article is identifiable without its preset name. No appearance should be promoted based on this static pass.
