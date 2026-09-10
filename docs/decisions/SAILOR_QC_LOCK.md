# Sailor pool QC — locked

**Status:** locked, 2026-09-04, by human visual review of a 96-seed batch.
**Pinned by:** `v5/tests/test_v5.py::SailorQCLock` (4 tests).
**Evidence:** `output/v5_sailor_pool_08/` — batch, contact sheet, `nine_verdicts.png`.

## What is locked

Both Sailor Architectures declare:

| | CLASSIC_SQUARE_FLAP | MIDDY_YOKE |
|---|---|---|
| `identity_floor` | 80.0 | 80.0 |
| `identity_retention` | 0.80 | 0.80 |
| `identity_composite_floor` | 1.20 | 1.20 |
| `max_appearance_features` | 3 | 3 |

Separation rules (scale × floor, required?, gated on feature):

* CLASSIC — `trim_vs_body` 1.0 req · `under_layer_vs_trim` 0.5 req ·
  `accent_vs_body` 0.7 req (tie) · `accent_vs_trim` 0.8 req (tie)
* MIDDY — `under_layer_vs_trim` 1.0 req · `accent_vs_body` 0.7 req (tie) ·
  `accent_vs_under_layer` 0.4 warn (tie)

Acceptance is **compositional**: a required shortfall is recorded but is only
fatal when the weighted-mean identity composite also falls below 1.20.  Shortfalls
that the other cues carry become warnings.  **Retention is separate and remains
independently fatal** — it fixed a real defect (a braid repainting up to half of a
one-pixel collar) and is active on 44 of 96 rolls.

## Locked outcome, seeds 0–95

92 ACCEPT · 2 IDENTITY_TOO_WEAK (23, 46) · 2 NEAR_DUPLICATE (21→12, 73→44) ·
0 projection problems · colours median 13.

## Known, accepted residual

Seeds **24 and 30 are accepted** though a reviewer would reject them, and seed
**46 is rejected** though a reviewer would accept it.

Seven candidate cues were measured against the reviewer's split — collar-vs-body,
insert-vs-collar, tie-vs-body, tie-vs-collar, dominant-blob area, trim area
fraction, collar-mass vertical position.  **None orders the two groups apart.**
The blocking evidence:

* **30 vs 40** agree within ~10% on every cue (composite 1.42 vs 1.49) and the
  reviewer split them.
* **24 scores above 69** on the composite (1.31 vs 1.28) and the reviewer accepted 69.
* **46 has the lowest composite of the nine** (1.00) and the weakest
  collar-vs-body in the batch (91 against a floor of 80).

This is treated as human-review noise, not as a modelling gap.

## Deliberately not done

* No further tuning to reproduce the manual calls.
* No new identity metric.
* No low-chroma palette penalty — the current evidence does not justify
  broadening the rejection logic.

## Re-open condition

Only a **repeatable failure pattern found in in-game testing**.  That is the
evidence this configuration is waiting on and the only thing that should move
these numbers.  When it happens, change the declaration and update
`SailorQCLock` in the same commit, so the pin and the behaviour never disagree.
