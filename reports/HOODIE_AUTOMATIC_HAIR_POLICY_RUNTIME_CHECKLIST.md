# Automatic hoodie hair-policy runtime checklist

Install all three children from `test-packs/fashionsense/RNG-Clothing-Hoodie-Weather-Test/`, restart SMAPI completely, and equip **Hoodie Weather Test - Harbor Haze**.

## Passing/default vanilla Hair

- [ ] Clear/indoors: Hair preserved front/right/back/left
- [ ] Rain outdoors: front Hair preserved
- [ ] Rain outdoors: side Hair preserved and acceptably occluded
- [ ] Rain outdoors: back Hair hidden
- [ ] Turn rapidly through all directions without stale Hair state

## Severe vanilla Hair

Test at least IDs `26`, `101`, `102`, `33`, and `24`:

- [ ] Rain outdoors: front Hair preserved
- [ ] Rain outdoors: right Hair hidden
- [ ] Rain outdoors: left Hair hidden
- [ ] Rain outdoors: back Hair hidden
- [ ] Returning indoors restores Hair in all directions

## Body-branch cases

Test IDs `28`, `100`, and `115`:

- [ ] Masculine vanilla body branch uses `HideBackOnly`
- [ ] Feminine vanilla body branch uses `PreserveFrontOnly`

## Fail-open behavior

- [ ] Fashion Sense/custom Hair keeps the normal configured CP policy
- [ ] Custom Fashion Sense body keeps the normal configured CP policy
- [ ] Unrelated Hat is never replaced
- [ ] Removing/changing the Harbor Haze Shirt restores the base Harbor Haze Hat if needed
- [ ] Hood down always preserves normal Hair

## Motion and multiplayer

- [ ] Walk/run direction changes do not leave stale policy
- [ ] Tool use does not leave stale policy
- [ ] Horse/sitting state does not leave stale policy
- [ ] Local Farmer policy does not change a remote Farmer's selection
- [ ] Remote client sees the synchronized correct Hat when all content children are installed
- [ ] Split-screen Farmers select independently

Record the Hair ID, vanilla body branch, direction, weather/location state, and screenshot for every failure. Do not mark the hoodie `FROZEN_RUNTIME_PASS` from static validation alone.
