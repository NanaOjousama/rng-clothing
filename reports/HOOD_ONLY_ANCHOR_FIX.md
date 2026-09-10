# Hoodie Hat-Only Runtime Anchor Fix

## Result

The confirmed-working Shirt, native animated sleeves, and in-Shirt drawstrings are unchanged. Only the shared Fashion Sense `Hat`/hood positioning contract was corrected.

The rebuilt test pack is version `1.2.0`. Static validation passes, but the corrected Hat positions remain `EXPERIMENTAL` until the user retests them in Stardew.

## Failing component

Every coordinated preset equips its hood through:

```text
HatId = RNGClothing.FashionSense.HoodieLayerCorrection/Hat/<garment name> Hood
```

The Hat appearance was the only component still appearing under the Farmer. Shirt placement, native arms colored through `SleeveColors`, and Shirt-integrated drawstrings were already correct in live gameplay.

## Root cause

The higher-density hood doubles the reference logical dimensions and changes Fashion Sense draw scale from 4 to 2. The old conversion doubled the reference `HeadPosition` coordinates directly:

```text
old HD HeadPosition = 2 * reference HeadPosition
```

That is incomplete for a Fashion Sense Hat. In 7.5.0, `DrawManager.DrawAppearance` passes the Farmer draw origin into `SpriteBatch.Draw`, then adds the Hat's `HeadPosition` to that origin. The normal Farmer 16x32 draw origin is `(0,32)`.

For a Scale-2 asset to occupy the same screen position as the equivalent Scale-4 reference asset, the correct conversion is:

```text
HD HeadPosition = Farmer draw origin + 2 * reference HeadPosition
                = (0,32) + 2 * reference HeadPosition
```

The old conversion omitted the retained `+32` logical Y origin. Since the Hat draws at Scale 2, that omission displaced the complete hood by:

```text
32 logical origin units * Scale 2 = 64 display pixels downward
```

That is why only the hood appeared beneath the player while body-relative Shirt content remained correct.

## Exact correction

No X coordinate changed. Every Hat `HeadPosition.Y` gained the missing `+32` term.

### Hood up

| Direction | Old | Corrected |
|---|---:|---:|
| Front | `(-4,-4)` | `(-4,28)` |
| Right | `(-4,-6)` | `(-4,26)` |
| Back | `(-4,-6)` | `(-4,26)` |
| Left | `(-4,-6)` | `(-4,26)` |

### Hood down

| Direction | Old | Corrected |
|---|---:|---:|
| Front | `(0,0)` | `(0,32)` |
| Right | `(-6,-32)` | `(-6,0)` |
| Back | `(-12,-34)` | `(-12,-2)` |
| Left | `(-18,-32)` | `(-18,0)` |

## Preserved Hat behavior

- Category remains `Hat`.
- Hood-up frames remain 32x32 logical pixels at Scale 2.
- Hood-down frames remain 16x32 logical pixels at Scale 2.
- `StartingPosition` and directional source frames are unchanged.
- Hood-up continues to hide hair.
- Hood-down continues to preserve hair.
- Hood-down side views remain before `Player`.
- Hood-down back remains before `Hair`.
- Hat artwork and color masks are unchanged.
- Preset Hat IDs are unchanged.

## Working components preserved

A before/after hash comparison of all packed Shirt PNG and JSON files produced no differences. The correction did not change:

- Shirt art or `BodyPosition (0,32)`;
- `SleeveColors` or native animated arms;
- in-Shirt drawstrings;
- semantic recipes;
- preset Shirt selection.

## Validation

`tools/validate_hoodie_layer_correction.py` now rejects any recurrence of the old Hat origins. It requires the exact hood-up and hood-down direction maps listed above, along with the existing frame, scale, source-position, hair, draw-order, mask, alpha, and preset checks.

The focused preview is `output/fashionsense/hoodie-layer-correction/HOOD_ONLY_ANCHOR_VALIDATION.png`. It displays the actual generated Hat frames and each corrected `HeadPosition`; it is a contract diagnostic, not a fake runtime screenshot.

