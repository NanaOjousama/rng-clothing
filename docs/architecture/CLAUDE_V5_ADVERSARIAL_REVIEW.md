# V5 Adversarial Review

Status: review only. No implementation code was changed.
Author: Claude (Opus 5), 2026-09-02.
Reviews: `docs/architecture/CLAUDE_INDEPENDENT_ARCHITECTURE.md` and the revised V5 candidate.
Method: new measurements against the installed `Characters/Farmer/shirts.png` and `Data/Shirts.json` (1.6.15), aimed at breaking the proposal rather than confirming it.

---

## 0. Headline

`FULL GENERATOR REBUILD` remains the recommendation, and `resolve → compose → colorize` remains the right core. But the measurements below break one shared assumption in **both** my original proposal and your amendment B, and the correction makes the system substantially smaller than either of us proposed.

**All eleven vanilla garments I tested — tee, collared shirt, polo, pullover, vest (x2), sailor (x2), overalls (x2), button-down — share the same alpha silhouette to within 0 to 2 cells.** 140 of 302 vanilla shirts share one byte-identical silhouette, including Classic Overalls, Suit Top and Aquamarine Shirt.

Vanilla does not distinguish a vest from overalls from a sailor top by shape. It distinguishes them by **partitioning the same torso into two colour slots** and modulating shading inside them.

The consequence: the "authored blank + small authored stamps" framing is the wrong emphasis. The dominant primitive is a **region overlay** covering 10 to 40 of ~60 cells, not a small cluster anchored near the neck. The mechanism I proposed still works unchanged; the authoring expectation, the library size, and the Phase 1 scope all shrink.

Phase 1 needs **one blank, about ten pieces, and no resolver at all.**

---

## 1. New evidence

All figures measured this session from the installed game assets.

### 1.1 Silhouette is not the differentiator

| Measurement | Result |
|---|---|
| Distinct front+right+back alpha silhouettes across 302 vanilla shirts | 77 |
| Shirts sharing the single most common silhouette | 140 |
| Benchmark garments (1, 248, 20, 278, 19, 259, 0, 216, 198, 140, 176) differing from plain tee [1] | 0 cells front; 0 to 1 side; 0 to 2 back |

The shared front silhouette is the full 8x8 torso with a two-cell neck notch.

### 1.2 Identity is a two-slot region partition

Vanilla shirts have a fixed base layer and a dye-mask layer. That is a two-slot system. Mapping which cells belong to which layer gives the garment's identity directly:

| Garment | Front slot-A (dye) cells | Reads as |
|---|---|---|
| Blue Buttoned Vest [278] | cols 0 and 7, rows 0-4 | inner shirt showing at the arms; vest is the centre |
| Green Buttoned Vest [281] | identical to 278 | same piece, different palette |
| Plain Overalls [216] | cols 0 and 7 rows 0-6, plus an upper-chest notch at cols 2-5 | shirt at the sides and between the straps; bib is the centre |
| Sailor Shirt [259] | a 10-cell cluster at rows 0-3 centre | collar is the second slot, body is the first |
| Collared Shirt [248] | everything except 2 cells | one fabric; the 2 fixed cells are buttons |

Vests 278 and 281 have byte-identical structure. They are one plan with two palettes, which is exactly the output a generator should produce.

### 1.3 Colour budgets are tighter than I proposed

| Measurement | Result |
|---|---|
| Rendered distinct colours across all four views | 3 to 12; typical 5 to 8 |
| Fixed-colour garments, modal distinct colours | 5 to 8 |
| Dyeable garments, distinct mask steps | mostly 3 to 6 |
| Mask cells that are pure grey | 3,024 of 7,967 (38%) |

My original doc proposed a validator ceiling of 8 colours per view. Vanilla's *whole garment* often uses fewer than that. I also over-claimed a shared canonical ramp: garments 248, 176 and 259 share the steps 71/145/181/219, but across the corpus there is no canonical ramp, and 62% of mask cells are tinted rather than grey. **Correction to my own earlier reasoning; do not build a ramp engine on that assumption.**

### 1.4 Readability is contrast, not area

Collared Shirt [248], rendered with its default dye, front view luminance:

- body base: 65
- collar cells: 70 (delta 5, essentially invisible)
- placket column: 54 (delta 11, weak)
- two button cells: 220 (delta 155, unmistakable)

The most readable identity cue in vanilla's collared shirt is **two isolated single pixels**. This directly refutes the universal two-cell rule I proposed in the original document. Your amendment A is correct, and for a stronger reason than stated: readability is contrast times area, and vanilla routinely trades area for contrast.

### 1.5 Mirror behaviour

| Measurement | Result |
|---|---|
| Benchmark garments where left equals mirror(right) exactly | 13 of 20 tested |
| Remaining ones | 1 to 3 differing pixels; alpha identical except Work Shirt [29] |
| Corpus-wide garments differing from mirror | 90 of 302; 78 colour-only, 12 alpha |
| Most frequent single differing cell | (2,3), in 23 of those 90 garments |

The differences are not systematic. There is no universal left-side lighting correction to model.

---

## 2. Accepted amendments

**A. Vanilla is floor, not ceiling — ACCEPTED, with a binding constraint.**
The two-cell rule is withdrawn; section 1.4 shows vanilla's strongest cue is two single pixels. Replaced by an **identity salience** rule (section 5.4).

The constraint: this repository's entire failure history is the sentence "now that the basics work, we can render a little better." That sentence produced the V3 surface layer, the V5E art polish, the V5D masculine grammar, the HD art grammar and the V6 legendary tier. So the extra resolution is spent **by authors, inside blanks and pieces, in authored data**. No code stage may compute, refine, smooth or reinforce a pixel. That invariant is testable (section 5.5) and is the thing that keeps amendment A from re-creating the polish stack.

**E. Extended provenance — ACCEPTED, always on, not debug-only.**
Cost is four 16x16 byte arrays per garment, about 1 KB. Store `(piece_index, local_x, local_y)`; resolve to `collar_sailor/back/local(3,1)` only when printing. There is no reason to gate this behind a flag.

**F. Palette migration staged separately — ACCEPTED without reservation.**
This is the single best amendment in your list. It is also better supported than either of us knew: section 1.3 shows there is no corpus-wide ramp to derive, so an OKLCH engine in Phase 1 would have been building on a wrong premise. Phase 1 reads existing palette-story hex roles and maps them to slot ramps directly. See section 5.3 for the one gap this exposes.

**Vanilla reconstruction first — ACCEPTED**, with fairness corrections in section 6.

---

## 3. Rejected amendments

**B. Blank library must remain open-ended — REJECTED as framed.**

Your stated worry is "avoid recreating the old problem where many garment families become decorations on the same torso." The measurements say that decorating one torso **is what vanilla does**, for every garment on your list. Overalls, vest, sailor, collared shirt, polo and pullover are all the same silhouette.

The old system's failure was not silhouette sharing. It was that the decorations were computed by rule engines, overwritten by later polish passes, and too low in contrast to read. Adding blanks would not have fixed any of that, and it would have multiplied the hand-shading work by the number of families.

Counter-proposal: a new blank is justified only when one of these is true.

1. **Coverage differs.** Cropped garments vacate lower rows; sleeveless garments vacate side cells that native arms then fill.
2. **The light field genuinely differs.** An open-front cardigan has two hanging edges that cast a different interior shading structure than a closed torso; that cannot be expressed as a slot swap.
3. **Fit silhouette differs at 8x8 after downsample**, by at least 3 cells.

By that test the initial library is roughly: `torso_basic`, `torso_cropped`, `torso_open_front`, and later one or two feminine or boxy fit variants. Three to five, not eight and not open-ended. Blanks are expensive because each one needs its own hand-authored shading in three views; pieces are cheap because they are small and reusable.

The corpus supports the criteria directly. Of sixteen exemplars across your nine garment families, fourteen sit within 4 cells of the plain tee's silhouette. The two that do not are Gray Vest [167] at 9 cells, which is the sleeveless one whose coverage genuinely changes, and Mint Blouse [2] at 15 cells, which has a recut neckline. Both are admitted by criteria 1 and 3 above. Neither is admitted by "it is a different garment family", which is the criterion amendment B would install.

The real defence against "everything looks the same" is not more blanks. It is stronger slot partitioning and the contrast gate, because that is precisely what separates vanilla's vest from vanilla's tee on an identical torso.

**C. Three-mode direction policy — REJECTED, replaced by one mechanism.**

`MIRROR`, `MIRROR_WITH_PATCH` and `EXPLICIT` are not three behaviours. They are one behaviour with three data sizes. Proposal:

- Every blank and piece authors `front`, `side`, `back`.
- `left` is mirror(side) unless the file contains a `left` block.
- If a `left` block exists it may list a few cells or a whole view. The loader does not care which.

That is one rule and one optional key. Section 1.5 shows the benchmark garments need it 0 to 3 cells at a time and that the differences are not systematic, so there is nothing for a "patch mode" to systematise. Phase 1 should not use the override at all.

**D, partial: required-parent and incompatibility graphs — REJECTED for Phase 1.**

This is where V3 became unmaintainable. `specs/hybrid_garment_compiler/v3/component_definitions.json` carries five parallel relationship vocabularies: `compatibleFamilies`, `compatibleMaterials`, `providesAttachmentRegions`, `continuityBehavior` and `hardCompatibilityRules`, plus a separate `component_compatibility.json`. Every one of them was written to prevent combinations that a template could simply not list.

Minimum sufficient model: **a template lists which pieces may fill which slot.** Incompatibility is expressed by absence. A piece additionally declares which named blank rows it needs, checked at load. Nothing else in Phase 1.

---

## 4. Modified amendments

**D, remainder: layer vocabulary — MODIFIED.**
`UNDER / BODY_EDIT / OVER / DETAIL` is accepted purely as a sort key, implemented as the integers 0 to 3, with the template's slot order breaking ties. Occlusion needs no vocabulary because later pieces paint over earlier ones. `alpha add`, `alpha cut` and `paint-existing-alpha-only` are not relationship metadata; they are three cell operators in the piece's own rows (`+`, `-`, and the ordinary role letters). The relationship model is therefore the operator set, which is about six lines of compositor code.

**G. Component taxonomy — MODIFIED. Useful as an authoring index, wrong as a model.**

The proposed taxonomy mixes three different mechanisms under one heading:

- Genuine pieces: crew, V, polo collar, sailor collar, shawl lapel, placket, zipper, bib, inner shirt, rib hem, bow, pocket, emblem.
- Blank properties, not pieces: waist shaping, darts, princess seams. These are shading and silhouette, so they belong to a blank or a fit variant.
- Region recolours that I originally proposed as a separate primitive: yoke, stripe, colour blocking. Section 1.2 shows these are the *same* primitive as a collar. There is no third primitive.

Keep the taxonomy as a documentation index and as the `kind` string that template slots reference. Create no code branch per category. Correct the three misfiled entries above.

**A, mechanism: identity salience replaces the two-cell rule — see section 5.4.**

---

## 5. Revised V5 architecture

The pipeline shape you proposed survives. Four changes: one primitive is renamed and re-scoped, one stage is deferred out of Phase 1, one cell operator is added, and one invariant is made testable.

### 5.1 Primitives

**Blank.** Per view: alpha, an authored role field (the shading), and a few named rows (`neck_row`, `hem_row`, `waist_row`). Three to five blanks ever, by the test in section 3.

**Piece.** Per view: a set of local cells, each carrying an optional slot assignment and an optional role, plus optional alpha operators. Footprints range from 2 cells (buttons) to 40 (a bib). This replaces both "stamp" and the "region tint" primitive I floated in the original document; section 1.2 shows they are one thing. Renaming matters because "stamp" led me to propose a 35-item library of small clusters, which is not what the corpus needs.

The cell operator set is the whole relationship model:

| Symbol | Meaning |
|---|---|
| `b l s d` | set role (base, light, shadow, deep) on an existing opaque cell |
| `=` | keep the blank's role, change slot only |
| `.` | leave the cell untouched |
| `+` | add alpha, must be 4-adjacent to existing alpha |
| `-` | cut alpha |

`=` is new since my original document and is required: vest edge bands and overall bibs change slot while inheriting the blank's shading. Without it every region piece would have to restate the blank's light field, which would make pieces blank-specific and destroy reuse.

**Template.** A family: which blank(s), which slots, which pieces may fill each slot, which slot feeds `SleeveColors`, whether `HideSleeves` is set, and the identity list.

**Palette.** Per slot, four role colours. Phase 1 reads existing stories.

### 5.2 Stages

`RESOLVE` is unchanged in design but **deferred entirely out of Phase 1** (section 7). `COMPOSE` and `COLORIZE` are as you specified. `VALIDATE` and `EXPORT` as specified, with the validator changes in 5.4.

`COMPOSE` in full: copy the blank's role/slot/source arrays for the view; for each piece in `(layer, template slot order)` order, apply its cells; record `source` as `(piece_index, local_x, local_y)`; report any cell written twice.

That report is the entire conflict system. Deterministic order plus visibility. No ledger, no protection levels, no rejected-mutation log.

### 5.3 The palette gap amendment F exposes

Existing stories give **one** hex value for `SecondaryFabric`, `Trim` and `Accent`, but four for the primary fabric. A two-slot garment therefore has a four-step ramp for slot A and a single flat colour for slot B.

Two options, and the evidence picks one. Vanilla's own fixed base layers use 5 to 8 distinct colours per garment, so a *flat* second slot is not what vanilla does; the vest's inner shirt has its own light and shadow.

Decision: **Phase 1 authors an explicit four-step ramp for every slot it uses, as literal hex in five small palette files, seeded from the existing story values by hand.** Five garments need five palettes. This keeps zero colour maths in Phase 1, defers all derivation to the later OKLCH phase, and avoids a mini-blend-engine sneaking in through the adapter. That was a real hole in amendment F as written.

### 5.4 Validators, and which ones are dangerous

Useful, keep as hard gates:

- Sprite and runtime invariants: binary alpha, one connected component per view (two allowed for sleeveless sides), body coverage rows 0-2 opaque, no unsupported row-0 cells, 16x64 atlas, front/right/left/back order, Scale 2, `BodyPosition (0,32)`, `SleeveColors` present and length 3.
- Provenance invariant: every opaque cell has a `source`. This is the anti-polish guard.
- Template identity: every piece the template marks as identity actually painted cells in every view where it declares rows.
- Multi-view consistency: pieces of kind `hem`, `yoke` or `band` paint in all four views; left equals mirror(side) unless an explicit left block exists.
- Colour budget: at most 8 distinct rendered colours across all four views, from section 1.3.

**Identity salience**, replacing the two-cell rule. For each identity piece, compute on the *rendered* colours the maximum contrast between any of its cells and the 4-neighbourhood outside the piece, and the piece's cell count. Require `max_contrast >= T1` or `(cell_count >= 4 and max_contrast >= T2)`. Calibrate T1 and T2 from the five vanilla reconstructions rather than inventing them, then freeze. This admits both vanilla's 1-cell high-contrast button and its 10-cell moderate-contrast sailor collar, and rejects the 5-luminance-unit collar that only the item name makes legible.

Dangerous, and my original document proposed one of them:

- **The 8x8 majority downsample gate.** The engine never downsamples our art; at Scale 2 every 16x16 cell is drawn as a 2x2 screen block. The downsample is a *proxy* for "big enough to read", and a hard gate on a proxy is exactly how a system starts optimising a metric instead of art. Demote to a reported diagnostic printed on the preview sheet. Not a gate.
- **Diversity metrics as a gate.** Deferred with the resolver; when it lands, it should reject only near-duplicates, never push items apart.
- **Any metric on "detail count" or "identity cell count".** The old `identityDetailNotIncreased` check in `tools/generate_v4_vanilla_plus_proof.py` is a measure of process, not quality.

Human review on the Farmer sheet stays authoritative, and Phase 1 must actually close it rather than write `PENDING`.

### 5.5 The invariant that prevents relapse

Every opaque output cell traces to the blank or to a piece. Therefore no stage may invent a pixel from geometry. Enforce with one test asserting full source coverage, and one code rule: the `compose` module contains no function that reads neighbouring cells to decide a role. If a future contributor wants a polish pass, they must break a test that says what the architecture is for.

---

## 6. Is the reconstruction benchmark fair?

Mostly, with four corrections.

1. **Do not require matching vanilla's weaknesses.** Collared Shirt [248] has a collar at 5 luminance units of separation. Matching it exactly would be reproducing an unreadable feature. The gate should be salience **greater than or equal to** vanilla's, not equal.
2. **Vanilla is 8x8, we are 16x16.** Define the comparison once: alpha and slot compared after 2x2 majority reduction, identity compared by salience ranking, colour not compared at all. We are not copying colours.
3. **Overalls are a special case.** Vanilla fakes overalls entirely on the shirt layer; real overalls continue onto the legs. Phase 1 should fake it the same way and record the limitation, not attempt a lower-body solution.
4. **Reconstructions are internal fixtures.** They intentionally imitate specific vanilla items. Keep them out of any distributed pack and out of `test-packs/`; they belong in a `bench/` directory used only for regression.

One addition worth more than the five reconstructions combined: **the resolution experiment**. Nothing in this repository has ever established that 16x16 at Scale 2 beats vanilla's 8x8 at Scale 4 in front of a human. Community Fashion Sense packs I sampled ship 8x8 tiles. The extra resolution is the entire premise of "vanilla plus", and it is untested. Phase 1 should export one garment both ways and put them side by side on the Farmer. If 8x8 wins or ties, the project gets simpler and gains native vanilla shirt support for free.

---

## 7. Exact Phase 1 scope

**No RESOLVE stage.** The five GarmentPlans are authored JSON. This is the largest simplification available: it removes seeds, selection, weights and parameter ranges from Phase 1 while proving compose, colorize, validate and export. The plan schema is frozen in Phase 1 so the Phase 2 resolver emits exactly the same structure.

Hand-writing a plan is not hand-painting, because the plan names pieces by id and every pixel comes from the piece library. The reuse gate below is what enforces that.

### Code — new isolated package `rngc/`, target 600 to 800 lines

| Module | Contents |
|---|---|
| `roleimage.py` | `RoleImage` with `role`, `slot`, `source` arrays; copy; iteration |
| `data.py` | loaders and load-time validation for blank, piece, template, palette, plan |
| `compose.py` | apply pieces in `(layer, slot order)`; write source; report double-writes |
| `colorize.py` | `rgb = palette[slot][role]`; derive `SleeveColors` from the template's declared slot |
| `validate.py` | invariants of 5.4 plus the salience report |
| `preview.py` | Farmer sheet in four views, isolated 8x sheet, vanilla side-by-side, downsample diagnostic |
| `export_fs.py` | 16x64 atlas, `shirt.json`, `manifest.json`, `preset_outfits.json` |
| `cli.py` | `build <plan>`, `bench`, `preview <plan>` |

Reused unchanged: `png_utils.py` (moved in), and `_farmer_composite` from `tools/generate_controlled_grammar_hd_adapter_repair.py:68-85` (moved into `preview.py`).

### Data

- **1 blank**: `torso_basic`, front/side/back, hand-shaded once. Justified by section 1.1; all five benchmarks share this silhouette.
- **About 10 pieces**: `neck_crew`, `collar_shirt_folded`, `placket_buttons`, `button_accent`, `collar_sailor` (with back flap), `tie_sailor`, `panel_vest` (or its inverse `bands_inner_shirt`), `bib_overalls`, `straps_overalls`, `hem_plain`.
- **5 templates**: TEE, COLLARED_SHIRT, VEST, SAILOR, OVERALLS.
- **5 plans** and **5 palettes**, hex, authored per 5.3.

### Explicitly NOT in Phase 1

Resolver, seeds, RNG, diversity, rarity, catalog, OKLCH or any colour maths, pattern stage, additional blanks, fit variants, custom Sleeves, dye `ColorMaskLayers`, lower body, anchor system beyond named rows, incompatibility graph, left-override usage, a 35-piece library, and any migration of the legacy packages beyond moving them to `legacy/`.

---

## 8. Phase 1 acceptance gates

Numbered so failure is unambiguous.

1. **Reconstruction.** All five garments compose, validate and export with zero hand edits to output pixels.
2. **Reuse.** Total pieces at most 12; blanks exactly 1; at least 3 pieces used by 2 or more of the five templates. Any piece used by exactly one template is listed in the report for review. This is the gate that distinguishes an architecture from five hand-made garments.
3. **Cross-product.** At least 3 combinations that nobody authored as a benchmark compose and validate, for example sailor collar on the vest partition, or overall bib with the collared placket. These need not be beautiful; they must be structurally valid and traceable.
4. **Provenance.** Every opaque cell in all 4 views of all 5 garments resolves to a piece or the blank. Zero unattributed cells.
5. **Salience calibration.** Thresholds T1 and T2 derived from the five reconstructions, recorded, and frozen with the reconstructions as regression fixtures.
6. **Human A/B, closed not pending.** Farmer sheets for all five beside their vanilla counterparts; a reviewer names each garment without labels. Recorded as APPROVED or REJECTED, never PENDING.
7. **Resolution experiment.** One garment exported at 16x16/Scale 2 and 8x8/Scale 4; human picks; result recorded and binding on Phase 2.
8. **In-game load.** The exported pack loads in Stardew with Fashion Sense, at the confirmed anchor, in all four directions, standing and walking.

Gates 2, 3 and 6 are the ones that actually test the architecture. Gate 1 alone could be passed by hand-painting, which is the failure mode this review most wants to prevent.

---

## 9. Answers to the fifteen questions

1. **Does FULL GENERATOR REBUILD remain the recommendation?** Yes, and more strongly. The new evidence shows the target system is smaller than my original estimate: one blank rather than eight, about ten pieces rather than thirty-five, and no resolver in the first proof.

2. **Is resolve → compose → colorize still the right core?** Yes, unchanged. It is the only structure among those considered in which a bad pixel has exactly one author.

3. **What is unnecessary?** The three-mode direction policy; required-parent and incompatibility graphs; the pattern stage as a distinct primitive; a separate region-tint primitive; the resolver in Phase 1; OKLCH in Phase 1; my own two-cell rule; my own 8x8 downsample gate; the eight-blank library.

4. **What is still missing?** `SleeveColors` slot selection and `HideSleeves` as template fields, which carry real identity for vests and tanks. The `=` operator for slot-only changes. The palette gap in 5.3. The resolution experiment. A stated rule that reconstruction fixtures are never shipped. A written invariant forbidding computed pixels.

5. **Where could patch debt accumulate again?** Four places, in order of likelihood. First, a "just this once" refinement pass added to `compose`; the provenance invariant is the guard. Second, per-family branches in the validator, exactly as `compiler_validation.py:102-136` grew; the guard is that all family knowledge lives in template data. Third, per-blank piece variants, if pieces stop transferring between blanks; the guard is the reuse gate and keeping blanks few. Fourth, the exporter growing per-pack special cases, as the current 22 packagers did; the guard is one exporter with the contract in one module.

6. **Could authored pieces become a combinatorial mess?** Only if pieces become blank-specific or template-specific. Two guards: the `=` operator so pieces inherit blank shading rather than restating it, and gate 2 flagging any single-use piece. The library grows linearly with garment vocabulary, not multiplicatively, as long as those hold. If a piece needs a different version per blank, that is the signal that the blank should not exist.

7. **Is blank + piece sufficient for the nine listed garments?** Yes for all nine. Measured against vanilla exemplars, silhouette cells differing from the plain tee across front, side and back:

   | Garment | Exemplars | Cells differing |
   |---|---|---|
   | Overalls | 0, 216 | 2, 2 |
   | Vest | 278, 20 / 167 | 2, 2 / **9** |
   | Cardigan | 218 | 3 |
   | Blazer | 183, 10 | 0, 2 |
   | Bomber | 155 | 2 |
   | Work jacket | 163, 29 | 2, 4 |
   | Sailor | 19, 259 | 2, 2 |
   | Polo | 198 | 2 |
   | Blouse | 35 / 2 | 2 / **15** |

   Seven of nine sit on the shared torso outright. The two exceptions are the two cases my amendment-B counter-proposal already predicts: Gray Vest [167] is the sleeveless one, so its coverage differs where native arms take over, and Mint Blouse [2] has a genuinely recut neckline and shoulder. Coverage difference and silhouette difference are criteria 1 and 3 in section 3; family identity is not a criterion, and the table shows why.

   Cardigan, blazer and bomber need an open front with a visible inner layer, which is a centre-band region partition, plus for the cardigan the `torso_open_front` blank because its hanging edges change the interior light field. Blazer lapels are a region with role modulation. Bomber ribbing at the waist is a region; bomber ribbing at the cuffs is not shirt geometry at all.

8. **Which garments expose the biggest weakness?** Two classes, neither solvable by this architecture and both worth stating plainly. First, garments whose identity lives in the sleeves: rolled work sleeves, bomber cuffs, contrast raglan. The shirt layer has no sleeve pixels, so these are deferred to a custom Sleeves companion or simply not offered. Second, garments distinguished only by fabric texture at this scale: flannel, chambray, plaid and twill work shirts are the same 60 cells and the same 6 colours. No architecture fixes that. The consequence is a product risk rather than an art risk: **perceived duplication**. A generator that emits forty work shirts differing only in hue will read as forty copies. That is the strongest argument for the diversity gate in a later phase, and it is a catalog problem, not a compositor problem.

9. **Should some pieces be templates or regional overlays?** Regional overlays, and that is now the definition of a piece rather than a third primitive. Nothing should be a full garment template; that is hand-painting with extra steps. Vests 278 and 281 being byte-identical is the proof that garment-level authoring is the wrong unit.

10. **Is the directional model robust enough?** Yes, once simplified to "author three views, mirror the fourth, allow an optional explicit left". Section 1.5 shows the benchmarks need the override for 0 to 3 pixels and that the differences are unsystematic. The genuine directional risk is not left versus right; it is that side views compress differently per blank, which is why side rows are authored per piece and why keeping the blank count low keeps that cost low.

11. **What is the simplest possible composition and conflict system?** Sort pieces by `(layer, template slot order)`, apply cells in order, last writer wins, record source, report double-writes. Five rules, no ledger, no protection levels, no rejection log. The old ownership ledger existed to defend against stages that no longer exist.

12. **Which validators are useful and which risk optimising metrics?** Useful: runtime invariants, provenance coverage, template identity presence, multi-view consistency, colour budget, salience. Dangerous: the 8x8 downsample gate (demote to diagnostic), diversity as a hard gate, and any count of "details" or "identity cells". The general rule is that a validator may assert a garment is *valid*, never that it is *good*.

13. **Is the reconstruction benchmark fair?** Fair with the four corrections in section 6: greater-than-or-equal salience rather than equality, a defined cross-resolution comparison, overalls acknowledged as a vanilla fake, and fixtures excluded from shipped packs.

14. **What exactly should Phase 1 contain?** Section 7.

15. **What should Phase 1 explicitly not contain?** Section 7, final list.

---

## 10. Remaining risks

| Risk | Severity | Status after this review |
|---|---|---|
| Perceived duplication across a large batch | High | Unresolved by design; belongs to the Phase 3 diversity gate and to naming and palette variety, not to the compositor |
| 16x16 at Scale 2 is not actually better than 8x8 | Medium | Untested for the life of the project; Phase 1 gate 7 settles it |
| Authoring effort for blank shading in three views | Medium | Bounded by keeping blanks to 3 to 5; each is authored once |
| Pieces drift toward per-template bespoke assets | Medium | Gate 2 makes it visible immediately |
| A future contributor adds a refinement pass | Medium | Provenance invariant plus an explicit written rule |
| Sleeve-defined garments cannot be represented | Medium | Accepted scope limit; revisit only with custom Sleeves |
| Salience thresholds calibrated on five samples | Low | Widen the calibration set in Phase 2 before the resolver ships |
| Overalls semantics on the shirt layer only | Low | Matches vanilla; documented limitation |
| Fashion Sense contract drift | Low | One module, pinned source, one in-game check per phase |

---

## 11. Final recommendation

**FULL GENERATOR REBUILD**, confirmed.

The revised V5 candidate is sound and I would build it, with these binding changes:

- One blank in Phase 1, three to five ever, justified by coverage or light field rather than by garment family. Amendment B rejected as framed.
- "Stamp" renamed to **piece** and re-scoped to region size, absorbing the pattern and region-tint ideas into one primitive.
- The `=` operator added so pieces inherit blank shading.
- Direction policy reduced to mirror-by-default with an optional explicit left. Amendment C's three modes rejected.
- No incompatibility graph; templates express compatibility by listing.
- No resolver, no colour maths, no patterns in Phase 1.
- The two-cell rule and the 8x8 downsample gate, both from my own original document, withdrawn and replaced by contrast-based salience plus a diagnostic.
- Provenance always on, and elevated into the invariant that structurally forbids a return of the polish stack.

The strongest reason to proceed is that the measurements make the first proof genuinely small: one hand-shaded torso, about ten authored pieces, five plans, and roughly seven hundred lines of code, against 38,000 lines today. If that cannot produce five recognisable garments in front of a human reviewer, the failure will be visible in weeks and cheap to act on, which is more than the current system has offered in six versions.
