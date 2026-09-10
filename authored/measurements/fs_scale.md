# Fashion Sense `Scale` — measured, 2026-09-09

Session `20260909-190048`, pack `RNG-ScaleTest`, four appearances carrying
**identical art**; only `Scale` differs. `Scale` is per-direction on
`AppearanceModel` and defaults to `4f`, so the proposed 0.95 / 1.00 / 1.05
fitting multipliers are 3.8 / 4.0 / 4.2. A clean 2x (8.0) was included as a
sanity control.

## Verdict: 0.95 and 1.05 FAIL. Scale stays disabled.

## What was measured

Horizontal runs of one solid colour across the hat, over **every** hat pixel
with no exclusions. Under nearest-neighbour at Scale 4, one source pixel is
exactly 4 screen pixels, so every run must be a multiple of 4. A run that is
not is a source pixel that got stretched unevenly.

| Scale | facing | runs | not a multiple of 4 |
|---|---|---:|---:|
| 3.8 (0.95x) | front | 342 | 128 (**37.4%**) |
| 3.8 (0.95x) | right | 364 | 116 (**31.9%**) |
| **4.0 (default)** | front | 296 | 0 (**0.0%**) |
| **4.0 (default)** | right | 320 | 0 (**0.0%**) |
| 4.2 (1.05x) | front | 339 | 131 (**38.6%**) |
| 4.2 (1.05x) | right | 341 | 115 (**33.7%**) |
| **8.0 (2x)** | front | 624 | 0 (**0.0%**) |
| **8.0 (2x)** | right | 652 | 0 (**0.0%**) |

At 3.8 and 4.2 roughly a third of all runs are irregular, with widths of 1, 2,
3, 5, 7 and 9 screen pixels mixed together where every one should be 4. That is
**uneven pixel stretching**, which the acceptance criteria name as a failure.

Direction-specific jitter is present too: at 4.2 the front bounding box does not
change at all (56px, same as default) while the right view grows 68 → 72. The
same nominal scale therefore resizes some facings and not others.

## Two things this is NOT

**Not interpolation.** Foreign colours (values in neither of two blended source
colours) sit at 7.7–11.4% across *every* case including the crisp 4.0 default —
they are edge blending against the body, not resampling. Colour count cannot
separate these cases; run length can.

**Not rounding to an integer.** If Fashion Sense rounded 3.8 up to 4, the output
would be byte-identical to the default. It is not — the run histogram is
completely different. Fashion Sense honours the float and resamples with
nearest-neighbour, and nearest-neighbour at a non-integer factor is precisely
what produces uneven runs.

## Consequence

The fitting mod exposes **no scale control**. Only integer multiples of the
4.0 base (4.0, 8.0) render crisply, and those are far too coarse to be a
fitting adjustment — one step would double the hat.

Position, by contrast, is exact: whole-pixel `HeadPosition` steps move the hat
4 screen pixels each with no distortion.

## Reproduce

```
python3 tools/build_scale_test.py --install    # then restart the game
```
