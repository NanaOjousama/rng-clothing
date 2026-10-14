# RNG Clothing Feasibility Project

**Project navigation:** [Workspace map and cleanup notes](docs/PROJECT_LAYOUT.md) · [Current milestone](CURRENT_STATE.md) · [Claude operating rules](CLAUDE.md) · [LoRA research plan](experiments/lora_sdxl_research/PLAN_phase4.md).

## Generator V4 multi-garment experiment

V4 adds an article-translation layer above the frozen Generator V3 design system. The currently proven Fashion Sense set is `FITTED_SHIRT`, `SWEATER_TOP`, `VEST_TOP` (vest over an inner shirt), `CROPPED_JACKET`, and `SHORT_OUTERWEAR`. True long coats remain experimental and are rejected from generated output until lower-body animation/layering is proven. See `reports/V4_CAPABILITY_AUDIT.md` and `reports/V4_MULTI_GARMENT_REPORT.md`.

## V4.5 extended-garment audit

V4.5 adds isolated capability fixtures for Pants, a short Skirt, Footwear, and a Mantle without modifying frozen V4. All remain runtime-EXPERIMENTAL until `reports/V45_RUNTIME_TEST_CHECKLIST.md` is completed. A Coat-Tail companion is diagnostic-only and true Long Outerwear remains NOT READY. See `reports/V45_EXTENDED_GARMENT_REPORT.md`.

This is an isolated experiment for testing procedural Stardew Valley clothing generation.

It is NOT part of TFWR runtime yet.

## Goal

Determine whether we can reliably generate original Stardew-compatible clothing using:

fashion reference images
→ style traits
→ semantic garment recipes
→ logical pixel construction
→ valid native Stardew or Fashion Sense assets

The project should prioritize proven Stardew/Fashion Sense structures over inventing a custom clothing renderer.

## Core Rules

- Do not modify TFWR.
- Do not add runtime dependencies to TFWR.
- Do not build the full RNG reward system yet.
- Do not generate conventional high-resolution artwork and shrink it.
- Do not use bilinear, bicubic, Lanczos, smoothing, or anti-aliasing.
- Final game sprites must be constructed on the actual logical pixel grid required by the target format.
- Reference images are for STYLE ANALYSIS only.
- Do not copy reference outfits pixel-for-pixel.
- Prefer existing Stardew/Fashion Sense rendering, layering, animation, and equipment systems.
- Reuse APIs/contracts/helpers where appropriate instead of recreating framework behavior.
- Clearly distinguish confirmed, likely, and untested capabilities.

## Reference Folders

### `references/lifestyle/`

Normal non-themed clothing inspiration.

"Lifestyle" is a clothing category, NOT a rarity.

Examples:
- everyday outfits
- casual clothes
- jackets
- sweaters
- workwear
- streetwear
- dresses
- skirts
- seasonal everyday clothing

### `references/style-profiles/`

Collections that represent a recognizable fashion language.

Example:

`references/style-profiles/SailorStyles/`

These references should be analyzed for reusable traits such as:

- silhouette
- proportions
- layering
- sleeve shape
- collars
- garment length
- fit
- palette tendencies
- motif density
- accessories
- asymmetry
- detail density

### `references/benchmark/male clothing/`

Dedicated masculine-fashion benchmark corpus. Non-`Mixed_` packs are the primary masculine design evidence. Folders whose normalized name begins with `Mixed_` are secondary and require per-garment visual classification: feminine examples may teach general pixel technique, color blocking, and surface composition, but may not set masculine article or silhouette grammar automatically.

Masculine fashion must retain casual, workwear, farmwear, streetwear, hoodie, knit, formal, waistcoat, outerwear, military, period, fantasy, armor, tunic/tabard, and uniform variety where supported. It must not collapse into dark colors, broad shoulders, or generic jackets. See `specs/MALE_CLOTHING_BENCHMARK_RULES.md` for the permanent routing and quality policy.

### `references/sun/`

Future Sun-themed cosmetic references.

These are not needed for the first feasibility test unless specifically requested.

## Templates

### `templates/vanilla/`

Real Stardew Valley 1.6 clothing templates, formats, or clean working examples.

### `templates/fashionsense/`

Real current Fashion Sense templates, formats, or clean working examples.

Do not invent template dimensions. Verify them against current documentation/source.

## Specs

### `specs/CAPABILITIES.md`

Technical findings about:
- native Stardew clothing
- Fashion Sense
- tailoring
- random cosmetic selection
- frame sizes
- anchors
- layers
- animations
- automation feasibility

### `specs/STYLE_PROFILE.md`

Reusable clothing/style vocabulary extracted from reference images.

### `specs/PIXEL_RULES.md`

Hard technical rules for crisp logical-pixel sprite construction.

## Generator

`generator/`

Contains the completed V1 and V2 deterministic vanilla-shirt experiments and the optional Fashion Sense Generator V3 design-variety experiment. V3 adds coordinate-free design concepts, surface composition, motifs, trim, patterns, directional topology, and batch-diversity gates above the preserved V2 construction foundation. It does not replace either the vanilla backend or the permanent FS-HD construction/art grammar.

The first frozen-V3 external profile test is the six-garment `AoTInspired`
collection. It curates existing V3 systems; generation never reads the visual
reference files. Generate and validate it with:

```bash
python3 tools/generate_aot_v3_collection.py
python3 tools/validate_aot_v3_collection.py
```

The project still does not implement the reward economy, pants, hats, or TFWR integration. See `generator/README.md` for V1/V2/V3 generation and validation commands.

### Generator V5A experimental unified garments

V5A adds coordinate-free adapters for Dress, One-Piece/Costume, and Bounded Long Outerwear over the frozen V3/V4 systems. Generate and statically validate the exact nine-item diagnostic collection with:

```bash
python3 tools/generate_v5a_unified_garments.py
python3 tools/validate_generator_v5a.py
```

The installable test pack is `test-packs/fashionsense/RNG-Clothing-V5A-Unified-Garments/`. All V5A items remain `EXPERIMENTAL`: their taller Fashion Sense Shirt frames are not leg-articulated and require the manual checks in `reports/V5A_RUNTIME_TEST_CHECKLIST.md` before promotion. Archived V4.6 pants/shorts/skirt research remains preserved but is not an active generation target.

### Generator V5C2 vanilla study and hoodies

V5C2 fixes the V5B sleeveless missing-arm contract, adds vanilla-informed article signals, and formalizes five hood-down Hoodie subtypes without changing the proven 16×16 Scale-2 upper-body runtime architecture. Generate and validate the exact ten-item diagnostic batch with:

```bash
python3 tools/generate_v5c2_vanilla_hoodie.py
python3 tools/validate_generator_v5c2.py
```

The test pack is `test-packs/fashionsense/RNG-Clothing-V5C2-Vanilla-Hoodie/`. Equip entries through the paired `V5C2 - ...` Fashion Sense presets so each Shirt uses its matching animated Sleeves appearance. All items remain `EXPERIMENTAL / NOT TESTED`; see `reports/V5C2_RUNTIME_TEST_CHECKLIST.md`.

## Player-facing mods

### `mods/RNGClothingFitting/`

Fitting controls for generated caps, offered contextually at the **vanilla
sewing machine**. Standalone and player-facing — deliberately not part of the
dev-only QC Bridge, and it never uses the Fashion Sense Hand Mirror.

Adjusts hat position by whole sprite pixels (Fashion Sense `HeadPosition` is
integer-only; half-pixel offsets were tested in game and stop the hat drawing
entirely) and moves the front design inside its approved per-pixel safe mask,
blocking whole rather than clipping. Generated packs are never rewritten: a
player's fitting is stored per save and re-applied on load, so Reset recovers
the generated default exactly.

No Harmony patches, no global input suppression, and vanilla behaviour is
untouched for any item the generator did not make.

See `mods/RNGClothingFitting/README.md` and `VERIFICATION.md`.

## Output

`output/vanilla/`

Generated vanilla-compatible test assets.

`output/fashionsense/`

Generated Fashion Sense test assets.

## Tests

`tests/`

Validation scripts, test manifests, comparison images, and proof-of-concept results.

## Development Order

1. Study native Stardew clothing.
2. Study tailoring / sewing-machine recipe logic.
3. Study random cosmetic selection logic.
4. Study Fashion Sense.
5. Document capabilities.
6. Analyze reference styles.
7. Propose generator architecture.
8. Build ONE simple vanilla clothing proof-of-concept.
9. Test it in-game.
10. Build ONE Fashion Sense proof-of-concept.
11. Test it in-game.
12. Only then decide whether procedural RNG clothing is viable.

## Success Criteria

The experiment succeeds only if generated clothing:

- is crisp at native Stardew scale;
- does not rely on shrinking high-resolution artwork;
- aligns correctly with the Farmer;
- works across required facing directions;
- remains stable while moving;
- does not require extensive manual cleanup;
- can be generated repeatedly from semantic/style rules;
- works reliably in-game on the target Stardew/SMAPI setup.

If these conditions cannot be met, do not force the system.
Change or abandon the design instead.
# Generator V5D — Masculine Art Grammar Expansion

V5D adds a benchmark-informed, coordinate-free masculine art grammar over the frozen V3/V4/V5B upper-garment pipeline. It generates fourteen distinct Fashion Sense diagnostic garments across casual, workwear, knit, streetwear, cardigan, waistcoat, utility, outerwear, formal, period, military, fantasy, armor/tabard, and alt-fashion roles. The test pack remains experimental pending runtime review; see `reports/V5D_MASCULINE_ART_GRAMMAR_REPORT.md`.
