# Fashion Sense Quality Benchmark Analysis

Status: benchmark study complete; one original Mistral refinement generated and statically validated. The refined asset has not yet been judged in-game.

## Boundary of use

The attached packs in `references/benchmark/` were treated as a visual quality corpus only.

- No benchmark PNG is read by the Fashion Sense renderer.
- No benchmark PNG is read by the Mistral output generator.
- No benchmark coordinates, silhouettes, layouts, motifs, palettes, or outfits were encoded into the renderer.
- The semantic recipe, V2 recipe architecture, vanilla backend, scale, anchor, and runtime layering contract are unchanged.

The analysis tool reads benchmark files to calculate aggregate tendencies. The generated jacket is still resolved from the original Mistral semantic recipe and our own structural regions.

## Corpus and comparability

The benchmark folder contains four materially different art groups:

1. **Bonestealer shirts** — mostly 8×8 or 8×10/11 logical garments, with very dark silhouette anchors, bold material blocks, and a small number of highly visible accents.
2. **Layicn Sino-Western shirts** — 8×8 garments with strong diagonal closures/bands, high value range, and carefully compressed side views.
3. **SubabyTvanZ sailor shirts** — 8×8 garments using only three colors per sampled design. Their broad collar geometry, not texture, carries identity.
4. **Sun Haven capes** — 30×25, 35×20, or 40×40 accessory frames at Scale 2.5 with animation sequences. They demonstrate flowing silhouette, shade-band direction, and animation-aware construction, but are not same-footprint shirt comparisons.

Color variants were deduplicated. The quantitative shirt sample contains 11 representative designs × four directions = 44 frames. The large cape sheets were inspected visually and inventoried separately; their accessory coordinates are not applicable to the 16×16 shirt backend.

Several pack JSON files use permissive/trailing-comma syntax and older Fashion Sense defaults. They are quality references, not runtime-schema authorities.

## Measured art tendencies

Across the 44 representative benchmark shirt frames:

| Metric | Minimum | Median | Maximum |
|---|---:|---:|---:|
| Opaque colors | 3 | 8 | 15 |
| Luminance range | 31.0 | 196.0 | 242.0 |
| Darkest-35% cells located on exterior | 40.0% | 57.8% | 100% |
| Exterior cells acting as dark anchors | 42.9% | 69.0% | 90.0% |
| Dominant-color share | 19.2% | 37.2% | 65.4% |

The current Mistral C treatment uses six to nine colors and has comparable overall luminance range where the light inner layer is present. Its major outlier is exterior treatment: every exterior cell is assigned the darkest contour role. That guarantees separation, but it creates a mechanically uniform ring that the benchmark garments usually avoid.

The benchmark shirts do contain single-pixel color components. At native 8×8, many are intentional closure, trim, or highlight marks attached to a connected garment—not random texture noise. Therefore “zero singletons” is not a valid universal beauty rule. The reusable rule is that small marks must reinforce a larger construction gesture and must not become independent texture scatter.

One sampled Meat Apron back frame contains two detached two-pixel tie elements. That is an intentional accessory-like exception and is not adopted as a general shirt rule.

Full measurements: `output/fashionsense/benchmark-refinement/benchmark_metrics.json`.

## Reusable Fashion Sense art-grammar rules

### 1. Contour anchors, not a uniform ring

- Keep the darkest value at neck recesses, outer vertical sides, underarms, overlap bottoms, and hem corners.
- Permit short lit or mid-value exterior runs where a shoulder or fold faces the light.
- At Scale 2, restore Stardew optical weight with a selective second inward crease/shadow cell, not a two-cell black border around everything.
- The silhouette must remain readable even where the contour value changes.

### 2. One dominant construction gesture per view

- Front: lapel/opening or closure should dominate; minor seams stay subordinate.
- Back: yoke or center seam may dominate, but not both at equal strength.
- Side: one descending collar/opening rhythm is enough.
- Internal lines should terminate before colliding with every contour edge.

### 3. Light must follow form

- Pick a consistent light bias instead of lighting left/right panels identically.
- Use an attached stair-step or short band along a lapel, shoulder, fold, or cape sweep.
- Highlights may be tiny, but they should attach to a larger light mass.
- More logical pixels do not require more shade values.

### 4. Large color blocks establish identity

- Collar, inner layer, closure, yoke, and hem should be recognizable as areas before micro marks are considered.
- A contrasting region should have a deliberate beginning and end; it should not look like an accidental full-height stripe.
- Three-color designs can outperform ten-color designs when the large geometry is strong.

### 5. Hem and cuff shadows must terminate

- Avoid full-width shadow bars unless the garment truly has a contrast band.
- Attach lower shadows to corners, folds, cuffs, or overlap points.
- Preserve a strong underside, but allow the torso base color to reach the lower construction.

### 6. Side views are compressed reconstructions

- Do not merely crop or flatten the front.
- Preserve one collar/lapel diagonal, a recognizable inner/outer relationship, and the sleeve/body junction.
- Suppress details that do not physically remain visible.

### 7. Resolution is a construction budget

- Use extra cells for shoulder slope, overlap depth, fold direction, animation continuity, and cleaner termination.
- Do not spend them on textile speckle.
- Large animated accessories and same-footprint shirts need different grammars; cape density should not be imported into a torso sprite.

## Gaps in the current Mistral C grammar

1. **Uniform exterior contour:** 100% of exterior cells use the darkest role. It reads cleanly but also sticker-like.
2. **Symmetric lighting:** paired front highlights give both panels equal emphasis and flatten the garment.
3. **Overstated back yoke:** the complete dark V competes with the silhouette instead of sitting behind it.
4. **Lower shadow banding:** panel bounds cause several lower rows to darken together, partially recreating a horizontal bar.
5. **Side hierarchy:** the inner edge, lapel, and exterior can all reach similar emphasis, making the side diagrammatic.
6. **Role activation near the palette ceiling:** front/side commonly use nine colors. This is not excessive relative to the corpus, but any new color must replace or clarify another role rather than simply accumulate.
7. **Optical-weight handling:** one 16×16 cell at Scale 2 is half the displayed width of one 8×8 cell at default Scale 4. The backend needs selective inward reinforcement, not blanket thickening.

## Renderer refinement plan

### Implemented in this controlled test

- add selective exterior-edge breaks while retaining dark anchor coverage;
- add a directional light bias;
- make the front lapel the dominant construction gesture;
- soften most of the back yoke from structural edge to cloth shadow;
- remove broad lower panel shadowing and keep only attached corner clusters;
- reinforce selected long side runs with an inward crease/shadow cell;
- cap the refined front/side palette at nine colors;
- preserve the same structural masks and all runtime properties.

### Recommended future backend work

1. Generalize an `edgeExposure` classifier with `neck_anchor`, `side_anchor`, `underarm_anchor`, `hem_anchor`, and `lit_edge` roles.
2. Add a renderer-level light-direction policy shared across all directions.
3. Give each archetype/view a construction-gesture budget so yoke, closure, and seams cannot all become equally strong.
4. Add hem/cuff termination templates rather than deriving all lower shading from region bounds.
5. Activate only the shade roles needed by a garment; retain the seven-role vocabulary without requiring seven outer colors in every output.
6. Add multiple original side-construction templates before attempting a style-profile stress test.
7. Continue judging at exact gameplay footprint before accepting an enlarged diagnostic preview.

These are renderer concerns. They do not require changing semantic V2 recipes or rarity logic.

## Controlled Mistral refinement applied

The refined garment is driven by the same `lifestyle-v2-16` recipe and the same polished structural regions as current C. No opaque cell was added, removed, or moved.

Applied art-role changes:

- front: 58 role cells changed;
- back: 69 role cells changed;
- left/right: 38 role cells changed per side;
- darkest contour remains on 85.2% of front/back exterior cells and 83.3% of side exterior cells, down from a uniform 100%;
- front/side optional highlights are one connected three-cell cluster;
- the front/side default palette remains nine opaque colors; back uses six;
- broad lower shadowing is replaced by small attached corner masses;
- back yoke is mostly shadow with six structural anchor cells;
- native body coverage, silhouette, neck opening, and sleeve junction are unchanged.

## Visual comparison and critical result

At exact Scale-2 gameplay footprint, the refinement is an improvement, but a restrained one:

- shoulder edges have a clearer light-facing plane without losing dark separation;
- the front lapel has one readable emphasis rather than mirrored highlight blocks;
- lower panels feel less like a heavy horizontal band;
- the yoke sits within the back instead of being traced at equal strength throughout;
- side construction has better depth ordering.

The refined version is more cohesive and less mechanically outlined than current C. It does not yet demonstrate the full polish range visible in the best benchmark outfits. The side lapel remains the weakest view, and the cool-neutral palette still makes subtle midtone construction harder to read than the high-contrast benchmark palettes.

Offline judgment: the refinement passes as a material grammar improvement, not a dramatic redesign. Community-quality parity remains **unconfirmed** until the asset is tested on a live Farmer at normal zoom.

## Technical result

Static validation passes:

- 16×64 RGBA8 texture containing four 16×16 logical frames;
- binary alpha and unfiltered generated scanlines;
- exact integer nearest-neighbor previews;
- `Scale: 2`, `BodyPosition: (0,32)`, and direction mapping unchanged;
- native animated sleeves retained;
- body-coverage envelope passes all directions;
- intentional neck opening retained;
- current C baseline exported byte-identically;
- vanilla V2 Mistral output remains byte-equivalent to its renderer;
- test pack contains one original refined shirt and targets Fashion Sense 7.5.0.

Machine-readable result: `output/fashionsense/benchmark-refinement/validation.json`.

## Test pack

Copy the whole folder:

`test-packs/fashionsense/RNG-Clothing-HD-Benchmark-Refinement-Test/`

into `Stardew Valley/Mods/`, with Fashion Sense 7.5.0 installed separately, then fully restart SMAPI. Use `fs_add_mirror` if needed and select **Mistral Benchmark-Refined HD** under Shirts.

Nothing was installed automatically.
