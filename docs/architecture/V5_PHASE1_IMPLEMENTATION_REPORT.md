# V5 Phase 1 Implementation Report

Status: **implementation complete; HUMAN REVIEW AWAITING; IN-GAME NOT TESTED.**
Author: Claude (Opus 5), 2026-09-03.
Binding architecture: `docs/architecture/CLAUDE_V5_ADVERSARIAL_REVIEW.md` (which supersedes `CLAUDE_INDEPENDENT_ARCHITECTURE.md` where they differ).
Scope: Phase 1 only. No resolver, no RNG, no OKLCH, no patterns, no custom sleeves, no legacy migration.

---

## 1. Headline

The five benchmark garment types reconstruct through the new architecture from **one blank and ten authored pieces**, with zero manual edits to output pixels. Four unauthored cross-product combinations also compose and validate. All ten architecture tests pass, including the no-polish invariant.

| Gate | Result |
|---|---|
| 1. Reconstruction | 5/5 compose, validate, preview, export |
| 2. Reuse | 1 blank, 10 pieces, 5 reused across 2+ benchmarks (need 3) |
| 3. Cross-product | 4/4 unauthored combinations PASS |
| 4. Provenance | 8,532 opaque cells, 0 unattributed |
| 5. Salience | vanilla 14/15, V5 43/53, one open calibration question |
| 6. Human review | **AWAITING** |
| 7. Resolution experiment | sheet produced, **AWAITING HUMAN DECISION** |
| 8. In-game | pack built, **NOT TESTED** |

---

## 2. Files created

### Code — `rngc/`, 1,166 lines core + 106 lines of tests

| File | Lines | Role |
|---|---:|---|
| `rngc/__init__.py` | 15 | package docstring carrying the no-polish invariant |
| `rngc/pngio.py` | 149 | dependency-free PNG read/write, nearest scale, blit, 5x7 text. Moved from `generator/png_utils.py` |
| `rngc/roleimage.py` | 67 | the single intermediate representation |
| `rngc/data.py` | 236 | loaders and load-time validation for blank, piece, template, palette, plan |
| `rngc/compose.py` | 126 | the compositor |
| `rngc/colorize.py` | 38 | `rgb = palette[slot][role]`, once |
| `rngc/validate.py` | 130 | hard invariants plus the salience report |
| `rngc/preview.py` | 122 | Farmer compositor (moved out of the legacy tool) and contact sheets |
| `rngc/export_fs.py` | 70 | the one Fashion Sense exporter |
| `rngc/bench.py` | 91 | installed-vanilla reader, vanilla salience, 2x2 diagnostic reduction |
| `rngc/cli.py` | 122 | `build-all`, `build <plan>` |
| `rngc/tests/test_phase1.py` | 106 | architecture tests |

### Authored data — `rngc/data/`, 24 JSON files, 168 KB

`blanks/` 1, `pieces/` 10, `templates/` 5, `palettes/` 7, `plans/bench/` 5, `plans/xprod/` 4, `runtime/` 1.

### Nothing was changed outside `rngc/` and `docs/`

The legacy `generator/`, `tools/` and `test-packs/` trees are untouched. `rngc` imports nothing from them; a test asserts this.

---

## 3. Architecture as actually implemented

```
authored data (blank, pieces, template, palette, plan)
        │
        ▼   compose.py            one pass, pieces sorted by (layer, plan index), last writer wins
   RoleImage x4   role[16][16] · slot[16][16] · src[16][16] · src_x · src_y
        │
        ▼   colorize.py           rgb = palette[slot][role]   (exactly once, no blending)
   RGBA frames x4
        │
        ├──▶ validate.py          12 generic checks + salience report
        ├──▶ preview.py           Farmer composites, vanilla comparison, 8x8 diagnostic
        └──▶ export_fs.py         16x64 atlas, shirt.json, presets, manifest
```

There is no resolver. The five benchmark plans and four cross-product plans are authored JSON. The plan schema is frozen so a Phase 2 resolver can emit it unchanged.

### The no-polish invariant

Documented in `rngc/__init__.py` and `rngc/compose.py`, and enforced by two tests:

- `test_every_opaque_cell_has_provenance` — every opaque cell in every direction of every garment resolves to the blank or a named piece.
- `test_compositor_has_no_neighbour_logic` — `compose.py` executable code (docstrings and comments stripped by AST line range) contains none of `neighbor`, `neighbour`, `luminance`, `exterior`, `contour`, `polish`, `smooth`, `outline`, `[y±1]`, `x±1`; and neither `compose.py` nor `colorize.py` indexes a cell offset from the one being written.

The compositor cannot read a neighbouring cell, so it cannot shade, smooth, outline or reinforce anything. Art is fixed only in authored data.

### Cell operators

`b` `l` `s` `d` set role; `=` keeps the blank's role and changes slot only; `.` untouched; `+` adds alpha; `-` cuts alpha. The operator set is the entire relationship model. There is no ownership ledger, no protection level and no mutation-rejection machinery.

`=` earns its place: `bands_inner_shirt`, `bib_overalls` and `straps_overalls` are region partitions that inherit the blank's hand-authored shading instead of restating it. Without `=` those pieces would be blank-specific and reuse would collapse.

### Directions

Each blank and piece authors `front`, `side`, `back`. Left is `mirror(side)` unless explicit left data exists. **No explicit-left override is used in Phase 1**, and the validator asserts left is a true mirror for every garment. No mode enum exists.

---

## 4. Blank

**`torso_basic`** — the only blank, as the adversarial review requires.

Derived from the installed vanilla plain tee (sprite 1) silhouette at 2x, hand-shaded once: light from screen upper-left, shadow on the right and lower body, deep only at silhouette turns and hem corners. Named rows `neck_row=1`, `waist_row=11`, `hem_row=15`.

No second blank was needed. All five benchmarks and all four cross-products sit on it, which matches the measurement in the adversarial review that eleven vanilla garments share this silhouette to within two cells.

---

## 5. Pieces (10)

| id | kind | layer | slot | identity | note |
|---|---|---|---|---|---|
| `neck_crew` | neck | OVER | inherit | yes | deep binding ring + shadow row |
| `collar_shirt_folded` | collar | OVER | inherit | yes | two light leaves; slot overridable per plan |
| `placket_buttons` | opening | OVER | inherit | no | centre shadow column, front only |
| `button_accent` | detail | DETAIL | accent | yes | three single high-contrast cells |
| `collar_sailor` | collar | OVER | trim | yes | front leaves, side wrap, square rear flap |
| `tie_sailor` | detail | DETAIL | accent | yes | knot and two hanging ends |
| `bands_inner_shirt` | layer | UNDER | secondary | yes | vest partition, uses `=` |
| `bib_overalls` | layer | UNDER | secondary | yes | bib region, uses `=` |
| `straps_overalls` | layer | OVER | secondary | yes | two shoulder straps, uses `=` |
| `hem_plain` | hem | OVER | inherit | no | wrap piece, anchored to `hem_row` |

### Reuse matrix (X = used by that benchmark)

| piece | collared | overalls | sailor | tee | vest | bench uses | xprod uses |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `hem_plain` | X | X | X | X | X | 5 | 4 |
| `button_accent` | X | . | . | . | X | 2 | 2 |
| `collar_shirt_folded` | X | . | . | . | X | 2 | 1 |
| `neck_crew` | . | X | . | X | . | 2 | 1 |
| `placket_buttons` | X | . | . | . | X | 2 | 2 |
| `bands_inner_shirt` | . | . | . | . | X | 1 | 2 |
| `bib_overalls` | . | X | . | . | . | 1 | 1 |
| `straps_overalls` | . | X | . | . | . | 1 | 1 |
| `collar_sailor` | . | . | X | . | . | 1 | 2 |
| `tie_sailor` | . | . | X | . | . | 1 | 1 |

**Gate 2: five pieces are used by two or more benchmarks** (`hem_plain`, `button_accent`, `collar_shirt_folded`, `neck_crew`, `placket_buttons`), against a requirement of three. Counting cross-products as well, **every one of the ten pieces is used by two or more plans.**

### Single-use pieces, and why

Four pieces appear in exactly one benchmark. None is a hidden handcrafted shirt; each is used again by a cross-product, which is the test that they are genuinely parameterless and portable.

- `collar_sailor` and `tie_sailor` — sailor identity. Reused by `xprod_sailor_vest` and `xprod_sailor_buttons` without modification.
- `bib_overalls` and `straps_overalls` — overalls identity. Reused by `xprod_overalls_collared`.
- `bands_inner_shirt` is single-use among benchmarks but appears in two cross-products.

No piece required a variant, an anchor tweak or a per-garment special case to be reused.

---

## 6. Five benchmark results

All five: **PASS**, zero manual output-pixel edits.

| plan | vanilla counterpart | colours | pieces | validator |
|---|---|---:|---|---|
| `bench_tee` | 1 Shirt | 4 | neck_crew, hem_plain | PASS |
| `bench_collared` | 248 Collared Shirt | 5 | collar_shirt_folded, placket_buttons, button_accent, hem_plain | PASS |
| `bench_vest` | 278 Blue Buttoned Vest | 9 | bands_inner_shirt, collar_shirt_folded (slot→secondary), placket_buttons, button_accent, hem_plain | PASS |
| `bench_sailor` | 259 Sailor Shirt | 8 | collar_sailor, tie_sailor, hem_plain | PASS |
| `bench_overalls` | 216 Plain Overalls | 8 | neck_crew, bib_overalls, straps_overalls, hem_plain | PASS |

`bench_vest` demonstrates the plan-level slot override: the shirt collar piece is reused in the `secondary` slot so it reads as the inner shirt's collar under the vest.

---

## 7. Cross-product results (gate 3)

Four combinations that were never authored as benchmarks. **All four PASS structurally with full provenance.** No piece was created or modified to make them pass.

| plan | combination | colours | result |
|---|---|---:|---|
| `xprod_sailor_vest` | sailor collar + tie on the vest partition | 12 | PASS |
| `xprod_overalls_collared` | overall bib + straps over a collared, buttoned shirt | 9 | PASS |
| `xprod_vest_crew` | vest partition with the tee's crew neck | 8 | PASS |
| `xprod_sailor_buttons` | sailor collar over a buttoned placket | 7 | PASS |

`xprod_sailor_vest` needed a raised colour budget of 12 because it combines three full ramps plus an accent. That is a real constraint discovered by the test, not a workaround: **a Phase 2 resolver must treat the colour budget as a combination constraint, not a per-garment constant.** It is recorded as a limitation rather than papered over.

---

## 8. Provenance results (gate 4)

Across nine garments and four directions each, **8,532 opaque cells, zero unattributed.** Every cell traces to `blank` or to a named piece with its local authoring coordinate.

Worked examples from `output/v5-phase1/garments/bench_sailor/roleimage.json`:

```
back  (3,1)  -> collar_sailor/local(1,1)
front (8,5)  -> tie_sailor/local(2,0)
front (0,7)  -> blank/local(0,7)
left  (13,2) -> collar_sailor/local(0,1)
```

The left example is the mirrored side view: the local coordinate is reported as authored, so a bad pixel on the left is traced back to the same authored cell as its right-side twin.

---

## 9. Salience measurements (gate 5)

Full data: `output/v5-phase1/salience-calibration.json`.

Method: for vanilla, the identity region is the minority colour layer (dye versus fixed) measured against the majority layer. For V5 it is the cells owned by an identity piece measured against adjacent cells owned by anything else. Contrast is the maximum absolute Rec.709 luminance difference across the region boundary, on a 0-255 scale.

### Vanilla evidence

| garment | view | cells (8x8) | contrast |
|---|---|---:|---:|
| 216 Plain Overalls | back | 8 | 25.4 |
| 278 Blue Buttoned Vest | back | 10 | 33.4 |
| 278 Blue Buttoned Vest | front | 10 | 33.7 |
| 278 Blue Buttoned Vest | right/left | 5 | 36.4 |
| 216 Plain Overalls | front | 24 | 129.7 |
| 216 Plain Overalls | right/left | 21 | 153.0 |
| 248 Collared Shirt | front/right/left | 2 | 181.8 |
| 259 Sailor Shirt | front | 10 | 187.4 |
| 259 Sailor Shirt | back | 30 | 218.9 |

Green Vest [20] and Vintage Polo [198] are single-layer garments whose identity is role modulation inside one fabric, so this measure returns zero for them and they are excluded.

### Proposed thresholds — candidates, not gates

- **T1** (high-contrast small feature): contrast ≥ 150, cells ≥ 2 at 8x8 (≥ 4 at 16x16). Evidence: the Collared Shirt reads from two cells at 181.8.
- **T2** (low-contrast region): cells ≥ 5 at 8x8 (≥ 20 at 16x16) and contrast ≥ 30. Evidence: the vest side view is the weakest passing case at 5 cells and 36.4.
- Rule: pass if T1, or if T2.

Against vanilla this gives **14/15**. The single failure is the Plain Overalls back at 8 cells and 25.4 contrast, a view that genuinely reads weakly in game, so failing it is the intended behaviour.

**These thresholds are not wired into the validator.** `validate.py` reports cell count and contrast per identity piece and never gates on them, exactly as instructed.

### V5 measurements and one open question

V5 scores **43/53** against the same rule. The failures cluster on one piece and one cross-product:

| plan | piece | cells (16x16) | contrast | note |
|---|---|---:|---:|---|
| `bench_tee` | `neck_crew` | 12 | 95.6 | band identity, see below |
| `xprod_vest_crew` | `neck_crew` | 12 | 53.7 | same piece, lower-contrast palette |
| `xprod_overalls_collared` | `collar_shirt_folded` | 14 | 46.5 | blue collar on blue shirt in a cross-product |

**One authored fix was made during Phase 1 and is worth recording as evidence the loop works.** `neck_crew` was first authored as a single-cell binding ring and measured 8 cells at 53.2 contrast. A 1-cell binding at 16x16 is proportionally half of vanilla's 1-cell binding at 8x8, so the piece was rewritten as a two-row deep binding, now 12 cells at 95.6. **The piece data changed; the compositor, the validator and the metric did not.**

It still fails T2 on area. This is an open calibration question, not a defect I have resolved:

> T1 and T2 were calibrated from region identities (vest bands, overall bibs) and accent identities (buttons). A **band** identity such as a neck binding falls between them. A candidate T3 of "cells ≥ 8 at 16x16 and contrast ≥ 60" would admit it, but I have **not adopted it**, because vanilla's plain tee has no separable identity layer at all and therefore offers no evidence for how salient a crew binding must be. Adopting T3 now would mean widening the rule until my own output passes, which is precisely the metric-optimisation failure the adversarial review warned against. This awaits your judgement on the tee sheet.

No visual success is claimed from these numbers.

---

## 10. Validator results

Twelve generic checks run per garment, with **no per-family Python branches**; every family-specific requirement lives in template or plan data.

`dimensions`, `binary_alpha`, `connected_components`, `required_coverage`, `provenance_complete`, `identity_pieces_painted`, `left_is_mirror_of_side`, `wrap_pieces_all_directions`, `colour_budget`, `sleeve_slot_in_palette`, plus `double_writes` and `skipped_cells` as reports.

All nine garments PASS. Connected components are 1 per direction everywhere. `skipped_cells` is empty for every garment, meaning no authored piece paints outside the blank's alpha.

### Double writes (reported, not errors)

| plan | count | overlaps |
|---|---:|---|
| `bench_overalls` | 48 | `hem_plain` and `neck_crew` over `bib_overalls` |
| `xprod_overalls_collared` | 87 | bib under collar, placket, buttons, hem; straps over collar |
| `xprod_sailor_buttons` | 1 | `placket_buttons` over `collar_sailor` |

These are intended layer stacking: an `UNDER` region piece is deliberately overpainted by `OVER` and `DETAIL` pieces. The report exists so an author can see when a bow eats a collar; it is not a failure condition. The two heavy counts are both overalls, where the bib legitimately covers most of the torso before the hem and neck are drawn on top.

---

## 11. Preview and comparison sheets

All under `output/v5-phase1/sheets/`:

| sheet | contents |
|---|---|
| `PHASE1_BENCH_FIVE_VS_VANILLA.png` | **primary review sheet.** Five benchmarks on the Farmer beside their vanilla counterparts, all four directions |
| `PHASE1_GARMENT_bench_*.png` (5) | per garment: 16x16 at 8x, Farmer composite, vanilla on Farmer, vanilla at 16x, 8x8 diagnostic |
| `PHASE1_GARMENT_xprod_*.png` (4) | same layout for the cross-products |
| `PHASE1_CROSS_PRODUCTS.png` | four unauthored combinations on the Farmer |
| `PHASE1_RESOLUTION_EXPERIMENT.png` | **decision sheet**, see below |

The Farmer compositor was moved into `rngc/preview.py` from `tools/generate_controlled_grammar_hd_adapter_repair.py`; the offsets are unchanged (Farmer at 4x, shirt at 2x for 16x16 or 4x for 8x8, so both occupy the same 32x32 display box).

The 8x8 reduction appears only as a labelled diagnostic row and in the resolution sheet. It is **not** a validation gate.

---

## 12. Resolution experiment (gate 7)

`output/v5-phase1/sheets/PHASE1_RESOLUTION_EXPERIMENT.png`

Two garments (`bench_sailor`, `bench_collared`) in three columns at equal display size on the Farmer:

- **A** — V5 16x16 logical at Scale 2
- **B** — 8x8 logical at Scale 4, produced by 2x2 majority reduction of A
- **C** — the vanilla counterpart, 8x8 at Scale 4

Both A and B are also exported as installable Fashion Sense shirts in the bench pack, so the comparison can be repeated in game rather than only on a contact sheet.

**No winner is declared.** The sheet is labelled `AWAITING HUMAN DECISION`. Your choice is binding for Phase 2.

---

## 13. Fashion Sense test pack (gate 8)

`output/v5-phase1/bench/fs-pack/RNG-Clothing-V5-Phase1-Bench/`

Eleven shirts: five benchmarks, four cross-products, and two 8x8 resolution-experiment variants. Contract values come from `rngc/data/runtime/fs_shirt_contract.json` and are emitted by the single exporter:

```
Scale 2.0 · BodyPosition (0,32) · ShirtSize 16x16 · atlas 16x64 · order front/right/left/back
DisableGrayscale true · HideSleeves false · SleeveColors 3 entries from the template's sleeve slot
```

The 8x8 variants correctly emit `Scale 4.0`, `BodyPosition (0,0)`, `ShirtSize 8x8`, atlas 8x32.

Sleeve slots are template-declared and differ where identity requires it: `bench_vest` and `xprod_vest_crew` feed native sleeves from the **secondary** slot so the arms match the inner shirt rather than the vest.

The pack is under `output/v5-phase1/bench/`, **not** in `test-packs/`, and its README and manifest both mark it INTERNAL and not for distribution, because these fixtures intentionally reconstruct vanilla garment types.

**Runtime status: NOT TESTED.** No runtime claim is made until you load it in Stardew.

---

## 14. Known limitations

1. **Colour budget is a combination constraint.** `xprod_sailor_vest` needs 12 colours; the vanilla-derived default is 8. Phase 2's resolver must budget across the whole combination.
2. **Band-identity salience is uncalibrated.** See section 9. Awaiting your judgement.
3. **The sailor rear flap is a bordered panel, not a filled one.** Vanilla 259's back is a filled white region with a dark centre; mine reads as a light square with an interior ring. Recognisable, but a deliberate authoring difference to note.
4. **Overalls are faked on the shirt layer only**, exactly as vanilla does. Real overalls continue onto the legs; the shirt layer cannot express that.
5. **The vest's upper chest reads broad.** Combining `bands_inner_shirt` with a secondary-slot collar produces a large cream area at the shoulders. Structurally correct, aesthetically for you to judge.
6. **One blank means no fit variation.** By design for Phase 1.
7. **The 2x2 reduction is approximate.** It resolves ties toward non-primary slots and darker roles so identity survives; it is a diagnostic, not a renderer.
8. **`bench.py` reads the installed game.** Without Stardew installed, previews still build but vanilla comparison columns are omitted.

---

## 15. Deviations from the frozen architecture

Three, all minor, none altering the pipeline shape.

1. **A `bench.py` module was added** beyond the suggested module list, to keep installed-game reading and the 2x2 diagnostic out of `preview.py` and `validate.py`. It is read-only and touches no art path.
2. **Ten pieces, but `hem_plain` and `placket_buttons` are not identity pieces.** The suggested list implied all ten carry identity. Marking them non-identity keeps the salience report honest, since a hem is a termination, not an identity cue.
3. **`collar_shirt_folded` is authored more saliently than vanilla 248's collar** (92.5 contrast against vanilla's 5.0 luminance separation). This uses the "greater than or equal to vanilla salience" rule agreed in the adversarial review, section 6, rather than reproducing a feature that only the item name makes legible.

No deviation required a code branch, a per-family rule, or a refinement pass.

---

## 16. Status

| Gate | Status |
|---|---|
| 1. Reconstruction | **PASS** — 5/5, no manual pixel edits |
| 2. Reuse | **PASS** — 1 blank, 10 pieces, 5 reused across benchmarks (need 3) |
| 3. Cross-product | **PASS** — 4/4 (need 3) |
| 4. Provenance | **PASS** — 8,532 cells, 0 unattributed |
| 5. Salience | **REPORTED** — thresholds proposed, one open question, no visual claim |
| 6. Human review | **AWAITING HUMAN REVIEW** |
| 7. Resolution experiment | **AWAITING HUMAN DECISION** |
| 8. In-game | **NOT TESTED** |

Phase 2 has not been started and will not be until gates 6, 7 and 8 are closed by you.

### To review

1. `output/v5-phase1/sheets/PHASE1_BENCH_FIVE_VS_VANILLA.png` — can you name each garment without its label?
2. `output/v5-phase1/sheets/PHASE1_RESOLUTION_EXPERIMENT.png` — A, B or C?
3. Install `output/v5-phase1/bench/fs-pack/RNG-Clothing-V5-Phase1-Bench/` and test the `V5P1` presets.

### Reproduce

```bash
python3 -B -m unittest rngc.tests.test_phase1   # 10 tests
python3 -B -m rngc.cli build-all                # ~7 s, writes output/v5-phase1/
```
