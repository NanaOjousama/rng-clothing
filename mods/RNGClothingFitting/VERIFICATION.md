# Fitting mod — in-game verification

Everything below needs **one game restart first**: `RNGClothingFitting`,
`RNG-Cap2Fit` and `RNG-ScaleTest` are all new folders, and Fashion Sense only
registers packs the game already knew about at startup (`fs_reload` refreshes
existing packs; it cannot introduce a new one).

## Getting a test cap

The `RNG-Cap2Fit` pack ships six controlled rolls, chosen by the same roller as
every other Cap 2 proof. Two are worth using:

```
qc give RNGClothing.FashionSense.Cap2Fit/Hat/Cap2_Unco_Desert_bar_846106117/Item
qc give RNGClothing.FashionSense.Cap2Fit/Hat/Cap2_Rare_Pastel_ring_clasp_905331759/Item
```

`bar` has 8 legal design positions, so design movement can actually be
exercised. `ring` has exactly one, so it is the case that must show the
*blocked* message rather than deform the mark.

Wear the cap, then use any sewing machine.

## Headless checks (run these first)

```
./tools/run_fitting_tests.sh     # 120 checks over the pure logic
```

Covers what does not need a running game: the HeadPosition inversion, hat
bounds refusal, mask blocking, screen<->cell mapping (every pixel at 1x/2x/4x),
undo/redo exactness and bounding, symmetry legality, and session restore. They
run against the REAL generated sidecars, so a generator change that breaks the
mod's assumptions fails here.

## Steps

1. **Entry point.** At a sewing machine wearing the cap, *Adjust Fit* appears.
   Open it with the mouse and again with `LT`.
2. **Vanilla is preserved.** Remove the cap, or wear a vanilla hat, and reopen
   the sewing machine: no button, tailoring behaves normally.
3. **Live preview.** Move the cap one step in each of the four directions and
   confirm the farmer preview moves **the way the label says** — right is right,
   down is down. This is where an inverted sign would show.
4. **Whole pixels only.** Each step should move the cap exactly 4 screen pixels
   with no blur or partial offset.
5. **Bounds.** Push the cap past ±3 in any axis: the move is refused with a
   message, and the cap does not creep.
6. **Design, movable.** On the `bar` cap, switch to Design and move it. It stays
   inside the crown; the visor and rim never change.
7. **Design, blocked.** On the `ring` cap, any move is refused. Confirm the mark
   is **not** clipped or half-moved.
8. **Cancel.** Adjust, then Cancel: the cap returns to where it was on opening.
9. **Save and persist.** Adjust, Save, then sleep/save and reload: the fitting
   is still applied.
10. **Reset.** Reset returns the cap to the generated default exactly — check
    against a freshly given copy of the same cap.
11. **Controller only.** Repeat 3, 6, 8, 9, 10 using only the controller.
12. **No collateral.** Check the SMAPI log for warnings from
    `RNGClothing.Fitting`, and confirm other Fashion Sense hats are unaffected.
13. **Deferred open.** The log line `Opening fitting for <id> (via ...)` should
    appear on the tick AFTER the press, and opening must work from both the
    mouse and `LT`.
14. **Controller only.** Put the mouse down entirely. The d-pad must reach every
    control (tabs, the four nudge arrows, 1x/2x/4x, Turn, Undo, Redo, Reset,
    Cancel, Save) with A activating, B backing out. The left stick should nudge
    directly and the shoulder buttons switch target.
15. **Readability.** 1x / 2x / 4x change the grid zoom, and the worn farmer
    stays visible throughout — gameplay scale is the authority.
16. **Undo/redo.** A few nudges, then Undo repeatedly: each step must land
    exactly where it was. Redo retraces. A blocked nudge must NOT consume a step.
17. **Session restore.** Switch to Design, set 1x, Cancel, reopen: the tab and
    zoom come back, and the cap's fit does not change.
18. **No needless rebuilds.** Nudging the cap (not the design) should never
    rebuild the design texture.

## Scale (separate, gates a feature that is currently off)

`RNG-ScaleTest` holds identical art at Scale 4.0 / 3.8 / 4.2 / 8.0. Compare the
three near-default entries for blur, interpolation, uneven pixel stretching and
direction-specific jitter at normal gameplay scale.

If 3.8 and 4.2 are not crisp, the scale control stays disabled — it is not
exposed today and will not be until this passes.
