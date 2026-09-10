# Decorative line termination — shared rule

**Status:** applied, 2026-09-05. **Pinned by:** `LineTermination` (5 tests),
`SurfaceDropsSafely` (1 test).

## The rule

> Any decorative line or band whose run **ends** on the silhouette boundary
> should end one cell inboard instead.

The garment boundary is where the Farmer's arm and body edge are drawn, so a
line terminating exactly there reads as passing through the figure rather than
as part of the shirt. This is a general 8×8 sprite rule, not a Sailor one.

It arrived from three independent confirmations — `hem_band` (040's "yellow
rectangle across the torso"), the MIDDY `waistband`, and horizontal stripes
(025's "middle white line too continuous") — each fixed locally before the
shared shape was obvious.

Implemented once as `grammar.terminate_inboard(cells, run_axis, min_run)` and
called by both Surface and Ornament.

## What it applies to

| motif | layer | treated |
|---|---|---|
| `horizontal_stripe` | Surface | yes (run_axis 0) |
| `vertical_stripe` | Surface | yes (run_axis 1) |
| `hem_band` | Ornament | yes |
| `cuff_band` | Ornament | yes |
| `panel` | Surface | **no** — a contiguous structural block whose edges are meant to land on the garment boundary |
| seams, outlines, silhouette treatment | Construction | **no** — the boundary is the point |

## The guard

`LINE_MIN_RUN = 4`. A run shorter than that is returned intact.

This is the substance of the helper, not a detail. Insetting a 2-cell run
erases the pattern rather than softening it — the same class of failure as the
`surface_period` change that had to be reverted, where making every period fail
readability dropped Surface entirely and exposed a crash.

## Prerequisite: the Surface drop path

Fixed first, because broadening the rule increases the chance of producing an
unrenderable pattern.

`aa.py` read `spec.surface.get("period", 2)` — minting a period no variable had
rolled. The surface painted anyway, and `check_continuity` then raised
`KeyError: 'period'` on the key that was never set. A periodic family with no
resolved period is now **absent, not defaulted** (INV-04): it does not paint,
and continuity skips it. Verified by re-running the exact `(3, 4)` period
domain that used to crash — 96 rolls, no exception.

## Measured effect, seeds 0-95

Endpoints landing on the silhouette boundary:

| motif | before | after | note |
|---|---|---|---|
| `vertical_stripe` | 64 (6 rolls) | **18** (5 rolls) | all residual guarded |
| `cuff_band` | 53 (11 rolls) | **45** (11 rolls) | all residual guarded |
| `horizontal_stripe` | 0 | 0 | already treated |
| `hem_band` | 0 | 0 | already treated |
| `panel` | 0 | 0 | exempt by design |

Every remaining endpoint is a run shorter than `LINE_MIN_RUN`:

* `cuff_band` run=2 → 36, run=3 → 9. A PLAIN sleeve cap is one cell per side,
  so its cuff *cannot* be inset without deleting it.
* `vertical_stripe` run=1 → 16, run=2 → 2. Vertical stripes are fragmented by
  the collar and the identity quiet zone.

**Zero unguarded endpoints remain** — pinned by a test over all 96 rolls.

Acceptance unchanged: 93 ACCEPT / 1 IDENTITY_TOO_WEAK / 2 NEAR_DUPLICATE.
Seed 025 renders byte-identically; the helper reproduces the inline version.

## Known follow-on, not addressed

`cuff_band` on a PLAIN sleeve is a single cell per side that necessarily ends
on the arm edge. The honest fix is a readability gate — an ornament whose run
is too short to terminate properly should probably not be placed at all, the
same judgement `flap_stud` already makes for the side view. That is an Ornament
economy decision, not a line-termination one.
