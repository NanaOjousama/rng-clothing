# V2 jacket sleeve/cuff correction

Scope: a one-logical-pixel jacket-only sleeve-color correction. Recipes, structural masks, torso construction, other archetypes, dimensions, frame positions, Content Patcher data, and native Farmer arm geometry are unchanged.

## Installed vanilla constraint

Stardew Valley 1.6.15 does not read independent sleeve geometry from a vanilla shirt. With `HasSleeves=true`, `FarmerRenderer.ApplySleeveColor` recolors the fixed Farmer arm/sleeve mask from the front shirt tile at `(0,4)`, `(0,3)`, and `(0,2)` for its dark, middle, and light tones. A vanilla shirt asset therefore cannot genuinely lengthen the sleeve by one cell.

## Exact correction

For `JACKET` only, the darkest/cuff sample at front mask cell `(128,4)` changed from `main_shadow` value 136 to `main_deep` value 88. Middle `(128,3)` remains `main_base` 184 and light `(128,2)` remains `main_light` 224.

This strengthens the fixed sleeve mask's darkest terminal/outline pixels so the cuff reads as a deliberate endpoint and the arm feels visually fuller. It does not fake unsupported sleeve geometry.

Exactly one native dye-mask pixel changed in Stonefield Layer Jacket and exactly one in Mistral Lapel Layer Jacket. Their base layer, all other directions, split panels, visible inner layer, shoulder/collar correction, and hem are byte-identical to the prior pass. All 24 non-jacket native/preview/contact outputs are byte-identical.

Review sheet: `output/vanilla/v2/V2_JACKET_SLEEVE_BEFORE_AFTER.png`.
