# Mini Sailor prototype — evaluation

Built 2026-09-03. Scope: `SAILOR_TOP` / `CLASSIC_SQUARE_FLAP` only.
Status: **prototype complete; human visual review and in-game testing not done.**

---

## 1. Success criteria

| Criterion | Result |
|---|---|
| All variants read as sailor tops | Yes on the sheets; **awaiting your visual review** |
| Variants visibly distinct | Yes. No two share structure; median colour-independent difference is 189 of 1024 cells |
| Side view proves construction continuity | Yes. One collar run crosses the shoulder from flap to leaf |
| Back flap reads as attached fabric | Yes structurally, and the anatomy sheet shows why. **Your eye is the judge** |
| Batch shows controlled variation | Yes. Two pairs isolate one variable each |
| Code path understandable and isolated | Yes. 1,391 lines, no imports from the main repo, 14 tests |

---

## 2. The twelve variants

| id | collar | flap | trim | detail | fit | material | colour architecture | colours | collar/body contrast |
|---|---|---|---|---|---|---|---|---:|---:|
| `v01_narrow_shallow` | NARROW | SHALLOW | SINGLE | TIE | FITTED | COTTON | Dark body light collar | 10 | 176 |
| `v02_standard_standard` | STANDARD | STANDARD | SINGLE | TIE | REGULAR | WOVEN | Dark body light collar | 10 | 156 |
| `v03_wide_deep` | WIDE | DEEP | DOUBLE | BOW | RELAXED | WOVEN | Dark body light collar | 10 | 171 |
| `pairA1_flap_standard` | STANDARD | STANDARD | SINGLE | NONE | REGULAR | COTTON | Light body dark collar | 7 | 174 |
| `pairA2_flap_deep` | STANDARD | **DEEP** | SINGLE | NONE | REGULAR | COTTON | Light body dark collar | 7 | 174 |
| `pairB1_trim_single` | WIDE | STANDARD | SINGLE | TIE | REGULAR | WOVEN | Monochrome contrast trim | 7 | 0 |
| `pairB2_trim_double` | WIDE | STANDARD | **DOUBLE** | TIE | REGULAR | WOVEN | Monochrome contrast trim | 7 | 0 |
| `v08_no_detail_knit` | STANDARD | STANDARD | NONE | NONE | RELAXED | LIGHT_KNIT | Low contrast accent | 7 | 43 |
| `v09_bow_light_body` | STANDARD | DEEP | SINGLE | BOW | FITTED | COTTON | Light body dark collar | 10 | 176 |
| `v10_mono_trim` | STANDARD | STANDARD | DOUBLE | TIE | REGULAR | COTTON | Monochrome contrast trim | 7 | 0 |
| `v11_low_contrast` | NARROW | STANDARD | SINGLE | TIE | FITTED | LIGHT_KNIT | Low contrast accent | 10 | 43 |
| `v12_wide_relaxed_knit` | WIDE | STANDARD | SINGLE | NONE | RELAXED | LIGHT_KNIT | Dark body light collar | 7 | 174 |

Coverage: three collar states, three flap states, three trim states, three centre
details, three fits, three materials, four colour architectures, six palettes.

---

## 3. Does the dependency filter do real work?

The twelve batch variants are fully pinned, so they never reroll. A probe of 400
unpinned seeds is the evidence (`out/batch.json` → `dependency_probe`):

| Measure | Value |
|---|---:|
| Valid on the first roll | 247 of 400 |
| Needed at least one reroll | 153 |
| Worst case attempts used | 6 |
| Candidates rejected in total | 332 |

Rejections by rule: `BOW_NEEDS_OPEN_NECKLINE` 77, `WIDE_COLLAR_NEEDS_BODY` 67,
`KNIT_CANNOT_HOLD_DOUBLE_TRIM` 60, `NARROW_COLLAR_CANNOT_CARRY_DEEP_FLAP` 55,
`DOUBLE_TRIM_NEEDS_FLAP_DEPTH` 40, `DOUBLE_TRIM_NEEDS_COLLAR_AREA` 33.

Six of the seven rules fire. `CENTER_DETAIL_NEEDS_OPENING` never fires because
both necklines are V openings — it is currently dead code kept as a guard for a
future collarless or high neckline. Flagged rather than quietly left in.

---

## 4. Does the rear flap read as attached fabric?

This was the stated root issue. Three construction facts, all visible in
`out/sheets/SAILOR_ANATOMY.png` where yellow is a free edge and red is occlusion:

1. **No outline on the top edge.** Row 0 of the flap is classified ATTACHED across
   its full width, and the art grammar is forbidden from outlining an attached
   edge. A test asserts no free-edge op ever lands on an attached cell.
2. **The upper sides are attached too**, down to the shoulder line; only below it
   do the side columns become free. So the border starts partway down, exactly
   where the panel stops following the body.
3. **The free edges cast occlusion** onto the body: a shadow row under the bottom
   edge and a shadow cell outside each free side column. A panel that casts a
   shadow is on top of something.

Plus a lift gradient (lighter where it lies flat on the shoulders, darker toward
the free edge) and a 1-then-2 cell taper over the last three rows, so the outline
is a trapezoid rather than a rectangle.

The anatomy sheet makes the argument checkable: the yellow border is open at the
top on every one of the twelve.

---

## 5. Did the architecture / art-grammar split earn its keep?

Yes, and there is direct evidence. Four defects were found while building, and
each was fixed on exactly one side of the seam with no change to the other:

| Defect | Fixed in | Other stage touched |
|---|---|---|
| Front leaves 2 cells wide, read as a drawn line | architecture (convex outer curve) | none |
| Leaves consumed by outlines on both edges | architecture (second free edge only at width ≥ 3) | none |
| Edge plus shadow read as a 2-pixel black bar | art grammar (occlusion uses shadow, not deep) | none |
| Outlined collar read as a bordered sticker | art grammar (contrast-aware outline) | none |
| Trim splitting a narrow leaf | art grammar (skip leaves under 3 wide) | none |

That the seam held under five consecutive fixes is the strongest structural
result of the prototype.

The contrast-aware outline rule is worth keeping in any successor. Installed
vanilla sailor tops carry **no** outline around a white collar on a navy body:
the value change is the edge. Outlining it produced the sticker look. The rule is
now "the darkest step only when collar/body contrast is under 45".

---

## 6. Weaknesses found

1. **`v08_no_detail_knit` is the weakest variant.** Collar/body contrast 43, soft
   knit edge, no trim, no centre detail. Every readability lever is off at once
   and the collar nearly disappears. A candidate eighth rule is
   `LIGHT_KNIT + LOW_CONTRAST + trim NONE + detail NONE`, but I have not added it:
   the variant was requested to cover knit and low contrast, and inventing a rule
   to hide my own weakest output is the wrong instinct. Judge it on the sheet.
2. **`v02` and `pairA1` are structurally 9 cells apart** of 1024. Same collar,
   flap and trim; only the centre detail and material differ. At a batch scale
   this is the duplication risk: some variable combinations barely move pixels.
   `material` in particular buys almost nothing — a hem rib and up to two fold
   cells.
3. **Fit is nearly invisible.** FITTED removes one cell per side on three rows.
   It does not survive gameplay scale.
4. **Monochrome variants have collar/body contrast 0** and depend entirely on the
   outline and trim. They work, but they read as "shirt with stripes" more than
   "sailor top".
5. **The front V still reads narrow** in the lower rows on some variants, closer
   to a deep neckline than a broad collar.
6. **One silhouette only.** No sleeveless, cropped or bloused variation.
7. **No content pack and no in-game test.** Isolated previews only, as permitted.

---

## 7. Relationship to the V5 work in `rngc/`

These are two different bets and the difference is worth stating plainly.

- `rngc/` composes **authored multi-view pieces** onto an authored blank. Identity
  is a fixed shape a human drew.
- This prototype **computes geometry from variables**. Identity is a formula over
  collar span, V depth and flap depth.

The prototype shows parametric geometry works well *inside one family*, where the
variables have continuous numeric meaning: collar span and flap depth genuinely
want to be numbers, and authoring a piece per (collar_width × flap_depth × fit)
combination would be nine hand-drawn flaps for one family.

It does not show parametric geometry works *across* families, and I would expect
it not to: a lapel, a bib and a placket have no shared parameter space.

Both halves already share the same substrate: role/slot grids, a four-step ramp
per slot, per-cell provenance, and the same Fashion Sense contract. The plausible
synthesis is **per-family parametric generators emitting into the shared
RoleImage representation**, with one shared validator, exporter and preview —
authored pieces where identity is a fixed shape, parameters where it is a
dimension. This prototype is evidence for that shape, not for replacing `rngc/`.

---

## 8. Is it promising enough to be the new foundation?

**As the foundation for one family: yes.** The stage contract held, the seam
between architecture and art grammar absorbed every defect cleanly, the
dependency filter rejects a third of random candidates for stated reasons, and
twelve variants came out structurally distinct rather than recoloured.

**As the foundation for the whole generator: not on this evidence.** The
prototype proves one family with a naturally parametric collar. It says nothing
about families whose identity is a fixed shape, and the two weakest findings
above — near-duplicate variants and inert variables — are exactly the problems
that scale badly across thirty families.

Recommended next step, if you want to continue this line: take **one contrasting
family** with non-parametric identity, such as a collared shirt with a placket,
and try to build it in the same shape. If the stage contract survives a family
whose identity is a drawn shape rather than a dimension, it is a foundation. If
it does not, the answer is the hybrid in section 7.

Nothing here should be promoted until you have looked at the sheets and, ideally,
seen one of these in game.
