# AoT Style-Pool Differentiation Correction

Status: revised set generated and statically validated. The renderer, FS art grammar, anchors, coverage, and unrelated systems are unchanged.

## Why the previous pool converged

The prior selection contained two Jackets built from the same frozen front Jacket mask. Although Rampart and Mosswatch differed semantically in collar, hem, palette, and side template, both retained:

- the same waist-length outer-shell mass;
- two outer panels around a narrow center inner layer;
- similar upper collar framing;
- brown/olive field palette relationships;
- side views dominated by descending outer cloth around an inner strip.

Cadence used a different Button Shirt archetype, but its previous low-contrast khaki/gray palette reduced the yoke/vest distinction at gameplay size. The result was a coherent family with insufficient garment-role separation.

## Revised selection

### A. Rampart Field Jacket — iconic cropped field-jacket role

Unchanged because it remains the strongest profile anchor.

- archetype: Jacket;
- silhouette: compact outer shell;
- opening: wide lapel around visible dark olive inner layer;
- shoulder/neck: broad structured collar and outer-panel framing;
- hem: firm cropped-waist termination;
- side: `lapel_led` outer shell with visible opening;
- palette: warm tan/brown over dark olive.

Gameplay read: **the jacket**.

### B. Cadence Yoke Shirt — fitted shirt/vest role

Construction is retained, but its color hierarchy is corrected to make that construction legible.

- archetype: Button Shirt;
- silhouette: fitted rather than outer-shell broad;
- opening: tailored button/placket logic, not an exposed inner stripe;
- shoulder/neck: dark black-brown vest-like yoke over an ivory shirt body;
- hem: controlled contrast-band waist;
- side: `yoke_tailored`, preserving folded collar, yoke, and placket without jacket framing;
- palette: ivory / black-brown for immediate major-region separation.

It remains a Rare recipe with two substantial features (`yoke`, `structured_lower_band`). It is not a plain filler.

Gameplay read: **the shirt/vest top**.

### C. Nightwatch Collar Knit — dark civilian/formal role

This replaces the second jacket.

- archetype: Sweater;
- silhouette: heavy uninterrupted cloth mass;
- opening: none—no center stripe or split panels;
- shoulder/neck: broad charcoal collar rhythm rather than lapels or yoke;
- panel layout: solid;
- hem: structured waist without a contrast jacket band;
- side: `heavy_mass`, fuller and simpler than both jacket and tailored-shirt sides;
- palette: dark burgundy / charcoal.

It is a Strong Rare recipe with two substantial features (`broad_collar`, `structured_lower_band`). Its visual interest comes from collar, value mass, and waist construction rather than decoration.

Gameplay read: **the alternate dark civilian piece**.

## Shape-first differentiation result

The revised set separates these primary gestures:

| Role | Primary silhouette/construction | Center treatment | Upper treatment | Side template |
|---|---|---|---|---|
| Field jacket | framed outer shell | visible inner layer | wide lapel | `lapel_led` |
| Yoke shirt | fitted tailored torso | button/placket logic | vest-like yoke | `yoke_tailored` |
| Civilian knit | uninterrupted heavy mass | none | broad collar | `heavy_mass` |

Palette reinforces these differences but does not create them.

## Desirability review

- Rampart remains the strongest iconic Rare reward.
- Cadence now reads as deliberately high-contrast formal fieldwear rather than a muted generic top.
- Nightwatch provides a darker, moodier reward role with a clear collar and waist identity; it is visually quieter than Rampart but not plain.

All three selected recipes are Rare and use two substantial features. None relies on micro-detail noise.

## Validation

- exactly five valid profile recipes retained;
- exactly three selected outputs;
- selected archetypes: Jacket, Button Shirt, Sweater;
- selected side templates: three distinct templates;
- all existing FS permanent diagnostics pass without warnings;
- 16×16 frames, Scale 2, BodyPosition `(0,32)`, binary alpha, and native sleeves preserved;
- no renderer-specific profile code or special-case pixels;
- Generator V2 and the existing permanent FS control set remain valid.

## Outputs

- previous vs revised: `output/comparisons/AOT_STYLE_PROFILE_PREVIOUS_VS_REVISED.png`;
- revised three-way sheet: `output/comparisons/AOT_STYLE_PROFILE_3WAY.png`;
- revised assets/summaries: `output/fashionsense/style-profile-aot/revised/`;
- updated pack: `test-packs/fashionsense/RNG-Clothing-AoT-Style-POC/`.

The old Mosswatch test-pack folder was removed from the active pack and preserved temporarily under `/tmp/RNG-Clothing-AoT-Style-POC-MosswatchUtilityJacket-previous` during the correction.
