# RNG Clothing generators

## Shared taste / rarity gate

`generator/taste_policy.py` is the generator-wide semantic taste gate. Garment families opt in through `generator/data/taste_policy_registry.json` and provide family-specific `rarityRules` + `tastePolicy` data. The shared engine enforces four layers before visual generation: hard rarity floors, complexity budgets, incompatibility/conflict rules, and design-role/visual-channel control. Rarity means more distinctive, not more cluttered. Validate with `python3 tools/validate_taste_policy.py`.

## Catalog-backed template promotion

`tools/promote_catalog_families.py` promotes suitable `FAMILY_BASE` entries from `source_catalog/MASTER_CATALOG.json` into formal source-backed template contracts. Contracts reference exact rectangles in the local `generator content` source sheets, preserve source-declared mirroring/per-view sizes/wear offsets, and hash extracted pixels/alpha without copying third-party PNGs into Git. Each promoted family receives its own registered taste policy. `generator/catalog_templates.py` exposes template loading, family taste evaluation, and donor discovery through `SOURCE_TRANSFER_LIBRARY.json`. Validate with `python3 tools/validate_catalog_template_promotions.py`.

The project contains deterministic, dependency-free Python generation tools. V1/V2 export native Stardew shirts. V3 is an optional Fashion Sense 7.5.0 content-pack backend and does not replace them.

## Rarity renderer routing

The current production-facing policy routes Common to the vanilla Stardew clothing renderer, Uncommon to one simple Fashion Sense HD appearance, and Rare to the bounded RarePlus coordinated-layer capability. `RarePlus` is a renderer class, not a new semantic rarity. See `generator/data/rarity_renderer_architecture.json` and validate it with:

```bash
python3 tools/validate_rarity_renderer_architecture.py
```

The coordinated hoodie is the reference RarePlus template. It remains locked but `EXPERIMENTAL` until its final live checklist passes; static validation alone cannot freeze it.

## Generator V3

V3 keeps V2 construction coordinate-free, then adds a design concept, hierarchical surface composition, color story, directional topology, rarity surface budget, and batch diversity gate. Generated art is authored directly on 16×16 logical frames at Fashion Sense Scale 2.

Analyze the design-variety benchmark independently:

```bash
python3 tools/analyze_shirts_zip_design_grammar.py
```

Generate the controlled 12-garment benchmark and isolated pack:

```bash
python3 tools/generate_v3_benchmark.py
```

Validate schemas, logical pixels, pack metadata, diversity, body coverage, determinism, and V2 regressions:

```bash
python3 tools/validate_generator_v3.py
```

The generated pack is under `test-packs/fashionsense/RNG-Clothing-V3-Benchmark/`. Fashion Sense is required at runtime but is not vendored or installed. Benchmark art is read only by the isolated analysis tool; neither the V3 engine nor renderer accesses it.

## V5B semantic sleeves and upper garments

V5B wraps the frozen V3 design and V4 article recipes with coordinate-free
`SleeveIntent`, shoulder, neckline, collar, layering, and opening semantics.
Short sleeves retain the proven native animated path. Fitted long, rolled/cuffed,
and layered sleeves export a paired Fashion Sense `Sleeves` appearance using the
complete 252-frame FS 7.5.0 animation contract. Sleeveless garments conservatively
hide native sleeves and remove only the shirt-owned sleeve region.

```bash
python3 tools/generate_v5b_upper_garments.py
python3 tools/validate_generator_v5b.py
```

The isolated test pack is
`test-packs/fashionsense/RNG-Clothing-V5B-Upper-Garments/`. Its twelve Outfit
presets coordinate each Shirt with the correct Sleeves appearance. All custom
sleeve silhouettes remain `EXPERIMENTAL` until the in-game checklist in
`reports/V5B_RUNTIME_TEST_CHECKLIST.md` is completed.

## V4.6 lower-body runtime proof

V4.6 is an isolated experimental adapter for fitted Pants and Footwear. It
derives full 16×32 pose/coverage contracts from the installed Fashion Sense
7.5.0 developer templates, then generates original semantic surface treatment
inside those envelopes. It does not alter V3/V4 or the upper-body renderer.

```bash
python3 tools/build_v46_frame_contracts.py
python3 tools/generate_v46_lower_body_runtime.py
python3 tools/validate_generator_v46.py
```

The test pack is `test-packs/fashionsense/RNG-Clothing-V46-LowerBody-Runtime/`.
Static validation never promotes its four appearances beyond `EXPERIMENTAL`;
use `reports/V46_RUNTIME_TEST_CHECKLIST.md` for the required in-game evidence.

## V4.6B lower-body readability correction

V4.6B defers custom Shoes and separates Pants, Shorts, and Skirts into three
article-specific grammars over one shared Farmer motion contract. Final art is
authored directly in 32×64 logical frames at Fashion Sense Scale 2; the old
16×32 contract is used only to derive body/pose coverage, never as finished art
to enlarge.

```bash
python3 tools/build_v46b_article_contracts.py
python3 tools/generate_v46b_lower_body.py
python3 tools/validate_generator_v46b.py
```

The isolated pack is
`test-packs/fashionsense/RNG-Clothing-V46B-LowerBody-Readability/`. Fashion
Sense presents all six diagnostic articles in its Pants category. Static
identity validation does not promote any appearance beyond `EXPERIMENTAL`;
complete `reports/V46B_RUNTIME_TEST_CHECKLIST.md` before V4.7 work.

### External profile integration: AoTInspired

The first curated external profile uses the frozen V3 engine and renderer to
produce exactly six visible concepts with no hidden candidate pool:

```bash
python3 tools/generate_aot_v3_collection.py
python3 tools/validate_aot_v3_collection.py
```

The adapter lives under `generator/v3/style_profiles/`, while its coordinate-free
profile data lives under `style-profiles/AoTInspired/` and
`generator/data/v3/style_profiles/`. The output pack is
`test-packs/fashionsense/RNG-Clothing-V3-AoT-Collection/`. References inform the
curated vocabulary and report only; neither the adapter nor renderer reads them.
The profile also defines bounded Common/Uncommon/Rare art floors and ceilings;
its Rare tier permits a modest original crest but reserves larger emblems,
additional layers, animation, VFX, and bespoke silhouettes for future tiers.

## Generator V2

V2 is construction-first: it resolves a coordinate-free semantic recipe, validates archetype and rarity compatibility, builds named logical regions, applies color blocking and shading, and exports the vanilla sheet. Run the recipe-only gate first:

```bash
python3 -B -m generator.prepare_v2_recipes
```

Then render the two-color structural gate, ten full test garments, previews, and isolated pack:

```bash
python3 -B -m generator.generate_v2
```

Re-run the independent checker with:

```bash
python3 -B tools/validate_generator_v2.py
```

The default V2 seed is `202608282200`. A successful run deterministically writes:

- 20 migrated V1 recipes and 20 fresh V2 recipes under `output/recipes/`;
- five unshaded two-color archetype tests under `output/structural-tests/v2/`;
- exactly ten full native 256×32 shirt PNGs and their previews under `output/vanilla/v2/`;
- one isolated Content Patcher pack under `test-packs/vanilla/RNG-Clothing-V2/`;
- recipe, migration, structural-audit, validation, and critical completion reports.

## Generator V1

Run from the project root:

```bash
python3 -B -m generator.generate_v1
```

Re-run the independent checker with:

```bash
python3 -B tools/validate_generator_v1.py
```

The default seed is `202608281615`. A successful run deterministically writes:

- 20 semantic Lifestyle recipes to `output/recipes/lifestyle_v1_recipes.json`;
- exactly five native 256×32 shirt PNGs and their previews to `output/vanilla/v1/`;
- one isolated Content Patcher test pack to `test-packs/vanilla/RNG-Clothing-V1/`;
- recipe, grammar, validation, and critical quality reports.

For both vanilla versions, the authoritative art surface is always the logical 8×8 frame. Neither vanilla tool has a resampling path except integer nearest-neighbor preview enlargement. They do not install packs, touch the normal Mods folder, use Fashion Sense, or modify TFWR.

## Optional Fashion Sense HD jacket POC

The bounded Fashion Sense backend reuses the unchanged `lifestyle-v2-16` semantic recipe and resolves it through a renderer-specific 16×16 jacket grammar at Fashion Sense `Scale: 2`. It does not change or replace the vanilla renderer.

Generate the one content pack and comparisons:

```bash
python3 tools/generate_fs_hd_jacket_poc.py
```

Run its independent static/source-contract checker:

```bash
python3 tools/validate_fs_hd_jacket_poc.py
```

The generated pack is under `test-packs/fashionsense/RNG-Clothing-HD-Jacket-POC/`. These tools never install Fashion Sense or the pack, and never write to the normal Mods folder. Runtime alignment remains a manual in-game test boundary.
