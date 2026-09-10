# Hybrid Garment Compiler V3 Integration Plan

Status: **PLAN ONLY — NOT IMPLEMENTED**  
Target system: `RNG Clothing Hybrid Garment Compiler`  
Target schema: `3.0.0`  
Neutral-flat schema: `1.0`  
Renderer policy: **proven V5/HD backend frozen**  
Supersedes: `docs/architecture/GARMENT_ARCHITECTURE_V2_INTEGRATION_PLAN.md`

This document upgrades the V2 codebase inventory into the two-mode V3 architecture. The V2 plan must not be implemented. Its repository audit, family mappings, carrier findings, palette/material findings, and safety constraints remain useful evidence; its production placement of the neutral flat does not.

Authoritative study inputs:

- `RNG_Clothing_Codex_Architecture_Study_v2_1/RNG_CLOTHING_HYBRID_STUDY_GUIDE_V3.md`
- `RNG_Clothing_Codex_Architecture_Study_v2_1/RNG_CLOTHING_HYBRID_GENERATOR_SCHEMA_V3.json`
- `RNG_Clothing_Codex_Architecture_Study_v2_1/REAL_TO_PIXEL_TRANSLATION_FLAT.png`
- `RNG_Clothing_Codex_Architecture_Study_v2_1/real_to_pixel_translation_flat_schema.json`
- `docs/architecture/GARMENT_ARCHITECTURE_V2_INTEGRATION_PLAN.md`

The real-world and technical references named by the study are architecture evidence only. No source pixels, exact prints, logos, branding, or exact palettes become project output. Generated explanatory flats are not garment truth.

## 1. Current codebase reality

### Actual normal/recovery flow today

The active autonomous recovery path is:

```text
tools/generate_autonomous_generator_recovery.py
  -> generator.autonomous_recovery.concept_engine.concept_for
  -> semantic_errors
  -> structural_difference
  -> generator.autonomous_recovery.adapter.render_autonomous_concept
       -> _carrier
       -> render_fs_v5b or render_fs_v5d
          -> render_fs_v4
          -> render_fs_v3_surface
          -> render_fs_hd_v2
       -> _reset_to_proven_hd_planes
       -> _construct
       -> _coverage_missing
       -> polish_upper_frames
       -> soften_shared_rear_neck
       -> semantic palette/material resolution
  -> Farmer/contact-sheet validation and export
```

The route reaches the known-good art backend and retains 16×16 logical directional frames, a 16×64 Shirt atlas, Scale 2, `BodyPosition (0,32)`, binary alpha, native Farmer arms, and `SleeveColors`.

### Exact files and functions that presently own decisions

| Responsibility | Current file/function | V3 assessment |
|---|---|---|
| Family bundles and autonomous choice | `generator/autonomous_recovery/concept_engine.py::FAMILIES`, `ORDER`, `concept_for` | Upstream source of anatomy today. Must be replaced by versioned architecture, intent, fit, and component data—not extended as another monolith. |
| Basic semantic checks | `concept_engine.py::semantic_errors` | Reusable shell, but currently checks only broad conflicts, IDs, and custom-sleeve prohibition. Insufficient for physical validity. |
| Pairwise difference | `concept_engine.py::structural_difference` | Useful anti-convergence starting point. Must compare resolved canonical models and Farmer results, not strings alone. |
| Retry loop | `concept_engine.py::generate_recovery_concepts` and `tools/generate_autonomous_generator_recovery.py` | Reusable attempt policy. Stage-keyed determinism and rejection provenance are missing. |
| Carrier selection | `generator/autonomous_recovery/adapter.py::_carrier` | Reusable capability evidence. Replace family-index tables with a versioned carrier-capability registry. |
| Current architecture and pixels | `adapter.py::_construct` | It mixes garment anatomy with logical-pixel coordinates. V3 moves anatomy upstream; renderer-facing coordinates remain in component/family compiler handlers. |
| Frozen high-detail base | `generator/renderers/fashionsense/hd_garment_v2.py::render_fs_hd_v2` | Freeze. |
| Surface topology | `generator/renderers/fashionsense/surface_v3.py::render_fs_v3_surface` | Freeze. |
| Article translation | `generator/renderers/fashionsense/article_v4.py::render_fs_v4` | Freeze. |
| Upper construction | `generator/renderers/fashionsense/upper_v5b.py::render_fs_v5b` | Freeze. Existing custom-Sleeves generation is not an approved V3 runtime path. |
| Extended construction | `generator/renderers/fashionsense/upper_v5d.py::render_fs_v5d` | Freeze. Its family helpers are carrier capabilities, not architecture definitions. |
| Shared polish | `generator/renderers/fashionsense/art_polish_v5e.py::polish_upper_frames`, `soften_shared_rear_neck` | Freeze. Premium-cardigan experiment helpers remain excluded. |
| Semantic material ramps | `generator/controlled_test/hd_adapter.py` and project palette specs | Preserve behavior through a supported adapter boundary; experimental render profiles do not enter V3. |
| Native sleeve contract | `generator/data/fashionsense/runtime_sleeve_contracts.json::NATIVE_ANIMATED_SLEEVES_V1` | Frozen runtime authority. Custom 32×64 Scale-2 Sleeves remain rejected. |
| Rarity renderer lanes | `generator/data/rarity_renderer_architecture.json` | Read-only input for this phase. V3 adds a budget interface without changing current balance or probabilities. |
| Flat controlled rasterizer | `generator/renderers/fashionsense/reference_grammar.py::render_controlled_garment` | Debug/research only; forbidden as production art. |

### Present architectural weaknesses

1. `FAMILIES` bundles architecture, material, palette, names, and compatible-looking prose in one Python record.
2. `concept_for` independently rolls strings rather than instantiating a physical component graph.
3. `directionalAuthorship` is descriptive text; it is not a projection of one garment.
4. `_construct` is both anatomy authority and pixel placement code.
5. Accepted recipes do not persist complete seed, schema, data digest, canonical graph, projections, or compiler provenance.
6. Physical attachment, continuity, occlusion, view legality, parameter bounds, and carrier capability are not centrally validated.

## 2. V2 → V3 migration map

### V2 findings that remain valid

- The audited current-code stage mapping and exact renderer route.
- The 19 imported V2 family definitions and inheritance relationships.
- The mapping to the existing 33-family reference-corpus grammar.
- Current carrier coverage and missing-family inventory.
- Material-before-palette ordering and the semantic palette-role system.
- The need for stable keyed sub-seeds and saved data digests.
- Attachment, origin/termination, visibility, continuity, hard-reject, pixel-survival, carrier, and runtime-safety checks.
- All work that can occur upstream without touching V5/HD.
- The polo material inconsistency as a data/configuration defect.

### V2 concepts changed by V3

| V2 assumption | V3 replacement |
|---|---|
| Neutral-flat placement is a required production stage between validation and directional modeling. | The canonical garment model is production truth. Directional projection operates directly on it. A semantic flat may be emitted afterward as optional debug output. |
| One combined architecture/generation pipeline. | Separate Architecture Authoring Mode and Normal Generation Mode. |
| Feature registry plus directional feature instances are sufficient. | A parented component graph is instantiated into one canonical garment object before directions exist. |
| Direction descriptions can be compiled independently. | Front/Right/Back/Left are deterministic projections of the same component instances and continuity relationships. |
| Real-reference inspection may appear in the generation workflow. | References are consulted only while authoring or repairing versioned architecture data. Normal rolls load data only. |
| Fit is one of several concept strings. | Fit is a reusable proportion profile resolved against architecture parameter ranges. |

### V2 concepts now obsolete

- Treating the neutral flat as normal-generation ground truth.
- Inspecting a real reference on every normal roll.
- Saving neutral-flat marks as required production recipe structure.
- Allowing `_construct` or any four independent direction descriptions to define physical anatomy.
- Sending the flat controlled rasterizer to production export.
- Using family names or palette differences as proof of structural diversity.

## 3. Architecture Authoring Mode

Architecture Authoring Mode is a gated data-authoring workflow used only to add or repair garment knowledge:

```text
real photo / technical flat
  -> extract physical construction
  -> map attachment and continuity onto neutral flat
  -> define reusable components and parent graph
  -> define family constraints and parameter ranges
  -> define direction visibility, wrap, and occlusion
  -> define compatible fit/material/component variants
  -> define pixel priorities and legal degradation
  -> schema + graph + flat + human review
  -> save a versioned architecture definition
```

### Neutral-flat role in authoring

The supplied flat schema exposes `neck_collar`, `opening_placket`, `chest_pocket_panel`, `waist_belt`, `hem`, and `rear_structure` across Front/Right/Back/Left. It is a review scaffold for:

- parent attachment;
- origin and termination;
- per-view visibility;
- wraparound handoffs;
- occlusion and compression;
- component priority.

It never supplies source coordinates to the renderer and is never copied into a garment sprite.

### Proposed versioned data layout

No files in this proposed layout are created by this planning task:

```text
specs/hybrid_garment_compiler/v3/
  manifest.json
  canonical_garment_model.schema.json
  generated_recipe.schema.json
  architecture_definitions.json
  component_definitions.json
  component_compatibility.json
  design_intents.json
  fit_profiles.json
  family_material_compatibility.json
  carrier_capabilities.json
  rarity_budget_interface.json
  projection_contract.json
  pixel_grammar_contract.json
```

`manifest.json` should pin schema `3.0.0`, source-study hashes, compiler compatibility, content hashes, provenance, and reference-only policy. An architecture revision must change its own version or digest. Existing accepted garments keep their pinned version.

### Review and validation path

1. JSON/schema validation.
2. Inheritance and component-graph cycle validation.
3. Mandatory-component and attachment validation.
4. Parameter-range and compatibility validation.
5. Projection fixtures for all four views.
6. Neutral-flat review for placement and continuity.
7. Pixel-priority feasibility review against a declared carrier, without rendering final art.
8. Human architecture approval.
9. Versioned publication; normal generation can then load it.

Reference files remain read-only and are not bundled in runtime or generated packs.

## 4. Normal Generation Mode

The complete normal ordering is:

```text
SEED
  -> RARITY
  -> GARMENT FAMILY
  -> LOAD VERSIONED ARCHITECTURE
  -> DESIGN INTENT
  -> FIT PROFILE
  -> COMPATIBLE COMPONENT VARIANTS
  -> MATERIAL
  -> CANONICAL GARMENT MODEL
  -> PHYSICAL VALIDITY CHECK
  -> PROJECT FRONT / RIGHT / BACK / LEFT
  -> OPTIONAL SEMANTIC FLAT DEBUG PREVIEW
  -> PIXEL-GRAMMAR COMPILER
  -> SEMANTIC PIXEL REGIONS
  -> PALETTE
  -> RARITY POLISH
  -> PROVEN V5/HD RENDERER
  -> FARMER COMPOSITE
  -> QUALITY + DIVERSITY GATE
  -> ACCEPT / REROLL
```

Normal generation loads no photo, technical flat, or reference sprite. It consumes immutable versioned architecture/component/intent/fit data. The semantic-flat emission can be disabled without changing the canonical recipe, projections, compilation, or raster output.

## 5. Canonical Garment Model

### Exact insertion point

Insert the canonical model builder after family architecture, design intent, fit, compatible component variants, and material have been resolved, and before physical validity or directional construction. It replaces the current `concept_for -> directionalAuthorship -> _construct` handoff.

### Proposed resolved shape

```json
{
  "schemaVersion": "3.0.0",
  "identity": {
    "family": "POLO_SHIRT",
    "subtype": "KNIT_POLO",
    "architectureRef": {"id": "POLO_SHIRT", "version": "3.0.0", "digest": "..."},
    "designIntent": "COASTAL_SPORT",
    "rarityBudgetProfile": "..."
  },
  "fit": {
    "profile": "UNISEX_REGULAR",
    "resolved": {"shoulder": "medium", "waistSuppression": "low", "length": "normal", "volume": "regular"}
  },
  "material": {"id": "PIQUE_KNIT", "behaviorVersion": "..."},
  "components": [
    {"instanceId": "body", "type": "BODY", "variant": "KNIT_SHIRT", "parent": null, "attachment": "torso", "parameters": {}},
    {"instanceId": "collar", "type": "COLLAR", "variant": "FOLDED_MEDIUM", "parent": "body", "attachment": "neckline", "parameters": {"depth": "shallow"}},
    {"instanceId": "placket", "type": "PLACKET", "variant": "SHORT", "parent": "body", "attachment": "front_opening", "parameters": {"start": "neckline", "end": "upper_chest"}}
  ],
  "relations": [
    {"type": "ATTACHED_TO", "from": "collar", "to": "body"},
    {"type": "TERMINATES_AT", "from": "placket", "value": "upper_chest"}
  ],
  "rearStructure": {"rearCollarBand": true, "rearOpening": false},
  "surfaceIntent": {"colorBlockTopology": "construction_following", "motifBudget": 0},
  "runtimeEnvelope": {"carrierCapability": "...", "nativeSleeves": true},
  "provenance": {"rootSeed": 0, "generationIndex": 0, "attempt": 0, "dataDigests": {}}
}
```

The required V3 fields—family, architecture version, design intent, fit, body, neck, opening, sleeves/armholes, hem, panels, pockets, rear structure, material, component parameters, attachments, and directional visibility—are represented as resolved components and constraints. Directional visibility is component policy at this stage, not pre-painted per-direction art.

### Mapping from current code

- `concept_engine.FAMILIES`: split into architecture references, design-intent pools, fit compatibility, carrier capability, material eligibility, and later palette eligibility.
- `concept_for`: becomes an orchestrator that returns a canonical model plus provenance, not prose directions.
- `adapter._construct`: split into component/pixel compiler handlers. It receives projected components and cannot decide whether the garment has a collar, placket, pocket, yoke, or belt.
- `directionalAuthorship`: replaced by projector output.
- Names/lore remain presentation metadata and never affect anatomy.

## 6. Component graph

Every component definition requires: ID and type; parent attachment region; compatible families and materials; allowed parameter ranges; directional visibility policy; wrap/continuity behavior; occlusion policy; pixel priority; silhouette impact; carrier capability; and legal degradation or hard rejection.

| Component | Normal attachment | Direction/continuity contract | Key compatibility constraint |
|---|---|---|---|
| `BODY` | root torso | Present in all views; owns safe envelope | Family-specific volume/length only |
| `COLLAR` | body neckline | Front mass, side depth, rear band as variant requires | Neckline and material stiffness compatible |
| `LAPEL` | collar/front opening | Full front, depth-only side, forbidden rear face | Requires tailored/opening topology |
| `HOOD` | rear neckline/shoulder | Front opening, side depth, rear mass | Requires hood-capable family/carrier |
| `SLEEVE` | armhole | Attached all views through declared native relationship | V1 defaults to native Farmer sleeves |
| `ARMHOLE` | body shoulder/side | Must remain readable in sleeveless views | Must agree with sleeve presence/absence |
| `OPENING` | body front | Front dominant; limited side edge; never copied to back | Must declare start/end and open/closed topology |
| `PLACKET` | opening | Front only unless edge depth is physically visible | Short/full length cannot exceed architecture range |
| `ZIPPER` | opening | Follows opening and terminates physically | Cannot become generic center trim |
| `BELT` | waist/body | Wraparound continuity required across all views | Requires valid waist anchor and handoffs |
| `POCKET` | body or panel | Visible only on attached panel; may compress/occlude | Size/count/placement family compatible |
| `YOKE` | upper body | Front/rear/shoulder wrap according to variant | Must join side shoulder when continuous |
| `WAISTBAND` | lower body edge | Continuous front/side/back/left termination | Material and family must support gathered/banded edge |
| `HEM` | body termination | Continuous but view-reconstructed | Must remain inside safe runtime envelope |
| `CUFF` | sleeve termination | Follows native sleeve relationship | Cannot be emitted as detached Shirt geometry |
| `REAR_PANEL` | body back | Back full; side handoff only where attached | Never copied from a front-only panel |
| `LINING` | inside opening/collar/hood | Visible only at exposed inner edges | Requires outer/inner layer topology |
| `RIBBING` | neck/cuff/waist/hem | Continuous around its owning termination | Knit/sweat/bomber-compatible materials |
| `STORM_FLAP` | upper shell | Front or rear mass with side continuation | Outerwear only; attachment cannot float |
| `VENT` | rear or side hem | Rear/side only and begins at hem | Tailored/coat-compatible termination |

Graph edges include `ATTACHED_TO`, `ORIGINATES_AT`, `TERMINATES_AT`, `WRAPS_WITH`, `OCCLUDES`, `LAYERED_OVER`, `LAYERED_UNDER`, and `MUST_ALIGN_WITH`. Components are chosen only from the loaded family's allowed graph. Random component soup is invalid.

## 7. Design Intent

Design Intent provides coherent intra-family variation after architecture lookup. It does not replace family anatomy.

Each versioned intent should declare:

- one dominant construction idea;
- at most one strong supporting idea;
- explicit avoid/conflict rules;
- eligible fit profiles;
- eligible component variants and parameter tendencies;
- eligible material classes;
- color-block topology tendencies, but no palette assignment;
- structural and surface budget costs.

Example:

```text
CARDIGAN + ACADEMIC
  dominant: wide V framing a clean inner shirt
  supporting: restrained ribbed edge
  prefers: regular or softly tapered fit
  avoids: heavy utility pockets, loud asymmetry, large motif

CARDIGAN + RELAXED_WEEKEND
  dominant: broad hanging open front
  supporting: integrated lower patch pockets
  prefers: boxy relaxed fit
  avoids: hard lapels and tailored waist suppression
```

Current `FAMILIES` tuples can seed initial intent candidates, but they must be normalized and reviewed. They are not automatically architecture truth. The current `designHierarchy` idea is reusable once it references component variants and parameters rather than concatenated strings.

## 8. Fit Profile system

Fit profiles are reusable proportion tendencies applied within architecture-owned ranges. Gender presentation never selects palette, material quality, or rarity.

Proposed initial profiles:

| Profile | Shoulder tendency | Waist suppression | Length | Volume |
|---|---|---|---|---|
| `MASC_RELAXED` | slightly broader | low | normal-to-long | relaxed |
| `MASC_TAILORED` | medium/balanced | low-to-medium | normal | regular/tapered |
| `FEM_FITTED` | narrow-to-medium | medium | normal-to-cropped | fitted |
| `FEM_RELAXED` | medium | low | normal/cropped | relaxed |
| `UNISEX_REGULAR` | medium | low | normal | regular |
| `UNISEX_BOXY` | medium | none | normal | boxy |
| `UNISEX_CROPPED` | medium | low | cropped within safe bounds | regular/boxy |

Each profile should resolve numeric or discrete values for shoulder scale, torso width distribution, waist suppression, body length, volume/ease, armhole relationship, and hem spread. The architecture definition owns allowed ranges; the profile supplies tendencies. The canonical model stores the resolved result, not just the profile label.

Existing male/unisex research informs proportions, layering, collars, and construction compatibility. It must not reduce masculine design to dark colors, broad shoulders, or generic jackets.

## 9. Directional projection

The projector is deterministic and coordinate-free. It takes the canonical graph and produces four semantic views. It does not rotate a sprite and does not make new design choices.

Each projected component instance should record:

```json
{
  "componentInstance": "placket",
  "direction": "right",
  "visibility": "HIDDEN",
  "representation": "NONE",
  "attachment": "front_opening",
  "continuityIncoming": null,
  "continuityOutgoing": null,
  "occludedBy": ["body_side_plane"],
  "pixelPriority": 2
}
```

Allowed visibility states: `FULL`, `COMPRESSED`, `DEPTH_ONLY`, `EDGE_ONLY`, `OCCLUDED`, `HIDDEN`, and `FORBIDDEN`. Left and right are projected independently when pockets, overlap, ties, closures, or asymmetry differ.

Projection invariants include:

- polo placket: front only; side may show collar depth, never a full placket; rear collar band only;
- lapel: full front, side depth, no rear lapel face;
- hood: front opening, side depth, rear mass;
- sailor collar: front V, compressed shoulder depth, mandatory rear panel;
- belt/waistband/rib hem/yoke: declared wrap handoffs must connect across views;
- pocket: remains attached to its owning panel and disappears only by declared occlusion;
- rear opening: false unless the architecture explicitly owns one.

Reusable current code is limited to `DIRECTION_ORDER`, corpus directional research, carrier masks, and selected V5 direction-specific construction helpers. Current prose `directionalAuthorship` is not reusable as authority.

## 10. Semantic flat debug output

### Implementation location and contract

A future debug-only module should sit at a boundary such as:

```text
generator/hybrid_v3/debug/semantic_flat.py
  emit_semantic_flat(canonical_model, directional_projection, flat_schema)
```

It consumes the canonical model plus projector output and visualizes semantic attachment zones, component IDs, continuity groups, visibility states, and priority. Its output is never read by the pixel compiler.

### Exact V3 position

```text
CANONICAL GARMENT MODEL
  -> PHYSICAL VALIDITY
  -> DIRECTIONAL PROJECTION
  -> [OPTIONAL SEMANTIC FLAT DEBUG EMISSION]
  -> PIXEL-GRAMMAR COMPILATION
```

This updates V2: the flat is primarily an Architecture Authoring bridge and secondarily a normal-generation diagnostic. It is not production ground truth.

### Artifact isolation

- wrong in canonical model: architecture, intent, fit, or component-selection bug;
- canonical correct, projection/flat wrong: projection bug;
- projection correct, pixel-grammar map wrong: compiler bug;
- pixel map correct, final sprite wrong: renderer/palette/export bug.

The structure-only `reference_grammar.render_controlled_garment` must not be repurposed for final art.

## 11. Pixel-grammar compilation

The compiler translates projected components into the existing backend's semantic signals, masks, fabric assignments, carrier parameters, and construction operations.

```text
projected component instances
  -> verify carrier capabilities
  -> prioritize mandatory identity signals
  -> choose component compiler handlers
  -> emit coordinate-free semantic region intent
  -> lower to carrier-owned logical masks/signals
  -> invoke frozen V5/HD route
```

### Boundary with existing code

- The canonical model and projection contain no renderer coordinates.
- A compiler registry maps component variants/family compositions to existing V5B/V5D capabilities.
- Logical pixel coordinates currently in `adapter._construct` may remain in compiler handlers, because they are renderer-facing translation—not garment selection.
- `_carrier` becomes a lookup against `carrier_capabilities.json`, with required and forbidden capabilities.
- Existing `upper_v5d` helpers such as cardigan, waistcoat, utility vest, field jacket, blazer, period, tunic, and other construction routines are evidence of pixel capabilities only. They do not license a family until its V3 architecture and runtime constraints exist.
- Pixel priority drops optional buttons/motifs before mandatory collar, opening, armhole, hem, rear carrier, or continuity signals. If mandatory identity cannot survive 16×16, reject the candidate.

The frozen route remains:

```text
render_fs_hd_v2
  -> render_fs_v3_surface
  -> render_fs_v4
  -> render_fs_v5b
  -> render_fs_v5d when required
  -> reset named surface to proven HD planes where the proven route requires it
  -> compiled garment construction
  -> polish_upper_frames
  -> soften_shared_rear_neck
  -> semantic material/palette adapter
```

This trace distinguishes **semantic selection** from **final RGBA realization**. V3 selects the material, palette story, active color roles, and rarity-polish profile upstream in the required order. The compiler passes those decisions into the frozen route. The existing adapter may realize the already-selected role ramps into final RGB values after shared shade-role polish; that late conversion is not a second palette roll and may not change architecture or color topology. Likewise, V3 rarity polish is a semantic sophistication/finishing profile supplied before rendering, while universal post-V5E cleanup remains a frozen technical art stage.

No V3 module may call premium-cardigan experimental profiles or export the flat role grid.

## 12. Material + palette

Preserve:

- `specs/palettes/material_color_behavior.json`
- `specs/palettes/color_roles.json`
- `specs/palettes/palette_stories.json`
- the existing semantic ramp adapter and material-aware shade behavior.

Ordering is mandatory:

```text
family architecture
  -> intent
  -> fit
  -> compatible components
  -> compatible material
  -> canonical model
  -> validity/projection
  -> pixel regions and color-block topology
  -> palette story
  -> rarity polish
  -> render
```

Architecture constrains eligible materials; material affects stiffness, fold behavior, seam prominence, ribbing, value spacing, highlight behavior, and bulk. It never invents anatomy. Palette fills only semantic roles required by compiled regions and cannot rescue weak structure. Color topology follows components: yokes and bands wrap, front inner layers compress at sides and disappear at back, and rear fields are not mirrored front layouts.

Material and palette IDs must be separately seeded and versioned. Masculine/unisex fit never narrows palette eligibility. Rarity never hard-codes hue families.

## 13. Rarity architecture budget

Rarity rolls first and supplies a budget/capability interface. This plan does not change probabilities, current route balance, or active production rarity definitions.

The interface should expose:

- eligible family and architecture-variant classes;
- maximum construction cost;
- maximum optional component count;
- maximum layer count;
- allowed fit/proportion deviation;
- surface-system budget;
- asymmetry budget;
- signature-hook/state-behavior allowance;
- renderer/runtime capability lane;
- mandatory art competence and quality floor.

Initial semantic interpretation follows V3 study data:

- **Common:** simple architecture and surface budget; clean finished art mandatory.
- **Uncommon:** broader construction, layering, material, and fit variation.
- **Rare:** premium but restrained architecture/proportion/finish; not spectacle.
- **Legendary:** signature architecture/silhouette/identity with a larger coherent budget.

Mandatory identity components are never removed to fit rarity. If a renderer lane cannot represent them, that family/variant is ineligible and must be rerolled. The existing numeric examples in the study schema are interface defaults for later review, not a probability or production-balance change in this plan.

## 14. Determinism + provenance

Use stable, keyed stage seeds rather than random-call order:

```text
rootSeed / generationIndex / retryAttempt
  / rarity
  / family
  / architectureVariant
  / designIntent
  / fitProfile
  / component:<slot-or-instance>
  / componentParameter:<key>
  / material
  / surface
  / palette
  / rarityPolish
```

A cryptographic keyed derivation such as SHA-256 should turn these paths into deterministic integer seeds. Adding a palette choice must not perturb family or component selection.

Every accepted and rejected candidate should save:

- root seed, generation index, attempt, and derived stage seeds;
- generator/compiler version and feature-flag state;
- rarity and budget-profile ID/version;
- family and architecture ID/version/digest/inheritance chain;
- design intent ID/version;
- fit-profile ID/version plus resolved proportions;
- selected component IDs/versions/parameters and complete graph relations;
- material behavior ID/version;
- canonical garment model;
- four directional projections;
- optional semantic-flat artifact path/digest when emitted;
- pixel-grammar compiler/carrier IDs and versions;
- compression/degradation decisions and omitted optional features;
- semantic regions and construction signals;
- palette story/roles and version;
- rarity-polish profile;
- frozen renderer route and runtime contract IDs;
- validation metrics, Farmer gate, pairwise diversity result, and rejection reasons.

Same seed plus identical versioned-data and compiler digests must reproduce the same semantic recipe. Pixel equality additionally requires identical frozen backend and export versions.

## 15. Physical validity

Validation occurs on the canonical graph before projection and again on projections before pixel compilation.

### Canonical graph checks

1. Architecture inheritance and component graph are acyclic.
2. Every mandatory component exists exactly as required.
3. Every component parent and attachment region exists.
4. Origins, terminations, parameter values, counts, and sizes lie inside family ranges.
5. Family, material, fit, intent, and component variants are mutually compatible.
6. Opening, placket, zipper, lapel, collar, inner layer, and rear structure agree.
7. Sleeves and armholes agree; V1 runtime output uses `NATIVE_ANIMATED_SLEEVES_V1` unless separately approved.
8. Silhouette effects remain inside the declared safe runtime envelope.
9. No rigid lower geometry is introduced over moving legs.
10. Budget use counts only optional sophistication; mandatory identity cannot be dropped.

### Projection checks

1. Every projected feature is permitted in that direction.
2. Front-only opening/lapel/placket faces do not appear on the back.
3. Every wraparound continuity group has correct side handoffs.
4. Occlusion is explicit; disappearing components are not accidental.
5. Left/right asymmetry follows one attached component, not independent improvisation.
6. Rear identity components exist where required: collar band, hood mass, sailor panel, yoke, seam, vent, or intentionally plain field.
7. Priority/compression preserves mandatory article signals.
8. No unattached line, alpha island, collar spill, or unsupported top-edge band survives.
9. Carrier capabilities cover every projected silhouette and layer operation.

Hard rejection is preferable to decoration-based repair or silent fallback.

## 16. Quality + diversity gate

### Debug-stage gate

Validation records the first failing representation:

1. canonical model coherence;
2. directional projection and optional flat consistency;
3. pixel-grammar component/priority map;
4. final isolated sprite;
5. Farmer composite.

### Farmer-scale authority

Front, Right, Back, and Left Farmer composites are authoritative. Reject when:

- article identity is unclear;
- a side is a squeezed front or a back copies front-only construction;
- required continuity disappears;
- the palette carries identity instead of architecture;
- details work only enlarged;
- malformed neckline, detached component, unsafe coverage, or runtime-contract regression appears;
- it becomes another fitted top, short jacket, or dark torso with a center accent despite semantic differences.

### Anti-convergence

Compare resolved models and worn results on high-impact axes—silhouette/volume, collar/neckline, opening, layering, hem/waist—and medium axes—pockets/panels, sleeve relationship, side construction, rear carrier, color-block topology. Require at least three meaningful structural differences from close accepted garments and at least one difference in silhouette/volume or opening/layering. Palette, name, trim, buttons, motif, and shading do not count.

### Retry

Use a stable `retryAttempt` sub-seed. On failure, reroll design intent/component choices rather than endlessly polishing the same sprite. Retain the current maximum-five-attempt policy unless separately reviewed. If no candidate passes, report an unfilled slot; do not weaken the gate.

Static success does not imply runtime promotion. Fashion Sense runtime evidence remains separately tracked.

## 17. Existing carrier coverage

The table distinguishes architecture knowledge, compiler availability, and renderer code. A V5D helper is not by itself a production-ready V3 family.

| V3/V2 family | Current carrier evidence | V3 readiness after data/compiler work |
|---|---|---|
| `T_SHIRT` | V5B plain tee | Strong immediate candidate. |
| `POLO_SHIRT` | V5B structured-shirt/polo-like route | Candidate after material correction and short-placket projection fixture. |
| `HENLEY` | General V5 shirt capability | Architecture exists; dedicated collarless short-placket compiler absent. |
| `BUTTON_SHIRT` | V5B structured shirt | Strong candidate; needs full opening/yoke compiler contract. |
| `OVERSHIRT` | Structured-shirt carrier | Needs heavier volume, layer depth, pocket, and yoke compiler. |
| `SWEATSHIRT` | V5B sweater/pullover | Strong immediate candidate. |
| `HOODIE` | Proven coordinated hoodie research/route | Capability-gated; must use the proven hoodie architecture and runtime status, never generic Shirt-only improvisation. |
| `SWEATER` | V5D knit | Strong immediate candidate. |
| `SWEATER_VEST` | V5B vest | Candidate with sleeveless armhole and no-floating-side-band hard checks. |
| `CARDIGAN` | V5D cardigan | Strong immediate candidate. |
| `WAISTCOAT` | V5D/V5B vest | Strong candidate with tailored armhole/rear rules. |
| `BOMBER_JACKET` | V5B variants | Needs dedicated rounded-shell/rib compiler and proof. |
| `VARSITY_JACKET` | V5B-style bomber capability | Needs contrast sleeve/body topology using native sleeves and dedicated validation. |
| `WORK_JACKET` | V5D work shell | Strong immediate candidate. |
| `DENIM_JACKET` | Work-shell carrier is plausible | Needs denim collar/yoke/pocket/waistband compiler. |
| `BLAZER` | V5D blazer | Strong candidate with lapel/side-depth/rear-vent projection. |
| `SAILOR_TOP` | V5B sailor | Strong candidate; rear panel mandatory. |
| `WRAP_TOP` | General upper carrier; no proven physical wrap compiler | Architecture exists but remains gated until overlap termination is demonstrated. |
| `TRENCH_COAT` | No safe long upper carrier | Unsupported. Known moving-leg/rigid Shirt geometry risk. |

### Existing 33-grammar corpus and known gaps

- `RELAXED_TEE`, `BUTTON_SHIRT`, `SWEATER`, cardigan, waistcoat, blazer, sailor, and related fit variants can map to the families above.
- `TURTLENECK` can be a sweater plus an explicit high/rolled collar component if it remains structurally distinct.
- `CROPPED_BOMBER` maps to bomber plus a safe cropped fit.
- `DOUBLE_BREASTED_FORMAL_TOP` can become a blazer/opening variant after projection/compiler support.
- `TRUE_HOODIE` maps to the coordinated hoodie capability, subject to its runtime gate.
- Track jacket has current V5D field-shell carrier usage but **no V2/V3 architecture definition**; do not alias it to bomber or field jacket.
- Utility vest, field jacket, period garment, and tunic have V5D construction helper evidence (`_utility_vest`, `_field_jacket`, `_period`, `_tunic`) but lack complete versioned V3 architectures and normal compilers.
- Moto jacket, tabard, traditional offset closure, ceremonial formal top, and physically grounded streetwear statement families lack complete architectures and/or carriers.
- Officer/military helpers exist, but a named costume/theme helper is not a substitute for a general officer architecture.
- Runtime-safe trench/long coat remains unsupported.

First implementation should include only families with both approved architecture data and a safe carrier capability. Unsupported families are skipped, not flattened through `STANDARD_JACKET`.

## 18. `POLO_KNIT` material inconsistency

### Exact cause and location

`generator/autonomous_recovery/concept_engine.py::FAMILIES["POLO_KNIT"]` currently hard-codes:

```python
material="WOVEN_SHIRT"
carrier="V5B_STRUCTURED_SHIRT"
```

The material value is inconsistent with the imported architecture, where `POLO_SHIRT` inherits the T-shirt/knit body and the V3 canonical example uses `material = PIQUE_KNIT`. The carrier can still be a valid pixel capability if it expresses the correct collar and short placket; the material defect is independent of renderer choice.

### Proposed correction

During later implementation—not in this planning task:

1. Remove the fixed material from the Python family bundle as that bundle is retired.
2. Put compatible knit materials in `family_material_compatibility.json` for `POLO_SHIRT`.
3. Prefer an approved `PIQUE_KNIT` behavior if added through material-spec review; otherwise use an existing compatible `COTTON_TEE`/`KNIT` behavior rather than silently inventing one.
4. Add hard tests: short placket ends at upper chest; no full rear opening; side has collar depth but no full placket; rear has a shallow collar band and uninterrupted knit field.
5. Keep the V5/HD renderer unchanged.

This is a data/configuration correction candidate, not a shading, anchor, or rasterizer problem.

## 19. Minimal implementation sequence

Each checkpoint is independently testable and requires separate implementation approval.

1. **Freeze baseline:** capture current autonomous route, renderer/runtime contract IDs, and golden diagnostics. No behavior change.
2. **Install V3 data namespace:** add manifest and schemas with hashes/provenance. Loader only; feature flag off.
3. **Normalize architecture data:** import the approved 19 family definitions and inheritance into versioned records. Validate cycles and parents.
4. **Build component registry:** definitions, attachment regions, compatibility, ranges, visibility, continuity, and priority. Recipe-only tests.
5. **Build Architecture Authoring tooling:** neutral-flat authoring/debug output and review validator. It cannot export Fashion Sense art.
6. **Add Design Intent data:** normalize a small reviewed intent set for already-supported families; validate dominant/supporting/avoid coherence.
7. **Add Fit Profiles:** resolve profiles to architecture-bounded proportions; no palette linkage.
8. **Build canonical-model builder:** deterministic component selection and complete provenance. Golden JSON fixtures only.
9. **Build physical validator:** graph, attachment, compatibility, runtime envelope, and mandatory identity tests, including deliberately invalid fixtures.
10. **Build directional projector:** four coordinate-free views plus continuity tests for polo, cardigan, sweater vest, blazer, sailor, and belt-like wrap features.
11. **Add optional semantic-flat diagnostics:** confirm disabling them produces identical canonical/projection/compiler inputs.
12. **Add carrier-capability registry and pixel-grammar interface:** first map a very small set of proven families. Do not alter renderer modules.
13. **Adapt material/palette ordering:** material eligibility before canonical completion; palette after compiled regions. Fix polo only after explicit approval.
14. **Add rarity-budget interface:** consume current rarity result without changing its probabilities or production balance.
15. **Add deterministic persistence/retry logs:** accepted and rejected recipe manifests with version digests.
16. **End-to-end recipe-only proof:** no clothing output; verify same seed/data reproduces canonical graph and projections.
17. **Controlled render proof after a new approval:** a separately authorized small set through the frozen backend and Farmer gate.
18. **Production migration only after visual/runtime approval:** enable family by family; never all at once.

## 20. Rollback / safety boundaries

1. Introduce a single opt-in gate such as `HYBRID_GARMENT_COMPILER_V3_ENABLED=false`; the existing generator remains the default until approved.
2. Place V3 loaders, canonical models, projection, validation, and compilation in a separate upstream namespace. Do not edit frozen renderer behavior.
3. Keep all V3 outputs in isolated experimental directories until promotion. Never overwrite production packs or accepted recipes.
4. Pin every recipe to architecture/component/intent/fit/compiler versions and digests. Never silently reinterpret an old recipe with new data.
5. A V3 failure must reject or fall back to the explicitly selected legacy route before rendering; it must not partially mix V3 semantics with legacy anatomy.
6. Do not call `reference_grammar.render_controlled_garment`, premium-cardigan experimental profiles, rejected custom Sleeves, or unsafe long-Shirt geometry.
7. Preserve `NATIVE_ANIMATED_SLEEVES_V1`, Scale 2, `BodyPosition (0,32)`, direction mapping, coverage checks, binary alpha, and Fashion Sense 7.5.0 contracts.
8. Add golden stage-trace and carrier-input tests around the frozen backend. A V3-only change that alters backend behavior outside declared semantic inputs is a regression.
9. Keep source/reference material read-only and out of generated packages.
10. Rollback is disabling the V3 feature gate and selecting the existing route; it requires no renderer or data reset.
11. Architecture revisions are additive/versioned. Do not rewrite a released architecture record in place.
12. No rarity rebalance, clothing generation, production migration, or V5/HD modification is authorized by this plan.

The recommended implementation boundary is therefore upstream and reversible: V3 owns architecture knowledge, canonical physical composition, projection, validation, and semantic compilation; the proven V5/HD stack continues to own pixel execution.
