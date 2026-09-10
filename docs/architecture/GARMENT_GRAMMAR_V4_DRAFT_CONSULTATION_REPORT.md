# Garment Grammar V4 Draft — Consultation and Integration Recommendation

Status: study and planning only. No generator, renderer, art, palette, or production files were changed.

## Executive opinion

The V4 draft identifies the project's current failure mode more accurately than the earlier attempts: the main bottleneck is no longer raster quality, Fashion Sense anchoring, or a lack of garment names. It is the loss of structural ownership between canonical garment construction, directional projection, component compilation, shared polish, and palette application.

My recommendation is to **approve V4 as an architectural direction, but not merge or implement its draft JSON literally**. The three JSON files are useful requirements sketches, not yet complete executable contracts. V4 should be developed as a reversible experimental compiler lane above the frozen V5/HD backend, carrying forward the strongest V3 systems rather than replacing them.

The best short description is:

> Keep the V3 garment brain and the V5/HD hand; replace the fragile middle translation layer with an ownership-aware shape and pixel-grammar compiler.

## Material reviewed

The entire draft folder was inspected:

- `docs/research/RNG_CLOTHING_GRAMMAR_REBUILD_AUDIT.md`
- `specs/garment_grammar_v4/architecture_grammar_v4.json`
- `specs/garment_grammar_v4/art_grammar_v4.json`
- `specs/garment_grammar_v4/palette_grammar_v4.json`

The proposal was compared against the current project, especially:

- the active autonomous-recovery concept and adapter route;
- Hybrid V3 canonical models, validation, projection, carrier registry, and Phase 2 compiler;
- the 33-family reference-corpus grammar library;
- the existing HD, V3, V4, V5B, V5D, and V5E art stages;
- current semantic material and palette specifications;
- the Coastal Knit Polo micro-fix failure audit;
- the established Fashion Sense/native-sleeve runtime contract.

## Current project reality

The normal recovery path remains:

```text
autonomous design concept
-> existing V5 carrier
-> render_fs_hd_v2
-> render_fs_v3_surface
-> render_fs_v4
-> render_fs_v5b
-> render_fs_v5d where required
-> reset to proven HD planes
-> article construction adapter
-> polish_upper_frames
-> soften_shared_rear_neck
-> semantic palette/material adapter
-> Farmer preview / Fashion Sense export
```

Hybrid V3 remains an isolated experimental route and its feature flag defaults to `false`. It currently models six families: T-shirt, polo, sweater vest, cardigan, blazer, and sailor top. The broader reference corpus defines 33 semantic grammars. The V4 draft proposes 39 family identities across seven groups.

The frozen renderer and runtime hashes still match `HYBRID_V3_BASELINE_FREEZE.md`. There is no evidence that the proven backend was overwritten or that V4 needs a new rasterizer.

## Where V4 is correct

### 1. It locates the failure at the ownership boundary

The Coastal Polo audit is strong evidence. Requested geometry changes either never became alpha, were expressed only as role/color changes, or were overwritten by later polish. This is exactly the failure V4 describes.

Current component painting is constrained by inherited carrier alpha. The component compiler often uses literal cell recipes, while the shared polish stage can rewrite those cells without knowing which component owns them. A semantic recipe may therefore be correct while the final Farmer sprite remains generic or unchanged.

### 2. It separates topology from shading

V4's proposed order is sound:

1. silhouette/topology;
2. semantic regions;
3. material/form shading;
4. surface design;
5. non-destructive cleanup.

This is materially better than asking one late polish function to infer garment anatomy from an already-painted carrier. Alpha geometry, component identity, shade roles, and decoration are different kinds of information and need different owners.

### 3. It upgrades directional projection from visibility to shape intent

V3's visibility values are necessary but insufficient. `FULL`, `COMPRESSED`, or `DEPTH_ONLY` does not say what a side collar, armhole, lapel depth, rear panel, or opening termination should look like.

The V4 fields—attachment anchor, extent, depth, orientation, occlusion, safe footprint, cluster topology, and termination—are the right kind of extension. They let four views remain projections of one garment without independently improvising four sprites.

### 4. It treats silhouette as legitimate compiler output

The current `_paint`-style behavior cannot reliably add alpha outside a carrier's existing opaque cells. That makes real cut-in armholes, boxiness, cropped edges, collar depth, and other structural distinctions difficult or impossible. A bounded topology stage must be allowed to add and remove cells inside a validated safe envelope.

### 5. It strengthens pixel-cluster discipline

Connectivity, supported overhangs, deliberate deep-shadow anchors, continuous garment mass, edge termination, and top-row contamination are more meaningful than raw color-count or changed-cell metrics. These rules directly address the vest and polo failures already seen.

### 6. It correctly keeps gender separate from palette

Fit, tailoring, proportion, and styling tendencies are the correct controls. Masculine/unisex clothing should not be reduced to dark military palettes, and feminine fit should not become a separate color database.

### 7. It preserves the proven runtime contract

The draft correctly avoids reopening native sleeves, Fashion Sense scale/anchor assumptions, or long geometry over moving legs. Those are established runtime boundaries and should remain frozen.

## Where the V4 draft is not yet implementation-ready

### 1. The JSON is descriptive, not operational

The draft enumerates 39 families, 25 component types, nine relation types, ownership stages, and palette principles. It does not yet define enough detail to compile them safely:

- stable component variant IDs;
- component parameters and ranges;
- family inheritance and mandatory identity rules;
- normalized shape templates;
- add/remove alpha operations;
- attachment support requirements;
- collision and occlusion resolution;
- degradation order at 16×16;
- per-direction safe envelopes;
- carrier capability mappings;
- schema digests and migration rules;
- deterministic seed stages;
- validation severity and failure codes.

Importing these files directly would recreate ambiguity inside a larger vocabulary.

### 2. It risks duplicating existing vocabularies

The project already has V3 IDs and a 33-grammar corpus. V4 introduces related but not identical names, such as `T_SHIRT` versus fitted/regular/relaxed tees and `POLO_SHIRT` versus `POLO_KNIT`. A migration table is required before any new source becomes authoritative.

Fit variants should not automatically become separate families. For example, fitted, regular, and relaxed tees may be one architecture with fit/design-intent variants unless their topology genuinely differs at Farmer scale.

### 3. Safe alpha modification is underspecified

Allowing the shape grammar to alter alpha is necessary, but dangerous without explicit limits. The compiler needs per-direction safe zones derived from the proven Shirt envelope, Farmer occlusion, native arm motion, and Fashion Sense anchoring. Added cells must be supported by a parent component and remain connected unless a separate runtime layer is intentionally declared.

V4 should not initially cover hoods, long coat geometry, custom sleeves, or accessories. Those introduce different Fashion Sense layer contracts.

### 4. Protected cells alone are not enough

A flat protected-cell set prevents some overwrites but does not explain who owns a cell, why it exists, or which later stage may modify it. The compiler needs an ownership ledger containing at least:

- component owner;
- topology role;
- semantic region;
- shade-role authority;
- protection level;
- allowed later mutations;
- originating stage.

Conflict resolution must be deterministic and validated, not order-dependent.

### 5. Palette work is partly a separate risk stream

The V4 palette diagnosis is valid. Current blending is ordinary RGB arithmetic, and only one of 30 project palette stories explicitly supplies `SecondaryFabricLight`; current fallback behavior can borrow the primary light and weaken fabric separation.

However, topology and palette modernization should not be changed simultaneously in the first proof. Otherwise a failure will be difficult to localize. First establish ownership and structural survival; then add independent secondary ramps and a perceptual working space with deterministic gamut mapping and snapshot tests.

Coverage percentages should remain guidance rather than hard universal thresholds. Small collars, inner layers, and trim cannot all satisfy the same role percentages without encouraging noise.

### 6. Human-gate semantics need tightening

The V3 Phase 2 artifacts could pass static checks while later failing human review. A generated preview should therefore be labeled `PENDING_HUMAN_REVIEW`, not `PASS`, until reviewed. Metrics may reject obvious defects, but must never certify appeal or garment identity.

### 7. Rarity terminology should stay out of the first compiler proof

The draft's `simple_common`-style surface budget mixes construction complexity with rarity language. The first V4 implementation should use neutral complexity budgets. Rarity may later constrain the available architecture budget, but must not become an art-quality shortcut.

## Preserve, replace, and defer

### Preserve unchanged

- canonical garment model concept;
- deterministic keyed seeds and saved provenance;
- architecture version/digest references;
- physical validator and fail-closed compilation;
- one-model-to-four-directions projection principle;
- carrier capability registry;
- semantic-flat and stage-trace diagnostics;
- Farmer composite as visual authority;
- the 33-family research corpus as design knowledge;
- semantic palette roles and material behaviors;
- native Farmer sleeves and SleeveColors;
- 16×16 logical Shirt frames, Scale 2, `BodyPosition (0,32)`, and binary alpha;
- frozen V5/HD/V3/V4/V5B/V5D renderer stages.

### Replace inside the experimental compiler

- literal family-specific coordinate patches as the primary construction model;
- carrier alpha as an immutable silhouette ceiling;
- visibility-only projection for structural components;
- inherited carrier shading as final garment form;
- global destructive polish after component construction;
- named one-off cleanup branches such as `coastal_cleanup`;
- metric-derived visual approval.

### Defer

- production enablement;
- all-family migration;
- rarity art escalation or probability changes;
- Legendary/Mythic behavior;
- custom sleeve atlases;
- hood/hat/accessory coordination;
- long coats or geometry over moving legs;
- automatic reference ingestion;
- full perceptual-palette replacement until topology ownership is proven.

## Recommended V4 data architecture

Create a new versioned experimental namespace rather than overwriting V3:

```text
specs/garment_grammar_v4/
  manifest.json
  family_architectures.json
  component_definitions.json
  component_shape_variants.json
  attachment_and_continuity.json
  directional_projection_rules.json
  safe_envelopes.json
  ownership_contract.json
  material_form_grammar.json
  palette_topology.json
  quality_gates.json
  v3_v4_migration_map.json
```

Each renderer-facing component shape variant should define semantic, parameterized information—not a copied garment sprite:

- stable variant and component IDs;
- compatible families, fit profiles, materials, and design intents;
- normalized attachment anchors;
- direction and projected visibility requirements;
- permitted footprint zone;
- alpha additions/removals;
- support/adjacency rules;
- semantic region labels;
- form-plane and edge hints;
- protected structural cells/roles;
- minimum identity cells;
- degradation order;
- connectivity expectations.

Logical coordinates may exist in the renderer-facing shape library because a 16×16 compiler eventually needs masks. They must be parameterized templates owned by the project, not hard-coded complete garments or copied reference pixels.

## Recommended compiler boundary

The safe integration route is:

```text
validated canonical garment
-> V4 directional shape intents
-> safe-envelope topology compiler
-> per-cell ownership ledger
-> semantic component regions
-> material/form shade roles
-> garment construction edges
-> restrained surface design
-> non-destructive cleanup
-> semantic palette resolution
-> frozen Fashion Sense export/runtime contract
```

The existing renderer can still provide proven base planes, lighting language, material cues, and carriers. It should not be allowed to re-infer anatomy after V4 owns it.

Initially, preserve `polish_upper_frames` unchanged and place it behind a wrapper:

1. run it on a clone or on unowned base regions;
2. merge back only cells the ownership contract permits it to change;
3. reject any attempted alpha or structural-role overwrite;
4. save the rejected merge diff in the stage trace.

This avoids changing the frozen backend while proving whether an ownership-aware boundary solves the actual problem.

## Suggested phased integration plan

### Phase 0 — Contract and migration design

- keep V4 disabled by default;
- turn the draft into validated JSON Schemas;
- map all V3 and reference-corpus IDs to V4 identities;
- decide which differences are families, fit variants, or design intents;
- define safe envelopes and ownership precedence;
- add version/digest/seed requirements;
- define rollback and artifact naming.

No clothing rendering in this phase.

### Phase 1 — Ownership and diagnostic infrastructure

- implement the per-cell ownership ledger;
- add stage-by-stage alpha, region, role, and final-color diffs;
- make shared polish non-destructive through the merge wrapper;
- add assertions that requested structural changes survive every later stage;
- preserve the current renderer hashes.

Use synthetic fixtures only. Do not judge fashion quality yet.

### Phase 2 — Golden structural regressions

Implement only three known failure-sensitive component paths:

- polo collar and short front-only placket;
- sweater-vest cut-in armhole and inner-layer exposure;
- sailor collar with mandatory rear panel.

These cover partial opening, subtractive/additive silhouette work, side topology, and rear-only construction. A change must be visible in the final logical frame and Farmer composite, not only in a role map.

### Phase 3 — Controlled family proof

Render a small controlled set spanning:

- tee baseline;
- polo knit;
- sweater vest;
- sailor top;
- button shirt as the first new woven architecture.

Do not expand if any pair collapses at Farmer scale. Cardigan and blazer should follow only after open-layer and lapel ownership contracts are explicitly defined.

### Phase 4 — Material and palette topology

- give secondary fabrics independent light/shadow ramps;
- add explicit value-topology metadata;
- introduce a tested perceptual working space if deterministic conversion and gamut handling are stable;
- validate palette application without changing topology ownership;
- keep palette family independent of gender and rarity.

### Phase 5 — Gradual architecture expansion

Migrate families in topology groups, not all 39 at once:

1. jersey/woven basics;
2. knit and open layers;
3. tailored/formal;
4. safe short outerwear;
5. specialty upper garments.

Unsupported architecture must fail compilation rather than fall back to `STANDARD_JACKET`.

### Phase 6 — Production consideration

Only after static human review and live Farmer testing should V4 become eligible for an opt-in production path. The current autonomous recovery route remains the rollback path until then.

## Required acceptance gates

### Structural

- mandatory components have owned, surviving pixels in required directions;
- forbidden components have none;
- silhouette edits remain inside per-direction safe envelopes;
- no detached alpha islands, unsupported top-edge pixels, or accidental bands;
- wraparound features satisfy continuity rules;
- side/back views preserve article identity without copying the front.

### Stage survival

- every requested structural edit is present at the topology stage;
- semantic regions agree with topology;
- later stages do not remove or recolor protected identity cells improperly;
- before/after sources and hashes are saved;
- any overwrite attempt is reported as a failure, not silently merged.

### Visual

- Farmer Front/Right/Back/Left composites are mandatory;
- gameplay-scale identity must be obvious without the garment name;
- a garment remains pending until human review;
- enlarged contact sheets cannot override a weak gameplay read;
- structural diversity, not palette, determines distinctness.

### Runtime

- native animated sleeves remain the default;
- no custom sleeve atlas is introduced;
- no component may appear near the feet;
- Fashion Sense 7.5.0 contract stays unchanged;
- live verification follows static approval and is never inferred from previews.

## Family coverage recommendation

The 39-family list is a useful coverage target, not an implementation backlog to execute wholesale. Before normalization, classify each proposed identity as one of:

- distinct topology family;
- fit/proportion variant;
- design intent;
- surface/material variant;
- currently runtime-unsupported.

Likely examples:

- fitted/regular/relaxed tee: primarily fit variants unless Farmer-scale topology proves otherwise;
- open/button cardigan: likely distinct opening variants within a cardigan architecture;
- fitted/relaxed blazer: fit/design-intent variants;
- pullover/zip hoodie: meaningful opening and layer variants, but deferred because of coordinated hood runtime layers;
- field/moto/period tops: potentially distinct families, but only after carrier and safe-envelope support exists.

This normalization will prevent the project from mistaking a longer list of names for real visual diversity.

## Specific technical recommendations

1. **Introduce a topology API separate from `_paint`.** It must support validated alpha additions and removals, parent support, attachment checks, and ownership recording.
2. **Do not edit `polish_upper_frames` first.** Wrap and constrain its output. Modify the frozen function only if the wrapper proves insufficient and a separate reviewed task authorizes it.
3. **Replace `coastal_cleanup` with component variant data.** A named garment cleanup is evidence that a missing shape rule was patched at the wrong level.
4. **Make stage diffs first-class artifacts.** Save canonical, projection, topology, semantic regions, material roles, pre/post-polish, palette, final atlas, and Farmer composites.
5. **Add a visual-change contract for micro-fixes.** If a requested collar move has zero alpha displacement, the system must say so. Role-only changes cannot be reported as silhouette fixes.
6. **Populate independent secondary ramps before perceptual color migration.** This is the lowest-risk palette correction. Treat OKLCH/OKLab as a later, separately testable implementation.
7. **Consolidate existing art knowledge instead of discarding it.** The HD art grammar, V5C2 quality grammar, V5D masculine grammar, reference corpus, and palette research already contain useful principles. V4 should normalize them into authoritative compiler data, not duplicate them in another prose layer.
8. **Keep complexity orthogonal to quality.** Every output receives clean form and lighting; complexity budgets only control architecture/surface scope.

## Principal risks

| Risk | Consequence | Mitigation |
|---|---|---|
| Draft JSON treated as complete schema | Ambiguous generation and another patch layer | Schema-first Phase 0 with migration map |
| Alpha additions exceed runtime-safe body envelope | Clipping or rigid geometry | Per-direction safe zones and Farmer/runtime fixtures |
| Ownership implemented as only a protected set | Hidden overwrite conflicts | Per-cell owner and mutation policy ledger |
| New palette math lands with topology rewrite | Failures become hard to localize | Separate palette phase |
| All 39 identities implemented at once | Shallow, unreviewable family support | Topology-group migration |
| Legacy polish remains globally authoritative | Structural work disappears late | Clone/merge wrapper with overwrite rejection |
| Static QC auto-approves clothing | Repeat of Polo false confidence | `PENDING_HUMAN_REVIEW` state |
| V4 becomes a new production renderer | Regression and duplicated engines | Experimental upstream compiler only |

## Final recommendation

Proceed with V4, but under these conditions:

1. treat the draft as an architectural specification to refine, not executable source data;
2. preserve V3 canonical modeling, determinism, validation, projection, and fail-closed carrier selection;
3. preserve the V5/HD renderer and Fashion Sense runtime contract unchanged;
4. build an explicit shape/topology compiler and per-cell ownership ledger;
5. constrain legacy polish through a non-destructive merge boundary;
6. prove the solution first on the Polo, Sweater Vest, and Sailor regression cases;
7. separate palette modernization from the first topology proof;
8. keep V4 disabled and reversible until Farmer-scale and live runtime review pass.

The V4 draft is the strongest architectural diagnosis currently available in the project. Its central thesis should be adopted. Its present data files should not yet be installed as authoritative production grammar. With the staged plan above, the project can improve real garment differentiation without discarding the substantial canonical-model, research, renderer, palette, and runtime work that already functions.
