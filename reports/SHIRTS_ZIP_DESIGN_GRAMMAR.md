# Shirts.zip Design-Variety Grammar

Status: corpus inspected and aggregate grammar extracted. The archive is a quality/variety benchmark only; no benchmark pixel, palette, silhouette, motif layout, or garment is consumed by Generator V3.

## Corpus actually inspected

The requested `/mnt/data/Shirts.zip` was not present. The same benchmark archive was available at `references/benchmark/shirts.zip` and was used instead.

- SHA-256: `821fdd7cafe74aea8efff362dba3c7e4df0cc11a7d7eb66a923984fef2f82bbe`
- appearances: 149
- directional frames inspected/inventoried: 596
- compact group: 123 appearances at 8×8, normally Scale 4
- oversized-canvas group: 26 appearances declared as 58×80 at Scale 2.9

The 58×80 definitions are not a valid target model for RNG Clothing's same-footprint 16×16 Scale-2 backend. Their opaque artwork occupies only a small part of those canvases and uses a materially different anchor/scale contract. They inform theme and focal-composition breadth only.

The dependency-free audit tool is `tools/analyze_shirts_zip_design_grammar.py`; aggregate measurements are in `output/analysis/shirts_zip_design_metrics.json`.

## Measured compact-shirt tendencies

Across the 123 compact front frames:

| Metric | Minimum | Median | Maximum |
|---|---:|---:|---:|
| Opaque cells | 22 | 61 | 64 |
| Opaque colors | 2 | 6 | 12 |
| Luminance range | 4.9 | 164.6 | 255.0 |
| Dominant-color share | 18.2% | 35.5% | 65.0% |
| Alpha-silhouette symmetry | 84.4% | 100% | 100% |

These statistics do not prove beauty. They support three useful conclusions: polished variety can coexist with a restrained median palette; most garment silhouettes remain stable while internal composition changes; and occasional asymmetry is a focal choice rather than the default.

## Reusable design grammar

### One dominant idea

The most readable garments establish one dominant composition before detail: a yoke, center closure, bold collar, lower band, paired vertical rhythm, front emblem, or asymmetric block. Supporting marks reinforce that gesture. Several weak-looking combinations in the corpus are instructive counterexamples: equal-strength decorations compete and make the shirt feel assembled rather than authored.

### Large geometry before motifs

Strong designs first divide the torso into purposeful color areas. Common structures include upper/lower division, center panel, side panels, shoulder/yoke block, wrapped band, and contrast sleeve/inner-layer emphasis. The motif sits within or against that geometry; it does not replace garment construction.

### Trim as rhythm

Collar, cuff, hem, piping, scallop, lace-like, and double-stripe systems are repeated with controlled intervals. Trim usually terminates at a seam or wraps consistently. It is not a collection of unrelated edge pixels.

### Focal motifs are clustered symbols

The named corpus demonstrates recognizable theme families—dessert, heart/romantic, floral, beach, witchy, crystal, cyber/machinery, creature, fairy-tale, seasonal, and elemental. Their reusable lesson is symbolic compression: a small connected color cluster and one clear silhouette are more legible than literal miniature illustration.

### Directional simplification

Fronts carry the focal feature. Sides preserve wrapping bands, shoulder transitions, or seam termination and suppress front-only emblems. Backs are typically quieter but retain yoke, band, paired cue, or a reduced related mark. The directions are related surfaces, not four independent paintings.

### Controlled palette roles

Compact shirts often use one dominant cloth family, a secondary structural color, and one accent family. More colors are useful when they clarify a symbol; additional near-duplicate shades are not the source of variety.

## Formal V3 families

The resulting original vocabulary supports beach/casual, seasonal soft, formal/elegant, floral/romantic, dessert/cute, witchy/dark, cyber/tech, military/structured, celestial/fantasy, storybook/whimsical, elemental, and creature-inspired concepts. Each family declares compatible moods, motif families, trim families, pattern families, and archetype preferences in `generator/data/v3/design_vocabulary.json`.

This is an abstraction, not a catalog of benchmark outfits. Generator V3 does not encode or reproduce the benchmark's named shirts.

## What was deliberately not learned

- no benchmark coordinates or pixel masks;
- no sampled colors;
- no exact silhouettes, motifs, emblems, or costume layouts;
- no 58×80 canvas/Scale-2.9 runtime behavior;
- no claim that filename labels alone establish aesthetic quality;
- no automatic benchmark access from generation or rendering code.

The corpus changed the architecture by demonstrating the need for surface composition and theme vocabulary. It did not become generator input.
