# Bucket hat head-to-head: recipe (A) vs AI-native tiny-pixel (B)

Branch `compare/bucket-recipe-vs-ai`. Read-only use of `prototypes/hat_recipe_engine_01`
(baseline A, unchanged). No generator, ESM or source-pack files touched.

    python3 prototypes/hat_compare_bucket_01/compare.py

## Contenders

| id | route | cost (PixelLab generations) | result |
|---|---|---|---|
| A | deterministic `crown_brim` recipe, `bucket` variant | 0 | 16x9 front, 6 colours, 4 consistent views |
| B1 | PixelLab Create Image **Pro**, 80x20 four-view sheet, vanilla 102 layout ref + vanilla style ref | 25 | **fail**: ignored the 4x20px layout; ~3 clipped front views per sheet, unrequested motifs |
| B2 | PixelLab **Pro Flash object**, text + vanilla 102 style ref, 8 directions at 20x20 | 6 | consistent views but 18x13 (crown too tall), 30 colours, stray "logo" square |
| B3 | PixelLab **Pro** 32x32, 64 front candidates, vanilla scale ref | 20 | nicest-looking shapes but all 26-28 px wide = **2x Stardew scale**; unusable without shrinking (forbidden) |
| B4 | PixelLab **Pro** 20x20, 64 front candidates -> best (#2) -> Pro Flash rotation | 20 + 1 | front at correct scale (15x10, 10 colours); **rotation fails**: right/left are tilted 3/4 views, back is a grey capsule |
| REF | vanilla Bucket Hat (102) | - | 14x9, 5 colours |

Retro Diffusion (the other native tiny-pixel model) was **not tested**: its API key is invalid
(401). A self-trained LoRA was not practical: no GPU and no torch on this machine, and the earlier
SDXL pipeline never downloaded weights.

AI frames are used as generated; the only operation is seating (translate the lowest row to
vanilla's brim row 12 and centre). Nothing was repainted, recoloured or scaled.

## Outputs (`out/`)

- `COMPARISON_SHEET.png`: A, B2, B4, REF; 6x strips (front, right, back, left) and worn head crops
- `WORN_1X_2X_4X.png`: worn on the vanilla farmer at native 1x, 2x and 4x (offline composite)
- `FAILED_ROUTES_NATIVE_6X.png`: B1 and B3 as generated, beside vanilla for scale
- `metrics.json`, `*_bucket_20x80.png` (seated strips, vanilla front/right/left/back order)

## Judgment

- **Better looking at 1x worn: A (recipe).** It is the only contender whose four views all read
  as the same bucket hat at Stardew scale.
- **Less cleanup: A.** A: ~5-10 px of taste edits (vary the stitch row, add some crown asymmetry).
  B4: its front alone would need ~5 px, but the right, left and back must be redrawn from
  scratch (= heavy repaint = failure). B2: crown and palette redraw (failure).
- **Acceptable?** A is close but not yet a definite keeper; it still looks a little mechanical
  (a perfectly regular stitch row, side ~= front). No AI output is acceptable as a 4-view hat.
- **Where AI was genuinely good:** single front views. B4's best fronts at 20 px and B3's at
  32 px have a more organic, hand-drawn shape than A. The failure is multi-view consistency in
  Stardew's flat front/side/back projection, plus scale control.
