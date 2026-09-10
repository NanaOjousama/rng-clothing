# V5D Masculine Runtime Test Checklist

Status: **EXPERIMENTAL / NOT TESTED**. Static validation is not runtime evidence.

## Recommended five-item subset

- Tideglass Henley — native `Default (Short)` sleeve path.
- Neon Harbor Street Hoodie — layered/decorated custom sleeve and dropped shoulder.
- Silverline Evening Waistcoat — vest/inner-shirt arm-visibility regression check.
- Sunfield Scout Jacket — cropped shell, rolled cuff, and side opening.
- Emberward Tabard Armor — heaviest panel construction and reinforced custom cuff.

Equip each from **Fashion Sense Hand Mirror → Outfits → Presets** using the matching `V5D - ...` preset.

## Per-garment matrix

Record garment, direction, state, symptom, and screenshot filename for every failure.

### Standing and movement

- [ ] Idle front
- [ ] Idle right
- [ ] Idle back
- [ ] Idle left
- [ ] Walk front/back/right/left
- [ ] Run front/back/right/left
- [ ] No shoulder or arm holes
- [ ] Shirt-to-sleeve connection stays attached
- [ ] Cuffs/stripes remain on the intended arm region

### Tools and carried poses

- [ ] Axe
- [ ] Pickaxe
- [ ] Hoe
- [ ] Watering can
- [ ] Scythe
- [ ] Fishing rod
- [ ] Hold item overhead
- [ ] Eat/drink

### General and transport

- [ ] Sit
- [ ] Stand after sitting
- [ ] Mount horse
- [ ] Ride front/back/side
- [ ] Dismount

### Fashion Sense

- [ ] Preset equips correct Shirt and Sleeves pair
- [ ] Manual Shirt/Sleeves pairing works
- [ ] Tideglass selects `Default (Short)`
- [ ] Equip/unequip restores normal arms
- [ ] Recolor preserves value hierarchy
- [ ] Hand Mirror preview agrees with runtime directions

### Deferred

- [ ] Multiplayer remote-farmer appearance sync
- [ ] Multiplayer recolor sync

## Promotion rule

Remain `EXPERIMENTAL` until the relevant checklist passes. Then evaluate `RUNTIME_PASS`; art and compatibility still require separate review before `ART_PASS` or `PRODUCTION_READY`.

