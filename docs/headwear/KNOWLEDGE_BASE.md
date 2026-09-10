# Headwear V5 — Grammar / Architecture Knowledge Base

Persistent notes from the **Vanilla Hat Reconstruction exercise**. Each hat was
rebuilt *through the V5 pipeline* (Architecture → Construction → AA → AG), not
by copying pixels. The residual mask difference against the vanilla reference
is the honest measure of what V5 can and cannot express.

Method: a brute-force search over every legal V5 parameter combination for the
closest silhouette match. Reconstruction quality is therefore an upper bound on
what the current vocabulary can do, not a hand-tuned best case.

---

## Lookup index

| want to build… | closest study | reuse |
|---|---|---|
| bowler / derby / rounded hat | **#1 Bowler** | `ROUND` profile, `SHARP` brim |
| top hat / stovepipe / formal | **#2 Top Hat** | `STOVEPIPE` + `STEPPED` brim — exact |
| baseball cap / trucker / visored | **#16 Trucker** | BRIMLESS; **visor motif missing** |
| witch / cone / wizard | **#70 Witch** | blocked by odd-width rows |
| cowboy / fedora / creased | **#0 Cowboy** | `CROWN_CREASE` + wide brim |
| cat ears / animal ears / horns | **#32 Cat Ears** | needs a new Architecture |
| santa / drooping / tasselled | **#25 Santa** | blocked by odd widths + droop |
| bow / one-sided ornament | **#14 Butterfly Bow** | needs asymmetric Architecture |

Lookup by property:

* **hair PRESERVE** — every brimmed and brimless study below
* **hair HIDE** — Knight's Helmet #50, Squire's #51, Pumpkin Mask #48 (not reconstructed; enclosing forms)
* **detached mass** — #32 Cat Ears (6 components), #31 Mouse Ears
* **enclosed holes** — #6 Blue Bonnet (22), #51 Squire's Helmet (16)
* **extreme asymmetry** — #14 Butterfly Bow (symmetry 0.11)
* **split rows / protrusions** — #0 Cowboy, #32 Cat Ears, #11 Earmuffs

---

## Study notes

### #2 Top Hat — **0% difference, pixel-exact**

*Structural type:* structured tall brimmed. *Recognition cue:* a constant-width
crown column over a flat disc brim. Essential: the straight section and the
sharp shoulder. Decorative: the band.

*Geometry:* crown 8 wide held for 6 rows, flare over 3 rows to 14, brim line 10,
2 rows below. `STOVEPIPE (4,3,3,3,3,3,3,1,0,0)` at `crown_width 14` reproduces
the widths exactly; `STEPPED (0,1,4)` reproduces the brim.

*V5 compatibility:* everything. This is the proof that the derived crown/brim
vocabulary is real and not an approximation.

*Reusable:* a constant-width crown is expressible as a profile with a long run
of equal insets. Any formal/structured hat should start here.

*Enhanced Vanilla candidate:* **yes, strong.** Identity fully preserved;
enhancement would be AG dome shading and a richer band. Name: *Gentleman's Top
Hat*.

### #1 Bowler Hat — **2% difference**

*Structural type:* simple brimmed. *Cue:* an even dome with a short, sharply
dropped brim. Essential: the smooth width progression 4→14.

*Geometry:* widths 4,6,8,10,10,12,14,14,12,8. Needed a crown inset of **5**;
our profiles stopped at 4, giving a 6-wide apex. Deepening `ROUND` to
`(5,4,3,2,2,1,0,0)` closed the gap from 8% to 2%. Residual: one brim row.

*V5 compatibility:* full, after the profile fix.

*Reusable:* **crown insets must reach 5.** A 4-cell apex on a 14 base is a
normal vanilla proportion, not an outlier.

*Enhanced Vanilla candidate:* **yes.** Name: *Polished Bowler*.

### #0 Cowboy Hat — **10% difference**

*Structural type:* wide-brimmed with a creased crown. *Cues, in order:* the
crease at the apex, the very wide brim (18), the side wings.

*Geometry:* apex `.......##..##.......` — a 2-cell gap in a 6-wide top. Brim 18
wide, 4 rows below the line. Row 3 carries **side wings resting on the brim**,
not on the crown.

*V5 compatibility:* the crease now reconstructs **exactly** via the new
`CROWN_CREASE` motif. The wings do not: `EARS_SIDE` anchors to the crown's
widest row, and these are anchored to the **brim's**.

*Reusable:* `CROWN_CREASE` (added). **Brim-anchored side wings** — a distinct
anchor from crown-anchored ears; logged, not built.

*Enhanced Vanilla candidate:* **yes**, once wings exist. Name: *Trailhand's Hat*.

### #16 Trucker Hat — **14% difference**

*Structural type:* soft cap. *Cue:* a constant 10-wide column with a fast
shoulder (4→8→10 in two rows).

*V5 compatibility:* best match was **BRIMMED, not BRIMLESS** — our cap domes
always taper gradually, so no cap could hold a constant column. The vanilla
front frame shows no visor; the visor lives in the side view, which our
side-view model does not vary independently.

*Reusable:* caps need a **fast-shoulder dome** (`(3,1,0)`-like) alongside the
gradual ones. Logged as authoring.

*Enhanced Vanilla candidate:* not yet — the shape is not reproduced.

### #70 Witch Hat — **15% difference**

*Structural type:* pointed cone. *Cue:* a tall narrow cone over a very wide brim.

*Geometry:* widths 5,6,5,6,6,8,12,14,16,16,14,12,8. **Odd widths, and
non-monotonic** — the cone wobbles.

*V5 compatibility:* **blocked.** `span()` produces only even widths so the mass
centres exactly; odd widths cannot be centred on a 20-wide frame and would
break the `mirror_symmetry == 1.0` contract. Vanilla accepts this (Witch
symmetry 0.95).

*Reusable:* odd-width rows are a **declared exception**, not a global change.

*Enhanced Vanilla candidate:* not until odd widths exist.

### #25 Santa Hat — **15% difference**

*Structural type:* soft drooping cone with a cuff and pom.
*Cues:* the droop, the cuff band, the pom.

*Geometry:* 3,5,7,9,10,11,10,10,10,12,12,10,2 — odd widths, non-monotonic
(11 then 10), and a final row of two separated cells (the pom tips).

*V5 compatibility:* blocked by odd widths; the droop needs a lateral lean that
grows with depth, which `TIP_LEAN` (a fixed column shift) cannot express.

*Reusable:* **cuff** and **pom** are real missing motifs; a *progressive* lean
is distinct from a tip lean.

### #32 Cat Ears — **not attempted; proven out of scope**

6 disconnected components, 4 enclosed holes, no crown at all, and mass in rows
9 and 11 separated by empty rows. Violates connected-mass and no-enclosed-holes,
both of which `BRIMMED_HAT`/`BRIMLESS_HAT` legitimately require.

*Verdict:* needs a **new Architecture** (`EARED`/`HORNED`) declaring detached
mass legal. Do not weaken the existing contracts for it.

### #14 Butterfly Bow — **not attempted; proven out of scope**

Symmetry **0.11** — the entire ornament sits on one side of the head. Our
contract enforces exact mirror symmetry unless a declared asymmetry motif
applies, and no motif of that magnitude exists or should.

*Verdict:* needs an Architecture whose identity *is* one-sidedness.

---

## Directional and hair findings

* Every reconstructed hat is `PRESERVE`. Vanilla agrees: all six carry
  `ShowRealHair=false`, which is *obscured* hair — a middle state Fashion Sense
  cannot give a custom hat (see `FASHION_SENSE_CAPABILITY_AUDIT.md`).
* Vanilla varies front/side/back freely; our crown is anchored identically in
  all views by contract. Correct for placement stability, but it is why the
  Trucker's visor — a side-view feature — cannot appear.

## Enhanced Vanilla Hat candidates

| hat | identity preserved | enhancement | proposed name |
|---|---|---|---|
| Top Hat | exact | dome shading, richer band | Gentleman's Top Hat |
| Bowler | 98% | contour, AA, palette depth | Polished Bowler |
| Cowboy | crease exact, wings missing | wings + brim shaping | Trailhand's Hat |

All three preserve silhouette and construction; none is a redesign.

---

# Phase 2 — closing the proven gaps

The first exercise classified gaps as pipeline / architecture / authoring / QC
and treated the classification as a prohibition. Phase 2 removed that rule: any
change was allowed if evidence justified it. Four prototypes; three adopted.

## ADOPTED — odd-width rows (declared, scoped)

**Limitation:** `span()` emitted only even widths so mass centred exactly.
Vanilla uses 3/5/7/9/11 freely and accepts the half-pixel offset (Witch 0.95,
Santa 0.94 symmetry).

**Why authoring alone was insufficient:** no authored profile can produce an odd
row through an even-only `span()`. This had to be a capability change.

**Implementation:** profile insets may be **half-integers**;
`row_width(cw, inset)` yields an odd width; `span(width, env, odd_bias)` places
the half-pixel on a declared side, constant per hat via a new `odd_bias`
variable so a hat leans consistently rather than jittering row to row.

**Declared exception, not a relaxation:** `has_odd_rows(profile)` is the single
predicate the symmetry and side-brim contracts consult. Every integer-inset
profile stays pixel-exact and is unaffected.

**Benefit:** Witch 15% → 3%, Santa 15% → 8%. Controls unchanged.
**Recommendation: ADOPT.** Low complexity, scoped, evidence across two hats.

## ADOPTED — CONE and DROOP profiles

Two general crown families the vocabulary lacked, both requiring odd rows:

* **CONE** `(5.5, 5, 5.5, 5, 5, 4, 2, 1, 0)` — tall narrow cone flaring late.
  Reusable: witch, wizard, party, dunce. The 5.5/5 alternation is edge
  stepping, not noise — it is what keeps a shallow diagonal reading straight.
* **DROOP** `(4.5, 3.5, 2.5, 1.5, 1.0, 0.5, 1.0, 1.0, 1.0, 0)` — a soft crown
  that swells, waists, then meets the brim. Non-monotonic by design.
  Reusable: santa, nightcap, slouch beanie.

CONE required a second declared exception: it is **narrow by design**, so it is
exempt from the 0.55 crown-proportion rule that exists to stop accidental
stem-and-dish reads. Declared per profile (`NARROW_BY_DESIGN`), not relaxed.

## ADOPTED — SWEEP brim (4 rows)

The brim vocabulary had 2-row (SHARP), 3-row (TAPERED/DIPPED/STEPPED/CURLED)
and 5-row (both retired) profiles and **nothing at 4**. `SWEEP (0,1,2,4)` fills
it. This alone took Witch from 7% to **3%**.

Lesson: check a vocabulary for *gaps in cardinality*, not just for shapes.

## KEEP EXPERIMENTAL — BRIM_WINGS

A protrusion anchored to the **brim's** widest row rather than the crown's — a
genuinely distinct anchor type, reusable for anything carried on a brim.

Implemented and legal-checked, but **currently unreachable**: a wing sits
outboard of the crown *at the brim row*, and every current profile has already
opened to full width by then. Vanilla's Cowboy keeps its crown 8 wide where
ours is 12, giving it the clearance we lack.

Same shape of finding as EARS_TALL: the motif is right, the crown vocabulary
cannot yet carry it. It unlocks the moment a profile is authored that stays
narrow to the brim line. **Left in the library at weight 0.**

## Reusable rules learned

1. **Odd widths are a declared per-Architecture capability**, gated by one
   predicate, never a global symmetry change.
2. **An anchor is a first-class concept.** Crown-anchored, apex-anchored and
   brim-anchored protrusions are the same shape with different attachment; the
   anchor decides whether a motif can exist at all.
3. **Vocabulary gaps hide in cardinality.** The missing 4-row brim was invisible
   to every shape-based check.
4. **A rule added to prevent a defect will eventually exclude a legitimate
   shape.** The 0.55 proportion rule stopped chess-piece hats and then blocked
   cones. The fix is a declared exemption, not deletion.

---

# PHASE 3 — closing the structural gaps

Phase 2 ended with three gaps that reconstruction had *proved*, rather than
guessed: direction-specific structure, brim-anchored construction, and Santa's
progressive/split lower forms. This phase attacked those three, and one
measurement problem that was hiding inside all of them.

## The measurement problem came first

Phase 2 scored the **front frame only**, and swept parameter values the
generator cannot actually roll. Both flattered the result.

* A front-only metric is **structurally blind to a directional feature**.
  Vanilla's Trucker draws its visor in the two side frames and nowhere else, so
  a perfect front match and a completely missing visor score identically. A
  hat is seen from four directions in game; two of them are the side frame.
* A sweep over undeclared values measures an *aspirational* Architecture. If a
  reconstruction needs `crown_width` 8 and the domain stops at 12, that is not
  a reconstruction, it is a wish.

The phase-3 harness scores **front + side + back**, weighted by how many
runtime directions each serves (side counts double), and pulls its domains,
`validate` and `activation` from each Architecture's own declared schema — so
every candidate it reports is a hat the resolver could legally produce.

**Numbers under the two metrics are not comparable.** Everything below is
measured under the new one, and the phase-2 figures are restated under it too.

---

## ADOPTED — the BACK frame is derived, not authored

**Limitation.** The back frame was authored separately: same crown, plus two
full-crown-width rows below the brim line. Nothing checked it against the
corpus, and nothing stopped it disagreeing with the front.

**Measured** over the 112 vanilla hats with mass in all four frames:

| | back − front |
|---|---|
| top row | **+1** (p10 0, p90 2) |
| bottom row | **+2** (p10 −1, p90 3) |
| cells | **+10** (p10 −12, p90 28) |

Exactly **1 of 112** draws the back as a copy of the front. The rule that
reproduces all three medians at once is: *the same hat, drawn one row lower,
with its lowest row repeated once* — seen from behind, the head is a little
further away and a little below the camera, so the hat rides down the frame and
you see more of its underside.

Predicting each vanilla back frame from its own front frame:

| rule | median error | mean |
|---|---|---|
| plain copy of front | 37.3% | 37.2% |
| old (front + full-width stub) | 28.8% | 32.9% |
| **new (drop 1, extend 1)** | **24.4%** | **28.3%** |

Better on **75 of 114** hats.

**Architecture value beyond the numbers:** the back frame is now a *function*
of the front, computed after every motif has run. A whole class of bug —
front and back disagreeing about the hat — is no longer expressible. Zero
design entropy, the same discipline Projection follows.

`grammar.back_view` / `HAT_BACK_DROP` / `HAT_BACK_EXTEND`; shared by both
Architectures via `brimmed_hat.fill_back`.

## ADOPTED — directional pieces (Priority 1)

**Limitation.** Every piece was view-uniform. Vanilla is not: Trucker's visor
exists only in profile (a cap facing you has its visor pointing at you, so the
crown occludes it), and Santa's tail hangs down-and-back only in profile.

**Concept.** A *directional piece* is:

* decided **once**, at Construction time, from the same roll as everything
  else — Projection still adds zero design entropy, and no direction rerolls
  the garment;
* declared **per frame**, present or absent — never a different hat;
* **anchored to the already-anchored crown**, built from the finished
  silhouette as its own `Piece`, so it can only *add* mass.

That last clause is the guard against the bug the anchoring rule exists to
prevent. `test_directional_piece_never_moves_the_hat` re-realizes the same spec
with the piece switched off and requires (a) every remaining cell to survive
in every frame, and (b) the undeclared frames to be **bit-identical**.

Two members, from two different reconstructions — which is what makes it a
concept rather than a special case for one hat:

| piece | frames | extent | anchor | reusable for |
|---|---|---|---|---|
| `VISOR` | side | 4,5,5,5,4 forward | crown, lifted 2 rows off the hem | baseball, trucker, jockey, kepi, newsboy |
| `TAIL` | side | 6,5,2 down-and-back | hem, hugging the back edge | nightcap, phrygian, elf, sleeping cap |

Gated on **`ArchitectureContract.allows_directional_pieces`**. BRIMLESS
declares it for both; BRIMMED declares it for `TAIL` only — a brimmed hat
already carries an all-round version of a visor's surface.

**Trucker's front frame is now pixel-exact (0%)** and the visor renders.

## ADOPTED — brim-anchored construction (Priority 2)

Investigated as two separate questions, as asked.

**(a) Should a reusable crown profile stay narrow to the brim line?** Yes, and
it is a missing *shape family*, not a fix for one hat: a short straight-sided
crown under a wide brim is the cowboy / gaucho / sombrero / boater group.
Authored as `COLUMN (0, 0, 0, 0)`.

Two supporting changes, both self-selecting rather than tuned:

* `crown_width` gains **8 and 10**. A tapering crown at 8 collapses under the
  corpus floor of 5 and is rejected automatically; `COLUMN` at 14 or 16 reports
  a median of 14/16 and is rejected by the ceiling of 12. The two ends of the
  domain pick each other with no extra rule.
* `brim_line` gains **8**, and the brim may be **deeper than half the crown**
  — both declared for `WIDE_BRIM_CROWNS` only. The half-crown depth rule
  exists to stop the goblet read (brim mass mirroring crown mass); on a short
  straight crown a deep brim *is* the shape. `ROLLED (0,0,1,2,4)` is the brim
  that goes with it: full width for two rows, then rolling down and in.

**(b) Is `BRIM_WINGS` the right anchor concept once the geometry exists?**
Yes — unchanged, and now **reachable** for the first time
(`test_brim_wings_are_now_reachable`). It is selected by the Cowboy
reconstruction, which is the check that matters: the motif was authored in
phase 2 against a crown that could not carry it, and the crown is what was
missing, not the motif.

## ADOPTED — split rows as a directional realization (Priority 3)

**Limitation.** 47 of 112 vanilla hats split a row at their **base**, and on a
wide-brimmed hat the reason is geometric rather than decorative: an upturned
brim seen edge-on shows its front and back ends hanging below the middle, with
daylight between. Vanilla #0's side frame is `..####......#####...` where its
front frame is solid.

This is a **directional realization of a structural piece** — same brim, same
rows, same columns, drawn as what the profile actually shows — so it belongs
with the directional-piece concept rather than in the motif library.

Gated on **`allows_split_rows`**, scoped to `SIDE_CURL_BRIMS`, and guarded:
the curl is only taken when *every* row below the opening is still wide enough
to split, so the gap stays open to the brim's edge. Without that guard the row
below closes it and the hat gains an **enclosed hole** — which is exactly what
happened, and was caught by a 400-seed sweep rather than the 48 the rest of the
suite uses. That sweep is now a permanent test.

## ADOPTED — TIP_DROOP, a progressive lean (Priority 3)

`TIP_LEAN` displaces up to three rows by one column each, which slides a block
sideways. A soft point does not do that, it curves. `TIP_DROOP` moves the top
rows by a **decreasing** amount — `DROOP_STEPS = (2, 1, 1)`, authored from
Witch #70 (tip centres 11, 10.5, 10 against a body centred on 9.5) and Santa
#25 in mirror. Rows are rewritten from the original crown, so offsets cannot
compound. Scoped to `CONE`, `DROOP`, `STOVEPIPE` — the crowns with a point.

## ADOPTED — base flare / cuff (Priority 3)

**25 of 112 vanilla hats (22%) end wider than the row above** — a rolled cuff
on a beanie, a fur band, a turn-up on a watch cap. Every shape in BRIMLESS
narrowed at the bottom, so a fifth of real headwear had no expression at all.

`CUFF` replaces the hem taper on the bottom two rows and flares **+2 columns**
(the corpus amount: Santa runs 10 → 12). Gated on `allows_base_flare`, and only
offered at `crown_width` 14+, where the resulting ratio (16/14 = 1.14) stays
under the 1.15 that separates BRIMLESS from BRIMMED — `test_a_cuffed_cap_is_
still_a_cap` asserts it per garment rather than trusting the threshold.

## ADOPTED — cap height belongs to the dome

`CAP_HEIGHT` was one module constant, so every cap was eleven rows tall
whatever shape it was. The baseball family is not: vanilla #16 runs nine rows.
Height now belongs to the authored dome (`CAP_HEIGHTS`), exactly as a brimmed
crown's height belongs to its authored profile. Only `FAST` changes; every
other dome keeps the eleven rows it had.

## FIXED — two latent bugs the above exposed

* `protrusion_options` and `has_odd_rows` read the **brimmed** profile table
  for brimless hats. They agreed by accident for the names both tables share
  and raised `KeyError` the moment one did not (`FAST`). Now
  `hat_motifs.crown_row_profile(profile, architecture)`.
* The brimless `crown_width` validator measured the brimmed profile against the
  **brimmed** corpus bound (5–12). Pointing it at the cap's own rows exposed
  the second half: against a ceiling meant for crowns that taper, **no cap
  wider than 12 was admissible at all** — and the brimless corpus median is
  **14**. Now bounded by `HAT_BRIMLESS_BOUNDS["crown_width"]` (10–16).

## REJECTED — flipping HAT_SIDE_BRIM_RISE to 0

Re-measured across the corpus, the side frame's widest row sits at the **same
row as the front's**: median delta 0, distribution −1: 24, 0: 32, +1: 23. Our
frozen constant of 1 is therefore not the corpus median.

But setting it to 0 trades two controls for two others — Top Hat 7.8 → 3.2%
and Witch 14.2 → 9.9%, against Bowler 10.6 → **15.6%** and Santa 16.4 →
**19.2%**. The distribution is symmetric with no measurable correlate (brim
width, crown height, brim depth), so **the corpus supplies no rule to replace
the constant with** — only a per-hat property we would have to invent or roll.
Rolling it would be adding a random dimension for variety, which is out of
bounds. **REJECTED**, and logged as gap #22.

## The declarative capability set

Five flags on `ArchitectureContract`, each defaulting to the strict behaviour,
each with a test that an Architecture declaring nothing cannot reach it:

| flag | declared by | what it opens |
|---|---|---|
| `allows_directional_pieces` | BRIMMED, BRIMLESS | a piece present in some frames only |
| `allows_split_rows` | BRIMMED | a row may open below the widest row |
| `allows_base_flare` | BRIMLESS | the base may be wider than the crown |
| `allows_detached_mass` | *nobody* | a second connected component |
| `allows_extreme_asymmetry` | *nobody* | symmetry below the corpus floor of 0.80 |

The last two exist to **mark the boundary**, not to be switched on:
`test_nothing_declares_detached_mass` asserts they stay off.

## KEEP EXPERIMENTAL — the profile brim curl

Implemented, guarded and correct, and **scoped to nothing**. On the one
reconstruction it applies to it makes things worse: Cowboy's side frame goes
31.0% → 35.1%, because our profile brim sits a row higher and a row deeper than
vanilla's, so the curl opens the wrong two rows. Shipping a split in the wrong
place is worse than not splitting. Same handling as `SIDE_TUFT`, and as
`BRIM_WINGS` had until this phase. It goes live once the profile brim's
placement is settled.

## FIXED — bounded repair could not exhaust a domain

`resolve_variable` allowed 4 samples before dropping a variable. Fine while
every structural domain had four or fewer members; widening `crown_width` to
five made it possible for a variable **with a legal value** to be dropped
because the first four samples happened to be the illegal ones. It surfaced
533 seeds in, as an `AbsentConcept` crash inside a downstream validator rather
than as a bad hat.

The obvious fix — make the bound the domain length everywhere — is arguably
more correct and was measured: shirt acceptance is unchanged at 187/200, but it
erases the complexity→features margin the shirt suite asserts (1.590/1.605
becomes 1.615/1.615), which was resting on noise either way. So the bound is
now **declared per variable** (`Variable.repair_attempts`, default 4) and the
hat variables with wide domains declare 8. The shirt path is bit-identical.

## Reusable rules learned (phase 3)

5. **A metric that cannot see a feature will report that the feature is not
   missing.** The front-only score rated a missing visor and a perfect visor
   identically for two phases. Before trusting a number, ask what it is
   *structurally* incapable of noticing.
6. **A derived frame is worth more than an authored one.** Making the back a
   function of the front removed a whole class of bug — front/back
   disagreement — and it happens to fit the corpus better than what was
   authored by hand.
7. **An anchor decides existence; a declaration decides permission.** Phase 2
   established the first half. Phase 3 adds the second: `BRIM_WINGS` needed a
   crown (anchor), directional pieces needed a flag (permission), and the two
   failure modes look identical from outside — the motif silently does nothing.
8. **Widening a domain can break bounded repair.** Any repair budget smaller
   than the domain can drop a legal value, and it fails far from the change.
9. **A validator can measure the right thing against the wrong constant.** The
   brimless `crown_width` check used the brimmed profile table AND the brimmed
   bound. Fixing the first exposed the second: two-thirds of the intended cap
   width range had never been reachable. Check both halves of a comparison.
