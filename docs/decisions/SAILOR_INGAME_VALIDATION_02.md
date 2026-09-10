# Sailor pool — in-game validation pass 02

**Status:** applied, 2026-09-04.
**Trigger:** second in-game Fashion Sense review of the 14-garment validation
pack, SMAPI session 21:16–21:25.
**Pinned by:** `v5/tests/test_v5.py::SilhouetteIntegrity` (4 tests).
**Evidence:** `output/v5_sailor_ingame_fix_02/before_after.png`.

Geometry only. No QC floor, separation rule, palette, weight or acceptance
threshold was touched.

## First: were pass 01's fixes actually tested?

Eight of the twelve reports were near-verbatim repeats of pass 01. The pack was
reinstalled at 21:06; SMAPI loaded it at 21:17:05 with no errors and the review
ran in that session. **The repeats are real.** Pass 01's fixes landed and were
insufficient.

The reason is worth recording: pass 01 declared success on metrics I chose to
describe the change I had made (flap-is-a-rectangle: 51/96 → 0), not on any
measure of what the eye was objecting to. Every metric it reported improved
while four of the same defects survived. Pass 02 was diagnosed against the
reference corpus instead.

## Diagnosis

Twelve reports, four shared motifs. Measured over the 68 frames of the shipping
reference packs and all 96 rolls:

| motif | reference | ours before | ours after | reports |
|---|---|---|---|---|
| transparent cell with fabric above **and** below | **0 / 68 frames** | 1 per roll (side) + 2 per strap roll (back) | 0 | 000, 001, 002, 011 |
| front neck notch depth | 1 (vanilla, 74%) / 2 (sailor ref) | 2 or **3** | 2 | 001, 083 |
| identity trim on the front shoulder corners | never | every roll | 0 | 003, 014, 040 |
| flap hem reaching the arm columns | — | every roll | 0 | 013, 025, 040, 045 |

### 1. Enclosed gaps — 000, 001, 002, 011

No frame in the reference pack contains a transparent cell with fabric directly
above and below it. Every one of our rolls did.

* `side` row 1 stepped its neck gap one column right of row 0's, stranding
  `(4,1)` between fabric — the "protruding / blocky side profile" (000).
* both strap silhouettes carved `.######.` into back row 2 with full rows above
  and below: a 1px bite out of each side, under the flap (002, 011).
* both strap silhouettes opened front row 0 as `##.##.##` — two 1px slots
  either side of a 2px fabric bridge, which is literally the reported "split
  hole" (001).

The strap read is now carried by the collar treatment. A silhouette should not
encode straps as missing fabric.

### 2. Neck opening depth — 001, 083

Vanilla: 236 of 318 shirts (74%) use a 1-row notch. The sailor reference uses
2. We had **zero rolls at either** — 59 at depth 2 and 37 at depth 3. A 2-wide
slot three rows deep reads as a hole, and it forces the dickey to start lower,
which is part of why it read as a box (083). Strap silhouettes are now depth 2.

### 3. Front shoulder corners — 003, 004, 014, 040

Every reference front and back frame keeps its darkest value at the frame's top
corners (`o##..##o`, `o######o`) — never identity trim, never a highlight. We
put the collar/yoke there and lit the articulation on top of it. That is 003's
collar "lying on the arm", and on a white-on-navy roll the lit corner is 004's
pale seam between sleeve and arm.

The corners are now body, and the articulation there is a shadow.

**Front only.** The back band keeps its corners: 003's back complaint is the
flap, fixed below, and stripping the back band cost it the area its
collar-against-body separation is measured on.

### 4. Flap hem — 013, 025, 040, 045

`flap_outline` inset the neck row and then held a constant 6-wide span for the
rest of its depth, so its outer columns ran straight down rows 2–4 — where the
Farmer's arms are drawn. Hence "a straight bar across the shoulders" and, on a
light flap over a dark shell, "two pale bars through the elbows" (045). The hem
rows now draw back inboard.

## Cost

Two rolls moved ACCEPT → IDENTITY_TOO_WEAK (92 → 90 of 96): seeds 13 and 54.

All five current identity rejections are the same combination — CLASSIC on
`LIGHT_BODY_DARK_COLLAR` — and all fail the same way: `under_layer_vs_trim`
collapses to 2–15 while `trim_vs_body` stays strong at 114–142. The dickey
disappears into the collar. That is the CLASSIC palette affinity already
recorded as marginal, surfacing on two more rolls because the neck geometry
moved. **The gate was not retuned**; its configuration test still passes
unchanged.

Seed 13 is one of the reported garments, so it is carried in the pack anyway
with its verdict recorded, rather than silently dropped.

## Traceability

Pack membership is now **pinned** to the 14 pass-01 seeds. Greedy set cover
re-derived membership from coverage axes, and the geometry fix moved those axes
enough to swap 13 and 25 out for 5 and 6 — which defeats the pack's only job.
Selection still runs if the pin is cleared.

Same 14 seeds, same folder names, all sheets 8×32.
