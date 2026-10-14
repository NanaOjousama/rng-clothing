# witch_cleanup_01 — AI-ORIGINAL witch hat cleanup pass (2026-10-13)

Lane: AI-ORIGINAL (§2b).  Isolated; nothing installed, nothing in generator / pools / training.
Inputs: round-2 witch s8 / s9 (`lora_worn_test_01`, from the phase-1/2 LoRA), their palettes;
proportion guidance from `witch_reference_packs_02` (REFERENCE, 492815.FS) — studied, not copied.

User asks addressed: "italic" lean (narrow crown slanted from the band up), s7's hanging orange buckle
(dropped; s7 itself is not carried forward), crude 4-view look (noise, blob back).

Changes, all four views hand-drawn in `tools/grids.py` (each hat's own round-2 palette, no new colours):
- crown base ~60-65% of brim width, upright and centred; only the top 3-4 rows bend; tip folds back/down
- s8 tip flops right on the front, s9 left (pair stays distinct); s9 crown 1 row shorter
- thin gull-wing front brim (drooping ends, open centre), one clean band row (+1 highlight px on s9)
- Back = Front crown mirrored with colour runs re-reversed (light stays upper-left); closed 3-row brim
- Left = Right mirrored.  4-5 colours per view instead of 6-8; no stray pixels
- seat: crown base row 9, brim ends to row 13 (vanilla witch brim bottom = row 12, ref 492815 = 14) — to verify worn

Build: `python3 -I tools/build.py` (dependency-free) -> `out/textures/witch_s{8,9}_clean.png` (20x80, F|R|L|B).
Sheets (analysis, .venv): `out/compare_v1_x8.png`, `out/compare_v1_x3.png` — before | cleanup | ref tall | ref short.

Not done yet: user review of the sheet; then worn QC through the staged ESM (Covered hair, `fs_clear_all`
before each hat, 4 directions).  e10 re-run from the new fronts is optional (comparison only).

## v2 (user review of v1, 2026-10-13)
User: (1) side view too flat / assembled — use the reference side construction; (2) band too straight, sticks out.
- Side (R; L mirrored): rebuilt on the ref 492815 construction — brim is one tilted piece, front edge out flat at
  rows 7-9 with its top surface lit, back edge sloping down-left to row 14; the crown sits INTO the brim (its back
  edge meets the sloping brim); tip still leans back and hangs.  s9 side = s8 side recoloured, 1 crown row shorter.
- Band follows the form, inside the crown silhouette: front arches (centre row 8, ends drop to row 9), side runs
  along the brim slope in 1-px stair steps, back dips (ends row 8, centre row 9).
- v1 grids kept in `tools/grids_v1.py`; textures `out/textures/witch_s{8,9}_clean_v1.png` / `_v2.png`.
- Sheets: `out/compare_v2_x8.png`, `out/compare_v2_x3.png` (round 2 | v1 | v2 per hat, + ref tall); v1 sheets kept.
