# Sailor pool — in-game validation pass 01

**Status:** applied, 2026-09-04.
**Trigger:** in-game Fashion Sense review of
`test-packs/fashionsense/RNG-Clothing-V5-Sailor-Validation` (14 garments).
**Pinned by:** `v5/tests/test_v5.py::InGameValidation` (5 tests).
**Evidence:** `output/v5_sailor_ingame_fix_01/before_after.png` — the same 14
seeds, before and after, four frames each.

This is the "REPEATABLE failure pattern" that `SAILOR_QC_LOCK.md` said was the
only thing that should re-open the pool. It re-opened **authored geometry**.
No QC floor, separation rule, palette or generator weight was touched.

## Reported

| seed | reported in game |
|---|---|
| 003 | rear flap / back straps sit too far outward |
| 004 | thin white separation line between sleeve/shoulder and arm, worst from the back |
| 013 | rear collar/flap reads as a flat horizontal band across the shoulders |
| 014 | front collar/insert collapses into a flat horizontal band; weak V |
| 025 | strong candidate; rear striped flap too blocky/straight |
| 040 | front collar mass too wide/flat vs the centre insert; back flap a straight bar |
| 045 | back white flap/stripe lines up as two bars through the arms |
| 083 | front insert/dickey reads as a rectangular box under the chin |

Held as borderline, not acted on: the neck-skin-pixel observation. It did not
repeat across garments, so there is nothing here to fix yet.

## Diagnosis

Seven of the eight are `CLASSIC_SQUARE_FLAP`; the eighth (003) is `MIDDY_YOKE`
but reports a back defect the two Architectures had **duplicated verbatim**. The
one unflagged CLASSIC in the pack (017) is the only one with a `POINTED` flap,
whose taper happened to mask two of the four motifs.

So the eight reports are not eight garments. They are four shared authored
motifs, each measured across the whole 96-seed pool:

| motif | measured before | after |
|---|---|---|
| back articulation ≥3 rows deep per side | 53 / 96 rolls | 0 |
| rear flap is a perfect rectangle | 51 / 96 rolls | 0 |
| collar shoulder row renders one flat colour | 95 / 110 rows | 0 |
| dickey brightest directly under the chin | 46 / 47 CLASSIC | 12 |

### 1. The back shoulder articulation was scoped to the flap depth

Both Architectures wrote the back articulation as
`for y in range(1, rear_flap_depth)` at columns 0 and 7, shaded one step
lighter. At `flap5` that is a four-row, one-pixel column of the lightest colour
on the sheet, down the outer edge of the back frame — which is where the
Farmer's arm is. That is 003 and 045 exactly, and where it crossed the sleeve it
also produced 004's split line.

The front already scoped the same piece to the **sleeve cap**. The back is now
scoped the same way, anchored at the shoulder row rather than at the flap.

### 2. The rear flap was a rectangle

`cols 1..6 × rows 0..depth`, constant, and `SQUARE` carved nothing at all — so
half the pool rendered a six-of-eight bar with a straight hem. Replaced with an
authored `flap_outline`: narrow at the neck junction, full span over the
shoulders, hem shaped by the edge profile. `apply_flap_edge`'s two-row curve now
only fires where a full-span row survives underneath, so a shallow flap is not
carved straight back into the rectangle it was meant to lose.

The flap's cast shadow (which `PIPED_EDGE` trim then follows) was also taken off
the nominal span, drawing a straight line under a carved hem — a second hard
band. It is now computed per column from the flap's own cells.

### 3. CLASSIC's collar had no authored interior

Every row above the V was filled with one flat shading value, so 95 of 110
shoulder rows rendered as a single colour across the whole frame. `MIDDY_YOKE`
already had `YOKE_STENCILS` for exactly this, which is why its fronts read as a
yoke worn on shoulders and CLASSIC's read as a slab. CLASSIC now has
`COLLAR_SHOULDER_STENCILS`, keyed by silhouette because each cuts its neck
opening differently.

### 4. The articulation was eating the collar's V arm

On the front, the articulation sat at columns 0/7 on the collar's **first V
row** — the row where the arm is widest. A two-wide collar therefore rendered
one wide, and the collar mass fell from full width to a single pixel in one
step. That step is 083's "box under the chin" and 040's "too wide/flat relative
to the centre insert". The articulation is now strictly outboard of the collar,
so it appears one row lower, where the collar has genuinely left the frame edge.

### 5. The dickey was lit upside down

`INSERT_STENCILS` put its brightest cells at the centre of the top row —
directly under the neck opening — on 46 of 47 CLASSIC rolls. The shadow is
written as **light on the outer pair** rather than dark on the centre pair,
because a dickey whose role already sits at the bottom of its ramp (every
`DARK_BODY_LIGHT_COLLAR` roll) cannot be darkened further and collapsed to one
flat colour when tried that way.

12 rolls still read brightest-under-chin and 6 render the row flat. In all of
them the AA edge pass spent the ramp separating a light collar from a light
dickey. Separation correctly outranks modelling, so the test bounds that
residual instead of forbidding it.

## Effect on the QC lock

The locked **configuration** is unchanged and its test still passes. The pinned
**outcome** moved, because the geometry it measures moved:

* accepted: 92 before, 92 after
* seed 46 — documented as "REJECTED though a reviewer would accept it" — now
  ACCEPTs
* seed 24 — documented as "ACCEPTED though a reviewer would reject it" — now
  REJECTs
* seed 73 is no longer a near-duplicate; seed 76 is newly rejected

Two of the three recorded human-review discrepancies closed on their own once
the geometry was corrected, both in the direction the reviewer called. That is
evidence the gate was reading real defects all along and the metric never needed
retuning. Seed 30 remains the one accepted roll a reviewer would reject; it is
still not worth a new cue.

## Traceability

The pack was rebuilt with `tools/build_sailor_test_pack.py`. Selection is a
deterministic greedy set-cover and it returned **the same 14 seeds, the same
folder names and the same coverage axes** — 0, 1, 2, 3, 4, 11, 13, 14, 17, 25,
27, 40, 45, 83 — so the same garments can be compared directly against this
round of in-game notes. All 14 sheets re-rendered.
