# Sailor pool — in-game validation pass 03

**Status:** applied, 2026-09-05.
**Trigger:** third in-game review (SMAPI session 22:20 → 00:32, testing the
pass-02 build installed at 22:01 — confirmed from the log).
**Evidence:** `output/v5_sailor_ingame_fix_03/before_after.png`.

Geometry / view-realization only.

## Why pass 02 did not fix 002, 004 and 011

Pass 02 treated "armpit hole" as a **mask** defect and proved transparency
bites were zero across all 96 rolls. The reports persisted because the defect
was never transparency — it was **value**.

The shoulder articulation piece carried the `under_layer` role. On the back its
cells sit at the frame's outer columns, *inside* the area the collar band and
flap cover. Measured over seeds 0–95 it rendered a median **+165 luminance
above its inboard neighbour on 76 of 96 rolls** — a lone near-white pixel at
the armpit, which reads as a cut-in.

Pass 02's "make it a shadow" change could not work: a shading offset moves
within the piece's *own* role ramp, and this role's ramp starts far lighter
than the fabric around it. On `SAILOR_WHITE_NAVY` the "darkened" cell still
rendered 209 against 34.

## Changes

| # | shared motif | change | addresses |
|---|---|---|---|
| 1 | shoulder articulation role | `under_layer` → `body` | 003, 004 |
| 2 | back articulation | removed entirely | 002, 011, 004, 045 |
| 3 | `hem_band` ornament | inset from the outer columns, `max_cells` 8 → 6 | 040 |
| 4 | MIDDY `waistband` | inset from the outer columns | the white/yellow band pattern |
| 5 | `TIE_SIDE_SHADING` | 4 cells wide → 2, tapering | 000 |
| 6 | `surface_period` weights | favour the sparser period (0.25/0.75) | 025 |

**On (2):** the back's top rows are covered by the collar band and the flap, so
this cell was never "the shirt re-emerging at the shoulder" — it was a hole
punched through the middle of the trim. No reference back frame carries a light
articulation.

**On (3) and (4):** both painted the entire bottom row edge to edge in a single
accent/trim value — literally a rectangle wrapped around the sprite. The
waistband alone owned 29 of the 43 such bands measured across the pool. A hem
band should sit *on* the garment, not wrap the frame.

**On (6):** the domain keeps 2. Moving it to (3,4) made both values fail
`period_reads` on shallow domains, which dropped Surface and exposed a latent
`KeyError` in `check_continuity`. Reweighting gets the same subtlety without
destabilising the drop path. Stripe cells are one row; spacing is the only
lever this envelope has.

## Measured effect

| | before | after |
|---|---|---|
| front outer-column luminance spike (median) | +159 | **0** |
| back outer-column luminance spike (median) | +165 | **+12** |
| rolls with a >60 spike (back) | 76 / 96 | **27 / 96** |
| full-width uniform high-contrast bands | 43 | 32 |
| side tie cells (median) | 9 | **4** |

## Acceptance moved UP

92 → **93 ACCEPT**, 1 IDENTITY_TOO_WEAK, 2 NEAR_DUPLICATE. Seeds 13, 23, 54 and
76 all recovered.

That is not a coincidence and not a retune: **no QC floor, separation rule,
retention setting or palette rule was touched**, and the configuration test
still passes unchanged. The articulation piece was `under_layer`, the same role
`under_layer_vs_trim` is measured on, and it was spending that role's area on a
pixel buried inside the trim. Removing it gave the measurement back the area it
was supposed to be reading. The defect and the false rejections had one cause.

Only seed 24 still fails identity — the CLASSIC / `LIGHT_BODY_DARK_COLLAR`
affinity already on record.

## Still borderline — not fixed

* **32 full-width bands remain** (down from 43), mostly MIDDY front row 7 where
  the hem row is the whole silhouette width. Insetting cannot help there.
* **025's stripes** are subtler but still read as banding on a shallow shell.
  Making them genuinely thinner is not expressible at 8×8.
* **013's back** is still a broad flat green mass; the flap taper helps the
  outline, not the interior.
* The side view is better but remains the weakest of the three frames.

## Addendum — 025 stripe termination

Requested after the pass-03 build: the back's middle white line still read as
too continuous. `figure_cells` now drops the first and last cell of each
horizontal-stripe run, so the stripe terminates on the garment body rather than
running edge to edge — the same rule already applied to `hem_band` and the
waistband, and matching how the front view cuts its linework at the garment
boundary.

Seed 025 back row 5 before `224 246 246 246 246 246 246 224`,
after `71 246 246 246 246 246 246 71`.

Only applied where the run has more than three cells, so a short stripe is not
erased. Acceptance unchanged (93 / 1 / 2); 60 tests pass.
