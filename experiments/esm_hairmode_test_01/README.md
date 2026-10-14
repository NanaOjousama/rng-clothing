# esm_hairmode_test_01: vanilla covered hair through the Enhanced Sewing Machine carrier (2026-10-13)

User request: test whether the ESM hat carrier gives the witch hats vanilla covered hair. No redesign, nothing in
the generator / permanent pool / repo ESM source or index. AI-ORIGINAL art from `../lora_worn_test_01` (round 2).

## Setup
- `tools/build_esm_test.py --install`: 4 temporary garments `exp.lw01.witch_s{8,9}.{full,covered}` (HairMode Full /
  Obscured), exact round-2 sprites, vanilla placement (20x20, RenderScale 1, anchor (10,16) = qc/vanilla_trucker16).
- Staged a copy of the packaged ESM build into `Mods/EnhancedSewingMachine` (marker `.esm_hairmode_test_01`) with an
  index.json registering ONLY these 4 garments. SMAPI: "Garment registry loaded 4/4". Undo: delete that folder.
- Equipped through the bridge's `equip_garment` = the real carrier `(H)RNGClothing.ESM.GeneratedHat` with the
  garment's hairDrawType (same as GarmentItemService.Write).

## Results (worn, session `qc_bridge/captures/20261013-000708/ESM2_*`, sheet `out/esm_hairmode_compare_x3.png`)
| check | result |
|---|---|
| covered hair activates automatically | **yes**: hair 38 -> 30 in all 4 directions for both `.covered` items; `.full` stays 38 |
| no duplicate vanilla sprite | **yes**: `.full` renders are PIXEL-IDENTICAL to the FS round-2 captures (both hats, 4 dirs) |
| looks better | **yes** (by eye): the hair no longer bulges under the narrow brim (s8 sides/back, s9 back); side locks instead |
| unequip restores hair | **yes**: no-hat render after unequip is pixel-identical to the original no-hat render |
| other hats / hairstyle untouched | **yes**: hairstyle setting 38 throughout; FS frog afterwards shows normal hair 38 |

## Gotchas found
- First attempt (`ESM_*`) drew the FS **bear** instead: the save still had FS custom hat = bear (FS stores it in
  player modData), and `equip_garment` does not clear it, so FS kept drawing its hat. Clear the FS hat first
  (`clear_hat`). Covered hair still applied there (FS reads the slot's hairDrawType).
- `equip_garment` moves the previously worn hat into the inventory. The first run left up to 3 test hats
  (witch s8 full, s8 covered, s9 full) in the player's inventory; the second run cleared before each equip.
