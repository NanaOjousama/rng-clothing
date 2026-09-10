# Hood-Only Runtime Retest Checklist

Replace the old `RNG-Clothing-Hoodie-Layer-Correction` pack with version `1.2.0`, fully restart SMAPI, and equip presets through **Fashion Sense Hand Mirror > Outfits > Presets**.

Test one hood-down preset first (`Harbor Haze Pullover`) and one hood-up preset (`Tidecap Contrast Hoodie`). Record the garment, direction/state, visible problem, and screenshot filename for every failure.

## Preserved components

- [ ] Shirt remains at the torso
- [ ] Native arms/sleeves remain attached
- [ ] Sleeve colors still match the hoodie
- [ ] In-Shirt drawstrings remain at the neckline
- [ ] No Shirt, arm, or string regression

## Hood-down positioning

- [ ] Front: hood rests at the neck/shoulders
- [ ] Right: hood rests behind the neck and does not cover the face
- [ ] Back: hood mass joins the upper back/neckline
- [ ] Left: hood mirrors the right-facing placement correctly
- [ ] Hood remains behind the intended Player/Hair layers
- [ ] Hair remains visible
- [ ] No hood pixels appear near or under the feet

## Hood-up positioning

- [ ] Front: opening surrounds the head without becoming a giant ring
- [ ] Right: opening and rear hood mass remain head-attached
- [ ] Back: hood encloses the head and joins the neckline
- [ ] Left: placement mirrors the right-facing view correctly
- [ ] Hair is hidden
- [ ] Face remains readable where intended
- [ ] No hood pixels appear near or under the feet

## Motion

- [ ] Walk front
- [ ] Walk right
- [ ] Walk back
- [ ] Walk left
- [ ] Hold item
- [ ] Use axe or pickaxe
- [ ] Use watering can
- [ ] Hood follows Farmer feature offsets during animation
- [ ] No intermittent feet-level hood frame appears

## Equip lifecycle

- [ ] Equip preset from Hand Mirror
- [ ] Switch between hood-up and hood-down presets
- [ ] Unequip preset
- [ ] Save/reload preserves the selected preset

Passing static validation does not mark these checks. The corrected hoods remain `EXPERIMENTAL` until observed runtime evidence passes.
