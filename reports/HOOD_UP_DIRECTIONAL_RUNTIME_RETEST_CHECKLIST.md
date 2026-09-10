# Hood Directional Runtime Retest

Status: **EXPERIMENTAL — LIVE RETEST REQUIRED**

Close Stardew and SMAPI. Use FS version `1.4.0` and replace the paired `[CP]` child with version `1.2.0`, then restart through SMAPI.

Equip **Hoodie Weather Test - Harbor Haze** through Fashion Sense presets.

## Hood up — wet outdoors

- [ ] Front: hood fabric sits above/around the head instead of behind it.
- [ ] Front: face opening remains visible and mouth is not swallowed.
- [ ] Right: side rim and rear hood mass are clearly visible.
- [ ] Left: side rim and rear hood mass are clearly visible.
- [ ] Back: hood is visible on the upper-back/back-of-head silhouette.
- [ ] Back: Hair or Sleeves do not bury the hood.
- [ ] PreserveHair: bangs appear through the transparent opening and do not cover the hood rim.
- [ ] HideBackOnly: front/right/left hair stays visible.
- [ ] HideBackOnly: back-facing hair is hidden and no longer conflicts with the hood.
- [ ] HideBackOnly: side hood fabric covers lower/rear side hair while upper/front hair remains visible.
- [ ] PreserveFrontOnly: front hair/bangs remain visible.
- [ ] PreserveFrontOnly: right/left/back hair is hidden and side clipping is gone.
- [ ] HideHair fallback: hood remains aligned with Hair hidden in every direction.

## Hood down — clear weather or indoors

- [ ] Front: fold is horizontally centered behind the neck/shoulders.
- [ ] Front: fold no longer drifts left.
- [ ] Front: Player naturally masks the middle while fabric shows on both sides.
- [ ] Front: record whether the now-centered 22-column fold still feels too small.
- [ ] Right/left/back: no regression from the prior build.

## Motion smoke test

- [ ] Walk front/right/back/left with hood up.
- [ ] Hold and use one basic tool in front and side views.
- [ ] Switch between clear/indoors and wet outdoors.
- [ ] Shirt, arms, native sleeves, and drawstrings remain unchanged.
- [ ] No component appears near the feet.

For a failure, record state, direction, hair mode/style, action, visible problem, and screenshot filename. Static validation does not promote the system beyond `EXPERIMENTAL`.
