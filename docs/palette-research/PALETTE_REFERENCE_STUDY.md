# Palette Reference Study

## Scope and safety

This research examines palette relationships only: value distribution, hue travel, shared darks, saturation hierarchy, temperature contrast, and accent allocation. Source swatches are not copied into the project palette library. All exact colors in `palette_stories.json` are original project selections and were checked against the studied source swatches.

Lospec is the authoritative reference page used for the named palettes. Its downloadable palette data was inspected temporarily; no Lospec file was added to the repository.

## References studied

| Group | References | General lesson |
|---|---|---|
| General purpose | [Endesga 32](https://lospec.com/palette-list/endesga-32), [Resurrect 64](https://lospec.com/palette-list/resurrect-64), [AAP-64](https://lospec.com/palette-list/aap-64), [Apollo](https://lospec.com/palette-list/apollo), [Pear36](https://lospec.com/palette-list/pear36), [Sweetie 16](https://lospec.com/palette-list/sweetie-16) | Broad palettes gain flexibility through reusable dark/neutral anchors and multiple hue ramps, not by giving every hue an unrelated black-to-white ladder. |
| Limited/discipline | [Oil 6](https://lospec.com/palette-list/oil-6), [Dream Haze 8](https://lospec.com/palette-list/dream-haze-8), [Dno't Froget](https://lospec.com/palette-list/dnot-froget), [Autumn Decay](https://lospec.com/palette-list/autumn-decay) | Six to eight colors can remain expressive when each has a distinct job and value transition. Closely related hues still need a structural endpoint. |
| Seasonal/natural | [Hidden Library](https://lospec.com/palette-list/hidden-library), [Wintercode](https://lospec.com/palette-list/wintercode), [Haunted Hues](https://lospec.com/palette-list/haunted-hues) | Seasonal identity comes from temperature and value relationships: warm lights against chromatic darks, icy lights against violet/navy support, or amber/gold against purple night. |
| Dark | [Gothic Bit](https://lospec.com/palette-list/gothic-bit) | Dark atmosphere can be built with a narrow-saturation, broad-value family; pure black is not required for every shadow or outline. |
| High saturation | [SHIDO CYBERNEON](https://lospec.com/palette-list/shido-cyberneon), [Cyberpunk Neons](https://lospec.com/palette-list/cyberpunk-neons) | Neon succeeds through contrast against deep support and selective use. Treating every role as saturated destroys hierarchy. |
| Broad expression | [Journey](https://lospec.com/palette-list/journey), [hept32](https://lospec.com/palette-list/hept32) | High range and saturation still require deliberate neutrals, readable value ladders, and controlled cross-ramp sharing. |

## Findings by system size

### Larger palettes

The 32–64 color references generally offer several chromatic ramps while sharing very dark purples, navies, charcoals, pale neutrals, and whites. This creates cross-hue cohesion and makes it possible to shade warm and cool objects without every material becoming isolated. For clothing, a small project-owned structural-dark library can support cream, teal, rose, green, blue, and orange fabric families.

Larger size does not justify activating more colors on one garment. It provides *choice across garments*. A typical garment should still select a compact role set.

### Limited palettes

The six- and eight-color references reveal three important disciplines:

1. every swatch occupies a meaningful value/temperature position;
2. shadows frequently travel in hue instead of simply reducing RGB values;
3. one pale or saturated endpoint can carry emphasis because the rest of the system is controlled.

For garments, limited discipline means omitting unnecessary semantic roles, not forcing every story to contain eight visibly different colors.

## Value and hue behavior

- Hue-shifted shadow is a relationship, not a universal “make shadows blue” rule. Warm rust may descend toward plum-brown; aqua may descend toward blue graphite; green may descend toward blue-green or brown-green depending on mood.
- Highlights can change temperature as well as lightness. Warm natural or formal cloth may lean cream; winter/synthetic fabric may remain cool.
- Light-primary stories still need a chromatic StructuralDark for collar recesses, lapels, seams, pockets and selective contour anchors.
- Dark-primary stories require middle and light planes; using several near-black values without separation produces a muddy torso.
- Neutral ramps are strongest when slightly chromatic. Blue-violet charcoal, green-black, warm brown-charcoal and plum-charcoal can unify several fabrics more gracefully than absolute black.

## Saturation hierarchy

Saturation is most readable when roles form a hierarchy:

- dominant fabric: low to moderate saturation in most stories;
- secondary fabric: either quieter or deliberately contrasted, depending on topology;
- trim: usually restrained so it supports construction;
- accent/motif: permitted to hold the strongest chroma but at low coverage;
- highlight: often less saturated than the fabric, except for deliberately luminous synthetic stories.

High-saturation references validate neon and vivid sport stories, but they also demonstrate the need for dark support. The project therefore localizes neon to panels, piping, a small motif, or one focal fastening.

## Principles adopted

1. Evaluate lightness perceptually, not by raw RGB channel distance.
2. Use hue travel through fabric ramps; never assume “base × scalar” is sufficient shading.
3. Share a few structural dark concepts across multiple hue families.
4. Permit light, pastel and colorful masculine/unisex clothing without darkening it for gender coding.
5. Keep a compact active role set per garment even when the library is large.
6. Let material modify value spacing and highlight behavior.
7. Let construction determine color topology.
8. Decouple hue family from rarity completely.

## Inspection status

All 18 requested references, including the two optional broad-expression palettes, were located and inspected. `Dno't Froget` required resolving its punctuation-sensitive Lospec slug (`dnot-froget`) but was successfully studied. No requested reference remained unavailable.
