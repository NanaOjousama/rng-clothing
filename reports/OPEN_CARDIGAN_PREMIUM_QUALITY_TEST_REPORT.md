# Open Cardigan Premium Quality Test Report

Status: **PASS_STATIC_VISUAL_REVIEW_REQUIRED**. Pack: **PASS_STATIC_RUNTIME_NOT_TESTED**. Runtime remains **NOT TESTED**.

## 1. Art-quality changes

The Premium specimen keeps the repaired `OPEN_CARDIGAN` topology but refines five existing systems: the two shawl/opening leaves receive directional light/shadow weight; the broad inner shirt gains a coherent neckline and fabric field; paired patch pockets become cloth planes rather than dark bars; the hem becomes one connected ribbed termination; and side/back views receive hanging-edge depth and cleaner continuous knit planes. No motif, button system, trim ornament, accessory, or custom sleeve was added.

The semantic palette roles are unchanged. Premium derives light and shadow values for the existing `Trim` role so the knit leaves turn in space; those two purposeful ramp values explain the active-color increase and are not an added hue story or color-count target.

## 2. Reused pipeline

Both specimens follow `render_fs_hd_v2 -> V3 surface -> V4/V5B STANDARD_JACKET cardigan base -> V5D CARDIGAN -> polish_upper_frames -> soften_shared_rear_neck -> semantic palette/material adapter`. Premium inserts only `polish_open_cardigan_premium_execution` after the shared rear-neck correction and resolves its existing semantic opening/collar carriers through shaded `Trim` roles.

## 3. New reusable capability

One bounded optional function was necessary: `art_polish_v5e.polish_open_cardigan_premium_execution`. It operates on shade roles and existing construction signals, preserves alpha/runtime fields, and is invoked only by `execution_profile=PREMIUM_CARDIGAN_V1`. It is not propagated to other garments.

## 4. Structural/artful difference

The grammar and construction signal topology are identical. Premium changes 73 front, 31 right, 32 back, and 30 left rendered cells through connected fabric planes and construction cleanup. The difference is execution quality: opening thickness, inner-layer hierarchy, pocket volume, hem finish, side depth, and rear knit articulation—not a new article.

## 5. Deliberately unchanged

- `OPEN_CARDIGAN`, `CARDIGAN`, and `LAVENDER_DAY`
- alpha silhouette and safe body envelope
- Scale 2, 16×64 atlas, BodyPosition `(0,32)`
- native Farmer sleeves and identical `SleeveColors`
- corrected shallow rear neck
- no rarity, motif, VFX, accessory, custom Sleeves, or additional garment

## 6. Prior quality anchors

| Anchor | Active front colors | Dominant front fill | Luminance range |
|---|---:|---:|---:|
| Sunfield Pathfinder Jacket | 11 | 27.3% | 189.96 |
| Juniper Vale Cardigan | 8 | 29.4% | 181.59 |
| Orchard Reserve Workshirt | 10 | 25.2% | 182.15 |

These metrics are contextual, not a score target. The Premium cardigan borrows the anchors' disciplined plane organization, selective contour exposure, and direction-owned construction while retaining its soft lavender knit identity. It does not copy their pixels, motifs, palettes, or article layouts.

Baseline front: 10 active colors, 29.4% dominant fill, 15 light-plane cells, 29 shadow-plane cells. Premium front: 12 active colors, 25.2% dominant fill, 27 light-plane cells, 59 shadow-plane cells. Counts are evidence only; the Farmer composite is authoritative.

## 7–9. Farmer review and decision

At gameplay scale, Premium remains immediately an open cardigan. Its inner shirt is cleaner and more continuous, the two knit leaves have different but coordinated plane weight, the lower front reads as pockets plus a finished hem rather than a dark bar, the side views retain hanging-layer depth, and the back carries a shallow neck with broad fabric articulation rather than a stamped V. The visual change remains controlled and unspeckled.

Decision: **PASS_PREMIUM_EXECUTION_CANDIDATE** for visual review. Premium is clearly more authored and dimensional in the generated Farmer comparison, although live animation review is still required. The improvement is primarily construction and material organization; decoration count remains zero and the semantic palette story is unchanged.

## 10. Remaining ceiling limitations

- Native Farmer sleeves constrain visible cardigan cuff volume in static Shirt art.
- The unchanged alpha envelope limits true loose-knit silhouette expansion.
- Static composites cannot prove motion, tool, sitting, horse, or multiplayer behavior.
- Low-contrast `LAVENDER_DAY` intentionally makes the quality jump subtler than a high-contrast recolor; this is useful evidence that the gain does not depend on luxury hues.

## Outputs

- Experimental pack: `/run/media/deck/USD00/RNG_clothing/test-packs/fashionsense/RNG-Clothing-Open-Cardigan-Premium-Quality-Test`
- Per-version assets: `/run/media/deck/USD00/RNG_clothing/output/fashionsense/open-cardigan-premium-quality-test`
- Isolated directions: `/run/media/deck/USD00/RNG_clothing/output/comparisons/OPEN_CARDIGAN_PREMIUM_ISOLATED_DIRECTIONS.png`
- Farmer composites: `/run/media/deck/USD00/RNG_clothing/output/comparisons/OPEN_CARDIGAN_PREMIUM_FARMER_COMPOSITES.png`
- Gameplay comparison: `/run/media/deck/USD00/RNG_clothing/output/comparisons/OPEN_CARDIGAN_PREMIUM_GAMEPLAY.png`
- Direct front comparison: `/run/media/deck/USD00/RNG_clothing/output/comparisons/OPEN_CARDIGAN_PREMIUM_FRONT_COMPARISON.png`
- Direct four-direction comparison: `/run/media/deck/USD00/RNG_clothing/output/comparisons/OPEN_CARDIGAN_PREMIUM_FOUR_DIRECTION_COMPARISON.png`
- Validation: `/run/media/deck/USD00/RNG_clothing/output/fashionsense/open-cardigan-premium-quality-test/static-validation.json`

Stop state: one Baseline cardigan and one Premium cardigan only; no propagation or additional generation.
