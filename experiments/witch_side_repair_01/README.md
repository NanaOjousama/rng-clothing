# witch_side_repair_01: small side-view repairs for the AI-ORIGINAL witch hats (user, 2026-10-13)

User request: 2-3 small repair variants of the witch hats' side silhouettes/brims (no redesign), originals kept,
each worn with vanilla Covered hair (ESM carrier, HairMode Obscured), 4 directions, FS hat/accessories cleared before
each capture. Nothing in the generator / permanent pool / repo ESM index.

## Variants (`tools/grids.py`, built by `tools/build_variants.py`; sprites `out/sprites_x12.png`)
Front and Back are the exact round-2 sprites; only Right is redrawn, Left = mirror of Right; own palette only; the
brim's bottom row is unchanged so the hat seats at the same height.
| variant | witch s8 | witch s9 |
|---|---|---|
| orig | round 2 | round 2 |
| A clean | solid curled tip (was a 1-px wire), closed brim tips, no light pixels in the bottom outline | black holes in the brim filled, back edge closed, under-brim lump evened |
| B clean + taper | A + crown flares into the band (no stick-on-plate) | A + band 1 row instead of a 2-row yellow block, even under-brim |
| C taper + compact | B + brim 2 px shorter | B + brim 2 px shorter |
| D lean back (s9 only) | - | B with the crown mirrored so the side tip curls toward the back of the head, like all 17 reference witch hats in `../witch_reference_packs_01` (round-2 s9 leans toward the face) |

Garments `exp.wsr01.witch_s{8,9}.{orig,A,B,C}` installed into the STAGED ESM copy (from esm_hairmode_test_01).
ESM loads a garment texture from disk by path on first draw, so no game restart is needed for new variants.

## Capture status
- Run `WSR_*` (session 20261013-000708) is INVALID: FS kept drawing the round-2 s9 hat on every capture (stale FS
  state after the bridge's `clear_hat` only deleted the FS key; FS itself writes "None").
- Bridge got `fs_dump` / `fs_clear_all` (FS API ClearAppearance Hat + Accessory -> CustomHat "None",
  accessories "[]", hat slot emptied). After a game restart the save still had FS hat = LW01 07 Bear; cleared.
- **Valid run `WSR3_*` (session 20261013-003631)**: fs_clear_all before every hat (each showed None / [] / empty slot).
  Checks: baseline no-hat and after-unequip renders pixel-identical to the original no-hat render (4 dirs);
  `orig` renders pixel-identical to the ESM2 covered captures; every variant has covered hair 30 in all 4 dirs;
  every variant differs from orig in Right/Left only (Front/Back identical).
- Sheets: `out/witch_s8_side_repair_worn_x3.png`, `out/witch_s9_side_repair_worn_x3.png`,
  true-size side views `out/side_views_true_size_x1.png`. (s9 orig front caught a blink; not a hat effect.)
