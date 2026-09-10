# Hood-Up Hair Policy Refinement

> Superseded by live side-hair clipping evidence. See `reports/HOOD_UP_SIDE_HAIR_POLICY_REFINEMENT.md`; the new default is `PreserveFrontOnly`.

## Source finding

Fashion Sense 7.5.0 resolves the equipped `HatContentPack` through `GetHatFromFacingDirection(facingDirection)` before constructing appearance metadata. `LayerManager` then calls `AppearanceHelpers.IsHatHidingHair` on that active directional model. Therefore `FrontHat`, `RightHat`, `BackHat`, and `LeftHat` can carry different `HideHair` values; hiding back hair does not inherently hide front or side hair.

The existing Content Patcher edit already targets `Data/PeacefulEnd/FashionSense/AppearanceData` and can update those four nested Hat models independently. No DLL, renderer patch, extra appearance, or artwork change is needed.

## Final configuration vocabulary

| Mode | Front | Right | Back | Left |
|---|---|---|---|---|
| `PreserveHair` | preserve | preserve | preserve | preserve |
| `HideBackOnly` | preserve | preserve | hide | preserve |
| `HideHair` | hide | hide | hide | hide |

Hood-down always writes `HideHair=false` for all four directions, regardless of the configured raised-hood mode.

`PreserveHair` remains the generated default because the new directional mode has not yet been observed live. If runtime confirms that Hair disappears only when facing back and returns immediately when turning front/side, `HideBackOnly` should become the default in the next revision.

## Implementation

The Content Patcher child is version `1.1.0` and accepts exactly:

```json
{
  "HoodUpHairMode": "PreserveHair"
}
```

Change the value to `HideBackOnly` for the focused test. The wet-outdoor CP change then applies:

```json
{
  "FrontHat": { "HideHair": false },
  "RightHat": { "HideHair": false },
  "BackHat": { "HideHair": true },
  "LeftHat": { "HideHair": false }
}
```

The update timing remains `OnDayStart, OnLocationChange`, matching the existing weather hair-policy experiment. Fully restarting after editing config is the cleanest test procedure.

## Focused runtime checks

- Hood down, every direction: Hair remains visible.
- Hood up front: bangs/front fringe remain visible through the opening.
- Hood up right/left: Hair remains visible.
- Hood up back: Hair is hidden and the raised hood remains visible.
- Turn back → side → front: Hair returns in the non-back directions.
- No change to hood anchors, layer order, Shirt, sleeves, or drawstrings.
