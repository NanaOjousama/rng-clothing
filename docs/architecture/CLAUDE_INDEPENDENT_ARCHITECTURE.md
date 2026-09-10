# Independent Architecture Proposal for the RNG Clothing Generator

Status: proposal only. No implementation code was changed.
Author: Claude (Fable 5.1), 2026-09-02.
Method: read the executable code under `generator/`, `tools/`, `tests/`, `specs/`, the Fashion Sense 7.5.0 source in `FASHION SENSE/`, the installed vanilla `Characters/Farmer/shirts.png` + `Data/Shirts.json`, and the generated output under `output/` and `test-packs/`. Ran the existing V4 tests and one instrumented compile to measure what the pipeline actually does. Architecture documents were used only to locate the live entry point, not as premises.

---

## 0. Summary

The repository contains a working, deterministic, dependency-free Python toolchain that can emit valid Fashion Sense shirt packs at a runtime-confirmed 16x16 / Scale 2 / `BodyPosition (0,32)` contract. That contract, the PNG utilities, the seed derivation, the Farmer preview compositor, the palette role vocabulary, and the vanilla research are real assets.

Everything between "pick a family" and "write shirt.png" is not. The live path (`generator/hybrid_v3/compiler/pixel_grammar_v4.py`) renders an unrelated benchmark garment through four legacy renderers, scrubs it back to a grayscale role field, repaints the body shading three separate times, paints identity from hard-coded coordinate lists, then runs an ownership ledger to stop its own later stages from undoing its earlier ones. Two different seeds for the same family produce byte-identical pixels. Human visual QC is `PENDING` in every artifact and runtime is `NOT TESTED` in every Fashion Sense report except the anchor proof.

Recommendation: **FULL GENERATOR REBUILD** around an authored, role-indexed component atlas plus a three-step compositor (resolve, compose, colorize), generated offline. Keep the utilities, the runtime contract, the palette data, the vanilla analysis tooling, and the micro-shape data as seed content for the atlas. Retire all seventeen versioned engine/renderer packages.

---

## 1. What the current system actually does

### 1.1 Entry point and call graph (live V4 path)

`tools/generate_v4_vanilla_plus_proof.py` is the newest generation entry (mtime 2026-09-02 10:32) and `tests/test_v4_vanilla_plus.py` exercises the same path. It does, per case:

1. `CanonicalGarmentBuilder.build()` in `generator/hybrid_v3/builder.py:40-210`
   loads `specs/hybrid_garment_compiler/v3/*.json`, resolves the family's slot list, and for each slot picks a component id and parameter values with `_choose()` (`builder.py:19-22`) seeded by `SeedBook` (`generator/hybrid_v3/seeding.py`). Every slot in `architecture_definitions.json` has exactly one candidate, so the only seeded decisions are parameter values such as `hem.shape` or `collar.width`.
2. `DirectionalProjector.project()` in `generator/hybrid_v3/projector.py:18-37`
   copies each component's `directionalVisibility` table into four lists. It performs no geometry; it is a dictionary reshuffle.
3. `PixelGrammarCompilerV4.compile()` in `generator/hybrid_v3/compiler/pixel_grammar_v4.py:56-173`, which is where all pixels come from. In order:
   - `CarrierRegistry.select()` (`compiler/carrier_registry.py:21-37`) calls `generate_v5b_benchmark()["recipes"][benchmarkRecipeIndex]` and renders it with `render_fs_v5b()`. The index comes from `specs/hybrid_garment_compiler/v3/carrier_capabilities.json`. For `POLO_SHIRT` that is benchmark recipe 1, the "Signalwork Rolled Shirt" (`cyber_tech`, Uncommon, `structured_shirt`) from `generator/v5b/engine.py:137`. For `SAILOR_TOP` it is recipe 10, the "Rose Circuit Sailor Blouse". The garment the user asked for is therefore always painted on top of a rendering of a different garment.
   - `render_fs_v5b` (`generator/renderers/fashionsense/upper_v5b.py:314-349`) calls `render_fs_v4` (`article_v4.py:144-175`), which calls `render_fs_v3` (`surface_v3.py:302-326`), which calls `render_fs_hd_v2` (`hd_garment_v2.py:660-689`). Each layer copies the previous layer's frames and mutates cells.
   - `_reset_to_proven_hd_planes()` (`generator/controlled_test/reference_guided.py:87-103`) then overwrites every opaque cell back to the HD V2 role field, discarding what V3/V4/V5B painted except alpha changes.
   - `_remove_closed_opening_from_hd_regions()` (`generator/controlled_test/hd_adapter.py:168-198`) erases the BUTTON_SHIRT placket that the carrier always carries.
   - `polish_upper_frames()` (`renderers/fashionsense/art_polish_v5e.py:46-103`) repaints exterior cells by row/column heuristics.
   - `normalize_body_form()` (`compiler/art_grammar_v4.py:22-86`) repaints every opaque cell again by row/column heuristics.
   - `compile_components()` (`compiler/component_compilers.py:409-429`) runs one handler per component type. The handlers are hard-coded coordinate lists with three competing branches per collar type: inline coordinates (`_collar`, lines 171-229), the V4.2 shape library (lines 158-170), and the vanilla-plus shape library (lines 124-137), selected by `shape_profile` string comparison.
   - `merge_legacy_polish_non_destructive()` (`compiler/non_destructive_polish_v4.py:12-51`) runs `polish_upper_frames` a second time on a clone and merges only cells the `OwnershipLedgerV4` (`compiler/ownership_v4.py`) permits.
   - `normalize_vanilla_plus_body_form()` (`art_grammar_v4.py:89-137`) repaints body shading a third time, skipping protected cells.
   - `soften_shared_rear_neck()` (`art_polish_v5e.py:106-184`) repairs a rear crease that the carrier inherited from the BUTTON_SHIRT template.
   - `_resolve()` (`reference_guided.py:336-365`) decodes each cell's grayscale value back to a role name via `MASK_ROLE_BY_VALUE` (`hd_adapter.py:33-40`), with a nearest-value fallback at line 348-352, then picks RGB from `_palette_ramps()` (`hd_adapter.py:202-235`).
   - `validate_compiled()` (`compiler/compiler_validation.py:59-197`).

The compiler's own `stage_trace` reports 14 stages. Measured: 1.4 s per garment, 804 ownership-ledger cell claims and 4 rejected mutations for one polo, 8 s for the four-case test suite.

### 1.2 The in-flight pixel representation

A cell is represented as up to six parallel facts spread across structures: an RGBA "mask frame" whose gray level encodes the shade role (`hd_garment_grammar_v2.json` `outerMaskRamp`, 48/72/104/136/184/224/244), an RGBA "default frame" (`_composite_default`, `hd_garment_v2.py:640-650`), a `fabrics[direction][(x,y)]` slot name, `SemanticRegionLedger.systems`, `component_cells`, and a `CellOwnership` record. Role identity survives only as a gray integer and is recovered by lookup. That is why `_resolve` needs a nearest-value fallback and why `_old_fixed_role()` (`hd_adapter.py:238-248`) has to guess a role from RGB distance.

### 1.3 Directions

`hd_garment_v2.build_hd_regions()` (lines 158-167) decodes ASCII 16x16 region templates for front, back and one side, and builds left as `_mirror(right)` (lines 149-154). Light is then recomputed by screen position rather than mirrored (`_apply_large_light_and_shadow`, lines 306-325). Every later stage applies its own per-direction heuristics (`art_grammar_v4.py:70-76`, `component_compilers.py` per-direction literal lists, `vanilla_plus_micro_shapes.json` per-direction anchors). There is no single object that says "this collar, seen from four sides".

### 1.4 Palette

`specs/palettes/palette_stories.json` provides seven hex roles per story. `MATERIAL_RAMP_POLICY` (`hd_adapter.py:45-60`) holds three hand-tuned blend fractions per material; ramps are linear RGB blends between story roles (`_palette_ramps`). `SleeveColors` are three ramp steps (`pixel_grammar_v4.py:116-118`).

### 1.5 Export

There is no shared exporter. 22 tools define their own `_package`/`_shirt_json`; 48 files write a `ContentPackFor` manifest. All 43 generated Fashion Sense `shirt.json` files set `DisableGrayscale: true` and none declare `ColorMasks`, so no generated garment is dyeable in game. The atlas is 16x64 with direction order front/right/left/back (`_stack`, `hd_garment_v2.py:653-658`), Scale 2, `BodyPosition (0,32)` (`tools/generate_hybrid_v3_phase2.py:122`).

### 1.6 Validation

`compiler_validation.py` mixes three kinds of check: generic sprite invariants (connectivity, row-0 support, binary alpha, coverage envelope, dark-band scan; lines 69-88), family-specific hard-coded thresholds (`POLO_SHIRT` collar >= 6 cells, `SAILOR_TOP` rear >= 12; lines 113-130), and process contracts (expected shape-variant ids, minimum topology ADD/REMOVE counts; lines 132-172). `tools/generate_v4_vanilla_plus_proof.py:93-119` and `:42-47` duplicate these expectations as literal cell counts and literal topology operations per family. `humanVisualQC` is written as `PENDING` in every output (`compiler_validation.py:195`).

### 1.7 Farmer previews

`tools/generate_controlled_grammar_hd_adapter_repair.py:80-85` (`_farmer_composite`) reads the installed `farmer_base.png` and `hairstyles.png`, draws the body at 4x and the shirt at 2x at `(16, 56 + featureY*4)`. It is idle-frame only and is imported by other tools from this tool module (`generate_v4_vanilla_plus_proof.py:20`).

### 1.8 Measured behaviour

| Measurement | Value |
|---|---|
| Generator package size | 20,263 lines across 17 versioned packages (v1, v2, v3, v4, v45, v46, v46b, v5a, v5b, v5c2, v5d, v5e, v6, hybrid_v3, controlled_test, autonomous_recovery, hoodie_layers) |
| Tool scripts | 38 `generate_*`, 32 `validate_*`, 18,022 lines |
| Data files | 76 JSON documents under `generator/data` and `specs` |
| Fashion Sense test packs | 26 |
| Pixels differing between root seeds 420201 and 999, same family/intent/fit/palette (POLO_SHIRT) | 0 |
| Human visual QC status in any artifact | PENDING |
| Runtime status in Fashion Sense reports | NOT TESTED, except the HD jacket anchor (`reports/HD_JACKET_POC.md:7`) |

The zero-pixel seed result is the most important number in this document. The seed changed `hem.shape` from `straight` to `soft_curve`; `_hem()` (`component_compilers.py:301-328`) never reads `shape`. The "procedural" generator does not currently generate variety at the pixel level; variety comes only from switching family, fit profile, or palette story by hand in `CASES`.

---

## 2. Main architectural problems

1. **The garment is painted over a different garment.** `carrier_registry.py:33-36` renders a fixed benchmark recipe unrelated to the requested design, and the first two compiler stages exist only to erase it. Every "hidden stage conflict" in the failure audits traces to this: `docs/quality/COASTAL_POLO_MICROFIX_FAILURE_AUDIT.md` shows `polish_upper_frames` removing an intended row-0 rear collar change. The ownership ledger, the clone/merge polish wrapper, the topology API and the "frozen backend" SHA pins in `compiler/stage_trace.py:9-18` are all defences against the pipeline's own stages.

2. **Body shading is computed four times by four different heuristics** (`hd_garment_v2.build_hd_roles`, `art_polish_v5e.polish_upper_frames`, `art_grammar_v4.normalize_body_form`, `art_grammar_v4.normalize_vanilla_plus_body_form`). Each is a set of row/column rules such as `if 3<=y<=7 and x<=lo+2: role='LIGHT'`. None of them knows what the garment is. At 16x16 the entire torso is roughly 180 cells; a rule engine is not needed to shade it, and four rule engines guarantee disagreement.

3. **Identity is code, not data, and the code forbids it being data.** `generator/v5b/engine.py:43-53` and `generator/hybrid_v3/data_validation.py:38` reject any recipe key named `x`, `y`, `coordinates` or `pixels`. The consequence is that coordinates live in Python: 100 coordinate-literal lines in `generator/renderer.py`, 79 in `upper_v5d.py`, 46 in `hoodie_layers.py`, 41 in `upper_v5c2.py`, 33 in `component_compilers.py`. The one place coordinates were allowed into data (`specs/garment_grammar_v4/vanilla_plus_micro_shapes.json`) is the cleanest part of the repository, which is the strongest evidence in the repo for where the design should go.

4. **Five overlapping taxonomies for the same garments.** V2 archetypes (`BUTTON_SHIRT/JACKET/SWEATER/SAILOR_TOP`), V4 articles (`FITTED_SHIRT/VEST_TOP/CROPPED_JACKET/...`), V5B article types (`STANDARD_JACKET/BLOUSE/...`), controlled grammars (`FITTED_TEE/OPEN_CARDIGAN/WORK_JACKET`), and hybrid families (`T_SHIRT/POLO_SHIRT/SWEATER_VEST/...`). A polo is a `POLO_SHIRT` that is compiled on a `FITTED_SHIRT` V4 article of a `BUTTON_SHIRT` V2 archetype from a `structured_shirt` V5B variant. Adding one garment type means touching every layer.

5. **Family-specific hacks throughout the "generic" stages.** `art_polish_v5e.py:68` special-cases `STRUCTURED_FIELD_JACKET`; `pixel_grammar_v4.py:105` special-cases `SWEATER_VEST`; `component_compilers.py:60` special-cases `BODY_KNIT_VEST`; `refine_open_cardigan_premium_construction` hard-codes per-direction row bounds for one garment (`art_polish_v5e.py:326-331`); `compiler_validation.py:102-136` hard-codes cell counts per family; `generate_v4_vanilla_plus_proof.py:42-47` hard-codes expected topology per family.

6. **Lossy intermediate encoding.** Roles are encoded as gray levels and decoded by table (`MASK_ROLE_BY_VALUE`), with nearest-value fallbacks. A parallel "default frame" is maintained everywhere. This doubles every mutation and makes provenance unrecoverable.

7. **No shared exporter, no shared preview, no shared validator.** 22 packagers; the Farmer compositor lives in a tool script; each validator re-implements connectivity.

8. **Validation validates the process, not the garment.** "Expected shape variant ids executed", "at least 2 ADD topology operations", "ownership rejections preserved" test that the pipeline ran the way its author intended, not that the result reads as a polo. The checks that would matter (contrast at worn scale, readability after downsampling, identity present in each view) are absent, and human QC never closes.

9. **Determinism without variety.** `SeedBook` is good engineering, but the seeded parameters are ignored downstream, so the output space is the product of hand-written `CASES`.

10. **Sunk-cost layering.** The README rules say to "prefer proven Stardew/Fashion Sense structures over inventing a custom renderer", and every version since V2 has honoured that by wrapping the previous version rather than replacing it. The result is a stack in which the newest code cannot be understood without the six frozen files it pins by hash.

---

## 3. What I would keep

| Asset | Where | Why |
|---|---|---|
| PNG codec, nearest-neighbour scale, 5x7 text, blit | `generator/png_utils.py` | Dependency-free, correct, already used by every tool |
| Deterministic path-keyed seeding | `generator/hybrid_v3/seeding.py` (`derive_seed`, `SeedBook`) | Call-order independent, produces provenance |
| Runtime contract | 16x16 logical frame, Scale 2, `BodyPosition (0,32)`, 16x64 atlas front/right/left/back, `SleeveColors` triple, `HideSleeves false` — confirmed in `reports/HD_JACKET_POC.md:7` and `reports/FS_HD_JACKET_ANCHOR_CORRECTION.md` | The only in-game-verified fact in the repo |
| Body coverage envelope | `generator/data/fashionsense/hd_garment_grammar_v2.json` `bodyCoverageEnvelope` | Rows 0-2 that must stay opaque so the Farmer's shoulders do not show skin |
| Farmer preview compositor | `_farmer_composite` in `tools/generate_controlled_grammar_hd_adapter_repair.py:68-85` | Correct offsets; move into a library module |
| Color role vocabulary and stories | `specs/palettes/color_roles.json`, `palette_stories.json`, `material_color_behavior.json` | Good concepts; numeric parts to be re-encoded |
| Micro-shape data | `specs/garment_grammar_v4/vanilla_plus_micro_shapes.json` | Becomes the first entries of the authored component atlas |
| ASCII region templates | `hd_garment_grammar_v2.json` archetype `front/back/sideTemplates` | Become body blanks after conversion to role-index rows |
| Vanilla research tooling and findings | `tools/analyze_vanilla_shirts.py`, `reports/VANILLA_SHIRT_GRAMMAR.md` | Measurement baseline for the benchmark in section 15 |
| Generic sprite invariants | connectivity, row-0 support, binary alpha, dark-band scan in `compiler_validation.py:11-88` | Port as-is into the new validator |
| Fashion Sense source and sleeve templates | `FASHION SENSE/FashionSense-stable/...` | Contract source of truth; Sleeves templates for a later phase |

---

## 4. What I would remove

- All versioned engines and renderers: `generator/generate_v1.py`, `generate_v2.py`, `recipe_engine.py`, `v2_*.py`, `renderer.py`, `v3/`, `v4/`, `v45/`, `v46/`, `v46b/`, `v5a/`, `v5b/`, `v5c2/`, `v5d/`, `v5e/`, `v6/`, `renderers/fashionsense/*`, `renderers/vanilla/`, `controlled_test/`, `autonomous_recovery/`, `hoodie_layers/`, `rarity_renderer_policy.py`.
- The hybrid V3/V4 compiler: `generator/hybrid_v3/compiler/*` including the carrier registry, ownership ledger, topology editor, stage trace, polish wrapper, art grammar, shape library loader, and compiler validation. The builder/projector/validator trio can go too; the new resolver is smaller than `builder.py`.
- The five schema generations under `generator/schema/`.
- All `tools/generate_*` and `tools/validate_*` scripts except the vanilla analysis tools. Replace with one CLI.
- The "coordinate-free recipe" rule (`_coordinate_key_errors`, `data_validation.py:38`). Coordinates belong in authored data.
- Rarity budgets as a rendering input (`shadeActivation` in `hd_garment_grammar_v2.json`, `rarity_budgets.json`). Rarity is a catalog policy, not a pixel policy.

Archive rather than delete: move to `legacy/` with a README, keep `test-packs/` as historical outputs. Nothing in the new system imports from `legacy/`.

---

## 5. What I would replace

| Current | Replacement |
|---|---|
| Carrier render chain + reset + polish x3 + component painting | One compositor over authored role-indexed blanks and stamps |
| Grayscale-encoded roles + default frames + fabrics dict + ledger | One `RoleImage` per view: two small integer arrays (`role`, `slot`) plus a `source` array for provenance |
| Five taxonomies | One `GarmentTemplate` document per family |
| Blend-fraction palette ramps | OKLCH ramp derivation from (base color, material profile) |
| 22 packagers | One exporter with three targets: Fashion Sense pack, preview sheets, catalog JSON |
| Process-contract validation | Garment-contract validation plus the vanilla reconstruction benchmark |

---

## 6. Proposed architecture

### 6.1 What the system is fundamentally doing (answer to key question 1)

It places a small number of readable identity pixels on a fixed torso footprint, in four views, and colours them coherently. The footprint is fixed by the Farmer. The views are fixed by the game. The identity vocabulary is small: vanilla communicates "sailor", "vest", "overalls", "collared", "polo", "cardigan" with 2 to 14 pixels per view at 8x8 (see section 15). The variety players perceive comes from silhouette class, one or two identity components, colour, and pattern, in that order.

This is a **composition and colouring problem**, not a rendering problem. The correct abstraction at this scale is "select, place, mirror, recolour authored pieces", with procedural generation limited to the decisions, the palette, and pattern phase.

### 6.2 Is procedural pixel drawing the right abstraction at 16x16? (key question 4)

No. Evidence from the repo:

- Every version that used rule-based shading needed a later "polish" version to undo it (`V5E art polish`, `V4 art grammar`, `vanilla-plus body abstraction`).
- The one component of the current output that reviewers accepted, the vanilla-plus micro-shapes, is authored data placed by anchor.
- 16x16 at Scale 2 occupies the same 32x32 display box as the vanilla 8x8 at scale 4. A vanilla pixel is a 2x2 logical cell. Any identity feature thinner than 2 cells is sub-vanilla resolution and will not read at gameplay scale; rule engines produce 1-cell features constantly (`_sleeve`, `_ribbing`, `_waistband` in `component_compilers.py`).
- Rule-based shading is where family-specific hacks accumulate, because shading rules do not know what they are shading.

Procedural generation should stop at the boundary between *decision* and *pixel*. Pixels are authored; decisions are generated.

### 6.3 Layers

```
                     ┌──────────────────────────────┐
  authored atlas ──▶ │ 1. RESOLVE  (spec + seed →   │
  (blanks, stamps,   │    GarmentPlan)              │
   patterns,         └──────────────┬───────────────┘
   templates,                       │ plan: blank id, stamp ids + params,
   palettes,                        │ palette, material, sleeve policy
   materials)                       ▼
                     ┌──────────────────────────────┐
                     │ 2. COMPOSE  (plan → 4 x      │
                     │    RoleImage 16x16)          │
                     └──────────────┬───────────────┘
                                    │ role, slot, source arrays; no RGB
                                    ▼
                     ┌──────────────────────────────┐
                     │ 3. COLORIZE (RoleImage +     │
                     │    palette → RGBA frames)    │
                     └──────────────┬───────────────┘
                                    ▼
             ┌────────────┬─────────┴─────────┬──────────────┐
             ▼            ▼                   ▼              ▼
        VALIDATE      EXPORT FS pack    PREVIEW sheets   CATALOG json
```

Three stages, one intermediate representation, no repaint passes. Each stage is a pure function. A bad pixel is attributable by reading `source[y][x]` (which stamp or blank painted it), which makes the ownership ledger unnecessary because provenance is a by-product of composition rather than a defence.

---

## 7. Full pipeline

### Stage 0: Authoring (offline, human, with tooling)

- Author blanks, stamps, and pattern tiles in a text format (section 8), preview them instantly with a `preview` CLI that renders the piece on every blank it is compatible with, on the Farmer, in four views.
- Each authored piece is validated on save: dimensions, legal role chars, anchor existence, 2-cell minimum for identity features, mirror sanity.

### Stage 1: Resolve

Input: `GarmentSpec {seed, family, optional overrides (fit, palette, material, season, role)}`.

1. Load `GarmentTemplate[family]`.
2. Derive per-decision seeds with `SeedBook` (`derive_seed(root, "blank")`, `("stamp", slot_name)`, `("palette")`, ...).
3. Choose a blank from the template's allowed silhouette classes filtered by fit override.
4. For each template slot: required slots pick from the slot's candidate stamp list; optional slots roll against the slot's probability; parameters (e.g. button count, pocket x offset) are drawn from declared ranges; compatibility rules are checked (stamp declares `requires_anchor`, `conflicts_with`).
5. Choose material from the template's allowed set, then palette: either a curated story compatible with the material, or a generated palette from a hue seed + material profile + optional season/role bias.
6. Assign fabric slots: each stamp declares which palette slot it paints (`primary`, `secondary`, `trim`, `accent`) and the template can override.
7. Emit `GarmentPlan` (JSON, fully serialisable, sufficient to reproduce the sprite without the seed).

Nothing in this stage touches pixels. It is ~200 lines.

### Stage 2: Compose

For each view in `front, side, back`:

1. Copy the blank's `RoleImage` for that view (`role` array of `{0 transparent, 1 base, 2 light, 3 shadow, 4 deep}`, `slot` array all `primary`, `source` array all `blank`).
2. Apply stamps in the template's declared layer order (`under` stamps such as inner shirt first, then `body_edit` stamps such as cut-in armholes, then `over` stamps such as collars):
   - resolve the stamp's anchor for this view to a cell using the blank's anchor table (e.g. `neck_center`, `shoulder_r`, `hem_center`, `chest_center`, `side_front_edge`, `side_back_edge`);
   - apply the stamp's alpha edits (`-` cuts a body cell, `+` adds a supported cell);
   - paint the stamp's role/slot chars at anchor + offset, writing `source`.
3. Apply pattern overlay if any: a tiled role modifier clipped to a named blank region (e.g. `torso`, `yoke`, `lower_band`) with a per-view phase from the template so stripes align across views.
4. Derive `left` from `side` by horizontal mirror, unless the plan contains a stamp marked `asymmetric`, in which case that stamp's explicit `left` view (or its absence) is used.

Output: four `RoleImage`s. Roughly 150 lines.

### Stage 3: Colorize

`rgb = palette[slot][role]`. One lookup per cell. Sleeve colours are `palette[sleeve_slot][shadow, base, light]` where the template chooses `sleeve_slot` (primary for a tee, secondary for a vest so the inner shirt's sleeves show). ~30 lines.

### Stage 4: Validate (section 14)

### Stage 5: Export

- Fashion Sense pack: `Shirts/<Name>/shirt.png` (16x64, front/right/left/back), `shirt.json` at the confirmed contract, optional `ColorMaskLayers` for the primary slot to enable in-game dye, `preset_outfits.json`, `manifest.json`.
- Preview: isolated 8x sheet, Farmer sheet in four views, 8x8-downsampled "vanilla read" sheet.
- Catalog: one JSON per garment (`GarmentPlan` + validation result + identity vector) and a batch index.

### Stage 6: Batch and diversity

`generate --family any --count N --seed S` resolves N plans, composes, validates, and runs a diversity pass (identity-vector distance and 8x8-downsampled pixel distance against accepted items); rejected items are re-rolled with derived seeds. At ~10 ms per garment (array ops on 256 cells, no per-cell object churn) this can search thousands of candidates per batch.

---

## 8. Data model

All authored data is plain text so it diffs, reviews, and hand-edits well. A tiny legend:

```
role chars:  .  transparent (do not touch)     -  cut body alpha
             b  base   l  light   s  shadow    d  deep
             +  add cell as base (must be 4-adjacent to existing alpha)
slot:        lowercase = stamp's declared slot; UPPERCASE = stamp's second slot
```

### 8.1 Blank (silhouette)

```json
{
  "id": "tee_regular",
  "class": "TEE",
  "fit": "regular",
  "sleeves": "native_short",
  "views": {
    "front": {"rows": ["..dbbb....bbbd..", "dlllbb....bblssd", "..."],
              "anchors": {"neck_center": [8,1], "shoulder_l": [3,1], "shoulder_r": [12,1],
                          "chest_center": [8,5], "hem_center": [8,15], "hem_l": [2,15], "hem_r": [13,15]},
              "regions": {"yoke": "rows 1-3", "torso": "rows 4-13", "lower_band": "rows 12-14"}},
    "side":  {"rows": ["..."], "anchors": {"neck_center": [9,1], "front_edge": [12,4], "back_edge": [4,4], "hem_center": [8,15]}},
    "back":  {"rows": ["..."], "anchors": {"neck_center": [8,1], "hem_center": [8,15]}}
  },
  "left": "mirror"
}
```

Shading (light/shadow/deep) is authored in the blank once, from the vanilla convention: upper-left light, right/lower shadow, deep only at silhouette turns and under the hem. No code decides shading.

Initial blank set (from the vanilla contact sheet and the existing ASCII templates): `tee_regular`, `tee_fitted`, `tee_relaxed`, `boxy_jacket`, `cropped`, `vest_sleeveless` (class VEST, `sleeves: none_or_inner`), `tunic_long`, `feminine_fitted`. Eight blanks cover the listed garment list; blazers and bombers are `boxy_jacket` or `tee_regular` plus stamps.

### 8.2 Stamp (authored reusable pixel component)

```json
{
  "id": "collar_sailor",
  "kind": "collar",
  "layer": "over",
  "slot": "trim",
  "second_slot": "accent",
  "identity": true,
  "compatible_classes": ["TEE", "BLOUSE"],
  "views": {
    "front": {"anchor": "neck_center", "offset": [-4, 0],
              "rows": ["lbb....bbs", ".bs....bs.", "...dA.....", "...LS....."]},
    "side":  {"anchor": "neck_center", "offset": [-2, 0], "alpha": {"+": [[3,0]]},
              "rows": ["lbs", ".s."]},
    "back":  {"anchor": "neck_center", "offset": [-4, 0],
              "rows": ["lbbbbbbs", ".bbbbbs."]}
  },
  "min_cluster": 2,
  "mirror": true,
  "params": {"bow": {"type": "bool", "default": true, "controls": "second_slot cells"}}
}
```

The whole component, all views, lives in one file. Four-view consistency is a property of the data, not of a projection algorithm. `identity: true` marks stamps the validator must find in every view where the stamp has rows.

Initial stamp set (target ~35): `collar_crew`, `collar_polo`, `collar_shirt_folded`, `collar_sailor` (with rear flap and optional bow), `collar_stand`, `collar_hood_down`, `neck_v_bound`, `neck_deep_v_bound` (vest), `lapel_notch`, `lapel_shawl`, `placket_short` (polo), `placket_full` (buttons 2-4), `zip_center`, `open_front_inner` (cardigan/jacket: two leaves + inner slot column), `armhole_cutin` (body edit), `inner_shirt_side` (vest side reveal), `hem_rib`, `hem_band`, `hem_split`, `yoke_back`, `yoke_saddle`, `pocket_chest_flap`, `pocket_patch_pair`, `pocket_welt_pair`, `bib_overalls` (+ `straps_overalls` over the inner slot), `belt_band`, `epaulettes`, `tie_small`, `bow_neck`, `stripe_chest_band`, `emblem_small`. Cuffs are not shirt pixels (native sleeves), so a cuff is a sleeve-colour choice until custom Sleeves are added in phase 4.

### 8.3 Pattern tile

```json
{"id": "stripe_h_2", "cell": ["....", "ssss"], "modifies": "role", "phase_by_view": {"front": 0, "side": 0, "back": 0}}
```

Patterns modify roles (base→shadow or base→light) or slots (base→secondary) inside a named region, so they inherit shading and never overwrite identity stamps (`source != blank` cells are skipped).

### 8.4 Garment template (family)

```json
{
  "id": "POLO",
  "display": "Polo shirt",
  "blanks": ["tee_regular", "tee_fitted", "tee_relaxed", "feminine_fitted"],
  "sleeves": {"policy": "native_short", "slot": "primary"},
  "slots": {
    "collar":  {"required": true, "candidates": ["collar_polo"]},
    "placket": {"required": true, "candidates": ["placket_short"], "params": {"buttons": [1, 2]}},
    "hem":     {"required": false, "p": 0.3, "candidates": ["hem_band"]},
    "chest":   {"required": false, "p": 0.25, "candidates": ["emblem_small", "pocket_chest_flap"]},
    "pattern": {"required": false, "p": 0.3, "candidates": ["stripe_chest_band", "stripe_h_2"], "region": "torso"}
  },
  "materials": ["KNIT", "COTTON_TEE"],
  "slot_contrast": {"trim_vs_primary": {"min_dL": 0.10}},
  "identity_vector": ["class:TEE", "collar_polo", "placket_short"],
  "fit_profiles": {"masc": ["tee_regular", "tee_relaxed"], "fem": ["feminine_fitted", "tee_fitted"], "unisex": ["tee_regular"]}
}
```

Adding a garment family is one JSON file plus, at most, one or two new stamps. Overalls: template `OVERALLS_TOP` = `tee_regular` blank painted in `secondary` (the shirt) + `bib_overalls` + `straps_overalls` in `primary`, `sleeves.slot: secondary`.

### 8.5 Palette

```json
{"slots": {"primary": {"deep": "#..", "shadow": "#..", "base": "#..", "light": "#.."},
           "secondary": {...}, "trim": {...}, "accent": {"base": "#.."}},
 "story": "COASTAL_MIST", "material": "KNIT"}
```

Derived, not hand-blended: given a base colour in OKLCH and a material profile `{dL_shadow, dL_light, dL_deep, hue_shift_shadow, chroma_scale_light}`, compute the four steps. Curated stories supply base colours per slot; the generator can also draw base colours from hue families with seasonal/profession bias tables. The existing `palette_stories.json` stories are valid inputs after their prose fields are dropped.

### 8.6 RoleImage (only intermediate)

`role: int[16][16]`, `slot: int[16][16]`, `source: int[16][16]` (index into the plan's piece list). Four of them per garment. No RGB, no gray encoding, no default frame.

### 8.7 GarmentPlan (output record)

`{spec, blank, pieces: [{stamp, params, anchor_cells_per_view}], pattern, material, palette, sleeve, identity_vector, provenance: SeedBook.provenance()}`.

---

## 9. Rendering strategy

- **Index then colour.** All composition works on role/slot indices; RGB is produced once at the end. This removes the `MASK_ROLE_BY_VALUE` decode, the default frames, and every "resolve" fallback.
- **Shading is authored.** Blanks carry light/shadow/deep. Stamps carry their own local shading. No stage classifies edges, detects contours, or repaints. The vanilla convention (selective deep pixels at turns, hem, under-collar; no full outline) is followed by the authors, checked by the validator, and never "corrected" by code.
- **Two-cell rule.** Because a vanilla pixel is 2x2 logical cells, identity stamps must contain at least one 2x2 or 1x3 cluster per view and the validator enforces it. Single-cell accents are allowed only for non-identity detail (a button, a bow highlight).
- **No upscaling, no downscaling anywhere in the art path.** The 8x8 downsample exists only in validation and preview.
- **Sleeves.** Native Farmer sleeves recoloured via `SleeveColors` (proven). Long-sleeve identity (cuffs, contrast sleeves) is deferred to a custom Sleeves companion in phase 4, authored the same way (role-indexed frames over the Fashion Sense template), not derived by 2x seeding as `upper_v5b._target_atlas()` does now.
- **Output resolution.** 16x16 at Scale 2 stays. The additional density over vanilla is spent on cleaner curves and 2-cell collars, not on more features.

---

## 10. Four-direction strategy

- A stamp is one object with `front`, `side`, `back` views (any may be absent, meaning "not visible from here"). Consistency is guaranteed by authorship; the compositor cannot produce a collar in front without the same stamp's side and back rows.
- `left` is the mirror of `side` for both blanks and stamps, matching what vanilla does and what the Farmer sprite itself does. Measured on the installed `shirts.png`: 212 of 302 left tiles are exact mirrors of the right tile (base and dye mask), 78 differ by one to nine recoloured pixels with identical alpha (usually one shade pixel), and only 12 differ in alpha (asymmetric designs such as the poncho and the 80's shirts). Asymmetric stamps (single chest pocket, diagonal closure) opt out with `"mirror": false` and provide an explicit `left` view or none. No automatic left-view relighting is needed; where an author wants the vanilla-style one-pixel fix, the blank or stamp may carry an explicit `left`.
- Side views are authored compressed: collars move to the front edge, plackets vanish, wrap features (hem bands, yokes, sailor flap edge) continue. The blank's side anchors (`front_edge`, `back_edge`) are what stamps attach to, so a stamp authored once works on every blank of its class.
- Wrap continuity is validated: a stamp with `kind: hem|yoke|band` must paint on the same rows in all four views.
- Back views are simplified: the template lists which slots have back rows; most closures do not.

This replaces `directionalVisibility` tables, `DirectionalProjector`, the per-direction literal lists, and the safe-envelope topology API with data that a human can see in one file.

---

## 11. Procedural-vs-authored boundary

| Element | Decision | Reason |
|---|---|---|
| Torso silhouettes and fit | Authored blanks, selected | 8 blanks cover the target list; vanilla varies fit by lower-row contour, not by algorithm |
| Body shading | Authored in blanks | Four rule engines disagreeing is the current failure |
| Collars, lapels, plackets, bows, ties, vest bindings, sailor flaps, bibs and straps, pocket flaps, yokes, epaulettes, hoods-down | Authored stamps with views, selected | These are the identity pixels; vanilla shows each is 2-14 pixels and fixed in shape |
| Cuffs | Not shirt pixels; sleeve colour now, authored Sleeves later | Native sleeves are proven; custom sleeve atlases are a separate risk |
| Stamp placement | Parameterized (anchor + small offset range) | Pocket at x±1 is real variety; free placement is not |
| Stamp sizing | Selected from authored variants (`collar_polo_small`, `collar_polo`) | Scaled pixel art does not read |
| Button count, pocket count, bow on/off | Parameterized | Cheap, readable variety |
| Patterns (stripes, checks, dots, bands) | Procedural tiling of authored tiles into named regions | Phase, density, region are safe procedural axes |
| Colour blocking | Procedural selection of blank regions (yoke, lower band, side panels) painted in `secondary` | Regions are authored; the choice is generated |
| Palettes | Procedural derivation from curated or generated base colours + material profile | This is where perceived variety comes from |
| Which stamps, which blank, which palette, which pattern | Procedural (seeded resolve) | The whole point of the generator |
| Diversity, naming, rarity assignment | Procedural, at catalog level | Not a pixel concern |

Answer to key question 5: yes, garment details should come from an authored reusable component library. Answer to key question 6: shapes are curated, combinations and colours are generated.

---

## 12. Garment identity representation

`identity_vector = [class, identity stamps..., sleeve policy, slot relationship tags]`, e.g. `["TEE", "collar_sailor", "native_short", "trim>primary"]` for a sailor top, `["VEST", "neck_deep_v_bound", "armhole_cutin", "inner_shirt_side", "sleeves:secondary"]` for a sweater vest.

- Templates define identity; the validator asserts each identity stamp painted in every view where it has rows; the diversity pass measures distance on this vector before pixel distance.
- Identity never depends on colour. A sailor top in navy and in cream are both sailor tops; the validator's slot-contrast rule (`trim` vs `primary` minimum ΔL) guarantees the collar reads in either.
- Fit (`masc/fem/unisex`) is a blank choice, not an identity, so the same identity vector can render on `feminine_fitted` or `tee_relaxed`.
- Role/season/profession are template tags plus palette bias, not separate families.

---

## 13. Material and palette strategy

- **Material profile** (numeric): `{dL_shadow, dL_light, dL_deep, hue_shift_shadow_deg, chroma_scale_shadow, chroma_scale_light, preferred_hems: [...], allowed_patterns: [...], default_sleeve_policy}`. Replace the prose fields of `specs/palettes/material_color_behavior.json` with these numbers; keep the ids.
- **Palette derivation** in OKLCH: `base` per slot from a story or from a seeded hue with per-material chroma limits; `light = base + dL_light`, `shadow = base - dL_shadow` with hue shift, `deep = base - dL_deep`. `trim` and `accent` derive from the story or from a relationship rule (`trim = darker, lower-chroma neighbour of primary` or `contrast hue`). A single shared `deep` across slots is permitted when ΔE is small, mirroring the current "shared dark" policy.
- **Contrast gates** at worn scale: `trim` vs `primary` ΔL ≥ 0.10; `secondary` vs `primary` ΔL ≥ 0.12 or Δhue ≥ 40°; `accent` vs its host ≥ 0.15. Gates are template-adjustable.
- **Batch composition**: value-range and temperature histograms across a batch with caps (no more than 30 % dark-neutral primaries, at least 20 % light primaries), replacing prose anti-convergence notes with enforced counts.
- **Dye**: optional `ColorMaskLayers` for the primary slot on export so players can recolour; the four primary ramp colours are the mask values. Off by default until tested in game.

---

## 14. Validation strategy

Three tiers, all automatic, all producing a per-garment report that names the offending stamp via `source`.

1. **Sprite invariants** (ported): binary alpha, one connected component per view (two for sleeveless side views), rows 0-2 cover the body envelope, no unsupported row-0 cells, atlas dimensions and order, `SleeveColors` present, colour count per view ≤ 8.
2. **Garment contract** (from the template, no per-family code): each identity stamp painted in each view it defines; every identity stamp has a ≥2-cell cluster; wrap stamps continuous across views; slot contrast gates pass; pattern did not overwrite stamp cells; left equals mirrored side unless an asymmetric stamp is present; blank-authored shading untouched outside stamp footprints.
3. **Readability**: downsample each view to 8x8 by 2x2 majority role/slot; require the identity stamps to survive as ≥1 cell with contrast against neighbours; require the silhouette class's 8x8 alpha signature to match the blank's declared signature. This is the automated stand-in for "reads at Farmer scale".

Plus a batch tier: identity-vector diversity, pixel-distance diversity at 8x8, palette histograms.

Human review remains the final authority, but it is scheduled per family during authoring (phase 2), not deferred forever as `PENDING`. One in-game check per phase is part of the definition of done.

---

## 15. Vanilla reconstruction benchmark

The installed `shirts.png` and `Data/Shirts.json` were read directly. Observations from a 23-shirt contact sheet (indices 1, 19, 20, 0, 248, 198, 218, 155, 163, 29, 140, 10, 167, 278, 216, 176, 137, 178, 271, 157, 239, 259, 154), consistent with `reports/VANILLA_SHIRT_GRAMMAR.md`:

- Identity per family at 8x8: Sailor Shirt (19, 259): light collar wedge + 1-2 white pixels front, light square flap back, wedge edge on side. Green Vest (20) and Gray Vest (167): dark side panels + lighter centre column for the inner shirt; 167 disables sleeves so skin arms carry "sleeveless". Classic/Plain Overalls (0, 216): bib rectangle in the dye colour over a contrasting shirt colour with 2 strap pixels at the shoulders; the identity is a slot relationship, not a shape. Collared Shirt (248): two light neck pixels + 2-3 button pixels in the centre column. Vintage Polo (198): two collar pixels + one placket pixel. Cardigan (218) and Denim Jacket (163): a 2-wide light centre column (inner layer) with darker leaves. Bomber (155) and Letterman (137): colour-blocked shoulders/sleeve zones.
- Colours per view: 3 to 11, median 6. Occupancy 53-64 of 64 cells. No isolated single pixels.
- Left tiles are mirrors of right tiles in 212 of 302 cases; 78 more differ only by a few recoloured pixels; 12 are structurally asymmetric.
- Sleeves are not in the shirt tile; the game samples column 0 rows 2-4.

Benchmark procedure (a gate for phases 1 and 2):

1. Choose 12 vanilla targets covering the families above.
2. Author blanks/stamps until the kit can express each target as a `GarmentPlan` (this is also how the stamp library gets authored honestly: by tracing what vanilla does at 2x2).
3. Score: (a) alpha signature after 8x8 downsample equals the vanilla tile's alpha exactly; (b) role agreement ≥ 85 % on cells classified from the vanilla tile by luminance rank (deep/shadow/base/light) and by slot (base colour vs mask colour); (c) side-by-side Farmer sheet for human sign-off.
4. Keep the reconstructions as regression fixtures; any kit change that lowers a score fails CI.

"Vanilla plus" is then defined precisely: same identity pixels as the reconstruction, plus cleaner curves and 2-cell collar edges permitted by the 16x16 grid, minus nothing.

---

## 16. Migration and reuse plan

1. Create `generator2/` (or `rngc/`) with modules `pngio` (moved `png_utils.py`), `seeding` (moved), `atlas` (blank/stamp/pattern loaders + authoring validators), `resolve`, `compose`, `colorize`, `validate`, `export_fs`, `preview`, `cli`.
2. Convert data:
   - `hd_garment_grammar_v2.json` archetype ASCII templates → first blanks (`tee_regular` from BUTTON_SHIRT front/back/side with the placket columns set to body; `boxy_jacket` from JACKET; `vest_sleeveless` from the SWEATER body with sleeve columns cut). Shade them by hand once.
   - `vanilla_plus_micro_shapes.json` variants → first stamps (`collar_polo`, `placket_short`, `neck_deep_v_bound`, `armhole_cutin`, `inner_shirt_side`, `hem_rib`, `collar_sailor` + rear flap + bow, `collar_crew`).
   - `specs/palettes/*` → `palettes/stories/*.json` (hex roles only) and `materials/*.json` (numeric profiles).
   - `bodyCoverageEnvelope` → `validate` constant.
   - `_farmer_composite` → `preview.farmer_sheet`.
3. Move `generator/`, `tools/`, `generator/schema`, old specs to `legacy/`. Keep `tools/analyze_vanilla_shirts.py` and `analyze_fs_quality_benchmarks.py`, ported to the new `pngio`.
4. Keep `test-packs/` and `output/` as history; the new CLI writes to `dist/`.
5. Replace the README generation sections with the single CLI: `rngc author-check`, `rngc preview <piece>`, `rngc bench vanilla`, `rngc generate --family X --count N --seed S`, `rngc export fs`.

---

## 17. Implementation phases

| Phase | Deliverable | Gate |
|---|---|---|
| 0. Freeze | `legacy/` move, new package skeleton, `RoleImage`, loaders, CLI stub | Existing outputs untouched; new tests run in < 1 s |
| 1. Core + 3 reconstructions | compose/colorize/export/preview; blanks `tee_regular`, `vest_sleeveless`; stamps for tee, collared shirt, sailor; reconstruct vanilla 1, 248, 19 | Benchmark (a) exact alpha, (b) ≥ 85 %; one FS pack loads in game at the confirmed anchor |
| 2. Library | 8 blanks, ~35 stamps, 6 pattern tiles, 12 templates (tee, polo, collared, blouse, sweater vest, vest, cardigan, sailor, overalls top, work jacket, bomber, blazer), 16 palettes, material profiles; all 12 vanilla reconstructions | Human review per family on Farmer sheets; second in-game pack |
| 3. Generator | resolve with weights and params, palette derivation, diversity pass, catalog build of 300 items, validation report | ≥ 90 % of 300 pass all three validation tiers without hand edits; batch histograms within caps |
| 4. Extensions | dye `ColorMaskLayers`, custom Sleeves companions for long-sleeve identity, seasonal/profession template sets, fem/masc blank pairs for every template, pants/overalls lower half as a separate atlas of the same design | Each extension has its own in-game check |

Phases 1-3 are roughly 2,000-2,500 lines of Python plus authored data, against 38,000 lines today.

---

## 18. Risk analysis

| Risk | Likelihood | Mitigation |
|---|---|---|
| Authoring cost of stamps/blanks | Medium | Vanilla proves ~12 stamp kinds cover the family list; each stamp is 4-30 cells x 3 views; the benchmark makes authoring a tracing exercise; the instant preview CLI shortens the loop |
| Side views read badly | Medium | Side rows are authored per stamp, reviewed on the Farmer, and the 8x8 readability check runs on side views too |
| Perceived sameness ("all tees look alike") | Medium | Variety budget lives in palette derivation, patterns, colour-block regions, and optional stamps; the diversity pass rejects near-duplicates; the batch histogram caps dark neutrals |
| 16x16 features drawn at 1-cell width | Low with the 2-cell rule enforced | Validator tier 2 |
| Fashion Sense contract drift | Low | Contract constants in one module; `FASHION SENSE/` source pinned; one in-game check per phase |
| Dye masks conflicting with fixed colours | Medium | Off by default; when on, mask values are exactly the four primary ramp colours and the validator checks disjointness with other slots |
| Long sleeves, coats, dresses | High for coats/dresses | Out of scope for the shirt atlas; custom Sleeves in phase 4; lower-body remains a separate later atlas |
| Loss of the legacy "proven" behaviour | Low | The only in-game-proven facts are the contract constants, which are kept; nothing else was runtime-tested |
| Mirror asymmetry (light direction) | Low | Matches vanilla and the flipped Farmer; per-stamp opt-out exists |

---

## 19. Final recommendation

**FULL GENERATOR REBUILD.**

Why not the alternatives:

- *Evolve current system*: the defects are structural. The seed does nothing, the garment is painted over a foreign garment, shading is recomputed four times, and identity is spread across five taxonomies and three shape-library branches. Evolution means a V4.3 that wraps V4.2.
- *Partial rebuild*: keeping `hd_garment_v2` as the "proven raster backend" keeps the grayscale role encoding, the default frames, the coverage/edge/gesture heuristics, and the need for reset and polish stages. Everything downstream exists to cope with it.
- *Full middle-layer rebuild*: the repo already did this twice (`hybrid_v3` Phase 2, then V4.1/V4.2). Each time the middle layer grew an ownership or topology mechanism to defend against the renderer. The middle layer and the renderer are the same problem.

Why a rebuild is cheap here: the runtime contract, PNG IO, seeding, preview, palette data, coverage envelope, and micro-shape data are all reusable, and the target implementation is an order of magnitude smaller than what exists. The expensive part of the new system is authored pixel data, and the vanilla reconstruction benchmark turns that authoring into a bounded, checkable task rather than open-ended art direction.

The simplest pipeline that still supports meaningful variety is: resolve a plan from a seed, stamp authored role-indexed pieces onto an authored role-indexed blank, colour once from a derived palette, validate against the template and the 8x8 read, export. That is the architecture I would build.
