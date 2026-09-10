# Final Hoodie Runtime Checklist

Pack under test:

- Fashion Sense child `1.5.0`
- Content Patcher hair-policy child `1.3.0`
- Preset: **Hoodie Weather Test - Harbor Haze**

Promotion target: `RARE_PLUS_COMPLEX_LAYER_GARMENT_V1`

## Evidence already established

- [x] Shirt torso anchor is correct in live gameplay (user runtime evidence).
- [x] Native animated arms/sleeves remain attached (user runtime evidence).
- [x] Shirt-integrated drawstrings remain in the correct place (user runtime evidence).
- [x] Hat no longer uses the original feet-level anchor (user runtime evidence).
- [x] Static FS/CP schema, frame, alpha, deterministic-pixel, anchor, offset, layer-order, and hair-policy checks pass.
- [x] Static idle audit covers all 74 selectable vanilla Hair IDs, both Farmer Hair-offset branches, and all four directions (592 composites).
- [x] Static audit identifies 13 severe side-Hair IDs requiring the existing `PreserveFrontOnly` fallback: `17, 24, 26, 28, 29, 33, 34, 100, 101, 102, 103, 104, 115`.

The following final-build items are intentionally not pre-filled. FS `1.5.0` adds only a side-Hat visual masking plane and CP `1.3.0` defaults to `HideBackOnly`; static checks cannot establish the live hair occlusion result.

## Installation and state selection

- [ ] Stardew/SMAPI fully closed before replacing both test children.
- [ ] SMAPI loads FS `1.5.0` and CP `1.3.0` without warnings.
- [ ] Preset equips Shirt and Hat together.
- [ ] Indoors/clear outdoors selects hood down.
- [ ] Rain, storm, or snow outdoors selects hood up.
- [ ] Location transition refreshes the active state.

## Hood down — `PreserveHair` in every direction

- [ ] Front: fold is centered behind neck/shoulders and does not drift left.
- [ ] Front: both shoulder folds remain visible after Player occlusion.
- [ ] Right: hood rests at neck/shoulder and remains attached.
- [ ] Back: hood draws over the upper garment and reads as folded fabric.
- [ ] Left: mirrored side remains attached and correctly oriented.
- [ ] Short hair preserves natural visibility.
- [ ] Long hair naturally occludes the fold without moving it.

## Hood up — direction and layer order

- [ ] Front: hood sits on/frames the head; mouth remains visible.
- [ ] Right: hood rim and rear mass remain visible above Hair/Player.
- [ ] Back: hood sits visibly on the back-of-head/upper-back silhouette.
- [ ] Left: hood rim and rear mass remain visible above Hair/Player.
- [ ] No raised direction appears behind the Farmer.
- [ ] Micro-polished rim reads cleanly without dotted noise.
- [ ] Front, sides, and back feel proportionally related.

## Hair modes

### PreserveHair

- [ ] Front/right/back/left Hair remains visible while hood up.

### HideBackOnly — current default

- [ ] Hood down preserves Hair in all four directions.
- [ ] Hood up front preserves bangs/front hair.
- [ ] Hood up right preserves upper/front Hair while hood fabric covers lower/rear Hair.
- [ ] Hood up left preserves upper/front Hair while hood fabric covers lower/rear Hair.
- [ ] Hood up back hides Hair.
- [ ] Turning back → side/front restores Hair immediately.

### PreserveFrontOnly — fallback for incompatible side hairstyles

- [ ] Hood down preserves Hair in all four directions.
- [ ] Hood up front preserves bangs/front hair.
- [ ] Hood up right hides Hair; no side clipping remains.
- [ ] Hood up left hides Hair; no side clipping remains.
- [ ] Hood up back hides Hair.
- [ ] Turning to front restores Hair immediately.
- [ ] Stress-test Hair IDs `26`, `101`, `102`, `33`, and `24` first.
- [ ] Verify remaining fallback IDs `17`, `28`, `29`, `34`, `100`, `103`, `104`, and `115`.

### HideHair

- [ ] Hood up hides Hair in all four directions.
- [ ] Hood down restores Hair in all four directions.

## Motion and interaction

- [ ] Idle front/right/back/left.
- [ ] Walk front/right/back/left.
- [ ] Run front/right/back/left.
- [ ] Axe.
- [ ] Pickaxe.
- [ ] Hoe.
- [ ] Watering can.
- [ ] Fishing rod.
- [ ] Hold item.
- [ ] Eat/drink.
- [ ] Sit and stand.
- [ ] Mount, ride front/back/side, and dismount horse.
- [ ] Swimming/bathing hides the coordinated appearance as configured.
- [ ] Exiting water restores the preset correctly.

## Fashion Sense and compatibility

- [ ] Equip/unequip does not leave stale components.
- [ ] Recolor keeps Shirt and hood visually coordinated.
- [ ] Hand Mirror preview uses the correct directions.
- [ ] No component appears near the feet.
- [ ] No Shirt, sleeve, drawstring, or anchor regression.
- [ ] Multiplayer local rendering (if available).
- [ ] Multiplayer remote rendering and appearance sync (if available).

## Freeze gate

Freeze and promote only when every applicable critical item above passes. Multiplayer may remain explicitly documented as unverified if unavailable, but direction, weather, all four hair modes, normal movement, tools, sitting, horse, and water transitions are mandatory.

The full vanilla static audit is not runtime evidence. Custom/modded hairstyles remain experimental/unsupported for V1.

Until then:

- architecture: `LOCKED_PENDING_FINAL_RUNTIME_CONFIRMATION`
- runtime promotion: `EXPERIMENTAL`
- default hair mode: `HideBackOnly`
- fallback modes: `PreserveHair`, `PreserveFrontOnly`, `HideHair`
