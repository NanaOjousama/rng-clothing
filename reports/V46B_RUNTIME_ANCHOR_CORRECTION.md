# V4.6B Runtime Anchor Correction

## Status

The shared runtime contract was corrected and all six V4.6B appearances were
rebuilt. Static validation passes. Runtime status remains **EXPERIMENTAL —
RETEST REQUIRED**.

## 1. Exact root cause

The 32×64 Scale-2 backend inherited the official 16×32 Scale-4 Pants
`BodyPosition.Y=-1` and naively multiplied it to `-2`. That treated
BodyPosition as a simple positional offset. Fashion Sense actually adds
BodyPosition to the Farmer draw **origin**, then scales the combined origin.

For a normal world Farmer, the installed Stardew 1.6.15 draw origin is
`(0,32)`. Fashion Sense draws the custom appearance using:

`topLeft = position + origin - (origin + BodyPosition) × appearanceScale`

The official Scale-4 Pants reference therefore has relative Y:

`32 - (32 + -1) × 4 = -92`

The failed V4.6B value produced:

`32 - (32 + -2) × 2 = -28`

That is **64 display pixels too low**. The equivalent Scale-2 value is:

`32 - (32 + 30) × 2 = -92`

Therefore the correct shared BodyPosition is **`(0,30)`**.

Because V4.6B intentionally uses `HideLegs=false`, the native Farmer
legs/pants remained near the character while the entire custom appearance was
drawn 64 pixels below. This made the runtime symptom look like a correctly
placed upper portion plus a detached lower chunk. The lower chunk was not a
second source rectangle or accessory layer; it was the complete generated
Pants appearance at the wrong draw origin.

## 2. Affected frame/state

The bad BodyPosition belonged to all four Pants models and was independent of
the selected animation frame. It affected:

- standing front, right, back, and left;
- all walking/running frames;
- tool, sitting, riding, and other mapped states;
- Pants, Shorts, and Skirts, because all use the same FS Pants contract.

The visible geometry varied by frame, but the 64-pixel anchor error was
constant.

## 3. Old contract

| Property | Old value |
|---|---|
| `PantsSize` | 32×64 |
| `Scale` | 2 |
| `BodyPosition` | `(0,-2)` |
| Native Farmer origin | `(0,32)` |
| Relative top-left Y | -28 |
| Error from official Pants placement | +64 display pixels |

## 4. Corrected contract

| Property | Corrected value |
|---|---|
| `PantsSize` | 32×64 |
| `Scale` | 2 |
| `BodyPosition` | `(0,30)` |
| Native Farmer origin | `(0,32)` |
| Relative top-left Y | -92 |
| Error from official Pants placement | 0 |

No per-garment adjustment was added. Every direction and all six prototypes
consume the same corrected contract.

## 5. Other contracts audited

- **Frame dimensions:** 32×64 at Scale 2 are valid and produce the same 64×128
  displayed frame footprint as 16×32 at Scale 4.
- **Source rectangles:** Fashion Sense computes rows from `frame × width`, pack
  texture width, and the model's StartingPosition. Every V4.6B rectangle remains
  inside its assigned direction block.
- **Direction mapping:** remains Front/Down frame 0, Right frame 6, Back/Up frame
  12, Left frame 6 with `LeftPants.Flipped=true`.
- **Animation mapping:** the installed official SimplePantsTemplate
  `UniformAnimation` remains intact. No idle/walk/sitting override created the
  detachment.
- **`DisableNativeOffset`:** remains true, as in the official full-frame Pants
  template. It was not the anchor error.
- **Layer type:** every appearance remains a Fashion Sense `PantsModel`; no
  accessory/body/footwear type leakage was found.

## 6. Recurrence guards

`tools/validate_generator_v46b.py` now fails if:

- the native origin is not `(0,32)`;
- the official source BodyPosition/Scale and target BodyPosition/Scale do not
  resolve to the same display top-left;
- any direction does not use `BodyPosition (0,30)`;
- any animation source rectangle exceeds the texture width;
- any source rectangle leaves its assigned direction block;
- the orientation/left-flip contract regresses.

## Diagnostic garment

The minimal `V4.6B Scale-2 Anchor Probe` uses a magenta waistband, cyan body,
and gold termination. It was generated outside the six-item test pack at:

`output/fashionsense/v46b-runtime-anchor-diagnostic/`

Its sheet renders front/right/back/left standing poses and the first front walk
frame using the corrected shared contract:

`output/comparisons/V46B_RUNTIME_ANCHOR_DIAGNOSTIC.png`

This is a static contract simulation, not runtime proof.

## Rebuild result

All six V4.6B test-pack JSON models now use `BodyPosition (0,30)`. Their garment
PNG art is unchanged. Test-pack version is 0.1.1 so an installed pre-correction
copy can be identified and replaced.

