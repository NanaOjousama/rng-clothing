# Hoodie vanilla-hair compatibility audit

## Result

The hood-up template was checked against the complete Stardew Valley 1.6.15 selectable vanilla hairstyle list: **74 styles**, both vanilla Farmer body-offset branches, and front/right/back/left. This produced **592 exact idle source-contract composites**.

The result is not a universal `HideBackOnly` pass:

- **Front:** all 74 preserve Hair and remain readable in the static audit.
- **Back:** all 74 are contained by the intended directional `HideHair` behavior.
- **Sides:** 61 style IDs pass the current native Hat-occlusion approach across both body-offset branches.
- **Sides:** 13 style IDs retain a substantial hair mass below the hood in at least one body branch and require the existing `PreserveFrontOnly` fallback.

Because one default policy does not pass all vanilla styles—and this milestone produced static source-contract evidence rather than live animation evidence—the Rare+ hoodie template remains:

- architecture: `LOCKED_PENDING_FINAL_RUNTIME_CONFIRMATION`
- promotion: `EXPERIMENTAL`
- **not** `FROZEN_RUNTIME_PASS`

## Authority and coverage

The audit reads the installed game content directly:

- `Characters/Farmer/hairstyles.png`
- `Characters/Farmer/hairstyles2.png`
- `Data/HairData.json`
- `Characters/Farmer/farmer_base.png`
- `Characters/Farmer/farmer_girl_base.png`

Stardew's `Farmer.GetAllHairstyleIndices` contract yields:

- legacy IDs `0–55` from `hairstyles.png`;
- positive IDs `100–117` from `HairData`/`hairstyles2.png`;
- negative covered variants are not player-selectable and are excluded, matching vanilla's list construction.

The compositor reproduces:

- front/down, right, back/up, and flipped/unique-left Hair source selection;
- the installed `usesUniqueLeftSprite` metadata;
- vanilla masculine/feminine hairstyle Y-offset branches;
- representative standing Farmer frames `0`, `6`, and `12`;
- Fashion Sense Scale-2 Shirt and Hat origins;
- Shirt → Hair → topmost raised Hat order;
- `HideBackOnly`: front/right/left preserve Hair; back omits Hair.

This is an exact static idle-layer audit. It does not fabricate a claim about walking, tool, sitting, horse, or weather-transition runtime behavior.

## Severe side cases

The following styles leave at least eight vanilla logical hair pixels' worth of visible area below the hood (128 Scale-4 display pixels) in the reviewed static side composites. The threshold is a diagnostic guardrail confirmed by visual review, not an automated beauty score.

All listed failures affect **both right and left** in the affected body branch.

| Vanilla hair ID | Masculine offset branch | Feminine offset branch | V1 action |
|---:|---|---|---|
| 17 | severe | severe | `PreserveFrontOnly` |
| 24 | severe | severe | `PreserveFrontOnly` |
| 26 | severe | severe | `PreserveFrontOnly` |
| 28 | acceptable | severe | `PreserveFrontOnly` for feminine branch |
| 29 | severe | severe | `PreserveFrontOnly` |
| 33 | severe | severe | `PreserveFrontOnly` |
| 34 | severe | severe | `PreserveFrontOnly` |
| 100 | acceptable | severe | `PreserveFrontOnly` for feminine branch |
| 101 | severe | severe | `PreserveFrontOnly` |
| 102 | severe | severe | `PreserveFrontOnly` |
| 103 | severe | severe | `PreserveFrontOnly` |
| 104 | severe | severe | `PreserveFrontOnly` |
| 115 | acceptable | severe | `PreserveFrontOnly` for feminine branch |

The most extreme cases are IDs `26`, `101`, `102`, `33`, and `24`. Their long rear masses extend materially below the 32-logical-pixel Hat frame. A head-sized hood cannot cover those pixels without becoming an implausible long side garment.

Moderate cases below the severe boundary remain recorded in `audit.json`; these include styles such as `12`, `28`, `30`, `39`, `40`, `105`, `106`, and `114`, depending on body branch. They should be included in live spot checks even where the static review is acceptable.

## Art-only occlusion attempt

An art-only adjustment was tested before changing policy:

- widened the rear edge of the final seven side-hood rows by two to three HD logical cells;
- preserved the upper/front opening and all anchors;
- retained native topmost Hat occlusion.

It reduced the largest surviving side-hair counts, for example:

- hair `26`, feminine: `792 → 744` display pixels at/below Shirt top;
- hair `101`, feminine: `628 → 584`;
- hair `24`, feminine: `476 → 428`.

It did **not** contain the long styles. More importantly, the widened lower rows created a pointed cloth tail down the side of every hairstyle, degrading the hood silhouette. The attempt failed the art-quality gate and was reverted. The generated runtime pack uses the cleaner pre-attempt hood art.

Evidence retained:

- `output/fashionsense/hoodie-vanilla-hair-audit/audit-before-side-drape.json`
- `output/fashionsense/hoodie-vanilla-hair-audit/audit-rejected-side-drape.json`
- `output/comparisons/HOODIE_VANILLA_HAIR_STRESS_SET_BEFORE.png`
- `output/comparisons/HOODIE_VANILLA_HAIR_STRESS_SET_REJECTED_SIDE_DRAPE.png`

## V1 compatibility policy

### Default: `HideBackOnly`

- front Hair preserved;
- right/left Hair preserved and visually occluded by the raised Hat;
- back Hair hidden;
- appropriate for the 61 fully passing vanilla style IDs and many moderate styles.

### Vanilla fallback: `PreserveFrontOnly`

- front Hair/bangs preserved;
- right, left, and back Hair hidden while hood-up;
- removes every severe side conflict listed above;
- limitation: Fashion Sense hides the entire directional Hair layer, so side bangs are lost too.

The base FS/CP architecture still supports manual selection through its config. A later, optional helper now automates the audited vanilla mapping without changing rendering: it selects between two locked, pixel-identical Hat appearances whose only difference is the Content Patcher-managed `HideHair` policy. Removing the helper returns to the normal configured policy.

### Universal fallback: `HideHair`

Use only where front Hair also overwhelms the hood opening. No vanilla front style required this in the static audit.

## Custom/modded Hair policy

Custom and Fashion Sense Hair appearances are **experimental/unsupported for V1**. Their sizes, anchors, animation frames, scales, and silhouettes are not constrained by the vanilla 16×32 Hair contract. Passing all vanilla styles does not imply compatibility with them.

No clipping renderer, custom Hair renderer, Harmony patch, or FarmerRenderer modification was added.

## Outputs

- `tools/audit_hoodie_vanilla_hair.py`
- `output/fashionsense/hoodie-vanilla-hair-audit/audit.json`
- eight all-style sheets: masculine/feminine × front/right/back/left
- `output/comparisons/HOODIE_VANILLA_HAIR_STRESS_SET.png`
- `output/comparisons/HOODIE_VANILLA_HAIR_POLICY_FALLBACKS.png`

The fallback sheet shows the 13 severe style IDs under native side-Hair preservation and `PreserveFrontOnly` side hiding.

## Freeze decision

**Do not freeze yet.** Static validation proves the full vanilla coverage map and the available fallback, but not a single universal side-Hair policy or complete live behavior.

The template becomes eligible for `FROZEN_RUNTIME_PASS` only after:

1. live testing confirms `HideBackOnly` on representative passing, moderate, and extreme styles;
2. live testing confirms `PreserveFrontOnly` on all 13 severe style IDs (or at minimum the five extreme IDs plus every unique-left case);
3. turning directions restores/hides Hair immediately without stale frames;
4. existing movement/tool/sitting/horse/water checklist remains clean;
5. the accepted limitation—manual fallback for some vanilla Hair—is explicitly considered part of V1 support.
