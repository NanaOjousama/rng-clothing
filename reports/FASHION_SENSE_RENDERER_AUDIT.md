# Fashion Sense 7.5.0 renderer audit

Audit target: Fashion Sense **7.5.0**, official tag `v7.5.0`, commit `39e9e9e13c9f9a78416172e73a229cf8703ddb59`, against Stardew Valley 1.6.15. The official source, the 7.5.0 example pack, the official wiki, the release metadata, and current issue tracker were inspected. The source tag is authoritative where older wiki language differs.

This project emits a Fashion Sense content pack. It does not link against, copy, or redistribute Fashion Sense code or binaries. The dependency remains runtime-optional and the vanilla renderer is unchanged.

## Findings at a glance

- **Confirmed:** Fashion Sense can draw a 16×16 logical shirt frame at `Scale: 2`. The source passes `model.Scale * DrawTool.Scale` to `SpriteBatch.Draw`; the official scale documentation gives the same 16×16-at-2-equals-32×32 example.
- **Confirmed:** the official baseline shirt template is four 8×8 frames in an 8×32 PNG at the default `Scale: 4`. Both configurations therefore have a nominal 32×32 display box.
- **Confirmed:** `StartingPosition` and `ShirtSize` select a source rectangle. `BodyPosition` is added to the draw origin in source-pixel coordinates. Zero is the official compact-shirt anchor only at the default `Scale: 4`; a same-footprint `Scale: 2` shirt must compensate for Stardew's nonzero Farmer draw origin.
- **Confirmed:** a shirt's `SleeveColors` patches the three native Farmer sleeve tones. This retains Stardew's animated arm geometry and explicit slingshot handling without a separate custom Sleeves appearance.
- **Confirmed:** color masks are exact source-color lists. Fashion Sense builds a full-size mask texture per color-mask layer and applies the selected color multiplicatively at draw time.
- **Confirmed:** non-default scale has current risk evidence: the official tracker has open reports for Scale-based horseback misalignment, `DefaultColor` initialization, and Steam Deck lag. Source capability does not eliminate those runtime risks.
- **Runtime evidence:** the pack and texture draw in Fashion Sense 7.5.0, but the original `(0,0)` Scale-2 anchor rendered 64 display pixels low. The corrected `(0,32)` anchor is source/game-math validated and awaits an in-game reload check. Horse, tool, controller, multiplayer, and initial mask-color behavior remain unconfirmed.

## Content-pack and loader contract

Minimal current folder structure:

```text
RNG-Clothing-HD-Jacket-POC/
├── manifest.json
└── Shirts/
    └── MistralLapelLayerJacketHD/
        ├── shirt.json
        └── shirt.png
```

The manifest uses:

```json
"ContentPackFor": {
  "UniqueID": "PeacefulEnd.FashionSense",
  "MinimumVersion": "7.5.0"
}
```

The 7.5.0 loader recursively scans `Shirts`, reads folders containing `shirt.json`, requires `Name`, at least one directional model, a `ShirtSize` on every supplied model, and `shirt.png`. It then loads the texture, attaches the owner/content-pack ID, links each direction to the pack, and registers the appearance as `PackId/Shirt/Name`.

The wiki labels `StartingPosition`, `BodyPosition`, and `ShirtSize` required. Current source only explicitly rejects a missing `ShirtSize`; `TextureManager` fills a missing `StartingPosition` with `(0,0)`, while `BodyPosition` has a `(0,0)` model default. Generated content should still declare all three explicitly. Relying on implicit defaults would make frame overlap easy and reduce portability.

The `Format` field is a `Version` on the appearance content model. The wiki recommends setting it to the current Fashion Sense version; the POC uses `"7.5.0"`.

## Shirt model properties and draw behavior

| Property | Current 7.5.0 source behavior | POC value |
|---|---|---|
| `StartingPosition` | Integer top-left of the selected source rectangle. Animation changes this source rectangle by declared frame data. | `(0,0)`, `(0,16)`, `(0,32)`, `(0,48)` for front/right/left/back. |
| `ShirtSize` | Integer `Width` and `Length` used as the source-rectangle dimensions. Arbitrary compact rectangles are supported. | `16×16` each direction. |
| `Scale` | Float, default `4f`; passed to `SpriteBatch.Draw` as `model.Scale * DrawTool.Scale`. | `2.0`. |
| `BodyPosition` | Integer position added to the sprite origin before multiplication by the model scale; positive Y moves the texture upward. Animation `Offset` is added if active. | `(0,32)` in all directions, compensating the default Farmer origin when drawing at Scale 2. |
| `DisableNativeOffset` | When false, Farmer feature X/Y offsets and custom-body height offsets move the shirt with the current Farmer frame. | Omitted/false. |
| `Flipped` | Optional horizontal draw flip. | False; left is an authored mirrored logical frame. |
| `DisableGrayscale` | When true, author colors are preserved and color masks are disabled. | False, so the outer panel mask remains recolorable. |
| `ColorMaskLayers` | Named exact-color groups; a full-size mask texture is cached per layer and tinted during draw. | One `Outer Fabric` layer with five grayscale shade values. |
| `DefaultColor` | `GetAllAppearanceColors` uses this when no player color is stored. | Cool-neutral `[112,130,145]`; see runtime caveat below. |
| `SleeveColors` | Up to three values mapped to native darkest/medium/lightest sleeve tones; missing later values fall back to the previous tone. | Three outer-mask values: 76, 184, 224. |
| `HideSleeves` | Suppresses the native/custom sleeves layer when true. | False. |
| `DrawOrderOverride` | Can move an appearance before/after another type; 7.5.0 also supports per-animation-frame overrides. | Not used. |

### Exact scale/footprint result

World draw math:

```text
source width × model Scale = nominal displayed width
```

Therefore:

```text
official compact shirt: 8 × 4 = 32 display pixels
HD POC shirt:          16 × 2 = 32 display pixels
```

The logical canvas goes from 64 cells per direction to 256 cells per direction: **4× as many logical cells**, with each source cell half the display width/height. This is a genuine density increase rather than a larger nominal bounding box.

### Scale-2 anchor correction

Installed Stardew Valley 1.6.15 constructs the normal world Farmer draw origin as `(xOffset, (yOffset + 128 - boundingBoxHeight / 2) / 4 + 4)`. With the normal values `xOffset=0`, `yOffset=0`, and a 32-pixel Farmer bounding-box height, that is `(0,32)`. Fashion Sense passes `DrawTool.Origin + BodyPosition` as the SpriteBatch source origin and draws with `model.Scale * DrawTool.Scale`.

Ignoring position and native feature terms shared by both cases, the vertical term is:

```text
default shirt: 32 - 32 × 4       = -96
old HD shirt:  32 - (32 + 0) × 2 = -32   (64 display pixels too low)
fixed HD:      32 - (32 + 32) × 2 = -96
```

Therefore the calculated POC value is positive `BodyPosition: (0,32)`, not a negative Y. One BodyPosition source pixel moves the Scale-2 texture upward by two display pixels. `DisableNativeOffset` does not control this base-origin scaling; enabling it would suppress the Farmer frame/feature offsets the shirt needs while leaving the underlying scale mismatch unresolved.

There are two qualifications:

1. transparent contour cells make visible silhouettes differ even when the bounding boxes match;
2. Fashion Sense applies a special vertical correction while drawing for UI: `(4 - model.Scale) * 32`. At Scale 2 this adds 64 display pixels, while `BodyPosition.Y=32` subtracts 64. World and Hand Mirror placement should still both be rechecked at runtime.

## Direction mapping and animation ownership

`ShirtContentPack.GetShirtFromFacingDirection` confirms:

| Farmer direction | Model |
|---:|---|
| 0 | `BackShirt` |
| 1 | `RightShirt` |
| 2 | `FrontShirt` |
| 3 | `LeftShirt` |

The source allows missing directions and then falls back to the corresponding vanilla layer in broader renderer logic. This POC supplies all four to avoid a mixed custom/vanilla garment.

Static shirt art does not morph for walking or tools. Fashion Sense applies Farmer feature offsets based on the current frame, so the torso overlay follows normal bob/feature positioning. `UniformAnimation`, `IdleAnimation`, and `MovementAnimation` can select other texture frames and add offsets, conditions, subframes, lights, and draw-order overrides. The POC intentionally defines no extra shirt animation.

## Sleeves: what the framework owns and what we generate

Fashion Sense exposes a full separate Sleeves appearance type with per-direction `StartingPosition`, `BodyPosition`, `SleevesSize`, `Scale`, animation lists, `DrawBeforeShirt`, `DrawBehindHead`, `UseShirtColors`, shirt-tone masks, skin masks, and generic draw-order overrides. Current custom-sleeve drawing follows `who.armOffset`; it also has special slingshot subframe handling.

However, a separate Sleeves appearance is not automatically the shirt itself:

- it has its own equipped Fashion Sense ID and Hand Mirror category;
- a complete action-safe pack needs extensive Farmer-frame/condition mappings;
- the official comprehensive sleeve template is 192×672 with 16×32 source frames, while the smaller striped example is 208×96 and covers a narrower pose set;
- a fully custom high-density sleeve atlas would be a second POC, not a small part of this controlled shirt comparison.

For this POC the correct conservative method is `ShirtModel.SleeveColors` with no custom Sleeves appearance. `DrawPatch.ApplySleeveColorPrefix` replaces the native Farmer texture's three sleeve tones. The normal native sleeves path then draws the current Farmer/arm frame and has explicit slingshot handling. Consequences:

- **Confirmed framework/game-owned:** native arm geometry, Farmer-frame walking poses, `armOffset`, and the vanilla slingshot arm path.
- **Generated by us:** the three semantic jacket sleeve tones plus high-density shoulder/cuff transition pixels in the shirt frame.
- **Limitation:** the arm itself does not gain 2× logical geometry. The POC improves sleeve attachment and termination, not elbow/tool-pose anatomy.
- **Manual test still required:** standing, walking, every facing direction, basic tools, slingshot, carrying, and horseback.

## Color masks and dye behavior

The POC uses one recolorable outer-fabric layer. Its five grayscale values encode deep, shadow, base, light, and restrained highlight. The visible inner layer uses authored cool-neutral secondary RGB colors not listed in the mask, so it stays a stable contrasting under-layer. This preserves the V2 recipe's semantic color blocking without building a general Fashion Sense dye architecture.

The three `SleeveColors` are members of the first mask layer. Source checks those exact values and multiplies them by the active shirt color, which is how dyed native sleeves can follow the outer jacket.

Current caveat: the source has a `DefaultColor` path, but the official issue tracker contains an open **“Color Mask Layers `DefaultColor` Not Loading”** report. The README therefore instructs testers to set `Outer Fabric` once to RGB `112,130,145` if initial color or sleeve tint is unexpected. Until observed in 7.5.0 in game, default initialization and sleeve-default synchronization are **untested**, not confirmed.

## Draw order

Current `LayerManager` constructs the default sequence as Player, Shoes, Pants, Shirt, Hair, accessories, Sleeves, Hat. Back-facing Sleeves are moved before Hair. Shirts have no additional type-specific sort rule. Generic `DrawOrderOverride` and animation-specific overrides can change this.

The official wiki's older summary places Pants before Shoes and Sleeves before Accessories. Current 7.5.0 source is authoritative. The POC uses no override: the high-density shirt remains on the normal Shirt layer and native animated sleeves remain on the normal Sleeves path.

## Linux and Steam Deck assessment

### Platform contract

Fashion Sense 7.5.0 targets .NET 6 and is a SMAPI/Harmony mod using Stardew/MonoGame types. Its manifest requires Stardew 1.6.14 or later and has no declared native platform library. This architecture is platform-neutral through the game's supported SMAPI/.NET runtime; the content pack itself is JSON and RGBA PNG.

That does **not** prove Steam Deck performance. Relevant current evidence:

- the release history records earlier Linux compatibility work;
- the official tracker has an open Steam Deck lag report describing inconsistent severe cost when Fashion Sense is combined with a very large mod list and reflection/UI rendering, including controller menu lag;
- an open issue reports horseback position misalignment when appearances use non-default `Scale`;
- current issue listings also include a massive-content-pack crash report.

These reports do not show that one 16×64 static shirt is expensive. They do show that “SMAPI/.NET is cross-platform” is not enough to declare Steam Deck success.

### Texture and animation cost

Raw RGBA8 comparison:

| Resource | Pixels | Raw RGBA bytes |
|---|---:|---:|
| Vanilla generated atlas | 256×32 = 8,192 | 32 KiB |
| Vanilla four used 8×8 frames | 256 | 1 KiB |
| FS POC source texture | 16×64 = 1,024 | 4 KiB |
| FS four used 16×16 frames | 1,024 | 4 KiB |

The tight Fashion Sense file allocates less raw source texture than the padded vanilla atlas, while representing four times as many per-frame logical cells. Fashion Sense also retains a cached and mutable texture and creates one full-size color-mask texture for this POC. A lower-bound pixel-store estimate is therefore roughly 12 KiB for cached source + active texture + one mask, excluding framework, driver, SpriteBatch, and UI overhead. Exact GPU allocation was not measured.

Animations enlarge the source texture approximately linearly with frame count and add condition/animation updates. Separate fully animated sleeves can dwarf this static shirt (the official 192×672 sleeve template is about 504 KiB as one raw RGBA source before mask copies). This POC has no shirt animation and no custom sleeve texture.

For tens of similarly tight static shirts, texture memory alone should remain small relative to the game, but the issue reports make large-pack/UI/reflection behavior an empirical Steam Deck test, not a safe extrapolation. Prefer lazy/bounded content batches and avoid animation until profiling.

## Capability status after audit

### Confirmed from 7.5.0 source

- 16×16 source rectangles and `Scale: 2` are supported.
- nominal same-footprint scale math is 32×32 for both configurations.
- four-direction mapping, zero compact-shirt body anchor, current-frame feature offsets, mask layers, default draw order, and native sleeve recoloring exist.
- the generated folder/manifest/JSON/PNG shape matches the loader contract.

### Likely but requires this pack in game

- the 16×16 jacket aligns correctly for normal standing/walking on the default Farmer body;
- native recolored sleeves remain visually coherent with the high-density torso;
- the smaller source cells remain crisp and aesthetically compatible with the Farmer base.

### Untested / explicitly not promised

- horseback alignment at `Scale: 2`;
- all basic tool/carry/slingshot poses;
- reliable initial `DefaultColor` behavior;
- controller smoothness on this Steam Deck setup;
- multiplayer peers without identical pack data;
- performance of a large generated Fashion Sense wardrobe.

## Primary sources

- [Fashion Sense 7.5.0 release](https://github.com/Floogen/FashionSense/releases/tag/v7.5.0)
- [Inspected official source commit](https://github.com/Floogen/FashionSense/tree/39e9e9e13c9f9a78416172e73a229cf8703ddb59)
- [AppearanceModel source](https://github.com/Floogen/FashionSense/blob/39e9e9e13c9f9a78416172e73a229cf8703ddb59/FashionSense/Framework/Models/Appearances/AppearanceModel.cs)
- [ShirtModel source](https://github.com/Floogen/FashionSense/blob/39e9e9e13c9f9a78416172e73a229cf8703ddb59/FashionSense/Framework/Models/Appearances/Shirt/ShirtModel.cs)
- [SleevesModel source](https://github.com/Floogen/FashionSense/blob/39e9e9e13c9f9a78416172e73a229cf8703ddb59/FashionSense/Framework/Models/Appearances/Sleeves/SleevesModel.cs)
- [DrawManager source](https://github.com/Floogen/FashionSense/blob/39e9e9e13c9f9a78416172e73a229cf8703ddb59/FashionSense/Framework/Managers/DrawManager.cs)
- [LayerManager source](https://github.com/Floogen/FashionSense/blob/39e9e9e13c9f9a78416172e73a229cf8703ddb59/FashionSense/Framework/Managers/LayerManager.cs)
- [Renderer sleeve-color patch](https://github.com/Floogen/FashionSense/blob/39e9e9e13c9f9a78416172e73a229cf8703ddb59/FashionSense/Framework/Patches/Renderer/DrawPatch.cs)
- [Official 7.5.0 example pack](https://github.com/Floogen/FashionSense/tree/v7.5.0/FashionSense/Examples/%5BFS%5D%20Example%20Pack)
- [Official shirt creation guide](https://github.com/Floogen/FashionSense/wiki/Creating-a-Shirt-Content-Pack)
- [Official Scale documentation](https://github.com/Floogen/FashionSense/wiki/Scale-Property)
- [Official Shirt model properties](https://github.com/Floogen/FashionSense/wiki/Shirt-Model-Properties)
- [Official Sleeves model properties](https://github.com/Floogen/FashionSense/wiki/Sleeves-Model-Properties)
- [Official color-mask layers documentation](https://github.com/Floogen/FashionSense/wiki/Color-Mask-Layers-Property)
- [Official current issue list, including Steam Deck, Scale, color, and large-pack reports](https://github.com/Floogen/FashionSense/issues)
