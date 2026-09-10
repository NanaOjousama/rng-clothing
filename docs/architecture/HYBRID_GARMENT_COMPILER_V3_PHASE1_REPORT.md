# Hybrid Garment Compiler V3 — Phase 1 Report

Status: **PASS — RECIPE-ONLY / NO RENDERER INTEGRATION**  
Feature flag: `HYBRID_GARMENT_COMPILER_V3_ENABLED=false`  
Valid deterministic cases: **18**  
Deliberate invalid cases rejected: **9/9**  
Semantic-flat diagnostics: **6** (one per family)  
Fashion Sense clothing generated: **0**

## 1. Files added or changed

Architecture documentation:

- `docs/architecture/HYBRID_V3_BASELINE_FREEZE.md`
- `docs/architecture/HYBRID_GARMENT_COMPILER_V3_PHASE1_REPORT.md`

Versioned data:

- `specs/hybrid_garment_compiler/v3/manifest.json`
- `canonical_garment_model.schema.json`
- `generated_recipe.schema.json`
- `architecture_definitions.json`
- `component_definitions.json`
- `component_compatibility.json`
- `design_intents.json`
- `fit_profiles.json`
- `family_material_compatibility.json`
- `projection_contract.json`

Isolated Phase 1 implementation:

- `generator/hybrid_v3/config.py`
- `data.py`
- `data_validation.py`
- `seeding.py`
- `builder.py`
- `validator.py`
- `projector.py`
- `semantic_flat.py`
- `generator/hybrid_v3/__init__.py`

Fixtures and tools:

- `tests/fixtures/hybrid_v3_invalid_cases.json`
- `tools/generate_hybrid_v3_phase1.py`
- `tools/validate_hybrid_v3_phase1.py`

Generated recipe-only evidence:

- `output/hybrid-v3-phase1/phase1-summary.json`
- `output/hybrid-v3-phase1/independent-validation.json`
- `output/hybrid-v3-phase1/valid/*`
- `output/hybrid-v3-phase1/invalid/*`

## 2. Legacy path preservation

The legacy/current recovery entry point, concept engine, and adapter were not modified. `tools/generate_autonomous_generator_recovery.py` still imports `generator.autonomous_recovery`, not V3. The new feature flag is isolated in `generator/hybrid_v3/config.py`, defaults to false, and has an explicit no-partial-mix assertion.

Phase 1 tools call the V3 package directly for recipe diagnostics. This does not enable production integration. No V3 canonical model is partially combined with legacy `_construct` anatomy.

The baseline route and SHA-256 contract freeze are recorded in `HYBRID_V3_BASELINE_FREEZE.md`.

## 3. Architecture schemas

The V3 namespace is versioned at `3.0.0`. The canonical schema requires identity, rarity-budget reference, architecture reference/version/digest, intent, fit and resolved proportions, material, component graph, relations, rear structure, surface intent, runtime envelope, and seed/data provenance.

The generated-recipe schema requires the canonical model plus Front/Right/Back/Left projections, validation, renderer-isolation provenance, and an optional semantic-flat path. Architecture data and canonical outputs contain no renderer coordinates.

`data_validation.py` additionally checks the six-family manifest, component field completeness, four-direction policies, material IDs against the approved material behavior library, inheritance resolution, mandatory slots, intent/palette separation, and the seven fit profiles without requiring an external JSON-schema package.

## 4. Component registry

The registry implements the required reusable component types:

`BODY`, `COLLAR`, `LAPEL`, `SLEEVE`, `ARMHOLE`, `OPENING`, `PLACKET`, `POCKET`, `HEM`, `WAISTBAND`, `REAR_PANEL`, `RIBBING`, and `INNER_LAYER`.

Every definition declares a stable ID, type, attachment region, family/material compatibility, parameter ranges, directional visibility, continuity, pixel priority, silhouette impact, and hard compatibility rules. Root body definitions declare the attachment regions they provide. Opening definitions provide a front-opening child anchor for plackets/lapels. No definition contains sprite or renderer coordinates.

## 5. Six implemented families

| Family | Composition proven |
|---|---|
| `T_SHIRT` | Knit root body + bound crew + native short sleeves + continuous light hem |
| `POLO_SHIRT` | Inherits T-shirt body/sleeves/hem; replaces crew with folded collar; adds short front opening and upper-chest placket |
| `SWEATER_VEST` | Knit vest body + deep bound V + cut-in armholes + inner shirt + ribbed hem/waist; sleeves forbidden |
| `CARDIGAN` | Soft knit body + open band + soft opening + broad inner layer + native long sleeves + ribbed termination; optional attached patch pockets |
| `BLAZER` | Tailored body + rear collar band + notched lapels + shaped opening + inner shirt + native long sleeves + shaped hem + authored rear seam/vent |
| `SAILOR_TOP` | Woven body + broad sailor collar + native short sleeves + simple hem + mandatory rear sailor panel |

`POLO_SHIRT` resolves an inheritance chain of `T_SHIRT -> POLO_SHIRT`; directions are not independently authored.

## 6. Design Intent implementation

Two reviewed intents exist for every initial family:

- Tee: `TEE_CLEAN_ESSENTIAL`, `TEE_RELAXED_WEEKEND`
- Polo: `POLO_CLASSIC`, `POLO_COASTAL_SPORT`
- Sweater vest: `VEST_ACADEMIC`, `VEST_RELAXED_KNIT`
- Cardigan: `CARDIGAN_ACADEMIC`, `CARDIGAN_RELAXED_WEEKEND`
- Blazer: `BLAZER_CLEAN_TAILORED`, `BLAZER_SOFT_SMART_CASUAL`
- Sailor: `SAILOR_DECK_CLASSIC`, `SAILOR_SOFT_MARITIME`

Each intent has one dominant construction idea, one supporting idea, avoid rules, fit preferences, component/parameter tendencies, optional slots, and semantic surface topology. Intents assign no final palette.

## 7. Fit Profile implementation

Implemented profiles:

- `MASC_RELAXED`
- `MASC_TAILORED`
- `FEM_FITTED`
- `FEM_RELAXED`
- `UNISEX_REGULAR`
- `UNISEX_BOXY`
- `UNISEX_CROPPED`

Fit affects only shoulder tendency, waist suppression, body length, and volume. The builder clamps tendencies to the selected architecture's approved ranges and saves the resolved proportions. Fit does not select palette, rarity, material quality, or decoration.

## 8. Canonical garment model

`CanonicalGarmentBuilder` constructs one coordinate-free object after resolving architecture, intent, fit, component variants, and material. It saves:

- garment identity;
- recipe-only rarity/budget interface reference;
- architecture version, digest, and inheritance chain;
- intent and fit;
- resolved proportions;
- approved material behavior ID;
- component instances and parameters;
- parent attachments and wrap relations;
- rear structure and surface intent;
- safe runtime envelope;
- root/stage seeds and versioned-data digests.

The model is the sole input to validation and projection. There are no independently improvised directional recipes.

## 9. Physical validator

`PhysicalValidator` checks:

- component and inheritance graph cycles;
- duplicate or missing mandatory instances/types;
- parent existence and attachment-region support;
- component definition/family/type/material compatibility;
- allowed parameter ranges;
- illegal direction-policy overrides;
- wraparound continuity groups;
- family material compatibility;
- fit values against architecture ranges;
- opening/placket and collar/lapel relationships;
- sleeve/armhole contradictions;
- polo placket and rear-opening rules;
- vest armhole/sleeve rules;
- cardigan lapel prohibition;
- blazer lapel requirement;
- sailor rear-panel requirement;
- safe upper-body/native-sleeve runtime envelope.

Projection validation separately verifies that all four views contain exactly the canonical component instances with unchanged visibility decisions.

## 10. Directional projector

`DirectionalProjector` is deterministic and performs no random choice. It projects every canonical component into Front, Right, Back, and Left with one of:

`FULL`, `COMPRESSED`, `DEPTH_ONLY`, `EDGE_ONLY`, `OCCLUDED`, `HIDDEN`, or `FORBIDDEN`.

Verified examples include:

- polo placket: Front `FULL`, sides `HIDDEN`, Back `FORBIDDEN`;
- polo collar: Front `FULL`, sides `DEPTH_ONLY`, Back `EDGE_ONLY`;
- blazer lapels: Front `FULL`, sides `DEPTH_ONLY`, Back `FORBIDDEN`;
- sweater-vest armhole: Front/Back `FULL`, sides `COMPRESSED`;
- sailor rear panel: Front `HIDDEN`, sides `COMPRESSED`, Back `FULL`.

## 11. Neutral-flat debug output

`semantic_flat.emit_semantic_flat` reads the supplied RGB8 neutral authoring flat through a local debug-only decoder and emits annotated RGBA diagnostics. It displays component instance IDs, attachment zones, visibility, continuity groups, and priority for all four views.

One diagnostic was generated per family. The debug flat is not read by the canonical builder, projector, validator, a pixel compiler, or a renderer. The Phase 1 summary confirms no renderer modules were imported.

## 12. Deterministic seed system

`seeding.py` derives stable 64-bit stage seeds from SHA-256 over root seed plus a named path. Phase 1 records:

- rarity;
- family;
- architecture;
- design intent;
- fit;
- each component selection;
- each component parameter;
- material.

The independent validator rebuilds the same polo twice and requires exact canonical-model equality. A synthetic future `palette` seed is separately namespaced and cannot perturb saved architecture seeds.

## 13. Polo material correction

`POLO_SHIRT` allows `KNIT` and `COTTON_TEE`, defaults to `KNIT`, and explicitly forbids `WOVEN_SHIRT`. `PIQUE_KNIT` does not exist in the approved material behavior library, so Phase 1 records this as a temporary mapping to existing `KNIT`. No renderer material or shading behavior was invented or modified.

All three polo fixtures resolved to `KNIT`.

## 14. Valid test cases

Eighteen valid recipes passed: three per family using masculine, feminine, and unisex fit profiles, with both family intents represented across each group. Each output contains:

- `canonical-model.json`
- `projections.json`
- `validation.json`
- `generated-recipe.json`
- optional `semantic-flat.png`

Generation summary: `output/hybrid-v3-phase1/phase1-summary.json`.

## 15. Invalid/rejected test cases

All nine checked-in invalid fixture definitions were rejected with their required codes:

1. polo with full/rear placket;
2. sweater vest with sleeve component;
3. cardigan with blazer lapel;
4. blazer without lapel;
5. sailor top without rear panel;
6. unattached collar;
7. wraparound hem without continuity group;
8. component used outside its allowed family;
9. component-parent cycle.

Actual validation outputs are saved under `output/hybrid-v3-phase1/invalid/`. Extra relevant codes are permitted, but every fixture's expected hard failure must be present.

## 16. Known remaining gaps

- Phase 1 has no pixel-grammar compiler or carrier-capability mapping.
- No final palette selection or rarity-polish implementation is connected.
- No Farmer composite or visual quality/diversity gate runs because there are no garment sprites.
- Only six families are loaded; the remaining architecture corpus is intentionally deferred.
- Component parameter vocabularies are discrete Phase 1 semantics and will require compiler feasibility review before expansion.
- The neutral flat displays semantic attachment; it does not prove 16×16 survival.
- JSON schemas are shipped as versioned contracts, while current validation is dependency-free project validation rather than an external `jsonschema` runtime dependency.
- Runtime behavior is only represented by envelope constraints; no Fashion Sense runtime claim is made.

## 17. V5/HD preservation confirmation

No file under `generator/renderers/fashionsense/` was edited. No Fashion Sense pack, Shirt atlas, preset, or final clothing PNG was generated. The Phase 1 process reports:

```json
{
  "featureFlagEnabled": false,
  "rendererModulesImported": [],
  "rendererInvoked": false
}
```

The independent validation result is `PASS` with zero errors.

## 18. Exact Phase 2 boundary

Phase 2 may begin only after review. Its first permitted boundary is:

```text
validated canonical model
-> validated directional projections
-> component/family pixel-grammar compiler
-> semantic pixel regions and carrier capability checks
```

Phase 2 should map a very small approved subset into existing carrier signals while preserving the frozen V5/HD renderer. It must not treat the semantic flat as input, independently design directions, import all remaining families, change rarity probabilities, or enable production by default. A controlled renderer proof and Farmer-scale gate remain separate approval points after compiler fixtures pass.
