# Higher-detail Mistral jacket POC

## Verdict

**The renderer experiment passes the logical-density and static visual test, but remains runtime-experimental.** A 16×16 Fashion Sense shirt at `Scale: 2` has the same nominal 32×32 display box as the vanilla 8×8 shirt at scale 4, while providing four times as many logical cells per direction. The extra cells visibly improve shoulder contour, lapel shape, sleeve attachment, side construction, and back yoke organization in the equal-footprint review.

The pack and texture now load and draw in Stardew, and the calculated `(0,32)` anchor is runtime-confirmed. A later runtime check exposed shoulder skin through an over-tapered HD mask. Version 1.0.2 restores a validated minimum upper-torso coverage envelope without changing the anchor, scale, recipe, or native-sleeve strategy. The corrected coverage still needs an in-game reload check. Tool, horse, mask-default, controller, Steam Deck performance, and multiplayer claims remain untested.

Comparison: [`output/comparisons/VANILLA_VS_FS_JACKET.png`](../output/comparisons/VANILLA_VS_FS_JACKET.png)

## Controlled semantic input

The Fashion Sense backend loads the existing fresh V2 recipe `lifestyle-v2-16` directly. It rejects any changed construction or identity field.

```json
{
  "category": "Lifestyle",
  "styleProfile": "General",
  "archetype": "JACKET",
  "rarity": "Rare",
  "construction": {
    "fit": "relaxed",
    "neckline": "open",
    "collar": "wide",
    "closure": "center_open",
    "layering": "visible_inner_layer",
    "hem": "structured",
    "panelLayout": "split_outer_panels"
  },
  "substantialFeatures": [
    "contrast_inner_layer",
    "broad_collar"
  ],
  "microDetails": [],
  "colorBlocking": {
    "primaryRegion": "outer_panels",
    "secondaryRegion": "inner_layer",
    "accentRegion": "none"
  },
  "paletteFamily": "cool_neutral"
}
```

The output copy at `output/fashionsense/poc_hd_jacket/semantic_recipe.json` is byte-for-field equivalent to the V2 batch recipe after JSON parsing. It contains no Fashion Sense coordinates. All 16×16 masks, source positions, anchor, scale, and color-mask values live in the backend/configuration.

## Density choice

Two configurations were evaluated from source behavior:

| Configuration | Logical frame | Logical cells | Draw scale | Nominal display box |
|---|---:|---:|---:|---:|
| Fashion Sense vanilla-equivalent baseline | 8×8 | 64 | 4 | 32×32 |
| Chosen HD POC | 16×16 | 256 | 2 | 32×32 |

The chosen configuration is the fairest comparison because it changes one variable: source-cell density. Width and height double, per-direction logical area quadruples, and draw scale halves. It does not enlarge the nominal Farmer-space bounding box.

`Scale: 1` at 32×32 would offer the same nominal box and another 4× area increase over this POC, but it would be a much larger design jump and a higher risk of visual style mismatch. V1 of this optional backend should first prove 2× density.

## Backend implementation

The existing vanilla module remains intact. The optional boundary is:

```text
unchanged V2 semantic recipe
├── generator/renderers/vanilla/        -> existing 8×8 renderer facade
└── generator/renderers/fashionsense/   -> bounded 16×16 jacket grammar
```

Renderer-specific data defines named regions, not a 2× image transform:

- `OUTER_PANEL_LEFT`
- `OUTER_PANEL_RIGHT`
- `INNER_LAYER`
- `COLLAR`
- `YOKE`
- `HEM`
- `SLEEVE`

The high-density renderer resolves region-specific deep/shadow/base/light/highlight roles after construction. The generated 16×16 front differs from a 2× nearest-neighbor vanilla frame in 28 occupancy cells, and only 14.06% of its aligned 2×2 blocks are uniform. A literal 2× source upscale would make every 2×2 block uniform. The validator rejects that path.

## Visual/structural result

### Front

- The top row is eight outer-panel/collar cells around a four-cell central neck gap, rather than a full-width band.
- Shoulders grow from 8 occupied top-row cells to the 16-cell mid-torso span, retaining a slope while covering the Farmer shoulder envelope.
- Left and right outer panels wrap a four-cell inner layer.
- Lapels step diagonally inward and stop before becoming a deep chest stripe.
- The structured lower hem preserves the center opening.

### Back

- A centered six-cell rear collar feeds a tapering yoke rather than a flat full-width upper band.
- The yoke narrows through 8, 6, 4, and 2-cell structural rows.
- Left/right back panels retain a center seam and a full outerwear hem.
- Sleeve/shoulder mass survives without a front-only chest feature.

### Sides

- Each side has a forward-facing four-cell inner layer, a diagonal lapel, a distinct outer body panel, and a separate sleeve-cap region.
- The sleeve tapers over multiple high-density rows instead of ending as one block.
- Left is an authored logical mirror with outer-panel semantics swapped, not a runtime pixel stretch.

### Critical art assessment

The equal-footprint sheet shows a material improvement over vanilla. The strongest gain is the side view: it now reads as an arm/sleeve attached to layered outerwear instead of an 8×8 compressed color block. Front shoulders are less rectangular, and the broad collar reads as two lapel slopes around a real opening. The back yoke is present but intentionally quiet.

The visual is not flawless. At normal game size the inner layer remains the strongest landmark, and some lapel shading may be too subtle beside the Farmer's coarser native pixels. The half-sized display pixels may also make the jacket look slightly higher-resolution than the unmodified body. Only an in-game composite can decide whether that contrast is attractive or stylistically mismatched.

## Sleeves and animation

No separate custom Sleeves appearance is included. The shirt declares three `SleeveColors` that are also part of the outer-fabric mask. Fashion Sense patches Stardew's native darkest/medium/lightest sleeve tones, and the normal Farmer renderer owns walking/tool arm geometry and explicit slingshot behavior.

This is the safest POC choice:

- standing/walking/basic tool geometry continues to use tested game frames;
- the jacket's high-density shirt adds shoulder and cuff transitions;
- no second appearance needs to be manually equipped;
- no large pose atlas or animation condition table is added.

The limitation is real: the animated arm pixels themselves remain vanilla-density. A future fully custom jacket-sleeve test must generate and validate a separate comprehensive sleeve atlas, outfit coordination, draw order, carrying/eating/tool/slingshot mappings, and every direction. That work is not implied by this POC.

## Color and dye scope

- `Outer Fabric` is one Fashion Sense color-mask layer with five grayscale values.
- Its declared default is the existing `cool_neutral` dye `[112,130,145]`.
- The contrast inner layer keeps the existing cool-neutral secondary shadow/base/light RGB colors and is not recolored.
- Native sleeve tones use three values from the outer layer, so a stored outer-fabric choice should tint sleeves with the jacket.

Fashion Sense's source contains `DefaultColor` handling, but its current tracker has an open default-color report. The test README tells the player to set the Outer Fabric color once if initial torso/sleeve tint is wrong. This is a known test boundary, not hidden behind a “dyeable works” claim.

## Validation result

`output/fashionsense/poc_hd_jacket/validation.json` reports `PASS_STATIC_SOURCE_CONTRACT`.

Passed checks:

- exact 16×64 non-interlaced RGBA8 pack texture;
- four non-overlapping 16×16 source rectangles;
- source positions front/right/left/back at Y 0/16/32/48;
- `Scale: 2`, `BodyPosition: (0,32)` for every direction, binary alpha only;
- installed-game/Fashion-Sense draw math gives zero residual torso offset after the correction;
- exact no-filter logical PNG output;
- raw and default-color previews are integer nearest-neighbor 8×;
- all four garment regions are connected;
- front/back/side retain required jacket structural regions;
- the separate body-coverage envelope has zero missing cells in all directions;
- center neck opening and non-rectangular shoulder progression survive;
- outer mask shades and fixed inner colors exist;
- pack texture exactly matches generated output texture;
- manifest targets `PeacefulEnd.FashionSense` 7.5.0;
- output is not a 2× vanilla nearest-neighbor upscale;
- the current vanilla Mistral PNG exactly matches the unchanged vanilla renderer output.

Per-direction occupied logical pixels:

| Direction | Vanilla 8×8 | FS 16×16 |
|---|---:|---:|
| Front | 62 | 238 |
| Back | 62 | 242 |
| Left | 56 | 189 |
| Right | 56 | 189 |

Runtime checks still required:

- version 1.0.2 shoulder coverage in the actual Farmer composite;
- four-direction standing/walking;
- basic tools, slingshot, carrying, and horse;
- initial `DefaultColor` and sleeve synchronization;
- controller menu behavior;
- multiplayer with matching packs.

## Performance and Steam Deck

The FS texture is 16×64 = 1,024 pixels = 4 KiB raw RGBA. The vanilla content texture is a padded 256×32 atlas = 32 KiB raw, although its four garment tiles use only 1 KiB of logical RGBA data. The FS appearance uses four times the actual per-direction logical data while remaining compact on disk/GPU as a source texture.

Fashion Sense retains cached/active texture data and creates one full-size mask texture for this color layer, so a lower-bound raw pixel-store estimate for this appearance is about 12 KiB before framework/driver overhead. There is no custom sleeve texture and no animation atlas.

One 16×64 static shirt is not a plausible texture-memory bottleneck by itself. Nevertheless, the official issue tracker includes an open Steam Deck lag report, an open Scale/horse alignment report, and a large-pack crash report. Large generated wardrobes and reflection-heavy mod lists must be profiled on the target Deck. Animation frames increase texture memory roughly linearly and should not be added until this static case is measured.

## Content pack

Pack folder:

```text
test-packs/fashionsense/RNG-Clothing-HD-Jacket-POC/
```

Copy that entire folder to:

```text
<Stardew Valley>/Mods/RNG-Clothing-HD-Jacket-POC/
```

Install Fashion Sense **7.5.0** separately from its official distribution. Do not copy audited source or binaries from this project. Content Patcher is not required by this POC pack.

After loading a save through SMAPI:

1. run `fs_add_mirror` if needed;
2. use the Hand Mirror;
3. open **Shirts**;
4. select **Mistral Lapel Layer Jacket HD POC**;
5. if needed, set `Outer Fabric` to approximately RGB 112/130/145;
6. test directions, walk, tools, slingshot, and horse.

For asset iteration:

```text
fs_reload RNGClothing.FashionSense.HDJacketPOC
```

## Output inventory

- `generator/renderers/fashionsense/hd_jacket.py` — bounded higher-density backend.
- `generator/renderers/vanilla/__init__.py` — facade over unchanged V2 vanilla rendering.
- `generator/data/fashionsense/hd_jacket_poc.json` — FS-only frame/scale/mask grammar.
- `tools/generate_fs_hd_jacket_poc.py` — deterministic one-POC exporter.
- `tools/validate_fs_hd_jacket_poc.py` — independent static/source-contract validator.
- `output/fashionsense/poc_hd_jacket/mistral_lapel_layer_jacket_hd.png` — native 16×64 FS texture.
- `output/fashionsense/poc_hd_jacket/mistral_lapel_layer_jacket_hd-native-8x.png` — exact raw-mask 8× nearest preview.
- `output/fashionsense/poc_hd_jacket/mistral_lapel_layer_jacket_hd-default-8x.png` — default-color logical composite, then exact 8× nearest preview.
- `output/fashionsense/poc_hd_jacket/mistral_lapel_layer_jacket_hd-directions-8x.png` — labeled directions.
- `output/comparisons/VANILLA_VS_FS_JACKET.png` — equal-footprint controlled comparison.
- `test-packs/fashionsense/RNG-Clothing-HD-Jacket-POC/` — isolated content pack.
- `reports/FASHION_SENSE_RENDERER_AUDIT.md` — source/framework audit.
- `reports/HD_JACKET_POC.md` — this result.

## Recommendation

Keep the Fashion Sense backend experimental until this exact pack passes in-game world/UI anchors, tools, horse, controller, and Deck profiling. Do not convert the V2 wardrobe yet.

The added density provides enough visual vocabulary for a **single bounded Attack on Titan jacket style-profile stress test**: shoulder contour, lapel/closure geometry, yoke/panel seams, cuff transitions, and controlled color blocks now have real space. That next test is justified only after the current pack confirms alignment and sleeve behavior. This report does not start or generate that style profile.
