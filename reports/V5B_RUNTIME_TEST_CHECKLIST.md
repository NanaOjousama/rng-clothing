# V5B Upper-Garment and Sleeve Runtime Checklist

Status at generation: **EXPERIMENTAL / NOT TESTED**. Static validation does not promote a custom sleeve.

Test pack: `test-packs/fashionsense/RNG-Clothing-V5B-Upper-Garments/`

## Installation and pairing

1. Copy the whole `RNG-Clothing-V5B-Upper-Garments` folder into `Stardew Valley/Mods`.
2. Confirm Fashion Sense 7.5.0 is installed separately.
3. Fully restart SMAPI.
4. Open the Hand Mirror, open **Outfits**, switch to **Presets**, and select a preset beginning with `V5B -`.
5. The preset equips the matching Shirt and Sleeves appearance. It may clear other Fashion Sense appearance slots, so test with a saved outfit/test character.

## Garment status

| ID | Garment | Sleeve path | Initial status |
|---|---|---|---|
| 01 | Saltair Fitted Tee | native Default Short | NOT TESTED |
| 02 | Signalwork Rolled Shirt | custom rolled/cuffed atlas | NOT TESTED |
| 03 | Maple Loom Knit | custom fitted-long atlas | NOT TESTED |
| 04 | Mosslight Familiar Knit | custom layered atlas | NOT TESTED |
| 05 | Duskline Waistcoat | generated skin-tone animated arm companion; `HideSleeves=false` | NOT TESTED |
| 06 | Relay Utility Vest | custom fitted-long atlas | NOT TESTED |
| 07 | Cinderstep Moto Jacket | custom rolled/cuffed atlas | NOT TESTED |
| 08 | Rookwing Cropped Field Jacket | custom layered atlas | NOT TESTED |
| 09 | Juniper Rain Cardigan | custom fitted-long atlas | NOT TESTED |
| 10 | Gilded Evening Blazer | custom layered atlas | NOT TESTED |
| 11 | Rose Circuit Sailor Blouse | native Default Short | NOT TESTED |
| 12 | Ribbonstar Bow Blouse | custom rolled/cuffed atlas | NOT TESTED |

## Required matrix

Run the whole matrix for at least one garment from each sleeve path: native short, generated sleeveless/bare-arm companion, fitted long, rolled/cuffed, and layered. Then perform idle/walk/tool spot checks on every remaining garment.

### Idle

- [ ] Front
- [ ] Right
- [ ] Back
- [ ] Left
- [ ] Shirt-to-sleeve shoulder connection remains closed
- [ ] Hands/skin are visible only where intended
- [ ] Cuffs remain attached to the arm

### Walk

- [ ] Front
- [ ] Right
- [ ] Back
- [ ] Left
- [ ] No detached arm pixels
- [ ] No left/right swap
- [ ] No shirt layer drawing over hands

### Run

- [ ] Front
- [ ] Right
- [ ] Back
- [ ] Left
- [ ] Sleeve termination tracks the stride/arm swing

### Tools and actions

- [ ] Axe
- [ ] Pickaxe
- [ ] Hoe
- [ ] Watering can
- [ ] Scythe
- [ ] Fishing rod
- [ ] Slingshot, if available
- [ ] Hold item overhead
- [ ] Eat/drink

Watch for tool pixels being doubled, hidden, recolored, or drawn at the wrong depth. The atlas preserves FS tool/subframe mappings, but only runtime observation can prove them.

### General and transport

- [ ] Sit facing each supported direction
- [ ] Stand up from sitting
- [ ] Mount horse
- [ ] Ride front/back/side
- [ ] Dismount
- [ ] Bed/sleep transition spot check
- [ ] Festival/special pose spot check

### Fashion Sense UX

- [ ] Each `V5B -` preset equips the intended Shirt and Sleeves pair
- [ ] Manual Shirt + Sleeves pairing works
- [ ] Equip
- [ ] Unequip
- [ ] Primary recolor affects torso and garment sleeve masks coherently
- [ ] Fixed cuff/trim accents remain intentional after recolor
- [ ] Mirror preview direction is correct
- [ ] Controller navigation can select presets and both appearance categories

### Multiplayer (may remain unverified for this milestone)

- [ ] Local farmer appearance
- [ ] Remote farmer appearance
- [ ] Shirt equip sync
- [ ] Sleeves equip sync
- [ ] Recolor sync

## Failure record

For each failure record:

- garment ID/name:
- sleeve intent:
- direction:
- Farmer state/current action:
- visible problem:
- whether Shirt, Sleeves, or their junction failed:
- screenshot filename:
- reproducible after full restart: yes / no

## Promotion rule

`EXPERIMENTAL → RUNTIME_PASS → ART_PASS → PRODUCTION_READY`

Do not mark any family `RUNTIME_PASS` until its representative garments pass idle, walk, run, tools, sitting, and horse tests. Multiplayer may remain explicitly unverified, but it must not be silently reported as passing.
