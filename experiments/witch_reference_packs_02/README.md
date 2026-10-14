# witch_reference_packs_02 — REFERENCE ONLY (2026-10-13)

`[FS] Witch Hat 492815` (uniqueid `492815.FS`, author 내편엘리엇, FS code by Mychocolate, v1.0.0), unpacked
from the user's `~/Downloads/[FS] Witch Hat 492815.zip` into `raw/`.  User instruction: study the shape and use it
to guide the witch cleanup pass; **not in training** unless decided later.  Personal-use project; author recorded.
Read-only: nothing here is composed, trained on or installed.

10 hats = **2 silhouettes x 5 colours** (odd hats_N = short crown, even = tall crown with a curled tip).
All 20x80, F|R|L|B at y 0/20/40/60, HeadPosition 0, so they sit at plain vanilla hat placement.

Tools (analysis only, `.venv`): `tools/witch_shape.py` (brim row/width, crown spine lean), `tools/sheet.py`
(zoomed grid sheet).  Sheet: `out/study_x8.png` (new short, new tall, two recolours, our round-2 s8/s9).

## What the shape does (by eye on the x8 grid, spine numbers from witch_shape.py)

| | new pack | ours (round-2 s8 / s9) |
|---|---|---|
| Front crown base width | 14-16 px of a 20 px brim (~75%) | 7-8 px (~40%) |
| Front lower crown | upright, centred, lean 0.0-0.2 px/row | narrow and slanted, off-centre -> the "italic" look |
| Bend | only the top 3-4 rows; tall version curls right then hangs **down**, tip pixel below the curl (tip folds back) | whole crown leans from the band up |
| Front brim | full 20 px, thin (2 rows), centre raised under the crown, both ends droop 4-5 rows: a gull-wing, not a flat oval | flat oval, thick, noisy |
| Band | one clean 1-row band at the crown base, + a few band-colour pixels on the brim edge | s7: buckle hanging below the brim; s8/s9: blocky |
| Side | brim is a long diagonal: front edge reaches out flat, back edge slopes down; crown sits toward the back, tip bends back (-1.5 to -2 px) | sides already OK after e10 |
| Back | same wide upright crown, tip flops to one side, brim droops lower than the front | dark blob |
| Shading | 3-4 tone ramp, light from upper left, outline mostly on the brim underside, no stray pixels | 6+ shades, stray pixels |

## Cleanup-pass targets taken from this (guidance, not copying)
1. Front: widen the crown base to ~70-75% of the brim, upright and centred; bend only the top third; the tip folds back/down.
2. Brim: thin gull-wing with drooping ends instead of a flat oval.
3. Band: single clean row at the crown base; s7's hanging buckle removed.
4. Back: wide crown matching the front, tip flopping to the same side as the side views' lean.
5. Palette: one 3-4 tone ramp + band colour; no stray pixels.
