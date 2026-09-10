# V5C2 Vanilla Clothing Study + Hoodie Reconstruction

## Outcome

V5C2 is statically complete as an **experimental** upper-garment quality pass. It fixes the known missing-arm contract, studies the installed Stardew Valley 1.6.15 shirt renderer and 54 representative vanilla shirts, formalizes a Hoodie article family, and generates exactly ten direct-logical-pixel Fashion Sense appearances.

The result is materially clearer than V5B: the revised garments use article-specific openings, yokes, pockets, hood masses, hems, and focal clusters rather than depending mainly on palette and shading. It is not yet honest to claim universal community-pack parity. Nightgarden, Cloudberry, Copperleaf, and the two jackets are the strongest static results; Harbor Haze is intentionally quiet, and Sproutwing's small focal mark remains the most gameplay-scale-sensitive design.

All ten items remain `EXPERIMENTAL / NOT_TESTED`. Static checks do not establish walk, tool, sitting, horse, or multiplayer behavior.

## Blocking defect: missing Duskline arm

### Exact cause

The V5B sleeveless path set `HideSleeves: true` on Duskline Waistcoat. In Fashion Sense 7.5.0, `AppearanceHelpers.AreSleevesForcedHidden` scans all equipped appearance metadata and returns true if **any** model requests `HideSleeves`. That is a global sleeve/arm suppression decision; it does not merely hide a small native shirt cuff. Consequently the selected Sleeves layer could not restore the arm, producing an invisible arm state.

### Shared correction

- `SLEEVELESS` now uses a generated full-motion Sleeves companion whose garment-mask cells are translated to Fashion Sense skin-tone masks.
- `HideSleeves` remains false on every V5B/V5C2 Shirt model.
- The validator rejects any V5C2 appearance with `HideSleeves != false`, a missing companion, an incomplete direction animation, or an empty/out-of-contract atlas.
- The original V5B pack was regenerated; Duskline now has a paired skin-tone animated arm companion.
- The new Slate & Saffron Waistcoat uses an explicitly sleeved inner shirt and a coordinated fitted-long-sleeve companion, so its article concept does not rely on bare-arm suppression.

This proves the content contract is no longer asking Fashion Sense to remove the arm. It does **not** pre-fill runtime PASS; Duskline/Slate still need the focused in-game matrix in `reports/V5C2_RUNTIME_TEST_CHECKLIST.md`.

## Installed vanilla technical study

### Authority inspected

- Installed game: Stardew Valley 1.6.15.
- `Content/Data/Shirts.xnb`, SHA-256 `f7853b9cb4612accea8b0aa6585a88fb6fa0853643ec81748a88b51964a9d08e`.
- `Content/Characters/Farmer/shirts.xnb`, SHA-256 `61d9e8a7d6342c4e05da3d2c56684a6c97b3ede86ae2138643a5f72a2718f640`.
- Extracted shirt sheet: 256×608 RGBA, SHA-256 `15c4ba90946be78be468d387afb7b20bfb2382e65acef88ddf22b8509f864fc8`.
- Installed `FarmerRenderer`, `Clothing`, and `ShirtData` implementations were decompiled and inspected.
- The Stardew Wiki shirt and Farmer-sprite modding pages were used as orientation references; installed 1.6.15 behavior remained authoritative.

The installed data contains 303 shirt entries. The study sampled 54 named shirts / 216 directional frames across early article signals, jackets/layers, vests/workwear, formal/blouse, knit/hoodie, uniform/outerwear, late vests/jackets, patterns/motifs, and graphic/rhythm designs. The reproducible study output is `output/research/v5c2/vanilla_clothing_metrics.json`; its visual contact sheet is `output/research/v5c2/VANILLA_CLOTHING_DESIGN_STUDY.png`.

### Confirmed renderer contract

- Each vanilla shirt direction is an 8×8 logical frame.
- Direction rows are front/down at Y+0, right at Y+8, left at Y+16, and back/up at Y+24.
- The dye half is selected by adding 128 source pixels horizontally.
- `ApplySleeveColor` obtains sleeve colors from the shirt texture; `HasSleeves=false` causes skin-color substitution instead.
- Animation belongs primarily to the Farmer body/arms. Vanilla does not generate independently articulated high-detail shirt art.

### Aggregate evidence

Across the 54-shirt sample:

| Property | Minimum | Median | Maximum |
|---|---:|---:|---:|
| Opaque cells per direction | 51 | 57.5 | 64 |
| Visible colors per direction | 3 | 7 | 11 |
| Luminance span | 21.36 | 163.96 | 224.93 |
| Dominant-color share | 18.75% | 32.26% | 67.74% |
| Row color transitions | 16 | 34 | 50 |
| Front alpha symmetry | 96.88% | 100% | 100% |
| Front/back alpha overlap | 87.5% | 93.75% | 100% |

These figures are descriptive, not beauty scores.

## Generalized vanilla design grammar

### Silhouette economy

- Vanilla changes very little alpha geometry: article identity often comes from two or three high-value internal regions rather than a radical outline.
- Stable shoulder/body mass creates animation reliability. A small lower-edge cut, neck recess, or side compression can carry silhouette identity when paired with a stronger construction cue.
- Near-symmetry is the norm for the front body envelope. Asymmetry is usually reserved for a motif or a small construction feature.

### Article identity

- **Jacket:** separated outer panels + a visible inner layer/opening + a decisive collar/lapel cue. Pockets/buttons are subordinate.
- **Vest/waistcoat:** high-contrast inner shirt + descending V/opening + narrow closure; the arm relationship must be explicit.
- **Blouse:** broad neckline/collar/yoke signal + a soft focal cluster; merely changing the side shade of a button shirt is insufficient.
- **Formalwear:** a small, high-contrast neck/center arrangement and quiet lower body communicate tailoring economically.
- **Sweater/knit:** uninterrupted cloth mass, substantial neckline, wrapped yoke/pattern, and a coherent ribbed termination.
- **Sailor/tunic/workwear:** one large upper or center construction region survives more reliably than several isolated marks.

### Pattern and pixel economy

- Useful patterns form bands, center arrangements, or paired blocks. They attach to garment topology instead of floating evenly over the torso.
- Vanilla often spends one tiny connected cluster on the identifying graphic and allows the rest of the garment to remain calm.
- Dark values establish silhouette/overlap; internal seams are usually weaker. Clean clusters beat peppered detail.
- Strong value separation does more work than adding near-duplicate colors.

### Directional reconstruction

- The side view compresses or terminates a front opening; it does not preserve every front detail.
- Front-only graphics disappear or reduce at the side.
- Back views preserve article identity through hood/yoke/collar/hem structure and are usually quieter than the front.
- Wrap features such as a yoke or ribbed hem continue around the body; pockets and central motifs terminate intentionally.

### Collectible appeal

Vanilla's charm comes from fast recognition, decisive color relationships, and one memorable cue. The garment is not required to fill every available cell. For the 16×16 backend, extra resolution is useful only when it improves construction, topology, or a coherent focal cluster.

## Community and hoodie corpus study

`style-profiles/hoodie.zip` contains two primary photographic design boards plus 136 supporting paths. Its reusable evidence includes:

- separate pullover, unzipped, pouch, baggy, and baggy-pouch bodies;
- hood-up, hood-down, and weather/dynamic hood concepts;
- pullstrings as a separable construction cue;
- a full animated Sleeves appearance rather than stretched Shirt-arm pixels;
- multiple simpler shirt-sheet hoodies and seasonal/hood-position variants.

Older included pack JSON was treated as historical design/runtime evidence only. Fashion Sense 7.5.0 source remains authoritative.

### `hoodie_design1.png` traits

The board mixes soft neutral/green/lavender hoodies and sweatshirts, varied standard/cropped/oversized proportions, drawstrings, quiet bodies, small whimsical graphics, and occasional larger front graphics. Its appeal comes from the contrast between a comfortable broad mass and one controlled personal focal mark—not from dense texture.

### `hoodie_design2.png` traits

The board emphasizes oversized dark/neutral sweatshirts, strong ribbed edges, restrained tonal palettes, and a larger ornate central crest/botanical geometry. The focal area is richer, but it remains a connected central composition with substantial empty cloth around it.

### Supporting strong-pack lessons

- Hood mass must be visible on the back and side, not represented only by front drawstrings.
- Zip, pouch, crop, and body volume are independent design axes.
- Small details should attach to a hood edge, opening, pouch, cuff, ribbing, or graphic cluster.
- Extra resolution pays for clean hood depth, pocket boundaries, zipper rhythm, and readable motifs—not texture noise.

No community/reference pixels, text graphics, motifs, or palettes are loaded by the generator.

## Permanent V5C2 grammar changes

- Added a coordinate-free Hoodie article with `pullover`, `zip`, `pouch_contrast`, `cropped_charm`, and `baggy_crest` subtypes.
- Added semantic hood state, volume, lining, and drawstring intent. V5C2 supports hood-down; hood-up is explicitly deferred because it needs a coordinated Fashion Sense Hat companion.
- Added article signals for waistcoat V/opening, blouse yoke, knit yoke/ribbing, jacket opening/pockets/yoke, and four-view hood mass.
- Added shading-independent design-interest floors and article-specific construction gates.
- Added direct structural/surface signatures so the five hoodie subtypes cannot validate as recolors of the same composition.
- Added a reference boundary: the renderer cannot read hoodie.zip, vanilla sprites, or benchmark PNGs.
- Preserved the proven 16×16, Scale 2, `BodyPosition (0,32)`, body-coverage envelope, direct logical pixels, and coordinated animated Sleeves architecture.

## Ten generated diagnostics

| # | Garment | Rarity | Article identity / primary idea |
|---:|---|---|---|
| 1 | Slate & Saffron Waistcoat | Common | V opening, visible inner shirt, narrow buttoned placket, fitted sleeves |
| 2 | Roseglass Yoke Blouse | Uncommon | Broad rounded yoke, attached ribbon cluster, soft fitted waist |
| 3 | Copperleaf Hearth Knit | Rare | Heavy knit mass, wrapped leaflike yoke, substantial neck, ribbed finish |
| 4 | Kestrel Cropped Field Jacket | Uncommon | Short outer shell, visible inner layer, lapels, paired pocket tabs |
| 5 | Pinewatch Field Jacket | Rare | Structured opening, field yoke, utility pockets, finished hem |
| 6 | Harbor Haze Pullover | Common | Quiet pullover, readable hood ring, strings, broad ribbing |
| 7 | Rainline Zip Hoodie | Uncommon | Compact hood plus dominant zipper/opening rhythm |
| 8 | Cloudberry Pouch Hoodie | Uncommon | Contrast hood lining, relaxed body, large connected pouch |
| 9 | Sproutwing Cropped Hoodie | Rare | Cropped form, pouch seam, contrast hood, original small sprout-wing focal cluster |
| 10 | Nightgarden Crest Hoodie | Rare | Baggy mass, broad hood, ribbing, original connected tonal garden crest |

### Reconstruction boundary

Sproutwing reconstructs the first board's soft/cropped/small-charm appeal using an original winged-sprout geometry and a different construction/palette. Nightgarden reconstructs the second board's oversized/tonal/central-crest appeal using an original abstract garden crest. Neither reproduces clothing text, a photographed graphic, an exact palette, or a source outfit layout.

The first Sproutwing render clipped the far side of its small motif and reduced it to an L-shaped mark. The internal art review rejected that pass; the final renderer keeps the complete connected 5×5 cluster inside the side-chest cloth region.

## Static validation

`tools/validate_generator_v5c2.py` reports PASS:

- exactly ten appearances and five hoodie subtypes;
- deterministic recipes, Shirt textures, and Sleeves atlases;
- 16×16 logical Shirt frames in a 16×64 sheet;
- Scale 2 and `BodyPosition (0,32)` in every direction;
- front/right/left/back source rows Y=0/16/32/48;
- binary alpha and no resampling path;
- ten 384×1344 full-motion Sleeves atlases with complete direction animation mappings;
- `HideSleeves=false` on every Shirt;
- no body-coverage gaps detected;
- valid paired outfit presets;
- no Pants/Shoes/Accessories/Hats leakage;
- generation code does not read reference pixels.

Regression validation also passes for Generator V3, V4, and V5B. V4 retains its pre-existing warnings about some same-article silhouette sharing and cross-article quality spread; V5C2 did not introduce them.

## Critical art review

### Strongest

- **Nightgarden Crest Hoodie:** clearest use of the 16×16 budget for an authored focal composition while retaining large quiet cloth regions.
- **Cloudberry Pouch Hoodie:** strongest immediate hoodie subtype read; hood lining and pouch have distinct jobs.
- **Copperleaf Hearth Knit:** yoke and ribbing communicate knit construction without relying on shading.
- **Pinewatch Field Jacket:** opening/yoke/pockets/hem survive the gameplay-footprint preview as a layered outer article.

### Weakest / remaining limits

- **Harbor Haze Pullover** is intentionally the calm Common baseline. It is readable, but its collectible appeal depends on color and hood shape more than the other outputs.
- **Sproutwing Cropped Hoodie** is improved after the clipped-motif correction, but its small charm is still more vulnerable to monitor zoom and in-game background contrast than Nightgarden's central crest.
- The 16×16 Shirt topology can describe a hood-down neck/back mass but cannot make a convincing hood-up silhouette without a Hat companion.
- Static previews do not prove that the custom Sleeve atlas remains visually perfect during every tool/sit/horse frame.
- Fixed accent regions are coordinated with the palette story, while Fashion Sense's current simple recolor layer primarily targets the main cloth. This milestone does not overbuild multi-channel dye UX.
- Article differences are materially better, but some shoulder/body envelopes remain intentionally conservative because body coverage and animation compatibility outrank silhouette novelty.

## Runtime risks and recommended test subset

Highest risk remains the coordinated custom Sleeves layer during non-idle animation. Body mods can also alter the expected shoulder/arm relationship. Test:

1. Slate & Saffron Waistcoat — blocking missing-arm regression.
2. Kestrel Cropped Field Jacket — rolled cuff and cropped shell.
3. Harbor Haze Pullover — simplest hood baseline.
4. Rainline Zip Hoodie — opening continuity.
5. Cloudberry Pouch Hoodie — pouch/side termination.
6. Sproutwing Cropped Hoodie — crop plus motif at gameplay size.
7. Nightgarden Crest Hoodie — baggy/crest direction handling.

Use `reports/V5C2_RUNTIME_TEST_CHECKLIST.md`. No garment should advance beyond `EXPERIMENTAL` before that evidence is recorded.

## Outputs

- Generator grammar: `generator/data/v5c2/upper_quality_grammar.json`
- Semantic schema: `generator/schema/garment_recipe_v5c2.schema.json`
- Recipe/design engine: `generator/v5c2/`
- Renderer: `generator/renderers/fashionsense/upper_v5c2.py`
- Vanilla study tool: `tools/analyze_vanilla_clothing_v5c2.py`
- Generation tool: `tools/generate_v5c2_vanilla_hoodie.py`
- Independent validator: `tools/validate_generator_v5c2.py`
- Recipes: `output/recipes/v5c2_vanilla_hoodie_diagnostics.json`
- Appearance outputs and comparisons: `output/fashionsense/v5c2-vanilla-hoodie/`
- Cross-version comparisons: `output/comparisons/V5C2_*.png`
- Test pack: `test-packs/fashionsense/RNG-Clothing-V5C2-Vanilla-Hoodie/`

## Bottom line

V5C2 clears the static technical bar and materially improves article grammar. It demonstrates that hoodie variety can come from hood mass, opening, pouch, crop, volume, ribbing, and focal composition rather than five recolors of a sweater. The best outputs meet the intended vanilla-clarity / higher-detail-craftsmanship direction. The batch as a whole is not promoted to art or runtime PASS: the simple Common and small-charm Rare still need gameplay-size user judgment, and the shared custom Sleeves path needs the requested in-game motion test.
