# Headwear V5 — HEADWEAR_MEMORY

> Compact persistent memory for Headwear V5.
> Read after `PROJECT_MEMORY.md`.
> Read `KNOWLEDGE_BASE.md` and `GAP_LOG.md` only when deeper evidence is needed.

## Current Goal
Prove that Headwear V5 can intentionally express a broad range of vanilla-quality hat constructions, then transfer those learned construction rules back into the normal random generator.

Current sequence:
1. close remaining reconstruction blockers
2. visual side-by-side QC
3. fresh random generator batch
4. in-game normal-scale QC
5. only after that, expand broadly into non-standard headwear

Do not expand prematurely into halos/masks/etc. unless a current reconstruction directly proves the needed Architecture concept.

## Slot / Resolution
- Headwear defaults to native vanilla parity: 20x20.
- Placement matters more than raw occupied coverage.
- `HEAD_BOX`, crown top, overhang, `HeadPosition.Y`, and derived occupied bbox are placement concepts.
- `HeadPosition.X` should be derived/formulaic where possible rather than independently rolled.

## Hair Policy
Fashion Sense custom hats can effectively preserve full hair or hide hair; they cannot request vanilla's obscured/covered-hair variant.

Rules:
- normal BRIMMED and BRIMLESS hats default to `PRESERVE`
- do **not** globally hide hair
- `HIDE` should be reserved for future enclosing forms whose geometry truly earns it
- bald-looking output is a real wearability bug, not a cosmetic nit

## Architecture Legality
Headwear legality must be declarative per Architecture.

Do not weaken BRIMMED/BRIMLESS globally because future headwear needs exceptions.

Capabilities may be declared per Architecture, for example:
- allows_directional_pieces
- allows_split_rows
- allows_detached_mass
- allows_enclosed_holes
- allows_extreme_asymmetry

Future likely structural classes include:
- brimmed/crowned
- close-fit/brimless
- projecting appendages
- circlet/ring/crown
- floating/orbiting
- rigid shell
- draped/enclosing
- one-sided/small attached ornament

Do not force all of these through BRIMMED/BRIMLESS.

## Core Projection Rule
Projection adds **zero design entropy**.

A hat resolves once.
Front/side/back are deterministic realizations of that same hat.

Per-direction structure is allowed only as a declared construction capability:
- do not reroll design by direction
- preserve placement stability
- a declared piece may be present/absent/differently realized by direction when that is part of the Architecture

## Side-View Rule Learned from Vanilla
Do not impose fake perspective skew on side brims.

Locked:
- `HAT_SIDE_BRIM_SKEW = 0`
- same width by default
- side brim line may rise one row (`HAT_SIDE_BRIM_RISE = 1`)

Fine side-view differences should come from authored construction, not a global skew formula.

## Outline / Shading
Headwear differs from shirts:
- vanilla hats overwhelmingly use darker outlines
- headwear should retain a darker-outline render class
- shading should communicate form/construction, not just fill a silhouette with highlight

Major visual lesson:
**silhouette + outline + highlight is not enough.**
Vanilla-quality hats need internal authored construction such as bands, seams, panels, cuffs, visors, knit segmentation, creases, crown structure, brim structure, and ornaments where appropriate.

## Current Reconstruction Benchmarks
- Top Hat: 0% difference — exact
- Bowler: 2%
- Witch: 3%
- Santa: 8%
- Cowboy: 10%
- Trucker: 11%

Regression controls:
- Top Hat
- Bowler
- Witch

Remaining targets:
- Santa
- Cowboy
- Trucker

## Adopted Capabilities / Vocabulary
### Odd-width rows
ADOPTED.
- profile insets may be half-integers
- `span()` supports stable declared `odd_bias`
- same half-pixel side is used consistently within a hat
- scoped by `has_odd_rows(profile)` or equivalent
- integer-inset profiles remain bit-identical

### Crown profiles
Active/learned vocabulary:
- ROUND
- DOMED
- SHALLOW
- TALL_FLAT
- STOVEPIPE
- PINCHED
- STEPPED
- FAST
- CONE
- DROOP

Important:
- Bowler proved crown insets must reach 5
- `FAST` supports fast-shoulder caps
- `CONE` is narrow by design and needs a declared exemption from generic anti-chess-piece proportion rules
- `DROOP` helps soft non-monotonic crowns but does not yet fully solve Santa construction

### Brims
Active learned vocabulary:
- TAPERED
- SHARP
- DIPPED
- STEPPED
- CURLED
- SWEEP

`SWEEP` fills the previously missing 4-row brim cardinality.

### Hem taper
ADOPTED as a closed vocabulary rather than one hardcoded sequence:
- TIGHT
- DROP
- FLARE
- SOFT

Pairings must be QC-checked; individually valid choices can still form a bad combination.

### Controlled asymmetry
Known motif concepts:
- TIP_LEAN
- CROWN_DENT
- BRIM_FLICK

`SIDE_TUFT` remains disabled/weight-0 because it read as a wart/nub.
Protrusion/asymmetry combinations should remain guarded when they conflict.

### Protrusions
- `EARS_SIDE` is anchored to a meaningful widest-row shoulder
- declared protrusions must actually render
- detached floating clusters are QC-detected
- `EARS_TALL` remains weight-0 until geometry supports it

## Current Proven Blockers
### Trucker
Needs a direction-specific visor concept.

Constraint:
- identical crown anchoring fixed a real placement bug
- do not globally undo that rule
- solve via Architecture-declared directional authored pieces

### Cowboy
`CROWN_CREASE` reproduces the apex cue.

Remaining:
- brim wings
- `BRIM_WINGS` is conceptually reasonable but currently unreachable
- crown must remain narrower until the brim line to create clearance

Need:
- reusable narrow-to-brim crown profile
- then re-evaluate `BRIM_WINGS`

### Santa
Odd-width + DROOP improved fidelity, but missing:
- stronger progressive droop path
- split lower hem / split lobe
- cuff
- pom/tassel

Do not globally legalize split rows or detached mass to solve one hat.

## Experimental / Not Yet Adopted
- `BRIM_WINGS`: weight 0 until supporting crown geometry exists
- direction-specific visor/pieces
- split-row construction
- progressive droop beyond current DROOP profile
- palette-from-reference path

## Out-of-Scope Structures Proven by Reconstruction
### Cat Ears
Needs a separate EARED/HORNED-like Architecture with declared detached-mass/enclosed-hole legality.

### Butterfly Bow
Needs an explicitly one-sided Architecture; it should not be represented as mild asymmetry inside normal hats.

## Reconstruction Method
For a reference hat:
- search every legal V5 parameter combination for the closest silhouette
- residual mask difference is an upper bound on current grammar expressiveness
- do not hand-copy final pixels
- classify mismatch as pipeline / Architecture / authoring / QC

Reconstruction catches expressiveness gaps that corpus statistics can miss.

## Current Phase
Phase 4: live in-game QC + mod-author quality calibration.

Phase 3 closed the reconstruction blockers (see KNOWLEDGE_BASE / GAP_LOG) and
then in-game review returned a blunt verdict: the hats look like "vases pasted
on my head". Investigation showed the silhouette was never the problem —
bbox 14x11 vanilla vs 14x11 ours, overhang 4 vs 4, Bowler mask 2%. Three phases
optimised an ALPHA MASK metric that is structurally incapable of seeing the
reported defect.

Two workflow rules follow, and they are durable:

1. **The real Stardew + Fashion Sense render is the authority for wearability
   and placement.** The synthetic farmer composite may stay as a cheap preview;
   it must never again be the final placement/fit gate.
2. **Silhouette metrics and rendering metrics are different questions.** A hat
   can be pixel-exact in the mask and still read as pottery.

## Phase 3 outcome (superseded metric)
Reconstruction was re-measured on a three-view, declared-domain-only metric.
Front-frame figures, comparable to the phase-2 table above:
Top Hat 0%, Bowler 2%, Witch 0%, Santa 7.7%, Cowboy 10%, Trucker 0%.
Three-view weighted: 7.8 / 10.6 / 13.6 / 16.4 / 23.9 / 16.2.
Adopted: derived back frame, directional pieces (VISOR/TAIL), COLUMN crown +
BRIM_WINGS reachable, TIP_DROOP, CUFF, per-dome cap height, declarative
capability flags. Parked: side-brim curl. 128 tests pass.

## Phase 3 (original plan, retained for context)

Focus:
1. Trucker — direction-specific visor
2. Cowboy — narrow-to-brim crown + brim wings
3. Santa — progressive droop + split lower hem + cuff/pom

Regression controls:
- Top Hat
- Bowler
- Witch

For meaningful prototypes report:
- limitation addressed
- why current vocabulary is insufficient
- hats benefiting
- before/after fidelity
- normal-generator impact
- regressions
- complexity/maintenance risk
- ADOPT / KEEP EXPERIMENTAL / REJECT

## After Phase 3
Do **not** immediately declare Headwear complete.

Next:
1. inspect side-by-side reconstructions visually
2. generate a fresh varied random hat batch
3. test in game at normal Stardew scale
4. inspect hair preservation, face clearance, vertical placement, turning stability, construction richness, silhouette diversity, and whether outputs still read as generic blobs
5. only lock normal hats if the user considers the output visually acceptable

## Deep References
Consult only when needed:
- `KNOWLEDGE_BASE.md`
- `GAP_LOG.md`
- Fashion Sense capability/source audit
- vanilla/corpus measurements

---

## PHASE 4 — measured findings (Part 9 complete, offline)

Four hats the user picked as genuinely good were measured against 116 vanilla
hats and 120 of ours. **Three claims made from looking at them did not survive
measurement.** Recorded here because they are the kind of mistake that repeats.

| metric | user's 4 | vanilla | ours | verdict |
|---|---|---|---|---|
| pixels far from the body hue | 15.6% | 8.1% | **0.0%** | **biggest gap** |
| highlight spread (% of sprite) | 5.2% | 6.4% | **19.9%** | **this is the "vase"** |
| darkest colour luminance | 26 | 15 | **47.5** | ramp floats in mid-tones |
| luminance span | ~155 | 182 | 120 | too narrow |
| distinct colours | 10.5 | 7 | 5 | low |
| 2nd-from-bottom row vs body | -10 | -19 | **0** | contact shadow missing |
| highlight depth from top | 0.36 | 0.44 | 0.51 | slightly low |
| perimeter - interior (contour) | -35 | -59 | -37 | **already fine** |
| flat blocks >= 3px | 8 | 10 | 9 | **already fine** |
| band area | 4.0% | 6.2% | **10%** | **too BIG, not too small** |

### Refuted
* **"No real outline."** Ours is -37; the references average -35. We are in
  range. Vanilla (-59) is the outlier, and vanilla is not the taste target.
* **"Smooth gradient instead of flat blocks."** Flat-block counts match (9 vs 8).
* **"The band is a one-pixel whisper."** It is 10% of the sprite — over twice the
  references. Its problem is hue, not size.
* **"Highlight sits at 70% depth."** That was a single brightest-PIXEL artifact.
  Measured over all near-brightest cells it is 0.51 vs 0.36 — a modest gap. The
  real defect is highlight **spread**: 19.9% against 5.2%.

### Confirmed
* The chromatic gap is real and large. By the strict measure our hats have
  **zero** area in a hue distinct from the body.
* The second-row contact shadow is universal in the references and vanilla, and
  we have none.
* Our darkest colour is 3x brighter than vanilla's, which is why the contour
  reads weak even though the relative delta is fine.

### How the accent actually works (decides the Color Architecture change)
Not simply "a different hue". Per reference:
* BoysCap — hue 31deg, **value 74**, saturation x0.98 (value-led)
* SweetGent — hue 31deg, value 34, **saturation x0.24** (saturation-led)
* hyoung_11 — **no chromatic accent at all**, and still reads well
* Kookoroo_8 — thin ribbon, 11.6% far-hue, no contiguous block

Vanilla is more chromatic: 75% carry a hue accent, median 79deg / value 77 /
area 6.2%. So a Hat Color Architecture needs accents distinguished by hue OR
value OR saturation, not one fixed recipe, and a monochrome hat must stay legal.

## Phase 4 infrastructure (built, not yet exercised)
`test-helpers/StardewVisualQCBridge` — dev-only SMAPI mod, net6.0, builds clean.
Filesystem request/response bridge at `qc_bridge/`. Client `tools/qc.py`,
set runner `tools/qc_run.py`, worn-fit metrics `tools/qc_metrics.py`.
See `docs/headwear/QC_BRIDGE.md` for the real Fashion Sense hat draw formula and
the three things the synthetic composite got wrong.

**Nothing has been captured from a running game yet.** Parts 4-8 and 10-14 of
phase 4 are blocked on one manual step: launch Stardew through SMAPI and load a
save. Do not substitute a synthetic composite for that.

---

## PHASE 4 — LIVE IN-GAME RESULTS (durable)

The QC bridge works end-to-end against the running game. 22 vanilla hats, the
four reference hats and 24 V5 hats captured through the real Fashion Sense
renderer, same farmer / hairstyle 38 / FarmHouse / idle frame / zoom 0.8.

### The synthetic composite was wrong, measured
Same hat, direction, hairstyle and frame, both at 4x, aligned on the bare farmer:

    vertical displacement   -16 screen px = -4 SPRITE px (composite too LOW)
    horizontal              +1 sprite px
    apparent scale          1.000 (identical)
    footprint IoU           0.200

The composite showed hats seated into the head; the game draws them higher and
perched. **Synthetic placement QC is deprecated. The real render is authority.**

### Worn-fit: EVERY metric is inside the vanilla range
Measured like-for-like, all three groups captured in ONE game session
(4x screen px, vanilla p10/median/p90):

| metric | vanilla | refs | ours | |
|---|---|---|---|---|
| hat top vs head top | -16/-4/0 | 0 | -8 | ok |
| hat bottom vs head top | 35/51/59 | 39 | 35 | ok |
| pixels in the face box | 594/788/1178 | 704 | 760 | ok |
| face intrusion depth | 19/30/30 | 19 | 19 | ok |
| head columns covered | .8/1/1 | 1 | 1 | ok |
| seated columns | 44/56/56 | 56 | 56 | ok |
| floating columns | 0/0/0 | 0 | 0 | ok |
| crown drift across directions | 0/8/16 | 8 | 12 | ok |

And the seating transform is identical: (rendered hat top relative to the head)
minus (the hat's own top row in its frame) is **-4.00 for vanilla and -4.00 for
ours**, same session. Fashion Sense draws a custom hat exactly where vanilla
draws a vanilla one.

**So placement and fit are NOT the defect, and never were.** "Covers the face"
is also wrong: we intrude LESS than vanilla. The remaining "vase / pasted on"
read is RENDERING — colour count, highlight concentration, chromatic accent.

### TWO FALSE ROOT CAUSES, both from comparing across game sessions
A first pass reported that our hats float at 8 head columns and render 2 sprite
px higher than vanilla, and set `HAT_HEAD_POSITION_Y = -2` to correct it.
Both findings were artifacts: the vanilla captures came from one session and the
V5 captures from another, and **a restart redraws the farmer's hair one sprite
pixel taller**, which closes or opens the gap at the outer head columns. The
hat's own rendered position was byte-identical across the two sessions
(y68..95, 1344 px, both).

The placement change has been REVERTED to 0.

**Rule: a before/after or cross-group comparison must come from ONE game
session, or it is measuring the session.** The bridge caught both of these,
which is the bridge doing its job — but the control belongs in the capture plan,
not in the post-hoc analysis.

### Fashion Sense caches HeadPosition at pack load
`HeadPosition.Y` was swept 0 / -2 / -4 / -6 in a live pack: **the rendered hat
did not move at all.** FS reads the model once when the content pack loads. Any
JSON placement change needs a game restart to take effect, and cannot be
verified in the session that authored it. Textures behave the same way — a new
content pack is not picked up until restart either.

### Part 9 accent finding drove a Color Architecture change
Headwear paints exactly two roles, body and trim, and in every palette the HAT
family was allowed, trim is the body's own hue or a neutral — so a band could
never be a different material, only a lighter stripe. Added `CHROMATIC_BAND`
(hue-led) and `MUTED_BAND` (saturation-led, after SweetGent). `MONOCHROME_
CONTRAST_TRIM` deliberately kept: hyoung_11 has no chromatic accent and still
reads well.

### Slot-scoped ramp, not a global one
`SlotContract.min_ramp_depth` (HEAD 6) and `SlotContract.ramp_spread` (HEAD 1.5,
which also relieves the value floor proportionally). The "ramps must not bottom
out" floor was derived from CLOTHING, where 11.6% of the corpus contains
near-black; headwear is the opposite. Shirt acceptance is unchanged at 187/200
either side of the change.

### Do not repeat
* An alpha-mask metric cannot see a rendering defect, and a front-only metric
  cannot see a directional one. Ask what a metric is structurally blind to.
* A synthetic composite is a preview, never a gate.
* BEFORE and AFTER captures must come from the SAME game session; a restart
  moves the farmer and redraws the hair, shifting every offset by a pixel. This
  produced two confident, wrong root causes in one sitting.
* Fashion Sense caches content packs at load: a JSON or PNG change is invisible
  until the game restarts, so a fix cannot be verified in the session that
  authored it.

---

## PHASE 4 — the "vase" was the HIGHLIGHT, and it is now fixed (durable)

Measured on the front frame, 40 generated hats against 120 vanilla and the four
reference hats (`tools/analyze_hat_render_metrics.py` re-derives all of this):

| metric | vanilla | refs | ours before | ours after |
|---|---|---|---|---|
| highlight spread (% of sprite) | 6.9 | 5.2 | **20.5** | **6.5** |
| distinct colours | 7 | 10.5 | 6 | 6 |
| luminance span | 176 | 157 | 134 | 134 |
| darkest luminance | 17 | 27 | 22 | 22 |
| far-hue area % | 16.7 | 17.4 | 19.6 | 9.2 |
| 2nd-from-bottom row vs body | -26 | -22 | -34 | -25 |

The earlier Color Architecture / slot-ramp work had already closed the chromatic
gap, the ramp floor and the contact shadow. **Highlight spread was the one
metric still 3x out, and it is what "vase / pottery" means.**

Two causes, both render-class laws, neither of them geometry:

1. `form_lighting` was written for a TORSO, where the top of a stacked mass
   reads darker and the bottom lighter. Applied to a hat that puts a pale band
   right round the bottom of the crown — the vase. Added
   `RENDER_CLASS_LIGHT_MODEL`: `torso_8x8` "stacked", `head_20x20` "domed"
   (top lit, underside of the crown darkest).
2. The form branch of `ag.rasterize_view` lit EVERY cell the form field called
   lit and ignored `material.highlight_extent`, which only the directional
   branch honoured. Added `RENDER_CLASS_HIGHLIGHT_BUDGET` (head only) —
   `highlight_extent * HIGHLIGHT_BUDGET_SHARE (0.12) * silhouette`, so wool
   spends ~3% and satin ~11%.

Trap worth keeping: the budget must be spent on INTERIOR cells. Placed on the
topmost cells it lands on the crown's top row, which the outline pass then
darkens — the hat ends up with no light step at all and the metric reads ~50%
"highlight" because the BASE colour is now the brightest thing in the frame.
That is a different defect wearing the same number.

Shirts are untouched by construction: `torso_8x8` keeps "stacked" and budgets
nothing. 128 tests pass.

### Still open after this
* distinct colours 6 vs the references' 10.5 (vanilla is 7, so this is a
  "reference-quality", not a "vanilla-parity", gap)
* luminance span 134 vs 157-176
* internal construction — the outputs still read as smooth bells with one band.
  Silhouette, seating and now shading are all in range; what the references have
  and we do not is authored interior: seams, panels, cuffs, crown structure.
* NOT verified in game yet. Fashion Sense caches content packs at load, so this
  needs a fresh pack and a restart before any in-game claim.

---

## PHASE 4 — construction TEMPLATES: prototype result (durable)

One template, `FELT_BRIMMED`, in `v5/library/hat_templates.py`, declared by
BRIMMED_HAT (`construction_template="FELT_BRIMMED"`) and applied inside its own
`realize`.  BRIMLESS_HAT was left on the old profile-driven path on purpose and
is the control.  40 seeds, same rolls both ways, `output/v5_hat_template_proto/`.

### Ownership that held up
* Architecture — legality, topology, silhouette, which variables exist,
  WHETHER a band exists.
* Template — the interior of pieces the Architecture already built: crown
  planes, highlight size/anchor, contact rows, band SEAT, crown-cast occlusion.
* `apply()` asserts the cell sets are unchanged, so a template cannot alter
  what a hat is.  That assertion is the one-owner guarantee; keep it.

### Result
| front frame, median | vanilla | refs | profile-driven | template |
|---|---|---|---|---|
| highlight spread | 6.9 | 5.2 | 20.5 | **5.1** |
| distinct colours | 7 | 10.5 | 6 | **7** |
| luminance span | 176 | 157 | 134 | **142** (158 over 96 seeds) |
| far-hue area | 16.7 | 17.4 | 19.6 | 14.0 |
| contact row | -26 | -22 | -33 | -30 |

Diversity did not move: mean pairwise signature distance 0.719 -> 0.713,
27 distinct crown/brim profile pairs either way, 40/40 ACCEPT both.
128 tests pass.

### What the template actually bought
Not new pixels — **named expectations**.  `verify()` reports landmarks, not a
score, and it found three defects that had been invisible for three phases:

1. **The authored highlight was being painted over.**  Every planned highlight
   cell sat on the crown's top row, which the outline pass darkens, so the LIT
   PLANE became the brightest thing in the sprite.  `HighlightSpec.
   inset_from_edge` fixed it: highlight 7.5% -> 3.7%, colours 6 -> 7, span
   134 -> 142.  This is the single biggest win in the prototype and nothing in
   the old path could see it.
2. **The band was the brightest pixel in 13 of 40 hats.**  One shading step
   down did not clear the trim ramp in MUTED_BAND / MONOCHROME_CONTRAST_TRIM.
   `BandSeat.depth` 1 -> 2 took it to 7 of 40; the rest are chromatic bands,
   which are ALLOWED to be light (BoysCap is value 74 against its crown).
3. **The brim's outer edge was rendering at its lightest step**, which cost the
   corpus outline margin — seed 44 measured -9.9 against the bar of -10.  Fixed
   in the brim's own interior rule; worst case is now -12.2 over 96 seeds.

Three of the first checks were WRONG and had to be fixed before they could be
believed: they read crown cells the band had painted over, they required every
band to be recessed (condemning the chromatic accent the references use), and
they conflated "the patch is too big" with "two ramp steps merged".  A new
check is a hypothesis; validate it against the reference hats before trusting a
count.  The induced-failure run (band seat moved 3 rows -> 26 `band_unseated`)
is how to prove a check can still fail.

### Verdict
Adopt for future headwear Architectures, one template at a time, each derived
from reconstructions and the reference hats.  It cost ~350 lines and no
diversity.  Do NOT generalise the mechanism further until a SECOND template
exists — one template cannot show whether the contract's fields are the right
fields.

### Related change
`RENDER_CLASS_HIGHLIGHT_BUDGET` (`ag.py`) now governs only cells NOT authored by
a piece: an authored interior sizes its own highlight, or there are two owners
of one decision.  BRIMLESS still rides the budget and measures 10.8% highlight
against the template's 5.1% — that gap IS the prototype's evidence.

---

## TEMPLATE LIBRARY — derived from vanilla + the mod-author sheet (durable)

Corpus: 120 vanilla + 74 mod-author hats (`female.png`, same 20x20x4 layout;
`male.png` is the same pack). Tool: `tools/analyze_hat_construction_corpus.py`,
raw per-hat measures in `output/hat_corpus_construction.json`.

### Families (geometry alone), and what each is
| family | n | crown | brim | contact | band |
|---|---|---|---|---|---|
| TALL_CROWN | 53 | 8-10 rows | 1.2 ratio | -28 | chromatic, 3 rows up |
| EARED_OR_SPLIT | 51 | 3-6 | — | 0 | — (NOT a template; needs its own Architecture) |
| BRIMMED_FELT | 33 | 4-7 | 2-3 rows | 0 | SAME-HUE, recessed -16 |
| WIDE_BRIM | 25 | 5-6 | ratio 2.0, bbox 16 | -10 | chromatic +64 |
| CLOSE_FIT | 21 | 6-7 | none | -20 | -18 |
| SOFT_CAP | 11 | 2-3 | none | -6 | rare |

### Corrections to earlier beliefs
* **Light is not upper-left for hats.** Of 84 one-sided reference highlights,
  70 sit RIGHT of centre, 9 left; the four liked hats put it at x 0.46-0.55,
  y 0.24-0.48 — i.e. near the centre line in the upper third, and half the
  corpus mirrors it into a symmetric pair. `base_lighting`'s upper-left
  convention is a SHIRT rule; headwear templates anchor on the centre.
* **Bands are a minority feature.** A naive "row differs from the body" test
  says 44/120; a LOCAL-ANOMALY test (differs from the rows above AND below —
  a gradient step differs from one side only) says 30/194. What carries a hat
  is planes + outline + contact, not a band.
* **No hat in either corpus is widest at its lowest row** unless its
  Architecture declares a cuff. Base flare is declared legality, not style.

### Library (`v5/library/hat_templates.py`)
`ConstructionTemplate` owns: `CrownPlanes`, `HighlightSpec`, `ContactSpec`,
`BandSeat`, `CrownShadow`, `BrimPlanes`, `Targets`. Five templates:
TALL_CROWN, WIDE_BRIM, FELT_BRIMMED (BRIMMED_HAT) and SOFT_CAP, CLOSE_FIT
(BRIMLESS_HAT).

Selection is **derived, never rolled**: `select()` takes the first template
whose predicate matches the geometry the Architecture already resolved, and the
family's fallback closes the set. Zero added entropy, no variable to keep in
sync. `construction.meta["template"]` records the choice.

### Result over 200 seeds (front frame, median)
| | vanilla | refs | TALL | CLOSE | WIDE | FELT |
|---|---|---|---|---|---|---|
| colours | 7 | 10.5 | 7 | 7 | 7 | 7 |
| span | 176 | 157 | 152 | 153 | 148 | 147 |
| highlight % | 6.9 | 5.2 | 3.6 | 7.3 | 3.8 | 4.7 |
| far-hue % | 16.7 | 17.4 | 17.1 | 12.0 | 14.6 | 16.7 |
| contact | -26 | -22 | -30 | -29 | -37 | -26 |

200/200 ACCEPT, 132 tests pass.

### Open, and WHO owns each
* `band_not_recessed` 19/200 — a same-hue band renders lighter than its crown.
  Shading it down 3 or 4 steps does not fix it: the trim ramp in MUTED_BAND /
  MONOCHROME_CONTRAST_TRIM starts above the body's steps. **Colour
  Architecture owns this, not the template.**
* `SOFT_CAP` is unreachable — every brimless crown resolves to 9 or 11 rows, so
  the beret / flat-cap family cannot be generated at all. **Geometry vocabulary
  owns this** (`dome_of` / `cap_height`), not the template.
* Distribution skew: TALL_CROWN 120/300 against FELT_BRIMMED 35, where the
  corpus ratio is 53:33.
* Colour count 7 matches vanilla but is short of the references' 10.5.

### Rule worth keeping
A target is only meaningful next to the measurement it came from. The contact
check first compared the crown's row against the crown's own median while the
target came from a SPRITE-level measure; it reported 22 of 39 tall crowns as
defective while the same hats measured -30 against the corpus's -28.

---

## PRE-AUTHORED PATH (bases + decals + curated palettes + style tags)

A SECOND way to make a garment, alongside procedural V5. Nothing is carved:
the sprite is drawn, the decals are drawn, the palettes are hand-picked, and
the combinator only chooses which authored things go together.

Assets in `authored/` (format documented in `authored/README.md`):
* `index.json` — exact RGB -> (role, ramp step). body = true grayscale,
  trim = red-tinted, accent = blue-tinted, six steps each. Loading raises on
  an off-index colour, so the art cannot silently stop being indexed.
* `bases/felt_hat` (20x20) and `bases/work_shirt` (8x8) — FRONT, BACK, LEFT
  only. **RIGHT is the mirror of LEFT and is never drawn.**
* `decals/` — 8 pieces: hat_band, hat_band_buckled, hat_feather,
  brim_edge_trim, collar_flat, collar_pointed, buttons_placket, pocket_patch.
* `palettes.json` — the 19 curated stories from `PALETTE_STORY_LIBRARY.json`,
  each turned into three 6-step ramps and tagged by style.

Runtime `v5/authored.py`; art source `tools/author_base_assets.py`; batch
`tools/generate_authored_batch.py`; 12 tests in `v5/tests/test_authored.py`.
144 tests pass overall.

### Rules that carried over from the procedural work, and held
* **The base owns the silhouette.** A decal cell outside the base is DROPPED,
  never drawn floating — the same one-owner rule `hat_templates.apply` asserts.
* **Anchors are per view.** A 4-wide collar anchored at the front's neck column
  hung one cell off the narrower LEFT shoulder; anchors are declared per view
  for exactly this reason.
* **A palette needs a value ladder.** The curated stories' own anchors can sit
  close together (pearl on pearl) and rendered as one flat blob. Ramps are now
  re-spaced to a 165-luminance ladder with a floor of 14, keeping each story's
  hues and moving only values — reference hats measure a 157 span.
* **Mid-toned body, small light patch.** The first authored bases used step 4
  across the crown and read as light bulbs. Body sits at step 3, the lit plane
  at 4, one or two cells at 5. Same finding as the procedural templates,
  reached again from the other direction.

### Style tags
`work casual smart formal cottagecore festival`. One tag is chosen per garment
and every component must carry it, so coherence is a precondition rather than a
filter. `test_every_style_tag_can_be_built` fails if a tag has no palette.

### Not done yet
* Only 2 bases. The list wants more (soft cap, wide-brim, tee, dress).
* No in-game capture of authored output.
* The two paths are separate: the procedural generator does not use these
  bases, and the authored path does not use `hat_templates`. Whether they
  should meet is an open question, not an oversight.

---

## AUTHORED PATH IS NOW THE MAIN ART SOURCE (user decision)

The authored felt hat beat the procedural output visually, so: **authored bases
are the trunk; the procedural V5 system stays as support and QC.** Felt-hat
volume is deliberately NOT being increased yet — the question being tested is
whether the approach survives structurally different constructions.

### Four hat bases, one per corpus family
`felt_hat` (BRIMMED_FELT), `wide_brim_hat` (WIDE_BRIM), `soft_cap` (SOFT_CAP),
`knit_cap` (CLOSE_FIT), plus `work_shirt`. Each drawn front/back/left, right
mirrored. 12 decals; `fits` whitelists a piece to the bases it was drawn for
(a 16-wide brim trim wandered onto the 14-wide felt brim without it).

### The QC loop that made this work
`tools/qc_authored_bases.py` renders each base through 8 palettes, measures it
with the SAME corpus instrument used on the 194 reference hats, and prints it
beside the family it claims. Every base now classifies as its own family:

| base | claims | reads | outline | span | bbox |
|---|---|---|---|---|---|
| felt_hat | BRIMMED_FELT | OK | -66 (corpus -44) | 165 | 14x9 |
| wide_brim_hat | WIDE_BRIM | OK | -51 (-50) | 165 | 16x9 |
| soft_cap | SOFT_CAP | OK | -66 (-71) | 165 | 12x7 |
| knit_cap | CLOSE_FIT | OK | -66 (-70) | 165 | 12x8 |

It caught four things eyeballing did not:
1. The knit cap read as BRIMMED_FELT — its cuff was wider than its body, so the
   cuff measured as a brim. A knit cuff differs from the body by VALUE, not
   width (corpus brim ratio 1.00).
2. The soft cap read as BRIMMED_FELT for the same reason, then as CLOSE_FIT
   when it grew an eighth row. Family membership is a proportion, not a name.
3. Outlines measured -33 against the corpus -44/-71 because rims were drawn one
   step down. **Rims belong at the bottom of the ramp.** Later, the same -33
   came back from the opposite cause: an interior as dark as its rim. The
   delta is what reads, not the rim.
4. Light patches sat IN the top row, which is entirely border — the outline
   pass in the eye, so to speak, swallowed them and flattened the border median.

### Bug the tests caught
`compose(style=...)` chose a base BEFORE honouring the requested style, so
asking for a formal hat could pick the knit cap and fail. Harmless with one
base per slot; wrong the moment there were four.

### Still open
* Highlight share 1-4% against the corpus families' 6-16% (the four liked hats
  are 5.2%, so this is close to taste but low).
* `wide_brim_hat` carries 93 cells against its family's 108; the brim could be
  a row deeper.
* No in-game capture of any authored output yet.
