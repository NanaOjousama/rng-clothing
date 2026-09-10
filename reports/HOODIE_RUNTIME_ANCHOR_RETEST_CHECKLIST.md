# Hoodie Runtime Anchor Retest Checklist

> Superseded for the focused version 1.2.0 hood retest by `reports/HOOD_ONLY_RUNTIME_RETEST_CHECKLIST.md`.

Install the replacement `RNG-Clothing-Hoodie-Layer-Correction` folder, remove any older copy of that same folder first, fully restart SMAPI, and equip from **Fashion Sense Hand Mirror > Outfits > Presets**.

Record garment, direction/state, visible problem, and screenshot filename for any failure.

## Assembly sanity

- [ ] Preset equips one Shirt and one Hat/Hood
- [ ] Preset does not equip a custom Sleeves appearance
- [ ] Preset does not equip an Accessory appearance
- [ ] No stale detached pixels remain after equip
- [ ] Unequip removes Shirt and Hood cleanly

## Standing

- [ ] Front: native arms attach at shoulders
- [ ] Right: native arm and hood remain aligned
- [ ] Back: native arms and lowered/raised hood remain aligned
- [ ] Left: native arm and hood remain aligned
- [ ] No component appears near or below feet in any direction

## Walking

- [ ] Walk front
- [ ] Walk right
- [ ] Walk back
- [ ] Walk left
- [ ] Native sleeves follow arm animation
- [ ] Hood remains attached
- [ ] In-Shirt strings remain on torso
- [ ] No detached lower-screen pixels

## Tool hold/use

- [ ] Hold item overhead
- [ ] Axe
- [ ] Pickaxe
- [ ] Hoe
- [ ] Watering can
- [ ] Fishing rod
- [ ] Native arms remain visible and correctly colored
- [ ] Hood remains aligned during tool frames
- [ ] No component appears near feet

## Hair and hood

- [ ] Hood-up presets hide hair
- [ ] Hood-up face opening is centered front/right/back/left
- [ ] Hood-down presets preserve hair
- [ ] Hood-down side mass draws behind the Player
- [ ] Hood-down back mass draws behind Hair
- [ ] Test at least one short and one long hairstyle

## Other states

- [ ] Sitting
- [ ] Horse mounting/riding/dismounting
- [ ] Swimming hides Hood appropriately
- [ ] Bathing-suit state hides Hood appropriately
- [ ] Save/reload preserves the preset

Passing static validation does not mark these boxes. Promotion remains `EXPERIMENTAL` until observed runtime evidence is recorded.
