# V5 First Sailor Build — Implementation Report

Answers section 61 of `V5_Clothing_Generator_Canonical_Merged_Architecture_Claude_Handoff.md`.
Scope built: `SAILOR_TOP → CLASSIC_SQUARE_FLAP` only, native 8×8 @ Scale 4, through the
new Decision + Construction + AA + AG + Projection pipeline. No legacy renderer, AA, AG
or Sailor code was imported or called.

**Batch:** seeds 0–95 → `output/v5_sailor_batch_01/` (per-garment atlas + dye mask + spec
JSON, `content.json`, `report.json`, `contact_sheet.png`).
**Tests:** 45 tests in `v5/tests/test_v5.py`, all passing.

## Module map

| Pass | File | Owns |
|---|---|---|
| 0 | `v5/grammar.py` | envelope, landmarks, zones, ramp capability, base lighting, edge kinds, occlusion composition, FS export contract |
| — | `v5/rng.py` | named hash-derived streams (a draw is a pure function of seed+stream+index) |
| 1 | `v5/context.py` | Roll Context, Style Context hooks, resolution-time gates |
| — | `v5/schema.py` | Variable, Budget, OccupancyLedger, Record, generic `resolve_variable` |
| — | `v5/contracts.py` | Slot / Family / Architecture contract types + registries |
| 2–9 | `v5/resolver.py` | the generic resolver and `GarmentSpec` |
| 3–4 | `v5/library/sailor_top.py` | **all** sailor authoring: vocabulary, commitments, child schema, authored geometry, style hooks |
| 6A/6B/7/8 | `v5/material.py`, `v5/color.py`, `v5/surface.py`, `v5/ornament.py` | shared libraries |
| 10 | `v5/construction.py` | Piece / Construction, region maps, occlusion fields |
| 11 | `v5/aa.py` | mass hierarchy, contrast distribution, surface & ornament placement, accent economy |
| 12 | `v5/ag.py` | ramps, lighting, occlusion, contrast-aware selective edges |
| 13 | `v5/projection.py` | 4 directions, dye mask, atlas, FS metadata, continuity/coverage checks |
| 14 | `v5/quality.py` | raster signature, perceptual distance, classification |

---

## 1. Did Family + Architecture contracts work without Sailor-specific resolver control flow?

**Yes.** `v5/resolver.py` contains no reference to `SAILOR_TOP`, `CLASSIC_SQUARE_FLAP`,
collars or flaps. It resolves Slot → Family → Architecture from the registries, then walks
whatever `Variable` list the Architecture publishes. Sailor lives entirely in
`v5/library/sailor_top.py`.

Three hooks were needed to keep it that way, and they are the honest cost of the design:

* `ArchitectureContract.declare_schema(family, arch, ctx, record)` — publishes the child schema.
* `ArchitectureContract.realize(spec, envelope)` — Pass 10.
* `ctx` exposes `budget`, `occupancy`, `record`, `geometry`, `palette` so that
  Architecture-authored activation predicates and validators can gate themselves without
  the engine knowing what they gate.

## 2. Which schema fields were unnecessary?

* **`Variable.significance`** never changed behaviour. It is read once (identity variables
  refuse to silently drop) and otherwise only documents intent. Keep it as measurement
  metadata, not as a resolution input.
* **`FamilyContract.closure_vocabulary` / `aperture_vocabulary` / `limb_vocabulary`** were
  write-only for a single-architecture family: they were validated against the Architecture
  and never read again. They will earn their place at Blazer (multiple closures), not here.
* **`SlotContract.render_class` / `dye_mask` / `coverage_axis`** are currently decoration.
* **`ArchitectureContract.topology`** duplicates what `realize()` actually builds; today it
  is only serialized as `construction_refs`.

## 3. Which missing fields were required?

1. **`Piece.identity: bool`** — AA needs to know which pieces carry family identity, in
   order to protect them. Without it, a repeating Surface ran straight through the V and the
   flap and the garment stopped reading as a sailor top (this was visible in the first batch).
2. **A `termination`/shadow footprint that doubles as trim geometry.** Reusing
   `Piece.occlusion[view]` as "the fabric this free edge lies over" removed a whole class of
   special cases: piping, single stripe and double stripe are all *distance rings measured
   outward from the termination*.
3. **`Variable.stream`** — a named RNG stream per variable group. Without it, adding an
   ornament shifted every later draw and the whole corpus changed.
4. **Spend-order enforcement in `Budget`.** The canonical text states Construction → Surface
   → Ornament as an order; the first implementation declared `collar_trim` in the structural
   block and silently spent ORNAMENT budget before Surface. Budget now refuses it, which
   forced the schema to be declared in the correct order.
5. **`Envelope` guard in `realize()`.** An Architecture must be able to *decline* an
   envelope it has no authored silhouette for, instead of stretching art it does not have.

## 4. Did authored-piece-first Construction work at native 8×8?

**Yes, and it is the right call.** Five authored pieces (`body`, `sleeve`, `front_insert`,
`collar`, `rear_flap`) plus three bounded parametric dimensions (`collar_width`,
`neckline_depth`, `rear_flap_depth`) cover the whole architecture. The V is generated by one
small function (`_v_geometry`) that widens/narrows an authored relationship; silhouettes are
three authored string-art sets. Nothing is carved procedurally.

The one place authored-first bit back: **a 1-pixel collar has no interior**. Any trim
treatment that paints "on the collar" consumes the collar entirely. That is a real
consequence of 8×8, not a bug, and it forced the distance-ring model in answer 3.

## 5. Which scoped parameters generated real visual diversity?

Measured as mean palette-independent raster distance between pairs that *differ* in the
parameter minus pairs that *share* it (96 garments, all pairs):

| parameter | Δ distance |
|---|---|
| `surface_family` | **+0.076** |
| `collar_trim` | **+0.058** |
| `collar_width` | **+0.052** |
| `silhouette` | **+0.045** |
| `rear_flap_depth` | +0.033 |
| `neckline_depth` | +0.025 |
| ornament set | +0.020 |
| `detail_package` | +0.013 |

On the full metric (palette included) `color_architecture` dominates everything at
**+0.123** — colour architecture is by a wide margin the strongest identity lever in the
system, exactly as section 21 predicts.

## 6. Which collapsed into near-duplicates?

* **`material` — Δ −0.010 structurally, +0.004 on value structure. It is currently invisible.**
  Ramp amplitude, depth and highlight extent all move, but at 8×8 with a mask this small the
  differences fall below one quantisation step. Material's only *reliable* effect today is
  indirect: pattern eligibility (wool and silk forbid stripes) and formality weighting.
* **`neck_accessory` — Δ −0.002.** Two or three accent pixels at the V apex, and the two
  values (`NECKERCHIEF`, `TIE_KNOT`) differ by one cell. Semantically real, visually nil.
* **`surface_phase`** was declared `SUBTLE` and behaves like it.
* **`DOUBLE_STRIPE` partially collapses**: on the deep rear flap it renders as two stripes
  with a gap (correct), but on a 2px collar there is no room for a gap and it renders as a
  single stripe. Same value, two different visual outcomes depending on the piece.

## 7. Did Material produce visible differences?

**No — this is the clearest negative result of the prototype.** See answer 6. Material earns
its place as a *compatibility* layer (which surfaces are legal, which formality it suits) but
not yet as a rendering layer. Recommendation in answer 17.

## 8. Did Color Architecture produce coherent rich palettes?

**Yes.** Distinct colours per garment across all views: min 10, **median 14**, p90 16, max 18
— against corpus median ~10 and p90 ~17. Ramp depth 4/5/6 in a 33/57/9 split. Every colour
traces to `ColorArchitecture → RoleSpec → harmony → material-aware ramp`; no piece ever rolls
RGB, and a test asserts every rasterized pixel is a member of the authored palette.

Residual miss: **22.9% of garments contain a pixel below luminance 40, against a corpus
figure of 11.6%**. Two rounds of ramp-floor recalibration took it from 36.5% to 22.9%. The
remainder comes from *occlusion stacking on an already-dark role*, not from outlining — the
dark pixels are interior shadow, not a silhouette ring.

## 9. Did the complexity budget improve busyness control?

**Yes, measurably.** Feature count (ornaments + surface + layers) is significantly lower for
complexity ≤ 2 than for complexity ≥ 3 across 400 rolls, and the assertion is a test. One
shared pool with tagged spends was sufficient; **do not split it yet.**

The tuning lesson: the pool must be sized for *design* spending, not construction. In the
first version, structural costs consumed the whole pool and Surface and Ornament were never
reached in any of 300 rolls. Making dimensional parameters free (`neckline_depth`,
`rear_flap_depth`) and charging only for genuine added busyness fixed it.

## 10. Did semantic occupancy remove special-case exclusions?

**Yes, and all three claim modes were exercised by real features:**

* `hem_band` claims `hem:girth` **exclusive**.
* `chest_emblem` claims `chest:center` **conditional-share** against the incumbent
  `front_insert`, with the condition being an actual contrast measurement between the accent
  role and the under-layer role.
* `neck_accessory` claims `collar:center` **overlay** over the collar.

No pair-specific exception exists anywhere in the code. The stripe-plus-emblem case the
handoff calls out is resolved by the overlay/share machinery, not by an if-statement.

## 11. Did Surface and Ornament stay cleanly separated?

**Yes.** Surface is a region treatment resolved in Pass 7, doubly gated on material
eligibility and readable area, with bounded in-domain repair on `surface_period`. Ornament is
discrete, resolved in Pass 8 from the remaining pool, gated on occupancy. They never touch
each other's data. `solid` correctly serializes as *absence of a surface feature*, not as
`surface: none`.

## 12. Did the new AA/AG produce convincing layered fabric?

**Yes for the front V and the rear flap.** Collar over insert over body reads as three
distinct fabric planes because the collar declares a free inner edge, stamps a shadow on the
insert beneath it, and AG darkens by ramp index rather than by painting a line.

**One AA responsibility had to be invented during the build:** an *identity quiet zone*. A
periodic surface running into the V or the flap destroyed the sailor read. AA now reverts the
surface figure in a one-cell ring around every identity piece. This is legitimately AA's job
(focal hierarchy and contrast distribution) and it invents no feature — but it was not
anticipated by the handoff and should be written into the canonical AA responsibilities.

## 13. Did contrast-aware outlining outperform global outlining?

**Yes. Only 50.0% of free-edge adjacencies (2,587 of 5,177 across 96 garments) needed any
edge treatment at all** — the colour architecture had already separated the other half. A
global dark pass would have laid down twice the ink, and would additionally have outlined the
~1,900 *attached* edges (sleeve-to-body, shoulder-to-collar) that correctly received nothing.
No garment in the batch has a silhouette outline ring.

## 14. Did local occlusion work without crushing ramps?

**Yes.** Stamps compose by MAX (tested), modify ramp indices only, and a test asserts every
back-view pixel is still a member of the authored palette. The clamped ramp floor stops
`shadow + occlusion` from bottoming out. One real bug was caught by the test suite: the
collar's side-view shadow was stamping a column where no collar sat above it.

## 15. Were side/back views naturally coherent?

**Yes — 0 continuity and 0 coverage failures across 96 garments** (and across 500 during
development). Backs are naturally simpler than fronts: the flap is one mass, plane-wrapped
surfaces and front-only ornaments do not appear, and nothing is cloned from the front.

The girth invariant needed correcting, and this is an amendment to section 38: a girth
feature does **not** occupy identical rows in every view. A sailor collar wraps the neck and
then descends into a V on the front only. The testable invariant is *presence in every view
plus a shared anchor row*, and for a girth **surface** it is that one period/phase rule holds
in every view — which cells are visible legitimately differs, because the flap covers the back.

## 16. Accepted / near-duplicate / weak / illegible

96 seeds, gate run over the batch:

| classification | count | % |
|---|---|---|
| ACCEPT | 95 | 99.0% |
| IDENTITY_TOO_WEAK | 1 | 1.0% |
| NEAR_DUPLICATE | 0 | 0.0% |
| LEGIBILITY_FAILURE | 0 | 0.0% |

Nearest-neighbour raster distance: min 0.158, p05 0.215, median 0.335 — against a provisional
near-duplicate threshold of 0.14. **Nothing in the batch came close to the threshold**, so
0% is a real result rather than a lenient one, but the threshold itself is unvalidated: it
has never been exercised against a true duplicate pair. Treat the 0% as "no duplicates found
by this metric", not as "the metric works".

Nine garments carry non-fatal warnings: 5 where the rear flap reads under the contrast floor
against the back body, 4 where the insert reads weakly against its own frame.

## 17. Architectural changes recommended before attempting Blazer

1. **Make Material a rendering layer or demote it.** Right now it is a compatibility table
   wearing a renderer's clothes. Either give it levers that survive 8×8 — a declared
   dither/texture stamp, a distinct edge-treatment behaviour, a cuff/hem rendering rule — or
   move `patterns` and `formality_weight` onto Color Architecture and delete the rest.
   Blazer will make this worse, not better: melton vs flannel vs worsted is exactly the kind
   of distinction that collapses.
2. **Add "identity protection" to the canonical AA responsibilities** (section 31). It was
   required, it is not decoration, and Blazer's lapels will need the same treatment against
   the same surfaces.
3. **Amend the girth/wrap definition in section 38** to anchor-agreement plus rule-agreement,
   per answer 15. The strict reading is not satisfiable by real garments.
4. **Give trim its own tier.** `collar_trim` is currently a structural-pass variable that
   spends ORNAMENT budget, which is a smell. Blazer will want lapel piping, pocket welts and
   button bands, all of which are "trim on a declared piece's free edge". The distance-ring
   mechanism generalises cleanly; it should be promoted from sailor authoring into a shared
   trim library.
5. **Split the quality gate's identity check from the family.** `identity_score` currently
   hard-codes sailor landmarks (V frame, insert, flap). Each Architecture should *declare*
   which piece pairs carry its identity, and the gate should measure whatever is declared.
   This is the last piece of family-specific logic outside the library, and Blazer is the
   right moment to remove it.
6. **Validate the near-duplicate threshold before trusting it.** Deliberately construct
   near-identical specs and check the metric fires. Consider dropping the palette term to a
   coarser bucket still — hue is continuous, so it currently supplies a constant distance
   floor that flatters every comparison.
7. **Reconsider `Variable.significance` as a measured field, not a declared one.** The batch
   already measures per-parameter visual leverage; that number is more trustworthy than the
   author's guess, and it is what should drive weighting.

## Section 57 review matrix

| dimension | verdict |
|---|---|
| Construction identity | Strong. V + flap read at every seed; identity comes from topology, not decoration. |
| Structural coherence | Strong. 0 validation failures, no orphan cells, no Frankenstein combinations. |
| Front/side/back continuity | Strong. 0 failures across 96 (and 500 in development). |
| Palette coherence | Strong. Every pixel traces to a role and an authored ramp. |
| Color richness | On target. Median 14 colours, p90 16. |
| Selective outlining | Strong. Half of all free edges needed nothing; attached edges never treated. |
| Free-edge behaviour | Correct and tested; sleeves have no free edges and are never outlined. |
| Local occlusion | Correct; MAX composition; no ramp crushing. |
| Material readability | **Weak — see answers 6, 7, 17.** |
| Surface-domain correctness | Good, once the AA quiet zone was added. |
| Ornament correctness | Good; occupancy-gated, budget-gated, correctly optional. |
| Accent economy | Good; capped at 2 point-accent features per view. |
| Diversity across seeds | Good; NN distance median 0.335, min 0.158. |
| Near-duplicate rate | 0% — but the threshold is unvalidated. |
| Native Stardew/FS readability | Good; 8×8 native, Scale 4, correct atlas order, dye mask emitted, shoulder coverage verified per direction. |
| Native mod art vs downscaled art | Reads as native. Nothing is resized; every decision is made at 8×8. |

## Where the canonical text was amended

Per section 60, these are the places the implementation departs from the letter of the
handoff, with the contradiction stated:

1. **Section 23 role list.** The canonical vocabulary mixes two orthogonal axes (`body`,
   `trim`, `accent` are *fabrics*; `shadow`, `mid`, `highlight` are *ramp steps*). Section 35
   requires occlusion to "modify existing ramp indices", which is impossible if a role *is* a
   ramp index. Split into `FABRIC_ROLES` × `RAMP_STEPS` (`v5/grammar.py`).
2. **Section 38 girth semantics.** See answer 15.
3. **Section 31 AA responsibilities.** Identity protection added. See answer 12.
