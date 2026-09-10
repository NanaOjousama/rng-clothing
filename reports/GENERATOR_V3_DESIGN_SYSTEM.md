# Generator V3 Design System

Generator version: `3.0.0`  
Scope: optional Fashion Sense shirts/tops, 16×16 logical frames, Scale 2, Common/Uncommon/Rare.

## Additive architecture

```text
style/theme request
  -> design concept engine
  -> preserved V2 construction adapter
  -> surface design engine
  -> color composition
  -> rarity budget
  -> permanent FS-HD construction/shading renderer
  -> directional surface compositor
  -> garment and batch validation
```

V3 does not change V2 recipes or the vanilla renderer. A V3 recipe is converted to a valid coordinate-free V2 construction recipe, which the permanent FS-HD renderer resolves first. Surface systems then decorate only occupied garment cells and protect exterior-contour/deep-crease anchors.

## Recipe contract

`generator/schema/garment_recipe_v3.schema.json` adds:

- concept: role, silhouette goal, mood, primary/secondary gesture, focal area, symmetry, density, theme emphasis;
- construction: the existing seven V2 semantic fields;
- substantial features: the existing V2 structural vocabulary;
- color block: semantic type, topology, and color role;
- surface design: hierarchical composition, supports, trim, motif, pattern, and detail layout;
- palette story;
- localization-ready name and description.

It contains no raw coordinates, frame positions, anchors, scales, or Fashion Sense properties. Coordinate-key rejection remains active.

## Design-concept engine

The engine answers what the garment is trying to be before it chooses surface cells. A stable SHA-256 selection resolves compatible construction presets from the request seed. Theme plans select a palette story and a dominant composition family. The controlled benchmark uses an explicit request list so its 4/4/4 rarity and theme coverage are reproducible; those requests remain concepts, not finished pixel layouts.

## Surface systems

### Color blocks

Supported grammar includes shoulder/yoke/chest/waist/lower blocks, vertical split, side and center panels, contrast sleeves, and inner-layer emphasis. Major blocks are resolved first and cannot erase protected outline anchors.

### Trim

Supported grammar includes collar, cuff, hem, lapel and seam trim; piping; double stripe; scalloped/lace-like/decorative edge rhythms. A construction-bound trim is moved onto an inward cloth plane when the true boundary is a protected dark anchor.

### Motifs

Original templates support fruit, flower, star, heart, ribbon, leaf, crystal, lightning, abstract military geometry, creature, dessert, cyber glyph, and sun/wave families. Templates live in renderer data. Rarity activates only two or three motif color roles and limits visible cells; no motif is resized, filtered, or sampled from the benchmark.

### Patterns

Supported systems include dots, stripes, chevrons, diamonds, checks, soft repeats, military repeats, and themed bands. Patterns use authored integer-cell rhythms, with side views carrying only a reduced wrapping phase.

## Directional topology

Every surface system declares one topology: front-only, front/back, paired back cue, wrapped, shoulder-wrapped, construction-bound, or asymmetric front. A wrapped band must survive all directions. A front-only motif may not leak to the back. Paired motifs render a deliberately reduced back cue. Side views never receive a compressed copy of the full front emblem.

## Rarity integration

| Rarity | Active systems | Composition intent | Surface-color maximum |
|---|---:|---|---:|
| Common | 1 | one clean visual idea | 2 |
| Uncommon | 2 | one primary + one support | 3 |
| Rare | 3 | one focal primary + two subordinate supports | 4 |

Per-view cell, motif, pattern, topology, and themed-view budgets are in `generator/data/v3/rarity_budgets.json`. More rarity gives coordinated design freedom, not permission to fill the canvas.

## Color and dye behavior

The primary fabric remains Fashion Sense grayscale-mask dyeable through the permanent renderer. V3 surface colors are fixed authored accents from original palette stories. This preserves a useful dye channel without pretending that the POC has a complete multi-channel dye UI. A production version would need an explicit decision about player recoloring of secondary/motif systems.

## Quality and diversity gates

Per-garment validation checks:

- V3 schema and coordinate ban;
- V2 construction legality;
- active-system count and rarity budget;
- visible surface, motif, pattern, and color budgets;
- protected contour and body-coverage preservation;
- primary/support hierarchy;
- isolated surface noise;
- topology continuity;
- shading-independent design interest.

Batch validation compares theme, archetype, composition, focal area, symmetry, color block, trim, motif, pattern, palette, panel layout, and hem. It combines semantic similarity with a color-independent surface-mask Jaccard guard, so a recolor cannot masquerade as a new design. These are rejection gates, not beauty scores.

## Determinism and isolation

The same requests and seed produce byte-identical recipes and direct logical PNGs. The V3 engine, renderer, and output generator do not read `Shirts.zip` or `references/benchmark`. Only `tools/analyze_shirts_zip_design_grammar.py` may open the benchmark corpus.

## Current boundary

V3 supports four permanent FS-HD archetypes: sweater, button shirt, jacket, and sailor top. T-shirts are not silently forced through an unsupported FS structure. It does not add pants, hats, accessories, animation atlases, reward logic, Legendary/Mythic rarity, TFWR integration, or a GUI.
