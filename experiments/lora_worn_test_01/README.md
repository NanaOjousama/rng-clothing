# lora_worn_test_01 — worn test of phase-2 LoRA hats (AI-ORIGINAL, CLAUDE.md §2b)

User request 2026-10-12: worn-test 7 picks from the phase-2 clean-front LoRA eval, colour drift corrected with
the front palette (keep shading/details), separate FS pack, 4-direction worn capture. **Experiments only:
nothing goes to the generator or any pool without explicit user approval.**

## Inputs / provenance
- `input/worn_picks_atlas.png`: 7 rows x front|right|left|back (20x20, alpha = hat mask), exported on the laptop
  from the eval renders (md5 de0eb4f9…, verified identical on the Deck). `input/worn_picks.json`: model, LoRA
  checkpoint (`sdvhat_phase2_cleanfront-000006`), render file + seed per hat, captions.
- Fronts: phase-1 LoRA renders (decoded). Right/left/back: phase-2 LoRA (method C, front held clean).
  Bear: corrected caption ('teddybear hat …', see `lora_sdxl_research/analysis/caption_audit.md`).

## Build
    python3 -I tools/build_worn_pack.py --install
- Colour: every side/back cell -> nearest FRONT colour (OKLab, chroma x2: hue family kept, lightness picks the
  ramp step). Front untouched. Mean move 0.02–0.06; ≤ 11 'far' cells per view (listed in `out/report.json`).
  Before/after: `out/<hat>_compare_x8.png`, `out/contact_x4.png`.
- Seat: HeadPosition from the source construction (flowers, bear) or best-IoU library host; all (0,0)/default,
  frog (0,1).
- Pack `[FS] LoRA Worn Test 01` (`LoraWorn.T01`), 7 hats `LW01 nn <name>`, installed in Mods.

## Worn QC 2026-10-12 (`qc_bridge/captures/20261012-222738/`, sheets `out/worn_heads_x3.png`, `out/worn_worn_contact.png`)
Note: the `_head`/`_screen` crops are taken from a vertically flipped screen grab and miss the farmer; the
`_worn` renders (isolated farmer, 256 px) are the valid evidence. Indoors capture is fine for `_worn`.

| hat | verdict (by eye, worn) |
|---|---|
| 02 Witch s9 | **best**: one hat in all 4 views, brim + buckle consistent, seated |
| 01 Witch s8 | good sides/back; front brim is ragged (phase-1 front), reads smaller than the sides |
| 06 Purple flower crown | good, consistent, seated; left view sits slightly forward |
| 03 Frog | good: eyes + white mouth carry to the sides; mouth line overhangs like a visor; plain back OK |
| 07 Bear | sides/back read as a bear head; **front covers the farmer's whole face** (front is taller than the sides) |
| 05 Pink flower crown | flowers move between views (big rose front-right / top / back-right); left view perches on top |
| 04 Bee | **seated too low / too big**: band crosses the eyes, side views cut diagonally across the face |

Not promoted. Next (user decides): fix bee seat (raise ~2 px) and bear front height, or drop them; witch s9,
witch s8, purple crown, frog are candidates for user approval.

## Round 2 (user review 2026-10-12, worn captures `qc_bridge/captures/20261012-231033/`, sheet `out/round2_before_after_x3.png`)
User flags: witch s8 shows the farmer's head through the hat (front + back); frog left-view eye not red;
witch s9 side 'a little deformed'.
- **Head gaps (witch s8, witch s9 only = solid felt hats):** empty cells inside a row's hat span, with hat right
  below them, that the round-1 *no-hat* capture shows lie over the farmer -> filled with the most common
  non-outline neighbour colour. Evidence-driven: gaps over empty background (tip curl) stay open. A first
  unrestricted pass also filled the frog's face opening and the gaps between crown flowers -> restricted.
- **Side accent sync** (not crowns): an accent colour on one side view and missing on the other is copied to the
  mirrored cells. Frog: red pupils copied to the left eye (the LoRA drew it solid black, before any snapping).
- **Witch s9:** right := mirror(left) (left was clean; right had a bent tip and a stray gold pixel).
- Result (worn, by eye): witch s8 no longer shows hair through the brim/crown; frog eyes match; witch s9 sides match.
- Install now updates the pack IN PLACE (recreating the folder changed its mtime and `qc.py refresh` correctly
  demanded a game restart, needed once this round).
- Bridge note: the first capture after a fresh save load returned wrong poses (front pose in every column) while
  render_state still said the right facing; a second `worn` run was correct. Always eyeball a capture sheet.

## Hat-hair test (user, 2026-10-12): vanilla covered-hair behaviour on the witch hats
Sheet: `out/hathair_test_x3.png`; captures `qc_bridge/captures/20261012-231033/HH_*`. No hat redesign; the user's
hairstyle (38) was never changed; the hat slot was empty before and was cleared after (`clear_hat`).
- **Vanilla mechanism** (Data/hats.json field 2): `true` = real hair (30 hats), `false` = covered hair (82 hats,
  incl. Witch Hat id 70), `hide` = no hair (10). Covered = `getHair()` swaps the hairstyle to its covered variant.
- **Fashion Sense: no hat-model property for it** (confirmed in `references/fashion-sense-official/src`).
  HatModel has only `HideHair` (no hair at all) and `UseBaldHead` (bald head sprite). The covered swap exists only
  in `DrawManager.DrawHairVanilla` (line 483) and is keyed to the VANILLA hat item in the slot
  (`who.hat.Value.hairDrawType == 1`), so it applies only to vanilla hairstyles, never to FS custom hairs.
- **Measured in game (confirmed):** FS witch hat + vanilla Witch Hat in the slot -> only our hat is drawn (no
  vanilla sprite: every extra changed pixel is in the hair band below the brim), hair 38 -> 30 (covered). The
  hair puff that stuck out under the narrow brim (s8 sides/back) is gone; hair hangs as side locks.
- **Limitation:** not an FS hat setting; it needs a real vanilla hat item (with showRealHair=false) occupying the
  hat slot. Workable for a dev test, not as an FS-only pack feature.
- **Likely route for shipped hats (untested):** the Enhanced Sewing Machine already gives every generated hat a real
  Stardew Hat carrier (`(H)RNGClothing.ESM.GeneratedHat`); its hats.json entry can say showRealHair=false and the
  vanilla renderer would apply covered hair natively. Needs its own worn test.
