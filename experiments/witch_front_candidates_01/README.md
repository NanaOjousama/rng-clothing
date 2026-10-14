# witch_front_candidates_01 — AI-ORIGINAL witch-hat front candidates (2026-10-13)

Lane: AI-ORIGINAL (§2b), isolated.  Nothing installed, nothing in generator / pools / training.
Brief (user): 8 original FRONT views — 2 short compact, 2 tall floppy, 2 low sweeping (Wildwood-inspired),
2 classic pointed; structural guidance from `witch_silhouette_matrix_01`, no pixel copying; native 20x20 first,
up to 24x24 only if the silhouette needs it.  Fronts must be approved before side/back views are made.

Method: silhouettes drawn as masks (`tools/masks.py`: `#` body, `b` band, `c` crease); `tools/shade.py`
(dependency-free) adds outline + 3-tone shading in ONE shared neutral palette so the shapes are judged, not
colour/decoration.  Bottom of every silhouette on row 13 (vanilla witch brim ends row 12, Naver 14).

| id | family | size |
|---|---|---|
| S1 | short compact: squat crown, flicked nub, gull-wing brim | 20x20 |
| S2 | short compact: pumpkin-round crown, curled tip, flat brim | 20x20 |
| T1 | tall floppy: top third flops LEFT and hangs | 20x20 |
| T2 | tall floppy: slumped, upper half folds RIGHT (crease line) | 20x20 |
| W1 | low sweeping: crown laid left, thick tube ending in a bulb past the brim | **22x20** |
| W2 | low sweeping: crown laid right, tip lies over and drops off the brim end | **22x20** |
| P1 | classic pointed: straight cone, flat brim | 20x20 |
| P2 | classic pointed: cone with crooked tip, drooped brim ends | 20x20 |

W1/W2 needed 22 wide (same as Luny/Wildwood) so the tip can pass the brim; height stays 20.
Outputs: `out/fronts/*.png`, `out/fronts.json` (grids), sheets `out/fronts_x10.png` (pixel grid, red lines =
20-px frame), `out/fronts_x4_real.png` (Stardew zoom 100% + x1), vanilla Witch Hat for scale.

Next after approval: run the selected fronts through the existing Phase-3 LoRA (e10) to generate their side/back
views — no retraining, Wildwood not added to any dataset.

## e10 side/back run 01 (2026-10-13, user picked S1 T1 W1 W2 P2 + optional P1 control; S2 T2 P1 held for revision)
Inference only on the laptop: `C:\Users\Chris\sdxl_lora_research\tools\witch_fronts_e10.py`, existing phase-3
final checkpoint (= e10, `runs\phase3_cleanfront_resume\sdvhat_phase3_cleanfront.safetensors`), seeds 7/8/9,
front held + pasted back (drift <= 0.01).  W1/W2 used the 20-wide test copies in `out/e10_fronts_20.json`.
Captions: `sdvhat, four views..., witch hat, <short squat / tall floppy / low swept / pointed...>, dark purple,
purple, yellow, pixel art, 20x20 sprites, dark outline`.  No training; Wildwood in no dataset.
Output (laptop): `runs\witch_fronts_e10_01\` — `witch_fronts_e10_x{1,4,10}.png`, per-seed png/npy, `strips_native.png`
(20x80 F|R|L|B per job x seed, alpha), `report.json`.

By eye (x10 sheet):
- colour drift: most seed-7/8 views come out near-black, not the front's grey-purple (model's witch prior is black);
  seed 9 keeps the purple best.
- shape: e10 pulls every hat toward its learned "average witch" (tall-ish crown, bent tip).  Works for the families
  it was trained on — T1, P1, P2 good (T1 s9, P2 s9, P1 s9 / s8 back); S1 sides come out taller than the front.
- low sweeping (W1/W2) is NOT carried: s7/s8 sides turn into ordinary witch hats; only s9 stays low on the sides,
  and the backs are blobs.  That family is effectively absent from training (Luny only; Wildwood not included).

User (2026-10-13): this run is a SILHOUETTE TEST only, not a content pass.  None of these hats go into the
generator and they are not polished further.  Verdict per family (can e10 rotate it?):
| family | candidate | verdict |
|---|---|---|
| tall floppy | T1 | rotates well (all seeds keep the hooked tip; s9 best) |
| classic pointed | P2, P1 (control) | rotates well (crooked tip carried; P1 s8 back is a clean cone) |
| short compact | S1 | partial: rotates, but sides grow taller than the front |
| low sweeping | W1, W2 | fails: 2 of 3 seeds turn it into an ordinary witch hat; backs are blobs |
Next (user): keep the matrix; make better-looking front designs before any more four-view hats.
