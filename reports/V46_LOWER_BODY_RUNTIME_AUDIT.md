# V4.6 Lower-Body Runtime Audit

## Evidence boundary

This audit targets installed Stardew Valley **1.6.15.24356** and installed Fashion Sense **7.5.0**. The installed Fashion Sense manifest declares minimum game version 1.6.14. Its DLL is 404,992 bytes, SHA-256 `28ea84800dadae414e8190e12b5e94f0db57184c0932452ebe99cd061e6412a6`.

Fashion Sense source and its installed-source official Pants/Shoes examples establish data contracts and selection behavior. They do **not** establish that the four generated V4.6 assets pass gameplay. Every runtime outcome below is therefore `NOT TESTED` unless it describes framework source behavior rather than visual success.

## Authoritative Fashion Sense contracts

### Fitted Pants

- Asset type: `Pants/<appearance>/pants.json|png`, with Front/Back/Right/Left `PantsModel` records.
- Model properties used: `StartingPosition`, `BodyPosition`, `PantsSize`, `Scale`, `DisableNativeOffset`, `ColorMaskLayers`, `UniformAnimation`, `HideLegs`, `HideShadow`, and water/bathing visibility.
- Logical source frame: **16×32** at Scale **4**.
- Generated atlas: **96×688**, six logical frames per row, capacity 126 frames.
- Anchor: `BodyPosition (0,-1)`, copied from Fashion Sense's `SimplePantsTemplate` runtime contract.
- Offset: `DisableNativeOffset=true`. Every full source frame already encodes its pose-relative lower-body position.
- Animation selection: the official template maps `CurrentFarmerFrame` 0–125 directly to source frame 0–125 for Front/Right/Left. Back has records 1–125. The source coverage is intentionally empty in frames 47, 118, and 119; V4.6 preserves those hidden/empty states instead of inventing geometry.
- Layer: Fashion Sense's Pants layer. V4.6 uses `HideLegs=false` and `HideShadow=false`; it overlays the native base rather than replacing leg anatomy.
- Visibility: hidden while swimming and while bathing clothes are active.
- Recolor: one `ColorMaskLayers` entry covers the generated grayscale material ramp; outline and controlled utility accents remain fixed.

### Footwear

- Asset type: `Shoes/<appearance>/shoes.json|png`, with four `ShoesModel` records.
- Model properties used: `StartingPosition`, `BodyPosition`, `ShoesSize`, `Scale`, `DisableNativeOffset`, `ColorMaskLayers`, `UniformAnimation`, `DrawBeforePants`, and water/bathing visibility.
- Logical source frame: **16×32** at Scale **4**.
- Generated atlas: **96×672**, six frames per row, capacity 126 frames.
- Anchor: `BodyPosition (0,0)` from Fashion Sense's `ShoesTemplate`.
- Offset: `DisableNativeOffset=true` for the same full-pose reason as Pants.
- Animation selection: the official Shoes template uses direction-specific conditional maps over source frames 0–125. Front has 46 records, Back 29, Right 30, Left 30. Conditions are primarily `CurrentFarmerFrame`, with disambiguation for `IsPassingOut` and `IsWatering` where the same Farmer frame can represent different actions.
- Layer: Shoes, explicitly `DrawBeforePants=true`, so trousers can cover the upper shoe/boot edge.
- Visibility: hidden while swimming and while bathing clothes are active.
- Recolor: one material mask layer; sole, outline, and small Rare fixed accents retain value hierarchy.

## Draw and frame math

Fashion Sense starts with the model's 16×32 source rectangle. For animation frame `n`, `AppearanceHelpers.GetAdjustedSourceRectangle` advances by `n × 16`, wraps at the 96-pixel texture width, and advances by 32 pixels per atlas row. All positions and dimensions are integers. The model's Scale 4 draw uses no resampling authored by this project.

The V4.6 data builder extracts only binary alpha/coverage from official example textures. It records per-frame row spans, occupied bounds, and official JSON animation records in `generator/data/fashionsense/v46/lower_body_frame_contracts.json`. It does not retain example colors, motifs, or surface art.

## Runtime-state assessment

| State | Pants contract behavior | Footwear contract behavior | V4.6 runtime evidence |
|---|---|---|---|
| Idle, four directions | current Farmer frame selects full source pose | direction-specific current-frame record | NOT TESTED |
| Walk | full source atlas follows current frame | official directional mappings | NOT TESTED |
| Run | full source atlas follows current frame | official directional mappings | NOT TESTED |
| Axe/pickaxe/hoe/scythe | pose follows current frame where Farmer is drawn | mapped source records where conditions match | NOT TESTED |
| Watering | current-frame mapping | explicit `IsWatering` disambiguation exists | NOT TESTED |
| Fishing | current-frame mapping | relevant source records exist in official template | NOT TESTED |
| Hold/eat/drink | current-frame mapping | relevant source records exist | NOT TESTED |
| Sitting/get-up | current-frame mapping only; no deformation | condition/frame selection only; no deformation | NOT TESTED |
| Horse mount/ride/dismount | current-frame mapping only | condition/frame selection only | NOT TESTED |
| Swimming | LayerManager hides Pants | LayerManager hides Shoes | source-confirmed hide rule; transition NOT TESTED |
| Bathing suit | LayerManager hides Pants | LayerManager hides Shoes | source-confirmed hide rule; transition NOT TESTED |
| Bed/sleep/pass-out | full frame mapping if Farmer layer is drawn | passing-out conditions exist; bed draw remains game-owned | NOT TESTED |
| Festival/special poses | frames 0–125 available for Pants | only records included by official Shoes template | NOT TESTED; unsupported pose fallback must be observed |
| Remote farmer | FS draws equipped model selected from Farmer data | same | NOT TESTED |
| Equip/unequip | first-class Hand Mirror Pants category | first-class Hand Mirror Shoes category | NOT TESTED |
| Dye/color | `ColorMaskLayers` source path is supported | same | NOT TESTED in Hand Mirror/multiplayer |

## Framework-owned versus generated behavior

Fashion Sense owns appearance loading, facing-model selection, condition evaluation, source-rectangle selection, layer ordering, Hand Mirror selection, color-mask rendering, and Farmer appearance data. Stardew owns the Farmer animation state and current frame.

V4.6 owns binary coverage masks, semantic zone translation, frame-relative surface placement, generated RGBA atlases, content-pack JSON, and static diagnostics. It cannot infer runtime success from those files.

## Development diagnostics

No new SMAPI debug mod is necessary. Fashion Sense 7.5.0 already provides:

- `fs_display_player_frames`
- `fs_display_movement`
- `fs_record_frames`
- `fs_play_next_frame`
- `fs_clear_recorded_frames`
- `fs_freeze_self`
- `fs_reload RNGClothing.FashionSense.V46LowerBodyRuntime`

For Pants, current Farmer frame and generated source frame are normally the same number. For Shoes, compare the shown Farmer frame and action with that direction's `UniformAnimation` condition in the pack JSON.

## Compatibility and performance risks

- The masks target the default Farmer's official frame envelopes. Body replacers with changed legs/feet are outside this proof.
- `HideLegs=false` is conservative but can expose native geometry if generated coverage is inadequate.
- The Rare boot adds a two-cell frame-relative shaft. It is the highest-risk geometry in this pack and must be checked in sitting, horse, tool, and exceptional poses.
- A full atlas increases texture memory relative to V4.5 compact prototypes, but all four remain tiny: two 96×688 and two 96×672 RGBA textures are about 1.0 MiB uncompressed in total. Source-frame changes do not add draw calls. One color-mask layer can add cached mask texture/draw work.
- Fashion Sense is SMAPI/.NET code with no Windows-only path found in the inspected contracts. This does not substitute for Steam Deck performance observation.
- Appearance IDs/colors are designed for Farmer data and remote rendering, but peer synchronization and missing-pack behavior remain unverified for these exact assets.

## Audit conclusion

The runtime architecture is materially stronger than V4.5's compact four-phase prototype: it uses full installed Fashion Sense example contracts and complete pose envelopes. It is safe enough for a controlled manual test pack. It is not yet a `RUNTIME_PASS`, and no lower-body art-quality or production promotion follows from this audit.
