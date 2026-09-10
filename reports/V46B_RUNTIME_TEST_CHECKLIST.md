# V4.6B Runtime Test Checklist

## Install and setup

Copy this whole folder into `Stardew Valley/Mods`:

`test-packs/fashionsense/RNG-Clothing-V46B-LowerBody-Readability/`

Use test-pack version **0.1.1** or newer. Version 0.1.0 had the disproven
Scale-2 `BodyPosition (0,-2)` contract and will render the custom lower-body
layer 64 display pixels too low. Delete/replace that older copy before testing.

Launch through SMAPI with Fashion Sense 7.5.0 installed. Open the Fashion Sense
Hand Mirror; all six appearances are in the **Pants** category. If a Hand Mirror
is needed, run `fs_add_mirror`. After replacing files during a running session,
run `fs_reload RNGClothing.FashionSense.V46BLowerBodyReadability`.

Test each appearance:

- Harborline Fitted Trousers — Pants / Common
- Ridgeline Panel Trousers — Pants / Rare
- Cedar Day Shorts — Shorts / Common
- Bramble Cuff Shorts — Shorts / Uncommon
- Willow A-Line Skirt — Skirt / Common
- Heather Pleat Skirt — Skirt / Rare

Record `PASS`, `FAIL`, or `NOT TESTED` for every cell. A static preview is not a
pass.

## Per-appearance matrix

Repeat this matrix for all six appearances.

### Idle

- [ ] Front
- [ ] Back
- [ ] Left
- [ ] Right

### Walk

- [ ] Front
- [ ] Back
- [ ] Left
- [ ] Right

### Run

- [ ] Front
- [ ] Back
- [ ] Left
- [ ] Right

### Tools

- [ ] Axe
- [ ] Pickaxe
- [ ] Watering can

### General

- [ ] Sit
- [ ] Get up from sitting

### Transport

- [ ] Mount horse
- [ ] Ride front
- [ ] Ride back
- [ ] Ride left/right
- [ ] Dismount

### Fashion Sense

- [ ] Equip
- [ ] Unequip
- [ ] Recolor
- [ ] Hand Mirror preview

## Article-specific observations

For every pose, check:

- [ ] garment remains attached to the waist/legs;
- [ ] left and right legs do not swap;
- [ ] no unexpected vertical bounce;
- [ ] no disappearing construction pixels;
- [ ] pants retain long two-leg readability;
- [ ] shorts retain two high, separate hems;
- [ ] skirts remain one mass and do not split into fake pant legs;
- [ ] no exposed-body holes;
- [ ] no torso clipping;
- [ ] front/back/side identity remains consistent.

## Failure record

| Appearance | Article | Direction | Farmer state/frame | Visible problem | Screenshot |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Promotion rule

`EXPERIMENTAL → RUNTIME_PASS → ART_PASS → PRODUCTION_READY`

Only observed in-game evidence can move an appearance to `RUNTIME_PASS`.
V4.6B intentionally stops at `EXPERIMENTAL`.
