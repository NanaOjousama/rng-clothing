# V5C2 Runtime Test Checklist

Static validation passed, but all garments remain **EXPERIMENTAL / NOT TESTED**. Use a test save. Install the pack by copying `test-packs/fashionsense/RNG-Clothing-V5C2-Vanilla-Hoodie/` into `Mods`, restart SMAPI, then equip each `V5C2 - ...` outfit through Fashion Sense's Hand Mirror **Presets** list.

The preset matters: it equips the generated Shirt and its coordinated full-motion Sleeves appearance together.

## Blocking regression check — Slate & Saffron Waistcoat

- [ ] Both arms visible while idle: front
- [ ] Both arms visible while idle: back
- [ ] Arm visible while idle: right
- [ ] Arm visible while idle: left
- [ ] No missing arm while walking all directions
- [ ] No missing arm while running all directions
- [ ] No missing arm during axe
- [ ] No missing arm during pickaxe
- [ ] No missing arm during watering can
- [ ] No missing arm during fishing
- [ ] No missing arm while sitting / standing up
- [ ] No missing arm mounting, riding, and dismounting horse
- [ ] Equip and unequip restores normal arm rendering

## Recommended focused subset

Test these first because they cover the most distinct construction paths:

1. Slate & Saffron Waistcoat — fixed arm contract + fitted inner sleeves.
2. Kestrel Cropped Field Jacket — cropped shell + rolled/cuffed sleeves.
3. Harbor Haze Pullover — simplest hood baseline.
4. Rainline Zip Hoodie — hood + full opening.
5. Cloudberry Pouch Hoodie — contrast hood + pouch + layered sleeves.
6. Sproutwing Cropped Hoodie — cropped hoodie + asymmetric focal cluster.
7. Nightgarden Crest Hoodie — baggy hood mass + larger restrained motif.

## Per-garment matrix

For every garment tested:

### Idle and movement

- [ ] front idle
- [ ] right idle
- [ ] back idle
- [ ] left idle
- [ ] walk all directions
- [ ] run all directions

### Tools and actions

- [ ] axe
- [ ] pickaxe
- [ ] hoe
- [ ] watering can
- [ ] scythe
- [ ] fishing rod
- [ ] hold item overhead
- [ ] eat/drink

### Poses and transport

- [ ] sit
- [ ] stand from sitting
- [ ] mount horse
- [ ] ride front/back/side
- [ ] dismount

### Fashion Sense

- [ ] preset equips matching Shirt + Sleeves
- [ ] equip/unequip leaves no invisible arms
- [ ] primary recolor works
- [ ] Hand Mirror preview direction is correct

## Failure record

| Garment | Direction | State/frame | Shirt issue | Sleeve/arm issue | Screenshot filename |
|---|---|---|---|---|---|
| | | | | | |

Do not promote any item to `RUNTIME_PASS` until the relevant rows are tested in-game.
