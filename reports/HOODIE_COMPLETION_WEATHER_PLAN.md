# Hoodie Completion and Weather-Hood Plan

## Outcome

The hood system now has complete original front, right, back, and left art for both lowered and raised states. The focused Harbor Haze runtime test changes one generated Hat appearance between those states using Fashion Sense 7.5.0 conditions. Shirt pixels, native animated `SleeveColors`, and Scale 2 remain unchanged; front and back Hat contracts incorporate the later live-runtime corrections documented separately.

Static validation passes. Runtime promotion remains **EXPERIMENTAL** until the new front occlusion, weather switch, and hair behavior are observed in game.

## Sources inspected

The implementation was checked against the installed/local Fashion Sense 7.5.0 source and the supplied Hoods & Hoodies content pack:

- `Framework/Managers/LayerManager.cs` uses an active animation frame's `DrawOrderOverride` in preference to the model-level order.
- `Framework/Models/Appearances/AnimationModel.cs` exposes per-frame `Offset` and `DrawOrderOverride`.
- `Framework/Utilities/AppearanceHelpers.cs` applies Hat `HideHair` at the model level.
- `Framework/Interfaces/API/Api.cs` exposes `SetAppearance`, which is relevant to a future manual toggle.
- The reference `conditions.json` defines precipitation as rain or snow and combines it with `IsOutdoors`.
- Its dynamic Hat selects raised/lowered frames conditionally. Its Content Patcher companion edits Fashion Sense's appearance-data asset to alter `HideHair` and directional draw order.
- Its lowered side views use `Before Player`; its lowered back uses `Before Hair`. That established that head-relative hood art can safely use directional layer changes. The new front-before-Player experiment is our own generalized use of the same supported Fashion Sense mechanism, not copied reference art.

The installed implementation was treated as authoritative. No Fashion Sense source or reference pixels were copied into generated content.

## Completed hood art

### Hood down

- **Front:** one complete, connected low folded mass. It has no hairstyle-shaped hole. The Hat animation draws it `Before Player`, so the Farmer is intended to occlude the center while the left/right shoulder folds remain visible. Normal Hair stays enabled and follows its normal order.
- **Right/left:** direction-reconstructed folds sit behind the Player, retaining the neck/shoulder drape.
- **Back:** a wider folded hood with a restrained center fold draws explicitly after Shirt, keeping it above the Farmer/torso and below normal Hair.
- **Anchor contract:** front `(-8,0)`, right `(-6,0)`, back `(-12,-2)`, left `(-18,0)` at Scale 2. Front alone uses a 24×32 source frame; side/back remain 16×32. The corrected front X is a SpriteBatch-origin value: decreasing it from `4` to `-8` moves the unchanged fold 24 display pixels right and centers it over the 16-cell torso.

The front strategy is deliberately a draw-order solution rather than an art cutout. The diagnostic image labels its neutral Player block as a schematic; it is not a fabricated Farmer composite.

### Hood up

- Four direction-specific 32×32 logical frames are present.
- The visible raised shape now occupies about the same optical fraction of its cell as the strongest reference hood: it no longer fills the entire frame.
- Front has a stepped face opening and restrained lining edge; sides have a directional opening; back has a simple central fold.
- The art uses direct integer logical pixels and binary alpha.
- **Anchor contract:** front `(-4,30)`, right/back/left `(-4,26)` at Scale 2. The front is four display pixels higher than the earlier runtime build.

The frame is 32×32 because it is a twice-density reconstruction of a 16×16 Scale-4 Hat footprint. It is not a nearest-neighbor enlargement of reference or previous art.

## Weather auto-switch

The focused test uses one 128×64 Hat atlas with eight 32×32 cells:

| State | Front | Right | Back | Left |
|---|---:|---:|---:|---:|
| Hood up | 0 | 1 | 2 | 3 |
| Hood down | 4 | 5 | 6 | 7 |

Fashion Sense conditions select:

- outdoors with rain, storm-as-rain, or snow → **hood up**;
- indoors, or outdoors without precipitation → **hood down**.

Each lowered animation frame supplies the difference between the raised and lowered calibrated `HeadPosition` as its integer `Offset`. It also supplies the appropriate per-frame draw order. This keeps both states in one Hat appearance without shifting either state toward the feet.

The paired Content Patcher pack does **not** choose the hood frame. It only changes the Hat's model-level hair policy because Fashion Sense 7.5.0 does not provide animation-frame-level `HideHair`.

## Hair policy

Current default for the side-Hat visual-mask test: `HoodUpHairMode = HideBackOnly`.

- Raised front/right/back/left use native Fashion Sense Hat order, which is topmost after Player, Shirt, Hair, and Sleeves. The transparent face opening reveals the face and permitted hair beneath it.
- Bangs and front fringe can remain visible.
- Long or very large hairstyles may obscure more hood fabric; this is intentional natural occlusion, but some styles may overwhelm the hood.
- Lowered hood always preserves normal Hair.

Side-incompatible fallback: `HoodUpHairMode = PreserveFrontOnly`.

- Front/right/left set directional `HideHair=false`; the topmost side Hat masks lower/rear Hair with opaque fabric.
- Back sets directional `HideHair=true`.
- This retains bangs and upper/front side hairstyle identity while preventing rear-hair conflict.

Fallback: `HoodUpHairMode = HideHair`.

- Content Patcher sets Hat `HideHair` while the wet outdoor rule is active.
- This is the reliable option when a hairstyle escapes or visually consumes the raised hood.

A generic `BangsOverlay` was not implemented. Fashion Sense does not provide a reliable way to extract only the bangs from arbitrary vanilla and custom hairstyles. Building such an extractor would be a separate body/hair compatibility system and would exceed this experiment.

## Manual toggle recommendation

Do not implement a manual toggle until the automatic state and hair modes pass runtime review. The clean future solution is a very small optional SMAPI test helper, separate from production generation:

1. export three coordinated Hat appearances for a hoodie: `Auto`, `Down`, and `Up`;
2. expose a keybind and console fallback that cycles `Auto → Down → Up`;
3. call Fashion Sense's public `SetAppearance(Type.Hat, packId, appearanceName, manifest)` API;
4. store the player's selection as `Auto/Down/Up` in mod data;
5. let `Auto` return control to the conditional Hat.

Swapping an entire preset is not recommended: it would unnecessarily replace unrelated appearance choices. Content Patcher alone also has no ergonomic player-controlled toggle state. No DLL or manual toggle was added in this pass.

## Critical limitations

- Static validation proves source rectangles, anchors, offsets, conditions, draw order metadata, alpha, and deterministic pixels. It cannot prove live occlusion against every Farmer animation.
- The new 24-cell front-before-Player lowered hood is supported by Fashion Sense's general draw-order system, but the exact amount of visible shoulder fabric needs live review.
- PreserveHair is intentionally permissive. HideBackOnly remains useful for hairstyles without side clipping; HideHair remains the safest fallback for large front hair.
- The raised hood uses one layer before Hair. A more sophisticated rear-fabric/bangs/front-rim sandwich would require at least two coordinated head layers and would reintroduce the anchor and ordering complexity already shown to be risky.
- Weather state selection is FS-native and live. The Content Patcher hair-policy edits use the same day/location update pattern as the reference pack; after forcing weather with debug tools, changing location is the safest way to force immediate hair-policy reevaluation.

## Outputs

- Renderer: `generator/renderers/fashionsense/hoodie_weather.py`
- Completed hood grammar: `generator/renderers/fashionsense/hoodie_layers.py`
- Weather generator: `tools/generate_hoodie_weather_test.py`
- Static validator: `tools/validate_hoodie_weather_test.py`
- Focused output: `output/fashionsense/hoodie-weather-test/`
- Weather comparison: `output/comparisons/WEATHER_HOOD_STATE_COMPARISON.png`
- Front layering diagnostic: `output/comparisons/HOOD_DOWN_FRONT_LAYERING.png`
- Front centering diagnostic: `output/comparisons/FRONT_HOOD_DOWN_CENTERING.png`
- Raised directional layer audit: `output/comparisons/HOOD_UP_DIRECTIONAL_LAYER_AUDIT.png`
- Test root: `test-packs/fashionsense/RNG-Clothing-Hoodie-Weather-Test/`

The test root contains one Fashion Sense content pack and one Content Patcher hair-policy pack. Nothing was installed automatically.
