# Generator V1 completion report

Generator version: `1.0.0`  
Deterministic seed: `202608281615`  
Scope: vanilla Stardew Valley shirts only.

## 1. Vanilla shirt grammar learned

V1 was grounded in 34 installed vanilla shirts (136 direction frames). The sample established the recurring connected 53–64-pixel garment field, centered shoulder/neck gap, compressed side geometry, simpler backs, edge/under-collar shadows, attached highlight clusters, sparse accents, and a median six rendered colors. Exact evidence and limits are in `reports/VANILLA_SHIRT_GRAMMAR.md` and `generator/data/vanilla_shirt_grammar.json`.

## 2. Archetypes implemented

Exactly five semantic archetypes exist: `T_SHIRT`, `SWEATER`, `BUTTON_SHIRT`, `JACKET`, and `SAILOR_TOP`. Each data file declares valid necklines, collars, closures, fits, details, patterns, directional structure, shading intent, and incompatibilities. Recipes never contain coordinates.

## 3. Palette and shading approach

Eight authored Lifestyle palette families are available. Main fabric uses the single native grayscale dye mask with a five-step restrained ramp; Common items collapse the brightest step to keep their palette smaller. Secondary cloth and one optional accent remain protected in the base half. No RGB auto-lightening, gradients, antialiasing, resampling, high-resolution source art, or downscaling occurs.

## 4. Recipe compatibility system

Components carry archetype allowlists, requirements, and exclusions. The validator rejects invalid collar/neckline, closure/detail, layer/pattern, accent, rarity, and two-detail combinations before rendering. The batch also enforces minimum semantic and visible-structure distance within each archetype.

## 5. Twenty generated recipes

The deterministic batch contains exactly 20 compatible Lifestyle recipes: four per archetype, spanning all eight palette families and Common/Uncommon/Rare. Exact duplicates: 0; near-duplicate structures: 0.

See `output/recipes/lifestyle_v1_recipes.json` and `reports/RECIPE_BATCH_V1.md`.

## 6. Five selected and why

The selection is one recipe per archetype: Bluebell Pin Tee, Hearth Ribbed Sweater, Cedar Button Shirt, Mistral Layer Jacket, Garnet Pin-Collar Top. It deliberately varies palette, neck/closure landmark, construction mass, rarity, and visible detail. The sweater and button shirt use quieter Common recipes so the final set does not mistake extra stripes for quality; the jacket and sailor top carry the denser layered/collar tests.

## 7. Rendered shirts

| Shirt | Archetype | Rarity | Palette | Validation | Rejection score* |
|---|---|---|---|---|---:|
| Bluebell Pin Tee | T_SHIRT | Uncommon | denim_cream | PASS | 100.0 |
| Hearth Ribbed Sweater | SWEATER | Common | rust_brown | PASS | 100.0 |
| Cedar Button Shirt | BUTTON_SHIRT | Common | warm_neutral | PASS | 100.0 |
| Mistral Layer Jacket | JACKET | Rare | cool_neutral | PASS | 100.0 |
| Garnet Pin-Collar Top | SAILOR_TOP | Rare | charcoal_burgundy | PASS | 100.0 |

*The score only summarizes obvious-failure checks. It does not prove beauty.

## 8. Validation results

Overall static result: **PASS**.

- every native PNG is exactly 256×32 RGBA8 with only alpha 0/255;
- all art is authored directly on four 8×8 logical grids;
- base frames occupy `x=0..7`, dye masks occupy `x=128..135`, with no spill or V1 overlap;
- front/right/left/back sit at `y=0/8/16/24`;
- dye masks are grayscale and use only the declared ramp;
- front sleeve sample cells are opaque and ordered dark/mid/light for the installed 1.6.15 renderer;
- every garment is connected, within occupied/color/accent budgets, and directionally consistent;
- every 8× preview is verified exact nearest-neighbor replication of the saved native PNG;
- the Content Patcher pack contains exactly five loads and five localization-ready `Data/Shirts` entries;
- pack PNGs are byte-identical to the approved output PNGs.

Not confirmed: actual in-game loading, movement/tool offsets, extreme dye choices, save/reload, or multiplayer. Static validation cannot substitute for those tests.

## 9. Files created

- grammar/component/palette/budget data under `generator/data/`;
- individual recipe schema at `generator/schema/garment_recipe.schema.json`;
- deterministic Python pipeline under `generator/`;
- independent checker at `tools/validate_generator_v1.py`;
- 20-recipe batch under `output/recipes/`;
- five native PNGs, five exact 8× sheet previews, five labeled direction contacts, and validation JSON under `output/vanilla/v1/`;
- one isolated Content Patcher pack under `test-packs/vanilla/RNG-Clothing-V1/`;
- grammar, recipe-batch, and V1 reports under `reports/`.

No Farmer composite was created. The installed Farmer base is an XNB, and the available unpack helper required a graphics device unavailable in this isolated environment. Using a Fashion Sense body, a modded body, or a reference-image Farmer would have invented a non-authoritative alignment. The labeled native contacts are therefore the honest preview boundary for V1.

## 10. Test-pack installation

Copy the entire folder:

```text
test-packs/vanilla/RNG-Clothing-V1/
```

into your normal Stardew Valley `Mods` directory, then launch through SMAPI. This project did not copy or install it automatically.

Use these SMAPI console commands:

```text
player_add (S)RNGClothing.V1.BluebellPinTee
player_add (S)RNGClothing.V1.HearthRibbedSweater
player_add (S)RNGClothing.V1.CedarButtonShirt
player_add (S)RNGClothing.V1.MistralLayerJacket
player_add (S)RNGClothing.V1.GarnetPinCollarTop
```

Move each resulting item into the native shirt slot. Full instructions are also in the pack's `README.md`.

## 11. What remains programmer-art-like

- The shared vanilla-aligned outer contour is necessarily similar across archetypes; garment identity lives in only a handful of interior cells.
- Back and side views are coherent but intentionally quieter, so the T-shirt and button shirt can look generic from behind.
- The sweater's knit identity is a neck/hem/value-mass suggestion, not literal texture.
- The sailor top's high-contrast yoke is clear but still close to the abstraction limit of 8×8.
- The chest pin/pocket cue on the tee is intentionally tiny and may read differently at different display scaling.

## 12. Where human judgment is still required

Automated checks cannot judge whether a collar feels elegant, whether a palette is emotionally appealing, or whether two clean designs are still too similar. Human review remains necessary for batch curation, accent placement, names, default dye color, and actual Farmer-body screenshots. Extreme player dyes may also undermine a protected secondary relationship even when luminance at the authored default passes.

## 13. Comparison with the Juniper Trail Cardigan POC

V1 is a material systems improvement: it replaces one hand-authored fixed grid with reusable grammar, legal semantic recipes, deterministic batch diversity, five archetypes, directional construction, palette roles, complexity rejection, repeatable export, and one five-item pack. Visually, the selected set is broader and cleaner than a palette-variant batch would have been.

The comparison is not a blanket claim that every V1 item is more art-directed than Juniper Trail Cardigan. The POC benefited from hand-tuning one garment; V1's quiet sweater and button shirt remain more generic. The promising result is that the jacket and broad-collar top retain deliberate identities while coming from shared rules. V1 passes the static technical test and, after three logical-grid review passes, passes the preliminary visual-quality bar for an in-game test—but final art success remains **untested until viewed on the real Farmer in motion**.

## Stop condition

V1 ends here. No pants, hats, Fashion Sense content, reward integration, TFWR changes, scraping, machine learning, GUI, or additional rendered shirts were added.
