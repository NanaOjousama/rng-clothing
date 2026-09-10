# Hood-up hair clipping feasibility

## Outcome

Fashion Sense 7.5.0 does **not** expose a native hair-visibility mask, stencil, crop envelope, or direction-specific partial-hair setting. Its Hat contract provides only the direction-specific boolean `HideHair`. When true, Fashion Sense suppresses the entire Hair layer for that active direction.

A generic mask for arbitrary vanilla and Fashion Sense hairstyles is technically possible only if another code mod takes responsibility for drawing Hair. Fashion Sense's public draw-override API is safer than patching `FarmerRenderer`, but its public draw context omits information required to reproduce arbitrary custom/animated Fashion Sense Hair faithfully. A fully generic implementation would therefore depend on Fashion Sense internals or invasive SpriteBatch/render-target handling. That is not justified for this hoodie experiment.

**Recommendation:** do not implement a clipping mod now. Keep the current native layered solution: preserve Hair where acceptable, draw the raised hood above Hair so opaque hood/neck/shoulder fabric visually covers conflicts, hide back Hair directionally, and retain `PreserveFrontOnly`/`HideHair` as compatibility fallbacks.

The ideal long-term solution is an upstream Fashion Sense feature: a per-direction Hat-owned `HairVisibilityMask` evaluated in Farmer/body space by Fashion Sense itself.

## Authoritative implementation inspected

- Installed framework: Fashion Sense **7.5.0** (`PeacefulEnd.FashionSense`).
- Project source identifies version 7.5.0 in `FASHION SENSE/FashionSense-stable/FashionSense/FashionSense.csproj`.
- Stardew Valley runtime target: 1.6.15.
- Fashion Sense patches `FarmerRenderer.draw` and reconstructs the appearance layer list in its own `DrawManager`/`LayerManager`.
- Vanilla `FarmerRenderer.drawHairAndAccesories` was compared with Fashion Sense's replacement hair paths.

Relevant source contracts:

- `Framework/Models/Appearances/Hat/HatModel.cs`
  - `HeadPosition`
  - `HatSize`
  - `HideHair`
  - no clip-mask property
- `Framework/Models/Appearances/Hair/HairModel.cs`
  - `HeadPosition`
  - `HairSize`
  - no external visibility-mask property
- `Framework/Models/Appearances/AppearanceModel.cs`
  - color masks, skin-tone masks, draw order, scale, animation data
  - no stencil/inter-layer alpha mask
- `Framework/Managers/LayerManager.cs`
  - creates one Hair layer
  - marks that whole layer hidden when the active directional Hat has `HideHair=true`
- `Framework/Managers/DrawManager.cs`
  - separately draws vanilla Hair and custom Fashion Sense Hair
  - draws custom Hair through the same generic appearance method used by several categories
- `Framework/Interfaces/API/Api.cs`
  - exposes `RegisterAppearanceDrawOverride(Type.Hair, ...)`
  - the callback receives `IDrawTool`, not the active Hair model or its calculated source rectangle

## Why Fashion Sense color masks do not solve this

`ColorMasks` and `SkinToneMasks` operate on pixels belonging to the appearance that declares them. Fashion Sense builds recolored textures from selected source colors, then draws those textures. They do not multiply the alpha of another layer, erase Hair beneath a Hat, or act as a stencil.

Content Patcher can edit directional `FrontHat`, `RightHat`, `BackHat`, and `LeftHat` model fields such as `HideHair` and draw order. It cannot add a renderer behavior that Fashion Sense does not implement. Therefore CP can choose whole-Hair visibility per direction, but not preserve bangs while clipping the rest.

## Existing native options

| Option | Scope | Generic hairstyles | Risk | Result |
|---|---|---:|---:|---|
| Directional `HideHair` | Whole Hair layer | Yes | Low | Stable, but removes bangs and all other Hair pixels. |
| Raised Hat drawn after Hair | Opaque hood pixels only | Yes | Low | Safest partial visual masking; cannot erase Hair outside the hood artwork. |
| Rear hood before Hair + front rim after Hair | Layered visual occlusion | Yes | Low–moderate | Best native illusion of bangs inside a hood; requires coordinated hood pieces/art. |
| Color/SkinTone masks | Declaring appearance only | No | Low | Recoloring only; not clipping. |
| Content Patcher data edits | Existing model fields | Yes | Low | Can switch `HideHair`/draw order, not add a mask. |

## Smallest code approaches evaluated

### 1. Public Fashion Sense Hair draw override with cached masked textures

Fashion Sense 7.5.0 exposes an official `RegisterAppearanceDrawOverride` API. A small optional SMAPI mod could register for `Type.Hair`, check the Farmer, exact hoodie Hat ID, direction, and hood-up state, then:

1. return `false` for every unaffected draw so Fashion Sense draws Hair normally;
2. for an affected draw, select the current hairstyle frame;
3. copy it once into a cached texture;
4. set pixels outside a direction-specific binary envelope to transparent;
5. draw the cached texture at the Hair layer depth;
6. return `true` to suppress Fashion Sense's normal Hair draw.

This avoids Harmony and avoids a per-frame render target. For **vanilla 16×32 Hair on the vanilla body**, it is feasible and inexpensive.

It is not a generic solution for arbitrary Fashion Sense Hair because public `IDrawTool` does not expose:

- whether the Hair layer is vanilla or custom;
- the active directional `HairModel`;
- its calculated source rectangle or animation/subframe;
- `HairSize`, `StartingPosition`, `HeadPosition`, or appearance `Scale`;
- custom-body feature offsets used by Fashion Sense;
- the currently selected Hat animation/state (the current weather Hat uses one appearance ID for hood down and hood up).

The API can return a whole appearance texture, but that is insufficient to reconstruct its directional and animated draw contract safely. Supporting those cases would require reading Fashion Sense's internal data models/reflection or duplicating its private source-rectangle and feature-offset logic.

**Classification:** feasible narrow prototype for vanilla Hair only; not acceptable as the requested generic arbitrary-hairstyle solution.

### 2. Harmony patch to Fashion Sense's Hair drawing

A patch could intercept `DrawManager.DrawHairVanilla` and the Hair branch of private `DrawAppearance`, gaining the exact source rectangle and model state. This would cover both vanilla and custom Hair, but it would bind to private Fashion Sense 7.5.0 methods and compiler layout.

The custom-Hair path shares a generic drawing method with Pants, Shirt, Accessory, Hat, and Shoes, so a clean postfix/prefix is not available at the category boundary. A transpiler or broader replacement would be especially brittle. Patching vanilla `FarmerRenderer` alone is not sufficient because Fashion Sense already intercepts/reconstructs its draw flow.

**Classification:** technically possible, version-sensitive and too invasive for this garment feature.

### 3. Screen-space alpha-mask compositing

The most visually general method is:

1. render the selected Hair into an offscreen `RenderTarget2D`;
2. multiply its alpha by a direction-specific hood/body mask;
3. composite the result at the Hair layer.

However, Fashion Sense calls the draw override while the game's `SpriteBatch` is already active. Switching render targets or effects safely would require ending and restarting the caller's batch with matching state, or patching Fashion Sense at a higher rendering boundary. That risks ordering/filtering conflicts with Fashion Sense and other appearance mods. It must also handle rotation, UI/mirror rendering, zoom, custom bodies, custom animated Hair, multiple Farmers, and split-screen/multiplayer.

**Classification:** correct visual mechanism, but invasive and not recommended here.

### 4. Curated bangs overlay

Hide the original Hair and equip a small Hair/Accessory appearance containing a curated fringe. This is stable for a known set of overlays but cannot preserve arbitrary hairstyles or colors/shapes generically. Automatically extracting bangs from unknown hairstyles has no reliable semantic boundary.

**Classification:** viable opt-in cosmetic feature later, not a generic mask.

## Direction-specific envelope design

If Fashion Sense eventually supports masking, the mask should be defined in Farmer/head space, not raw hairstyle texture coordinates. A robust contract would include:

- one binary mask for front, right, back, and left;
- an explicit coordinate origin tied to the Farmer head/body anchor;
- intersection with the currently drawn Hair pixels;
- Hat animation/subframe awareness;
- point-sampled binary alpha;
- independent behavior for world and UI/mirror draws;
- the ability to keep the upper/front side-hair region while removing lower/rear pixels beneath the hood and sweatshirt;
- per-Farmer activation based on the equipped Hat and active hood state.

Texture-relative masks are insufficient because Fashion Sense Hair appearances can use different dimensions, offsets, scales, and animation frames.

## Compatibility and performance

### Native visual occlusion

- No added draw passes.
- Works with vanilla and custom Hair because ordinary layer order performs the occlusion.
- Compatible with remote Farmers because appearance state and normal FS drawing are already per Farmer.
- Main limitation is artistic: opaque hood fabric can cover Hair, but cannot delete Hair beyond the fabric silhouette.

### Cached CPU-masked vanilla Hair

- Runtime cost after caching: one substitute texture draw, broadly comparable to the original Hair draw.
- Memory: tiny for vanilla directional Hair textures; cache must be invalidated for hairstyle/color/content changes.
- Compatibility risks: custom bodies, FS custom Hair, UI preview, covered-hair metadata, unique left sprites, other Hair draw overrides, and mods changing hairstyle textures.
- The FS API allows multiple override registrants, but the first callback returning `true` suppresses later/default drawing; interoperability therefore depends on registration order.

### Render-target masking

- Adds render-target switches and at least one extra render/composite pass for each affected Farmer draw.
- Raw texture memory would be small, but GPU state changes and repeated draws matter more than the tiny mask itself.
- Cost scales with visible Farmers and UI previews; remote Farmer and split-screen state must remain isolated.
- Steam Deck/Linux does not introduce a unique semantic problem, but MonoGame graphics-state handling makes invasive SpriteBatch manipulation a poor compatibility trade for one hoodie feature.

## Only-while-active gating

A helper must not infer activation merely from “a hoodie shirt is equipped.” It should require:

- the exact generated Hat appearance ID;
- the specific Farmer being drawn;
- a reliable hood-up state;
- the current facing direction;
- normal bypass for swimming/bathing/unequipped states.

The current weather hood changes animation/state within one Hat appearance. Fashion Sense's public Hair draw context does not expose the selected Hat animation frame. Mirroring outdoor/weather conditions in a helper is possible but can drift from Content Patcher/Fashion Sense condition evaluation. A future implementation should expose hood state explicitly or use separate hood-up/down appearance IDs before attempting a renderer override.

## Decision

Do **not** add a `FarmerRenderer` or Fashion Sense private-method patch for hair clipping.

For the present Rare+ hoodie template:

1. retain full Hair in front;
2. retain side Hair while the topmost raised hood masks as much lower/rear hair as its believable silhouette permits;
3. use directional back hiding where required;
4. offer `PreserveFrontOnly` when a long side hairstyle escapes the visual mask;
5. keep full `HideHair` as the universal compatibility fallback;
6. leave the hoodie architecture experimental until the live hairstyle matrix is reviewed.

If side clipping remains unacceptable across common hairstyles, the next responsible step is an upstream Fashion Sense feature request, not a project-local global renderer patch.

## Proposed upstream Fashion Sense contract

Conceptually, a Hat model could support:

```json
{
  "HideHair": false,
  "HairVisibilityMask": {
    "Texture": "hair-mask.png",
    "CoordinateSpace": "FarmerHead",
    "Mode": "KeepWhite",
    "ApplyTo": "CurrentDirectionAndAnimation"
  }
}
```

Fashion Sense would apply this inside its existing Hair draw path after resolving the active vanilla/custom Hair frame and before drawing Hat layers. Framework ownership is what makes this safe across custom Hair, custom bodies, animation, UI previews, and multiplayer.
