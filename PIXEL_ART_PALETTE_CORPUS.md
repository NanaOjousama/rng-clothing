# Pixel-Art Palette Corpus

## Research method

Lospec is used as a relationship/reference catalog, not a swatch donor. Lospec describes its Palette List as a database of hardware and artist-created pixel-art palettes and exposes downloads/API metadata ([Palette List](https://lospec.com/palette-list/tag/endesga), [API documentation](https://api.lospec.com/docs/)). The project records creator and URL, studies value/hue behavior, then authors independent garment-role colors.

Reference studies:

- [DawnBringer 16](https://lospec.com/palette-list/dawnbringer-16): compact cross-hue value coverage.
- [Sweetie 16](https://lospec.com/palette-list/sweetie-16): bright hue families held together by deep blue-violet anchors.
- [Resurrect 64](https://lospec.com/palette-list/resurrect-64): tinted neutrals and material-friendly warm/cool ramps.
- [Famicube](https://lospec.com/palette-list/famicube): broad gamut with explicit neutral/material ladders.
- [hept32](https://lospec.com/palette-list/hept32): high-contrast, high-saturation statement relationships.
- [AAP-64](https://lospec.com/palette-list/aap-64): broad color vocabulary from which a garment still needs a disciplined subset.

No exact external palette is imported. The project-owned library is [`PALETTE_STORY_LIBRARY.json`](PALETTE_STORY_LIBRARY.json).

## Semantic roles

Each story defines `DeepShadow`, `StructuralDark`, `PrimaryFabric`, `PrimaryLight`, `SecondaryFabric`, `Trim`, `Accent`, `OptionalMotif`, and `OptionalMetal`. A renderer selects only the roles needed by a garment. Structural dark establishes separation; it is not a continuous black trace. Accent is allocated to a focal region, not scattered.

## Coverage

The 19 project-authored stories cover everyday neutral, coastal, autumn, spring floral, winter frost, field/workwear, formal, luxury, gothic, streetwear, sailor, celestial, arcane, ember/sun, cyber/neon, ceremonial, pastel, denim workwear, and clay/turquoise statement.

Overrepresented in the old output: muted navy, brown, olive, burgundy, and dark-plum combinations. They remain useful but are no longer default-safe fallbacks.

Previously underrepresented and now explicitly represented: seafoam/coral, pearl/midnight, jade/bronze, frost/ink, cyan/magenta, peach/lilac, cobalt/cream, clay/turquoise, and crimson/ivory.

## Palette gates

1. Verify structural regions in grayscale first.
2. Require visible DeepShadow → PrimaryFabric and PrimaryFabric → PrimaryLight separation at gameplay size.
3. Keep accents below the story budget; more saturation is not more rarity.
4. Reject muddy near-neighbor role collisions.
5. Check common farm, indoor, snow, rain, and dark-background contexts later in runtime review.
6. Pairwise diversity compares hue family, value topology, and accent placement—but palette cannot rescue structural duplication.
