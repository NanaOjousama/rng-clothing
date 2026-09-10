# Garment Architecture V2 Integration Plan

Status: **PLAN ONLY — NOT IMPLEMENTED**  
Target architecture schema: `2.0.0`  
Neutral-flat schema: `1.0`  
Renderer policy: **proven V5/HD backend frozen**

## 1. Authority, scope, and safety

This plan adopts the supplied V2.1 study as the physical-garment authority:

- `RNG_Clothing_Codex_Architecture_Study_v2_1/RNG_CLOTHING_CODEX_ARCHITECTURE_STUDY_GUIDE_V2.md`
- `RNG_Clothing_Codex_Architecture_Study_v2_1/garment_architecture_and_generator_schema_v2.json`
- `RNG_Clothing_Codex_Architecture_Study_v2_1/REAL_TO_PIXEL_TRANSLATION_FLAT.png`
- `RNG_Clothing_Codex_Architecture_Study_v2_1/real_to_pixel_translation_flat_schema.json`

The architecture records and their linked real-world/technical references are construction truth. The neutral flat is only a semantic placement scaffold. Neither the flat nor any linked/reference artwork is a sprite source. Normal generation must load versioned project data and must not require a model to remember garment anatomy or load reference images.

This phase does not copy the source files into production data, change generator behavior, generate clothing, change rarity balance, or modify a renderer. Future implementation may normalize the supplied data into project-owned versioned specifications while preserving provenance and reference-only restrictions.

## 2. Current-state diagnosis

The recent autonomous recovery route correctly reaches the frozen backend:

`autonomous concept -> V5 carrier -> render_fs_hd_v2 -> V3 -> V4 -> V5B -> optional V5D -> reset carrier surface -> article construction -> polish_upper_frames -> soften_shared_rear_neck -> palette/material resolution`

Its weakness is upstream of rendering:

1. `generator/autonomous_recovery/concept_engine.py` keeps family anatomy in Python `FAMILIES` bundles rather than a versioned architecture definition.
2. `concept_for` rolls structure, material, palette, and name together. V2 requires structure and physical validity before material, and palette after material/semantic-region planning.
3. `directionalAuthorship` is descriptive text, not a validated feature graph with attachment, visibility, occlusion, continuity, and termination.
4. `semantic_errors` checks naming and broad incompatibilities, but not physical attachment, wrap continuity, inheritance, pixel-priority survival, or family hard rejects.
5. `generator/autonomous_recovery/adapter.py::_construct` currently owns both garment anatomy and logical-pixel placement. Architecture must move into data; a thin carrier compiler may continue to own renderer-facing placement.
6. The root recovery seed is a constant, but accepted recipes do not yet save the root seed, per-stage sub-seeds, architecture version/digest, flat-schema version, rarity-polish profile, or complete renderer-route contract.
7. The old controlled/flat rasterizer remains research-only and is already excluded from the recovery route. It must remain excluded.

## 3. Target pipeline and mapping from existing stages

| Target stage | Existing source to preserve or adapt | Planned responsibility |
|---|---|---|
| 1. Rarity lane | `generator/data/rarity_renderer_architecture.json` | Select an architecture budget and eligible renderer lane. Keep current balance values unchanged until a separate rarity review. |
| 2. Family roll | `autonomous_recovery.FAMILIES` / old V3 archetype roll | Replace hard-coded anatomy bundles with IDs from a versioned family registry filtered by rarity and carrier capability. |
| 3. Architecture lookup | `specs/reference_corpus/garment_grammars.json` | Load V2 architecture, resolve inheritance/composition, and retain old corpus grammar as supplementary design knowledge—not physical authority. |
| 4. Design-concept roll | V3 Design Concept Engine and autonomous axes | Roll compatible variants inside the resolved family. Structural options come from architecture data; V3 theme/composition remains a decorative/surface input. |
| 5. Fit profile | current `fitIntent`/silhouette strings | Create a separate fit object: presentation tendency plus fitted/regular/relaxed/boxy/cropped/longline/tapered proportions. Fit never selects palette or gender restrictions. |
| 6. Construction-feature roll | current collar/opening/hem/detail pools | Roll only features permitted by the resolved architecture, material eligibility, fit, carrier, and rarity budget. |
| 7. Physical validity | current `semantic_errors` and V5 recipe validators | Validate attachment, start/end, structural role, visibility, continuity, family hard rejects, material compatibility, safe runtime envelope, and carrier capability. |
| **7.5 Neutral-flat translation** | **new semantic stage using flat schema 1.0** | **Place validated features by attachment zone, per-view visibility, continuity group, occlusion, and pixel priority. It creates no raster pixels.** |
| 8. Directional model | current `directionalAuthorship` plus corpus direction rules | Compile the flat placement plan into structured Front/Right/Back/Left feature instances. Direction is reconstruction, not rotation. |
| 9. Material behavior | `specs/palettes/material_color_behavior.json` | Roll a compatible material after construction. Apply stiffness, value-spacing intent, fold/rib/seam/highlight rules to semantic regions. |
| 10. Pixel-priority compression | currently implicit in `_construct` | Retain mandatory family signals first, then supporting construction, then optional decoration. Record every omitted/degraded feature and reject if a hard identity feature cannot survive. |
| 11. Semantic region map | current construction signals/fabric assignments | Produce coordinate-free regions and shade/material roles for the carrier compiler. |
| 12. Palette story | `specs/palettes/color_roles.json` and `palette_stories.json` | Roll after architecture, material, compression, and color-block topology. Activate only roles required by the recipe. |
| 13. Rarity polish | V3 rarity budgets plus post-V5E polish policy | Constrain sophistication and optional architecture/surface budget. Do not change base art competence or use hue as rarity. |
| 14. Proven render | `render_fs_hd_v2`, V3, V4, V5B, V5D, `polish_upper_frames`, `soften_shared_rear_neck` | Frozen execution backend. A compiler selects a proven carrier and translates semantic regions; it must not invent anatomy. |
| 15–17. Farmer gate/retry | current preview and diversity validation | Composite Front/Right/Back/Left, check article/physical read, compare accepted designs, accept or reroll the concept (maximum attempt policy remains explicit). |

### Exact position of the neutral-flat stage

```text
LOAD + RESOLVE VERSIONED ARCHITECTURE
  -> ROLL CONCEPT / FIT / COMPATIBLE FEATURES
  -> VALIDATE PHYSICAL FEATURE GRAPH
  -> BUILD NEUTRAL_FLAT_PLACEMENT_PLAN       <-- flat schema 1.0
  -> VALIDATE CROSS-VIEW CONTINUITY
  -> BUILD SEMANTIC_DIRECTIONAL_MODEL       <-- Front/Right/Back/Left
  -> APPLY MATERIAL BEHAVIOR
  -> COMPRESS BY 16x16 PIXEL PRIORITY
  -> BUILD SEMANTIC REGION MAP
  -> PALETTE / RARITY POLISH
  -> COMPILE TO PROVEN V5/HD CARRIER
```

The flat therefore sits after architecture lookup/composition and physical feature selection, but before semantic directional rendering. It is an intermediate logical plan, not an image pasted into a sprite and not a coordinate map for the HD renderer.

## 4. Versioned project-data layout proposed for implementation

No files in this layout are created by this planning task. The proposed layout is:

```text
specs/garment_architecture/v2/
  manifest.json
  garment_architectures.json
  architecture_components.json
  feature_registry.json
  neutral_flat_schema.json
  family_aliases.json
  family_material_compatibility.json
  carrier_capabilities.json
  recipe_schema.json
```

`manifest.json` should record architecture version `2.0.0`, flat schema `1.0`, source-study version/path, import timestamp, content hashes, reference-only policy, and compatibility version for the compiler. Architecture inheritance must be resolved from data (`POLO_SHIRT -> T_SHIRT`, `CARDIGAN -> SWEATER`, etc.), with cycle and missing-parent checks.

`feature_registry.json` should define each feature independently of a family:

- structural/decorative classification;
- attachment region and required parent;
- physical origin and termination semantics;
- allowed/required/forbidden views;
- wrap/continuity group and view-to-view handoff;
- occlusion policy;
- material and fit compatibility;
- pixel priority and legal degradation fallback;
- required carrier capability;
- hard rejection conditions.

`recipe_schema.json` should require version and seed provenance, resolved architecture, selected feature instances, flat placement plan, directional model, material, compression decisions, semantic regions, palette, rarity polish, carrier, and renderer route. It must forbid renderer coordinates in the semantic recipe.

## 5. Existing-family mapping to V2 architecture

### Current autonomous-recovery families

| Current ID | V2 architecture | Mapping status | Existing carrier/adapter status |
|---|---|---|---|
| `FITTED_TEE` | `T_SHIRT` | Direct fit variant | V5B plain tee; viable. |
| `TEXTURED_KNIT` | `SWEATER` | Direct material/surface variant | V5D knit carrier; viable. |
| `SWEATER_VEST` | `SWEATER_VEST` | Direct | V5B vest; viable with the new floating-side-band hard reject and current top-overhang repair. |
| `OPEN_CARDIGAN` | `CARDIGAN` | Direct open-front variant | V5D cardigan; viable. |
| `OPEN_CASUAL_SHIRT` | `BUTTON_SHIRT` or `OVERSHIRT` | Partial. Needs an explicit open-woven-shell variant/component so it does not become a cardigan. | V5B structured-shirt carrier exists; architecture record needs extension. |
| `CREWNECK_SWEATSHIRT` | `SWEATSHIRT` | Direct | V5B sweater/pullover carrier; viable. |
| `WORK_JACKET` | `WORK_JACKET` | Direct | V5D work-shell carrier; viable. |
| `FORMAL_WAISTCOAT` | `WAISTCOAT` | Direct | V5D/V5B vest carrier; viable. |
| `TRACK_JACKET` | none exact | Missing V2 architecture. Do not alias to bomber solely because both are short jackets. | V5D field-shell carrier can carry current art, but needs a real track-jacket definition. |
| `FITTED_BLAZER` | `BLAZER` | Direct fit variant | V5D blazer carrier; viable. |
| `SAILOR_TOP` | `SAILOR_TOP` | Direct | V5B sailor carrier; viable. |
| `POLO_KNIT` | `POLO_SHIRT` | Rename/alias. Current `WOVEN_SHIRT` material default is inconsistent with the V2 knit/T-shirt base and must be corrected during implementation. | V5B structured/polo-like carrier available. |

### Remaining reference-corpus grammar IDs

| Existing IDs | V2 mapping | Status |
|---|---|---|
| `RELAXED_TEE` | `T_SHIRT` relaxed fit | Covered. |
| `HENLEY` | `HENLEY` | Covered; autonomous carrier adapter not yet exposed. |
| `BUTTON_SHIRT` | `BUTTON_SHIRT` | Covered; carrier exists. |
| `OVERSHIRT` | `OVERSHIRT` | Covered; dedicated architecture compiler still needed. |
| `TURTLENECK` | `SWEATER` + high/rolled-neck component | Partial; add an explicit high-neck component or family if its topology cannot be expressed as a sweater variant. |
| `UTILITY_VEST` | none | Missing family/component architecture. Do not collapse into `WAISTCOAT`. |
| `TRUE_HOODIE` | `HOODIE` | Covered architecturally; coordinated Shirt/Hat runtime route exists separately and must remain capability-gated. |
| `CROPPED_BOMBER` | `BOMBER_JACKET` cropped fit | Covered; dedicated autonomous adapter/runtime specimen still needed. |
| `VARSITY_JACKET` | `VARSITY_JACKET` | Covered; requires contrast native sleeve topology and dedicated adapter validation. |
| `FIELD_JACKET` | none exact | Missing field-jacket architecture; may inherit work/structured outerwear components but must retain its own guarded/yoke/pocket logic. |
| `MOTO_JACKET` | none | Missing. |
| `CROPPED_FASHION_JACKET` | none | Missing or should remain a concept label until a physically specific architecture is defined. |
| `DOUBLE_BREASTED_FORMAL_TOP` | `BLAZER` + double-breasted opening | Partial; add opening/quarter rules. |
| `PERIOD_COAT_TOP` | none | Missing bounded period coat-top definition and carrier proof. |
| `OFFICER_UNIFORM_TOP` | none | Missing officer/uniform architecture. |
| `WRAP_TOP` | `WRAP_TOP` | Covered; needs a dedicated safe adapter rather than a decorative diagonal. |
| `BELTED_TUNIC` | none | Missing tunic architecture and safe bounded carrier rules. |
| `TABARD_TOP` | none | Missing. |
| `TRADITIONAL_OFFSET_CLOSURE_TOP` | none | Missing. |
| `CEREMONIAL_FORMAL_TOP` | none | Missing. |
| `STREETWEAR_BLOCK_TOP` | none | Missing; must be based on physical shell/layer architecture, not block decoration alone. |

### New V2 families not fully represented today

- `DENIM_JACKET`: can likely compose from the proven work-jacket carrier, but needs its point collar, chest-pocket/yoke/waistband feature graph and directional adapter.
- `TRENCH_COAT`: no safe current carrier. Long rigid Shirt-layer geometry is known unsafe; keep unavailable until a separate runtime architecture exists.

## 6. Neutral-flat placement by architecture family

The table below maps real structural features to the flat through **attachment region + view visibility + continuity + pixel priority**. It does not prescribe sprite coordinates.

| V2 family | Flat attachment regions | View visibility and continuity | Priority order |
|---|---|---|---|
| `T_SHIRT` | `neck_collar`, `hem` | Neck band front/side/back; simple hem continuous; no opening. | neckline > shoulder/sleeve relationship > hem > optional cue |
| `POLO_SHIRT` | `neck_collar`, `opening_placket`, `hem` | Two collar leaves front, one fold per side, shallow rear band; placket front-only and ends at upper chest. | collar > short placket > sleeves/hem > buttons |
| `HENLEY` | `neck_collar`, `opening_placket`, `hem` | Collarless neck all views; short placket front-only; plain back. | neck opening > short placket > fit/hem |
| `BUTTON_SHIRT` | `neck_collar`, `opening_placket`, `chest_pocket_panel`, `hem`, `rear_structure` | Full front placket; collar has side depth/rear band; pocket may compress at side; rear yoke replaces opening. | collar > full opening > hem/yoke > pocket |
| `OVERSHIRT` | same as button shirt | Same continuity with greater side depth, larger attached pocket panels, heavier hem, broad rear yoke. | volume > collar/opening > large pockets > hem weight |
| `SWEATSHIRT` | `neck_collar`, `hem`, optional `rear_structure` | Rib neck and hem recur across views; rear remains quiet; no opening. | pullover volume > rib terminations > neckline |
| `HOODIE` | `neck_collar`, optional `opening_placket`, `chest_pocket_panel`, `hem`, `rear_structure` | Hood opening front, hood depth sides, hood mass back; pouch front compresses at side; ribs continue. | hood > silhouette > pouch/zip > drawstrings |
| `SWEATER` | `neck_collar`, `hem`, optional `chest_pocket_panel` | Knit neck/cuffs/hem continuous; texture simplifies at sides/back. | neckline > knit mass > rib terminations > one texture system |
| `SWEATER_VEST` | `neck_collar`, `hem`, `rear_structure` plus armhole attachment | Cut-in armholes and narrow shoulder straps visible front/side/back; no floating side band; optional shirt is a separate layer. | armholes > neck binding > hem > inner shirt |
| `CARDIGAN` | `neck_collar`, `opening_placket`, optional `chest_pocket_panel`, `hem`, `rear_structure` | Two front knit edges frame inner layer; one edge/depth at side; opening disappears into unified knit back. | open topology > soft edge/collar > layering > ribs |
| `WAISTCOAT` | `neck_collar`, `opening_placket`, `chest_pocket_panel`, `hem`, `rear_structure` plus armholes | Tailored V/opening front; shaped armhole side; rear fabric/adjuster replaces buttons. | tailored V > armholes > opening > waist shape |
| `BOMBER_JACKET` | `neck_collar`, `opening_placket`, `chest_pocket_panel`, `hem`, `rear_structure` | Zip/opening front; rounded shell depth side; rib collar/cuff/waist continuous; rounded clean back. | rib waist > rounded volume > collar/opening |
| `VARSITY_JACKET` | bomber zones plus sleeve/body boundary | Contrast sleeves wrap front/side/back; striped ribs continuous; snaps front-only; logo never structural. | sleeve contrast > ribs > snap opening |
| `WORK_JACKET` | `neck_collar`, `opening_placket`, `chest_pocket_panel`, `hem`, `rear_structure` | Firm opening/pockets front; one attached pocket/side seam side; rear yoke and durable plane back. | pockets/panels > collar > firm hem |
| `DENIM_JACKET` | work-jacket zones | Point collar and opening front; yoke/waistband wrap; side seam/tabs compress; rear yoke/panels mandatory. | collar > yoke/pockets > opening > waistband |
| `BLAZER` | `neck_collar`, `opening_placket`, `chest_pocket_panel`, `hem`, `rear_structure` | Lapel faces front; side shows collar/lapel depth and waist; back uses collar/seam/vent, never lapel faces. | lapels > tailored silhouette > opening > rear seam/vent |
| `TRENCH_COAT` | all six zones | Lapels/opening front; belt is one continuity group through all views; storm flap spans upper front/side/back; long hem and cuff straps recur. | long silhouette > lapels > belt continuity > storm yoke |
| `SAILOR_TOP` | `neck_collar`, `hem`, `rear_structure` | Broad V/collar front; collar compresses over side shoulders; square/tapered rear panel mandatory. | collar geometry > rear panel > V inset |
| `WRAP_TOP` | `opening_placket`, optional `waist_belt`, `hem`, optional `rear_structure` | Two front panels form one dominant diagonal; closure terminates at side; belt/tie reaches back only if physically wrapping. | diagonal overlap > waist closure > silhouette |

## 7. Physical-validity checks

The V2 validator should reject before carrier selection when any of these fail:

1. **Inheritance:** parent exists; graph is acyclic; overrides do not remove mandatory parent identity without an explicit subtraction such as sweater vest sleeves.
2. **Attachment:** every feature names a valid zone and parent panel; no floating trim, pocket, belt, collar, or armhole edge.
3. **Origin/termination:** plackets, zippers, lapels, overlaps, seams, and trims have physically plausible start/end semantics.
4. **Visibility:** every view instance is allowed by its feature type; front plackets/lapel faces cannot be copied to back.
5. **Continuity:** wrap features declare a continuity group and required view handoffs. Belt, yoke, rib hem, sleeve band, and storm flap cannot silently vanish.
6. **Occlusion:** pockets and inner layers may compress/disappear only with an explicit view/occlusion rule.
7. **Family hard rejects:** enforce all V2 hard rejects as data. The sweater-vest `floating top-edge band` rule directly covers the recently repaired side artifact.
8. **Fit compatibility:** selected length/volume/waist/shoulder variants remain valid for the base formula and safe carrier envelope.
9. **Material compatibility:** knit ribs cannot be assigned as denim construction; tailored lapels cannot use sweatshirt behavior without an explicit hybrid architecture.
10. **Pixel survival:** every mandatory identity feature has a compression representation at 16×16. If it cannot survive, reject rather than substitute decoration.
11. **Carrier capability:** the selected carrier supports required silhouette, native sleeve relationship, layers, and direction-specific topology.
12. **Runtime safety:** no unsafe leg overlap, rejected custom Sleeves contract, unsupported layer category, or unproven long geometry.

## 8. Directional visibility and attachment representation

Each selected feature should become a `FeatureInstance` resembling:

```json
{
  "featureId": "SHORT_CENTER_PLACKET",
  "classification": "STRUCTURAL",
  "attachmentRegion": "opening_placket",
  "parent": "front_torso_panel",
  "origin": "neckline_center",
  "termination": "upper_chest",
  "views": {
    "front": "FULL",
    "right": "OCCLUDED_OR_NONE",
    "back": "FORBIDDEN",
    "left": "OCCLUDED_OR_NONE"
  },
  "continuityGroup": null,
  "pixelPriority": 2,
  "degradation": "omit_buttons_before_shortening_placket"
}
```

Continuity groups should describe logical connections (`BELT_WRAP_1`, `REAR_YOKE_1`, `RIB_HEM_1`) rather than shared coordinates. The directional model then records whether a feature is full, compressed, edge-only, occluded, reconstructed, or forbidden in each view. Left/right may differ when opening, pocket, tie, or overlap construction is asymmetric.

## 9. Material and palette integration order

The existing semantic color system is retained:

- `specs/palettes/material_color_behavior.json`
- `specs/palettes/color_roles.json`
- `specs/palettes/palette_stories.json`

Changes are orchestration-only:

1. Architecture defines eligible materials; the concept rolls material only after the directional physical model exists.
2. Material behavior annotates region stiffness, edge softness, fold/rib/seam treatment, contrast spacing, and highlight policy.
3. Pixel compression uses the architecture priority plus material cues; material never adds noise.
4. The semantic region map declares required fabric/color roles.
5. Palette story is rolled last among design inputs and fills only required roles.
6. The existing material/palette adapter converts roles to shade ramps for the frozen backend.

The current autonomous defaults requiring correction during implementation include `POLO_KNIT -> WOVEN_SHIRT`; V2 defines a T-shirt/knit base. Family eligibility should be a data list, not one fixed material per family.

## 10. Seed and determinism storage

Use stable keyed sub-seeds, preferably the existing V3 SHA-256 pattern rather than relying on call order:

```text
rootSeed
  / rarity
  / family
  / architectureVariant
  / fit
  / feature:<feature-group>
  / material
  / surface
  / palette
  / rarityPolish
  / retry:<attempt>
```

Every candidate—accepted or rejected—should save:

- root seed, generation index, attempt, and each derived sub-seed;
- generator version;
- architecture schema version and content digest;
- neutral-flat schema version and content digest;
- family and fully resolved inheritance chain;
- exact selected options and physical feature graph;
- directional/flat placement plan and compression decisions;
- material, palette, rarity-polish profile;
- carrier/compiler version and frozen renderer route;
- validation result and rejection reasons.

The same seed plus identical versioned-data digests must reproduce the same semantic recipe. Raster reproducibility additionally requires the same compiler and renderer versions.

## 11. Rarity architecture-budget interface (balance unchanged)

Rarity remains first, but this plan does not assign or rebalance numeric limits. A future data object should expose:

- eligible family/variant classes;
- mandatory architecture features (never removed by rarity);
- maximum optional structural systems;
- maximum layering/components;
- permitted silhouette deviation;
- surface-system budget;
- asymmetry/signature-hook budget;
- renderer/layer capability lane.

Common still receives competent art. Rare still means premium/restrained rather than spectacle. Legendary remains signature architecture. Palette and material families remain rarity-neutral. If the selected renderer lane cannot represent all mandatory architecture signals—especially a Common vanilla lane—the family/variant is ineligible for that lane; the generator must not flatten it into a misleading article.

## 12. Integration possible without renderer changes

All of the following can be implemented upstream or in adapters while keeping `render_fs_hd_v2`, V3 surface rendering, V4, V5B, V5D, `polish_upper_frames`, the FS contract, and native sleeves unchanged:

- versioned architecture loader, inheritance resolver, and schema validator;
- family aliases and carrier-capability registry;
- deterministic concept/fit/feature/material/palette rolls;
- physical feature graph and neutral-flat placement plan;
- continuity and hard-reject validation;
- directional semantic model and pixel-priority compressor;
- semantic recipe persistence and retry logs;
- a thin compiler from semantic regions/features into existing carrier signals/fabric assignments;
- Farmer/comparison validation and anti-convergence gates.

The existing `_construct` branches should eventually become compiler implementations selected by feature/capability data. Their renderer-facing logical placement may remain in adapter code, but the decisions to create a collar, placket, yoke, belt, armhole, or pocket must come from the versioned recipe. Carrier placeholder surface art may still be reset to permanent HD planes; architecture-owned regions are then applied. Normal generation must never call `reference_grammar.render_controlled_garment` or premium-cardigan experiment profiles.

## 13. Missing or incomplete carriers

| Architecture | Gap |
|---|---|
| `HENLEY`, `BUTTON_SHIRT`, `OVERSHIRT` | Existing V5 carriers exist, but no V2-driven autonomous compiler path is exposed yet. |
| `HOODIE` | Proven coordinated architecture exists, but the project data still marks final runtime confirmation/promotion as pending; keep capability-gated. |
| `BOMBER_JACKET`, `VARSITY_JACKET` | V5B variants exist; need dedicated V2 feature compilers and Farmer/runtime checks. |
| `DENIM_JACKET` | Work-shell carrier is plausible; dedicated denim yoke/pocket/waistband compiler absent. |
| `WRAP_TOP` | Existing experimental/old carrier concepts are not sufficient proof of a physically terminating wrap. |
| `TRACK_JACKET` | Current autonomous family has no V2 architecture definition. Add data before retaining it. |
| `UTILITY_VEST`, `FIELD_JACKET`, `MOTO_JACKET` | Existing project vocabulary lacks corresponding V2 records. |
| `TRENCH_COAT` | No runtime-safe long carrier; explicitly unavailable. |
| period/officer/tunic/tabard/traditional/ceremonial/street statement families | Architecture definitions and/or safe carriers are missing. Do not infer them from names or force them through `STANDARD_JACKET`. |

## 14. Proposed implementation sequence after review

1. Import/normalize V2 architecture and flat schemas into the versioned data layout with hashes and provenance.
2. Add schema, inheritance, alias, and feature-registry validators; no rendering.
3. Define the V2 semantic recipe and stable seed/sub-seed manifest.
4. Build physical-validity and neutral-flat placement/continuity validators.
5. Build family-to-material and family-to-carrier capability data.
6. Replace the autonomous Python anatomy bundles with V2 data lookup and compatible rolls.
7. Refactor the current article adapter into a thin V2 recipe compiler while preserving every frozen renderer/runtime stage.
8. Run recipe-only deterministic fixtures and invalid-architecture rejection tests.
9. Only after those pass, authorize a small controlled render proof and Farmer gate in a separate task.

## 15. Review decisions required before implementation

1. Approve the proposed canonical paths and whether V2 source data is copied verbatim with provenance or normalized into component records plus a retained source snapshot.
2. Approve aliases (`FITTED_TEE -> T_SHIRT`, `POLO_KNIT -> POLO_SHIRT`, etc.).
3. Decide whether `OPEN_CASUAL_SHIRT`, `TRACK_JACKET`, `UTILITY_VEST`, and `FIELD_JACKET` receive new architecture records before migration.
4. Decide whether hoodie remains excluded from the first V2 implementation despite its existing coordinated runtime research.
5. Keep numeric rarity architecture budgets deferred to a separate calibration review, as required.

No clothing generation or renderer modification should begin until these decisions and this plan are approved.
