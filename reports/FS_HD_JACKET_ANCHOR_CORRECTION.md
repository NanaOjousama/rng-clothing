# Fashion Sense HD jacket torso-anchor correction

## Scope

This correction changes only Fashion Sense placement metadata for the existing Mistral Lapel Layer Jacket HD POC. The 16×16 artwork, `Scale: 2`, source rectangles, mask colors, sleeve colors, V2 semantic recipe, vanilla renderer, and structural grammar are unchanged.

## Root cause

Fashion Sense 7.5.0 draws a shirt with:

```text
position + FarmerOrigin + nativeFeatureOffset
origin = FarmerOrigin + BodyPosition
scale = ShirtModel.Scale × FarmerDrawScale
```

Installed Stardew Valley 1.6.15 supplies the normal standing Farmer origin `(0,32)`. The default 8×8 shirt is drawn at scale 4. The HD shirt is drawn at scale 2. Keeping `BodyPosition` at zero changed how far the nonzero Farmer origin moved the texture:

```text
default Scale 4: 32 - 32×4       = -96
old HD Scale 2:  32 - (32+0)×2   = -32
```

The old HD texture was consequently 64 display pixels lower than the default torso position. This was an anchor/scale interaction, not an artwork, source-frame, alpha, or visibility problem.

## Calculated correction

At `Scale: 2`, each positive BodyPosition Y source pixel moves the shirt up two display pixels. The calibration is:

| BodyPosition Y | Upward correction | Residual low offset |
|---:|---:|---:|
| 0 | 0 px | 64 px |
| 8 | 16 px | 48 px |
| 16 | 32 px | 32 px |
| 24 | 48 px | 16 px |
| 32 | 64 px | 0 px |

The corrected value is therefore:

```json
"BodyPosition": { "X": 0, "Y": 32 }
```

It is applied identically to `FrontShirt`, `BackShirt`, `LeftShirt`, and `RightShirt`. Fashion Sense's direction/frame feature offsets are separate from BodyPosition and remain enabled. `DisableNativeOffset` is omitted/false; it is not the fix because it controls native animation feature offsets, not the Scale-dependent SpriteBatch origin term.

Fashion Sense also applies `(4 - model.Scale) × 32` to UI Y positioning. At Scale 2 that is +64 display pixels; `BodyPosition.Y=32` contributes -64 display pixels, so the same correction is consistent with its UI path rather than requiring direction- or UI-specific art.

## Preservation and validation

- Existing Fashion Sense `shirt.png` SHA-256: `36615ec513e583c2e6b0e78d929bc7b2f59236f25cd511e2f754e961c80dbdee`.
- Existing vanilla Mistral PNG SHA-256: `19b63011cc370bace898e1324c04c87a7fb3e710051c2dffa6b82f3a32066cf4`.
- Pack refresh mode writes only `manifest.json`, `shirt.json`, and `README.md`; it refuses to proceed if the pack texture differs from the existing generated texture.
- The corrected pack passes the static Fashion Sense 7.5.0 source contract. A final in-game `fs_reload` check is still required to convert the calculated anchor into runtime-confirmed placement.

