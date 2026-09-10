# Generator V2 completion report

Generator version: `2.0.0`  
Deterministic recipe seed: `202608282200`  
Scope: native Stardew Valley shirts only; exactly ten full V2 garments.

## 1. Why V1's recipe architecture was insufficient

V1 treated `detail`, `secondaryDetail`, and `pattern` as peer-level additions. That encouraged rarity to stack lines, pins, and borders after a shared shirt body had already been chosen. The five in-game garments consequently had identical occupied masks, and their differences were concentrated in a few late overlay cells. Exact findings are in `reports/V2_STRUCTURAL_AUDIT.md`.

## 2. New V2 recipe architecture

V2 resolves category/style, archetype, seven construction fields, substantial features, rarity budget, named color blocks, micro details, and palette in that order. Recipes contain no coordinates. `BODY`, `COLLAR`, `YOKE`, `PLACKET`, `OUTER_PANEL_LEFT`, `OUTER_PANEL_RIGHT`, `INNER_LAYER`, `HEM`, `RIBBING`, plus neckline/stripe masks are renderer-owned data.

## 3. V1 to V2 migration

All 20 V1 recipes migrated deterministically and pass the V2 schema. Large cues became construction/features; chest marks and button dots became micro details; over-budget cues were explicitly dropped or absorbed into construction. The migration is for regression comparison and is not claimed to be optimal. See `reports/V1_TO_V2_RECIPE_MIGRATION.md`.

## 4. Twenty fresh V2 recipes

The fresh deterministic batch contains four recipes per archetype, represents Common/Uncommon/Rare, and has zero exact or near-duplicate construction signatures. Five deliberately invalid combinations were also rejected by the recipe gate. See `output/recipes/lifestyle_v2_recipes.json` and `reports/RECIPE_BATCH_V2.md`.

## 5. Rarity budget implementation

- Common: zero or one substantial feature, no micro detail, and archetype-specific restrictions on risky construction.
- Uncommon: exactly one substantial feature, optional one micro detail, and broader construction choices.
- Rare: one or two substantial features (the fresh batch uses two), optional one micro detail, and the widest legal construction/color-block freedom.

Two features which merely alias the same major region are rejected. Micro detail can never satisfy Rare identity.

## 6. V1 structural collapse

Every selected V1 garment occupied the same 62 front/back and 56 side cells. The button shirt and jacket differed by only 13 front, 10 back, and 13 side broad-role cells after decoration was included. Mistral and Garnet survived better because their connected inner-layer/yoke regions were larger. V2 addresses the actionable cause rather than blaming the 8×8 canvas.

## 7. Structural changes by archetype

- T-shirt: deliberately minimal body and neckline, with no borrowed collar/placket masks.
- Sweater: heavier neck plus connected lower ribbing/hem mass.
- Button shirt: continuous placket, folded collar, and tailored back yoke; buttons remain micro.
- Jacket: persistent left/right outer panels, broad visible inner layer, forward side opening, back yoke, and outerwear hem.
- Sailor top: dominant upper yoke/collar across front, back, and side with a clear lower body.

## 8. Major-region mask system

Named masks persist from construction through color blocking and shading. Micro details are applied only after those regions exist. Left/right are derived from one side, including outer-panel handedness.

## 9. Two-color comparison result

Result: **PASS**. All five archetypes were rendered with only primary Color A and structural Color B before shading. The first run rejected the Button Shirt back as too close to the T-shirt; a real back yoke was added. The final gate compared 10 pairs, rejected 0, and issued 0 warnings.

## 10. Structural similarity checks

The validator compares secondary-region placement on front, back, and side; exact named-region matches; total differing cells; per-direction survival; and high Jaccard overlap. It rejects obvious collapse but makes no beauty claim.

## 11. Ten rendered garments and recipes

| Set | Name | Archetype | Rarity | Panel / layering / hem | Substantial features | Palette |
|---|---|---|---|---|---|---|
| A | Stonefield Essential Tee | T_SHIRT | Common | solid / single_layer / plain | none | cool_neutral |
| A | Stonefield Rib-Knit Sweater | SWEATER | Common | solid / single_layer / ribbed | ribbed_hem | cool_neutral |
| A | Stonefield Tailored Shirt | BUTTON_SHIRT | Common | center_placket / single_layer / plain | center_placket | cool_neutral |
| A | Stonefield Layer Jacket | JACKET | Common | split_outer_panels / visible_inner_layer / structured | contrast_inner_layer | cool_neutral |
| A | Stonefield Sailor-Yoke Top | SAILOR_TOP | Common | yoke / overlay_panel / plain | yoke | cool_neutral |
| B | Meadow Everyday Tee | T_SHIRT | Common | solid / single_layer / plain | none | sage_tan |
| B | Woodland Yoke Sweater | SWEATER | Uncommon | yoke / overlay_panel / structured | yoke | forest_cream |
| B | Meadow Placket Shirt | BUTTON_SHIRT | Uncommon | center_placket / single_layer / plain | center_placket | sage_tan |
| B | Mistral Lapel Layer Jacket | JACKET | Rare | split_outer_panels / visible_inner_layer / structured | contrast_inner_layer, broad_collar | cool_neutral |
| B | Garnet Yoke Top | SAILOR_TOP | Rare | yoke / overlay_panel / contrast_band | yoke, structured_lower_band | charcoal_burgundy |

Set A uses one neutral palette, no micro details, and minimum surface patterning. Set B uses one Common, two Uncommon, and two Rare recipes. Selection reasons are recorded in `output/vanilla/v2/rendered_recipes.json`.

## 12. Validation results

Overall static result: **PASS**.

- 10/10 semantic recipes valid;
- 10/10 logical renders pass technical/readability/design rejection checks;
- 10/10 native PNG/preview exports pass;
- Content Patcher pack: PASS;
- native sheets are 256×32 RGBA8, base at x=0..7, dye mask at x=128..135, directions at y=0/8/16/24;
- alpha is binary, masks are grayscale, base/mask cells do not overlap, sleeve samples are ordered, and previews are exact 8× nearest-neighbor replications.

No Farmer composite was fabricated because no reliably decoded authoritative installed Farmer base is available. Runtime movement, extreme dyes, save/reload, and multiplayer remain untested for V2.

## 13. Install and spawn commands

Copy `test-packs/vanilla/RNG-Clothing-V2/` into the normal Stardew `Mods` directory, launch through SMAPI, and run:

```text
player_add (S)RNGClothing.V2.StonefieldEssentialTee
player_add (S)RNGClothing.V2.StonefieldRibKnitSweater
player_add (S)RNGClothing.V2.StonefieldTailoredShirt
player_add (S)RNGClothing.V2.StonefieldLayerJacket
player_add (S)RNGClothing.V2.StonefieldSailorYokeTop
player_add (S)RNGClothing.V2.MeadowEverydayTee
player_add (S)RNGClothing.V2.WoodlandYokeSweater
player_add (S)RNGClothing.V2.MeadowPlacketShirt
player_add (S)RNGClothing.V2.MistralLapelLayerJacket
player_add (S)RNGClothing.V2.GarnetYokeTop
```

Move each item into the native shirt slot. The project did not install the pack or touch the normal Mods folder.

## 14. Most improved archetype

The jacket is the largest structural improvement. It no longer relies on a center stripe: outer panels, inner layer, collar, side opening, back yoke, and hem all have persistent region ownership.

## 15. Weakest archetype

The Button Shirt remains the weakest directionally. Its front placket reads clearly and its back yoke prevents total collapse, but the physically correct side view cannot carry the center placket and still approaches the Jacket more closely than any other control pair (six differing side cells). The T-shirt is less elaborate, but that simplicity is its intended identity. Human curation is still needed for side-facing tailored shirts.

## 16. Jacket identity

Static logical review says **materially improved**: the inner region is four cells wide through much of the front, survives at the side's forward edge, and is replaced by outerwear-specific yoke/hem structure on the back. In-game motion still needs confirmation.

## 17. Rarity progression

V2 now changes connected construction and color-block composition rather than merely adding pixels. Common can remain plain; Uncommon adds one major region; Rare combines two compatible substantial decisions. The result is meaningful in the static comparison, but desirability still needs an in-game Farmer review.

## 18. External style-profile stress-test readiness

The V2 recipe and mask architecture is ready for a **bounded semantic style-profile stress test** after this isolated pack is inspected in game. It is not yet a production reward generator: themed profiles still need similarity safeguards and human art direction, and no anime/Sun/Fashion Sense work belongs in V2.

## Critical visual boundary

Manual nearest-neighbor review covered both comparison sheets and all ten directional contact sheets. The set passes this feasibility art review: the garments read as deliberate clustered sprites, and the two Rare designs are compositionally stronger without becoming noisy. Mistral and Garnet are the strongest; the Woodland Sweater's yoke can approach sailor vocabulary, and the Button Shirt's side remains the least communicative view.

This is not a production beauty certification. V2 reduces programmer-art convergence, but it does not automate taste. Palette choice, exactly how far a yoke descends, lapel proportions, dye behavior at extreme colors, and final batch curation remain human/artistic judgments. Static validation cannot certify that a reward feels desirable on the animated Farmer.

## Stop condition

V2 ends here. No pants, hats, Fashion Sense, anime/Sun content, TFWR integration, reward economy, GUI, scraping, or machine learning was added.
