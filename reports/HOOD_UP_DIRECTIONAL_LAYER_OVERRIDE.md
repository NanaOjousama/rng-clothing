# Hood Directional Runtime Override

Status: **STATIC PASS — LIVE RETEST REQUIRED**

This correction is limited to the raised hood's directional layer order and the lowered front hood's horizontal origin. Hoodie Shirt art, native animated sleeves, drawstrings, weather conditions, and all hood pixels are unchanged.

## Authoritative runtime finding

Fashion Sense 7.5.0's `LayerManager` normally sorts custom appearances as Player, Shoes, Pants, Shirt, Hair/accessories, Sleeves, then Hat. `SortHat` does not move Hat by facing direction. A Hat with no override therefore draws topmost.

The weather hood had overridden that safe native behavior:

- raised front/right/left used `Before Hair`;
- raised back used `After Shirt`.

Both placements leave the raised Hat below later Hair and/or Sleeves layers. That explains why the correct raised frames and anchors could still look hidden in live gameplay.

## Direction audit and fix

| View | Frame | Anchor | Old failure | Correction |
|---|---:|---:|---|---|
| Front/down-facing | 0 | `(-4,30)` | `Before Hair` let Hair/Sleeves cover the outer hood, so it read behind the head. | Removed the override; native topmost Hat order frames the head. |
| Right | 1 | `(-4,26)` | Correct side frame was present but `Before Hair` buried its projected silhouette. | Removed the override; native Hat order keeps it visible. |
| Back/up-facing | 2 | `(-4,26)` | `After Shirt` was still below Hair/Sleeves and buried the back mass. | Removed the override; native Hat order places it visibly on the back/head silhouette. |
| Left | 3 | `(-4,26)` | Correct unique left frame was present but used the same bad `Before Hair` order. | Removed the override; native Hat order keeps it visible. |

Frame selection, Hat category, Scale 2, source rectangles, raised anchors, and raised animation offsets were already correct. No raised-hood offset nudge was used.

The transparent openings remain the occlusion mechanism: face and permitted hair show through transparent pixels even though the hood fabric itself draws above Hair. After side-clipping evidence, the companion policy offers `PreserveHair`, `HideBackOnly`, `PreserveFrontOnly`, and `HideHair`; see `reports/HOOD_UP_SIDE_HAIR_POLICY_REFINEMENT.md`.

## Lowered-front centering root cause

The lowered front uses a 24×32 logical Hat cell to create shoulder spread around the 16×16 Shirt. It was assigned `HeadPosition.X = 4`.

Fashion Sense passes `HeadPosition` as the SpriteBatch origin, not as a simple top-left translation. At Scale 2, increasing the origin X moves the texture left. The old `4` therefore pushed the unchanged fold 24 display pixels left of its correct centered position.

Corrected contract:

- old lowered-front `HeadPosition`: `(4,0)`;
- new lowered-front `HeadPosition`: `(-8,0)`;
- weather animation front-down X offset: `+8` → `-4`, relative to the unchanged raised-front base `(-4,30)`.

The new X is obtained from the actual draw equation: a 24-cell Scale-2 shape has a 48-display-pixel width and must begin eight display pixels from the 64-display-pixel Farmer frame to share its center. With the Hat native X feature offset of `-8`, `HeadPosition.X=-8` produces that start position.

The lowered front remains `Before Player`, so the Farmer masks its center. Its Y origin, art, size, hair policy, and draw order are unchanged.

## Art decision

No size or design polish was applied in this correction. The current fold already spans 22 opaque logical columns inside its 24-cell frame; much of its apparent smallness may have resulted from the left displacement and Player occlusion. Size/readability should be reassessed only after the centered build is observed live.

## Pack revisions

- Static six-hoodie pack: `1.6.0`
- Weather test Fashion Sense child: `1.3.0`
- Content Patcher hair-policy child: unchanged

Static validators now reject any raised animation with a `DrawOrderOverride`, require the corrected lowered-front origin, verify the exact 0/1/2/3 raised frame map, and verify the derived front-down weather offset.
