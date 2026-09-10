# Lifestyle recipe batch V1

Generator version: `1.0.0`  
Deterministic seed: `202608281615`  
Scope: 20 semantic Lifestyle recipes; exactly five selected for rendering.

Recipes contain no pixel coordinates. All coordinates belong to the renderer grammar.

## Automated review

- Compatibility: **PASS** (20/20 valid).
- Exact duplicate recipes: 0.
- Near-duplicate structures: 0.
- Minimum accepted within-archetype semantic distance: 3 fields.
- Minimum accepted within-archetype visible-structure distance: 2 fields.
- Categories and rarity remain separate: every recipe is Lifestyle; rarity is Common, Uncommon, or Rare metadata.

## Twenty concepts

| # | Render | Name | Archetype | Rarity | Fit | Neck / collar | Closure | Detail(s) | Pattern | Palette | Accent |
|---:|:---:|---|---|---|---|---|---|---|---|---|---|
| 1 |  | Harbor Band Tee | T_SHIRT | Common | regular | crew / none | none | lower_trim | none | navy_ivory | none |
| 2 |  | Meadow Everyday Tee | T_SHIRT | Common | relaxed | round / none | none | none | none | sage_tan | none |
| 3 | ✓ | Bluebell Pin Tee | T_SHIRT | Uncommon | regular | round / none | none | chest_accent | simple_border | denim_cream | deep_brown |
| 4 |  | Cedar Pin Tee | T_SHIRT | Rare | relaxed | crew / none | none | chest_accent, center_stripe | none | warm_neutral | deep_brown |
| 5 | ✓ | Hearth Ribbed Sweater | SWEATER | Common | relaxed | crew / none | none | lower_trim | none | rust_brown | none |
| 6 |  | Woodland Ribbed Sweater | SWEATER | Uncommon | regular | shallow_v / wide | none | lower_trim | horizontal_stripe | forest_cream | none |
| 7 |  | Mistral Pin Sweater | SWEATER | Uncommon | relaxed | shallow_v / none | none | chest_accent | simple_border | cool_neutral | burgundy |
| 8 |  | Garnet Ribbed Sweater | SWEATER | Rare | relaxed | round / none | none | chest_accent, lower_trim | none | charcoal_burgundy | ivory |
| 9 | ✓ | Cedar Button Shirt | BUTTON_SHIRT | Common | regular | open / small_folded | buttons | button_line | none | warm_neutral | none |
| 10 |  | Meadow Pocket Shirt | BUTTON_SHIRT | Uncommon | fitted | open / small_folded | buttons | chest_accent | vertical_trim | sage_tan | rust |
| 11 |  | Harbor Button Shirt | BUTTON_SHIRT | Rare | regular | open / small_folded | buttons | chest_accent, button_line | simple_border | navy_ivory | brass |
| 12 |  | Bluebell Button Shirt | BUTTON_SHIRT | Uncommon | regular | open / small_folded | buttons | button_line | vertical_trim | denim_cream | brass |
| 13 |  | Woodland Layer Jacket | JACKET | Common | relaxed | open / small_folded | center_open | inner_layer | none | forest_cream | none |
| 14 |  | Garnet Button Jacket | JACKET | Uncommon | regular | open / small_folded | buttons | button_line | vertical_trim | charcoal_burgundy | ivory |
| 15 |  | Hearth Layer Jacket | JACKET | Rare | regular | open / small_folded | center_open | chest_accent, inner_layer | simple_border | rust_brown | deep_brown |
| 16 | ✓ | Mistral Layer Jacket | JACKET | Rare | regular | open / wide | center_open | lower_trim, inner_layer | none | cool_neutral | none |
| 17 |  | Harbor Center-Trim Top | SAILOR_TOP | Common | regular | open / sailor | none | center_stripe | none | navy_ivory | none |
| 18 |  | Meadow Pin-Collar Top | SAILOR_TOP | Uncommon | fitted | open / sailor | none | chest_accent | simple_border | sage_tan | rust |
| 19 | ✓ | Garnet Pin-Collar Top | SAILOR_TOP | Rare | regular | open / sailor | none | center_stripe, chest_accent | simple_border | charcoal_burgundy | brass |
| 20 |  | Bluebell Pin-Collar Top | SAILOR_TOP | Uncommon | regular | open / sailor | none | chest_accent | simple_border | denim_cream | deep_brown |

## Selected five

### Bluebell Pin Tee (`lifestyle-v1-03`)

Keeps the simplest archetype readable while adding one controlled Lifestyle cue.

Recipe: T_SHIRT, regular, round neckline, none collar, none closure, details chest_accent, simple_border pattern, denim_cream palette, Uncommon.

### Hearth Ribbed Sweater (`lifestyle-v1-05`)

Uses neckline and hem mass to read as knitwear without surface noise.

Recipe: SWEATER, relaxed, crew neckline, none collar, none closure, details lower_trim, none pattern, rust_brown palette, Common.

### Cedar Button Shirt (`lifestyle-v1-09`)

The collar and center closure remain legible in all directions with restrained detail.

Recipe: BUTTON_SHIRT, regular, open neckline, small_folded collar, buttons closure, details button_line, none pattern, warm_neutral palette, Common.

### Mistral Layer Jacket (`lifestyle-v1-16`)

Outer panels and a compatible inner-layer/closure relationship create the clearest layered identity.

Recipe: JACKET, regular, open neckline, wide collar, center_open closure, details lower_trim, inner_layer, none pattern, cool_neutral palette, Rare.

### Garnet Pin-Collar Top (`lifestyle-v1-19`)

The front collar and simplified back yoke provide a strong four-direction identity without an emblem.

Recipe: SAILOR_TOP, regular, open neckline, sailor collar, none closure, details center_stripe, chest_accent, simple_border pattern, charcoal_burgundy palette, Rare.

## Review boundary

Compatibility and redundancy checks reject illegal or repetitive recipes. They do not prove that a rendered shirt is attractive. The five rendered contacts still require human visual review.
