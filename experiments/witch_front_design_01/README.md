# witch_front_design_01 — method test, 2 sample fronts (AI-ORIGINAL)

User request 2026-10-14: show the proposed front-polish method on **2 samples only**, beside the originals
and references, before any batch / e10 / in-game work.

## Method: hand-placed pixels, reference-measured rules
- Every pixel is placed by hand (Claude) in a role grid (`tools/fronts.py`). There's no auto outline or auto shading.
- The earlier candidates (`witch_front_candidates_01/tools/shade.py`) shaded by horizontal position, with a near-black outline everywhere. That is why they looked mechanical and crude.
- Construction rules were measured from the polished references (Kailey `Witch Hat`, Naver 492815, Wildwood pixel dumps). No reference pixels were copied.
  1. **Brim is a ring around the head:**
     - lit top surface row
     - dark lip across the forehead
     - 4–5-px wings hanging past the temples, tips tucked in
     - open centre where the face shows
     The earlier candidates instead had a flat 1-px plate.
  2. **Band:** one row, lit left / shaded right. Its ends drop one row onto the brim, so it follows the curve.
  3. **Crown:** wide (~75% of the brim top) and upright, with the bend or flop only in the top rows (no "italic" lean).
  4. **Colour:** a hue-shifted purple ramp. The outline is the darkest purple, not black. The light comes from the upper-left as a highlight *cluster*, with a shadow mass on the right.
- 20x20 native; the wing bottom is on row 14 (Naver = 14, vanilla = 12). Scripts only render the grids and build the sheets.

## Samples
- `T1d`: tall, top flops left, tip hangs (family: tall floppy).
- `P2d`: classic cone, tip bends right with a thin curl (family: classic pointed).
- Iterations b/c were rejected in-session: thin "crab-leg" brim wings, a stovepipe crown, and a hook that read as a block.

## Outputs
- `out/fronts/*.png`, `out/fronts.json`
- `out/compare_x10.png`, `out/compare_x4_real.png` (= zoom 100%), `out/compare_x1.png`

## Status
Awaiting user approval of the method. There has been no e10 run, no in-game test, and nothing in the generator or pools.

## Method B: reference-based (user request 2026-10-14), `tools/refbased.py`
The same two designs, composed from REAL reference pixels and mapped role-by-role (outline / shade / base / light /
band) into one purple ramp. There are no hand-drawn pixels and no post-edits; a trial edit left a detached pixel and was removed.
- **T1r** (tall floppy, flops left):
  - Kailey `Witch Hat (Blue)` front rows 1–7, mirrored so its hook flops left
  - Naver 492815 `Witch Hat_10` front rows 7–14 for the band and gull-wing brim
- **P2r** (classic pointed, crooked tip):
  - vanilla Witch Hat front rows 0–5 (crooked cone)
  - the same Naver rows 6–14
- The comparison sheets now show the references | before | A (hand-placed) | B (reference-based).

**Assessment:**
- B sits much closer to the reference style: few tones, flat masses, a clean brim, and a consistent outline.
- It is also closer to the sources: T1r is mostly Kailey + Naver pixels.
- The vanilla crown is short, so P2r reads squatter and less "tall classic" than P2d.
- B's palette is darker and more muted (it follows the reference values); A is brighter.

Phase 4 training is SEPARATE: none of A/B is in any dataset.

## Decision (user, 2026-10-14)

- **Method B (reference-based) is the starting direction** for front artwork.
- T1r and P2r are **not approved final hats**. Nothing here enters the generator without the user's visual approval.
