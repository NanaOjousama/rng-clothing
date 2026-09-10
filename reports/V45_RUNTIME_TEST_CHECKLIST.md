# V4.5 Extended-Garment Runtime Test Checklist

## Test boundary

Static validation is complete. Every row below begins **NOT RUN** and must be checked in Stardew Valley 1.6.15 with SMAPI and Fashion Sense 7.5.0. Do not convert an article from EXPERIMENTAL to PASS until all required rows pass.

Test pack to copy manually:

```text
test-packs/fashionsense/RNG-Clothing-V45-Extended-Prototypes/
  -> Stardew Valley/Mods/RNG-Clothing-V45-Extended-Prototypes/
```

The coat-tail diagnostic is intentionally not in this pack.

## Prototypes

| ID | Article | Rarity |
|---|---|---|
| Wayfarer Field Trousers | fitted Pants | Common |
| Crossline Scout Trousers | panel/harness Pants | Rare |
| Palisade Field Skirt | short Skirt through Pants | Uncommon |
| Trailguard Field Shoes | short footwear | Common |
| Rampart Scout Boots | tall boots | Rare |
| Verdant Regiment Mantle | Accessory mantle | Rare |

Test each lower-body piece with at least one V4 fitted shirt and Rookfield Crop Jacket. Test boots with both trousers and skirt. Test the mantle with short and long hair, a hat, and native sleeves.

## Standing and basic movement

| Check | Expected | Status | Notes/evidence |
|---|---|---|---|
| Stand front/back/left/right | correct anchor, no body exposure or floating | NOT RUN | |
| Walk all directions | authored phases track steps; no leg/hem tearing | NOT RUN | |
| Run all directions | faster sequence remains coherent | NOT RUN | |
| Stop after movement | returns to frame 0 without stale phase | NOT RUN | |
| Direction change mid-step | source row/direction changes cleanly | NOT RUN | |

## Tools and actions

| Check | Expected | Status | Notes/evidence |
|---|---|---|---|
| Axe, all directions | pants/shoes/hem stay on legs; mantle does not cover arms/tool incorrectly | NOT RUN | |
| Pickaxe, all directions | same | NOT RUN | |
| Watering can, charge/use | lower layers remain anchored through body offsets | NOT RUN | |
| Hoe, charge/use | no leg clipping at extreme tool frames | NOT RUN | |
| Fishing cast/hold/catch | footwear/pants and mantle remain coherent | NOT RUN | |
| Slingshot | mantle ordering does not obscure custom/native arm behavior | NOT RUN | |
| Eat/drink/harvest/milk | compact assets do not lag special Farmer frames | NOT RUN | |

## Social, rest, and transport

| Check | Expected | Status | Notes/evidence |
|---|---|---|---|
| Sit facing supported directions | skirt/pants do not form a standing-shaped shell | NOT RUN | |
| Bench/chair rotation | direction switch and hem placement are correct | NOT RUN | |
| Bed/sleep/pass-out | no persistent floating footwear/mantle | NOT RUN | |
| Mount horse | pants/boots align with riding legs; mantle clears horse/player | NOT RUN | |
| Ride all directions | no tail/cape phase drift or horse clipping | NOT RUN | |
| Dismount | idle frames restore | NOT RUN | |

## Environment and visibility

| Check | Expected | Status | Notes/evidence |
|---|---|---|---|
| Enter water/swim | all prototypes hide as configured | NOT RUN | |
| Exit water | appearances restore and reset animation | NOT RUN | |
| Bathing suit transition | pants/shoes/mantle hide; no waterline artifact | NOT RUN | |
| Rain/night/background contrast | article silhouette and rarity details remain readable | NOT RUN | |

## Layer compatibility

| Check | Expected | Status | Notes/evidence |
|---|---|---|---|
| Boots + each Pants | trousers cover shaft appropriately; soles remain visible | NOT RUN | |
| Boots + skirt | no gap at leg/boot junction | NOT RUN | |
| Pants/skirt + V4 tops | shirt/pants waist overlap looks intentional | NOT RUN | |
| Mantle front | clasp appears after Shirt without covering face/arms | NOT RUN | |
| Mantle back/side | mantle stays behind Player and does not vanish behind wrong layers | NOT RUN | |
| Mantle + long/short hair | intentional hair ordering, no severe clipping | NOT RUN | |
| Mantle + hat | no unrelated ordering regression | NOT RUN | |

## UI, controller, save, and multiplayer

| Check | Expected | Status | Notes/evidence |
|---|---|---|---|
| Hand Mirror with controller | Pants, Shoes, Accessory can be selected without mouse | NOT RUN | |
| Preview rotation | all four directions show correct source rows | NOT RUN | |
| Save/reload | IDs persist and correct textures restore | NOT RUN | |
| `fs_reload` | pack reloads without stale frame data | NOT RUN | |
| Local host view | equipped appearance is stable | NOT RUN | |
| Remote farmer view | remote peer sees IDs/colors/animation | NOT RUN | |
| Host/client equip changes | selection propagates both directions | NOT RUN | |
| Peer missing pack | failure is nonfatal and documented; same-pack install remains requirement | NOT RUN | |

## Steam Deck performance capture

Record with the same save/location and zoom before/after enabling all three simultaneous layers:

- standing frame time/fps;
- walking frame time/fps;
- horse frame time/fps;
- menu/Hand Mirror responsiveness;
- memory change if measurable;
- SMAPI warnings/errors.

Expected texture payload is under 100 KB uncompressed for the six appearances, so any material slowdown likely indicates layer/animation/framework behavior rather than texture memory.

## Promotion rules

- **Footwear PASS:** all standing/walk/run/tool/horse/sit/water checks pass with trousers and skirt.
- **Pants PASS:** both pairs pass full pose coverage on default male/female Farmers; body mods remain a documented separate tier.
- **Skirt PASS:** no standing-shell artifact while sitting/horse and no leg exposure during movement.
- **Mantle PASS:** draw order, hair/sleeves/tools, horse, water, and remote-player rendering all pass.
- **Coat-tail experiment may begin in-game only after Mantle PASS.** It still needs atomic/preset pairing and synchronized lower-body motion.

