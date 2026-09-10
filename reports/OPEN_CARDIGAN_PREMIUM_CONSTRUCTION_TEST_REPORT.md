# Open Cardigan Premium Construction Test Report

Status: **PASS_STATIC_VISUAL_REVIEW_REQUIRED**. Pack: **PASS_STATIC_RUNTIME_NOT_TESTED**. Runtime remains **NOT TESTED**.

## 1. Silhouette and construction changes

`PREMIUM_CONSTRUCTION_CARDIGAN_V1` keeps the Premium Execution fabric-plane finish, then adds a bounded cardigan construction pass. It preserves the upper three-row coverage carrier; tapers the outermost mid-body column; re-flares into the existing lower knit footprint; changes the opening from parallel strips into curved leaves that narrow again toward the hem; reconstructs patch pockets as shallow trapezoids; bows the side opening outward before returning into the hem; and recomputes selective contours after geometry changes. The rear remains a quiet knit mass with the corrected shallow neck.

## 2. Alpha changes versus Premium Execution

| Direction | Added cells | Removed cells |
|---|---:|---:|
| front | 0 | 18 |
| right | 9 | 9 |
| back | 0 | 18 |
| left | 9 | 9 |

All alpha remains one connected component. No cell extends below logical row 15.

## 3. Safe-envelope verification

- Proven mandatory rows 0–2 preserved: **TRUE**
- Missing required body cells: **none**
- Frame: **16×16**, atlas: **16×64**
- Maximum occupied row: **15**
- Detached alpha components: **none**
- Scale / BodyPosition: **2 / (0,32)**
- Native Farmer sleeves and SleeveColors: **unchanged**
- Custom Sleeves: **absent**

## 4. Reused renderer stages

All variants use `render_fs_hd_v2 -> V3 surface -> V4/V5B STANDARD_JACKET cardigan base -> V5D CARDIGAN -> polish_upper_frames -> soften_shared_rear_neck -> semantic palette/material adapter`. Premium Execution adds `polish_open_cardigan_premium_execution`. Premium Construction is cumulative and then adds `refine_open_cardigan_premium_construction` before semantic palette resolution.

## 5. New bounded helper

`art_polish_v5e.refine_open_cardigan_premium_construction` is the only new construction helper. It is allowlisted only through `execution_profile=PREMIUM_CONSTRUCTION_CARDIGAN_V1`. It changes alpha and existing opening/layer/pocket carriers inside the frozen frame, verifies connectedness and coverage, and introduces zero motifs or palette roles. It has not been propagated.

## 6. Comparison against Premium Execution

Baseline and Premium Execution match the previous two-item pack byte-for-byte. Premium Construction uses the same grammar, material, palette, sleeve ramp, and underlying construction family. Its gain is geometric: a less rectangular torso, shaped lower drape, curved leaf relationship, integrated pockets, side hanging depth, and direction-owned contour termination. It does not merely increase shade counts.

## 7. Prior V5E/V6 anchors

| Anchor | Active front colors | Dominant front fill | Luminance range |
|---|---:|---:|---:|
| Sunfield Pathfinder Jacket | 11 | 27.3% | 189.96 |
| Juniper Vale Cardigan | 8 | 29.4% | 181.59 |
| Orchard Reserve Workshirt | 10 | 25.2% | 182.15 |

The candidate approaches those anchors through deliberate plane boundaries and authored directional construction, not by copying their palettes, motifs, or jacket logic. Native-sleeve and 16×16 limits still prevent true loose sleeve volume.

## 8–9. Farmer-scale observation and decision

At static Farmer scale the third variant remains an open cardigan: the inner shirt stays broad, soft knit leaves frame it, native sleeves remain exposed for animation, and the lower mass returns into a ribbed hem. Its front and side silhouette differs from both earlier versions without becoming a blazer or coat; the back is cleaner and subtly shaped rather than decorated.

Decision: **PASS_PREMIUM_CONSTRUCTION_CANDIDATE** for live review. The visible gain is construction-driven: alpha distribution, proportion, drape and layer topology changed while `LAVENDER_DAY`, semantic color roles, motif count, and garment family did not. Static preview cannot certify motion or clipping.

## 10. Reusability conclusion

The result supports a possible reusable *quality-sophistication layer* made of bounded, family-specific construction refiners after shared HD polish. It does **not** support applying one universal premium silhouette. Expansion should wait for live front/side/back/walk evidence from this pack.

## Outputs

- Experimental pack: `/run/media/deck/USD00/RNG_clothing/test-packs/fashionsense/RNG-Clothing-Open-Cardigan-Premium-Construction-Test`
- Per-version assets: `/run/media/deck/USD00/RNG_clothing/output/fashionsense/open-cardigan-premium-construction-test`
- Three-way front: `/run/media/deck/USD00/RNG_clothing/output/comparisons/OPEN_CARDIGAN_PREMIUM_CONSTRUCTION_FRONT.png`
- Four-direction comparison: `/run/media/deck/USD00/RNG_clothing/output/comparisons/OPEN_CARDIGAN_PREMIUM_CONSTRUCTION_FOUR_DIRECTION.png`
- Farmer composites: `/run/media/deck/USD00/RNG_clothing/output/comparisons/OPEN_CARDIGAN_PREMIUM_CONSTRUCTION_FARMER.png`
- Gameplay comparison: `/run/media/deck/USD00/RNG_clothing/output/comparisons/OPEN_CARDIGAN_PREMIUM_CONSTRUCTION_GAMEPLAY.png`
- Isolated 8× inspection: `/run/media/deck/USD00/RNG_clothing/output/comparisons/OPEN_CARDIGAN_PREMIUM_CONSTRUCTION_ISOLATED_8X.png`
- Validation: `/run/media/deck/USD00/RNG_clothing/output/fashionsense/open-cardigan-premium-construction-test/static-validation.json`

Stop state: exactly one Baseline, one Premium Execution, and one Premium Construction cardigan; no propagation or additional generation.
