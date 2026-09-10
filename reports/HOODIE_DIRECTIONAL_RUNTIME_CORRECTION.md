# Hoodie Directional Runtime Correction

> Later live evidence supersedes this report's lowered-front X value as well as its raised-layer conclusion. The corrected lowered-front origin is `(-8,0)`, and every raised direction uses native Hat order. See `reports/HOOD_UP_DIRECTIONAL_LAYER_OVERRIDE.md`.

Status: **STATIC PASS / RUNTIME RETEST REQUIRED**

This focused pass corrects three live issues without changing Shirt art, native sleeves, drawstrings, side hood pixels, back hood pixels, semantic recipes, weather rules, or scale.

## 1. Front hood-down anchor and size

### Root cause

The previous visible front fold used a 16×32 Hat frame with opaque pixels in source rows 0–6 and effective `HeadPosition (0,32)`. That placed the generated fold in the head zone.

The earlier origin was derived from the supplied reference pack's nominal lowered-front Hat model. The reference's actual lowered-front frame is completely transparent, however, so that model provides no visible front-art calibration. Applying its nominal Scale-4-to-Scale-2 conversion to our newly visible front art was invalid.

### Correction

- front frame: `16×32` → `24×32`;
- opaque horizontal span: 14 cells → 22 cells for the regular fold;
- `HeadPosition`: `(0,32)` → `(4,0)`;
- draw order remains `Before Player`;
- `HideHair` remains false;
- fold depth: 7 → 8 logical rows;
- shape now grows from a narrow neck crest into a shallow shoulder-wide mass, then folds inward.

`X=4` centers the wider 24-cell source over the existing 16-cell Shirt footprint. `Y=0` uses the torso-level lowered-hood contract already proven by the acceptable side view. The Farmer is still responsible for masking the complete center fabric.

Right, back, and left lowered pixels are byte-identical to the previous build. The Shirt texture hash is also unchanged.

Because the front and side models now have different source widths, the static Hat no longer relies on width-dependent animation frame stepping. Front/right/back use explicit source rows Y `0/32/64` with `Frame 0`; left reuses Y 32 with flipping. This prevents the 24-wide front from changing which pixels a 16-wide side model selects.

## 2. Hood-up front opening

### Root cause

The raised-front opening existed only over logical Y 11–26, leaving a closed lower rim across Y 27–31. Runtime then combined that lower band with the slightly low `HeadPosition.Y=28`, causing the hood to cover too much of the lower face and mouth.

### Correction

- raised-front `HeadPosition.Y`: `28` → `30`, moving the Scale-2 Hat four display pixels upward;
- opening begins at logical Y 9 instead of 11;
- opening remains transparent through Y 31 instead of ending at 26;
- temple/cheek side framing and the top arch remain intact;
- no side/back anchor changed.

This is a rim/opening correction, not a larger hood redesign. Static validation now rejects any opaque raised-front cell in the central lower-face corridor `(x 12–19, y 27–31)`.

## 3. Back directional layering

### Root cause

Back hoods used `Before Hair`. That target is unstable when a raised hood uses `HideHair=true`: the Hair layer may not exist in the active layer list. A relative move against a missing target can place the Hat at the back of the ordered layers, which matches the observed hood-behind-player result.

### Correction

Lowered BackHat uses:

```json
"DrawOrderOverride": {
  "Preposition": "After",
  "AppearanceType": "Shirt"
}
```

The generated Shirt is always present in the preset. `After Shirt` therefore gives the lowered back a stable direction-specific target and puts it above the Farmer and upper garment.

The subsequent hood-up live audit superseded the raised-back portion of this approach. All raised directions now use native topmost Hat order; see `reports/HOOD_UP_DIRECTIONAL_LAYER_OVERRIDE.md`.

## Minor art polish

Only two small structural changes were made:

- the lowered-front fold gained a wider shallow shoulder rhythm and one additional fold row;
- the raised-front rim was opened through the bottom and lifted.

No extra motif, noise, decoration, or palette role was added.

## Outputs

- Corrected weather Hat: `output/fashionsense/hoodie-weather-test/weather-hood.png`
- Updated directions: `output/fashionsense/hoodie-weather-test/HOOD_DOWN_DIRECTIONS.png` and `HOOD_UP_DIRECTIONS.png`
- Front lowered A/B: `output/comparisons/FRONT_HOOD_DOWN_BEFORE_AFTER.png`
- Raised-front A/B: `output/comparisons/HOOD_UP_FRONT_BEFORE_AFTER.png`
- Back layer diagnostic: `output/comparisons/BACK_HOOD_LAYER_ORDER.png`
- Updated state comparison: `output/comparisons/WEATHER_HOOD_STATE_COMPARISON.png`
- Focused test root: `test-packs/fashionsense/RNG-Clothing-Hoodie-Weather-Test/`

Static validators pass. No runtime success is claimed until the corrected pack is retested.
