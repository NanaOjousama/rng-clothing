# V5E Sunfield Pathfinder Jacket — Runtime Checklist

Current promotion: **EXPERIMENTAL**  
Static validation: **PASS**  
Native arm contract: **FROZEN_RUNTIME_PASS**  
Art revision: **LIVE SCREENSHOT RETEST REQUIRED**

Install the test pack, fully restart SMAPI, open the Fashion Sense Hand Mirror, then choose **Outfits → Presets → V5E - Sunfield Pathfinder Jacket**. Test the coordinated preset rather than only the Shirt component.

## Standing and movement

- [x] Front idle: native Farmer arm remains attached; no custom sleeve below the feet.
- [x] Right idle: native Farmer arm remains attached; no custom sleeve below the feet.
- [x] Back idle: native Farmer arms remain attached; no custom sleeve below the feet.
- [ ] Left idle: collar/opening and side seam remain readable.
- [ ] Walk front/back/left/right: long sleeves remain attached.
- [ ] Run front/back/left/right: cuffs do not detach or jump.

## Tools and general poses

- [ ] Axe.
- [ ] Pickaxe.
- [ ] Hoe.
- [ ] Watering can.
- [ ] Scythe.
- [ ] Fishing rod.
- [ ] Hold item overhead.
- [ ] Eat/drink.
- [ ] Sit and stand up.
- [ ] Mount, ride all directions, and dismount horse.

## Fashion Sense

- [x] Preset equips the Shirt and leaves `SleevesId` at `None`.
- [x] Native Farmer arms inherit the jacket's Shirt `SleeveColors`.
- [ ] Unequip restores the previous appearance cleanly.
- [ ] Recolor preserves lapel/pocket/inner-layer value separation.
- [ ] No Hat, Accessory, Pants, or Shoes are changed.
- [ ] Hand Mirror preview uses the intended direction mapping.

## Failure notes

For every failure record direction, animation/state, whether the Shirt or native arm drawing failed, visible symptom, and screenshot filename.

The native sleeve mechanism is frozen and may not regress to a custom Sleeves atlas. Keep the garment itself **EXPERIMENTAL** until the revised jacket read is reviewed in live screenshots and the remaining directions/poses are tested.
