# Clothing-generation capability study

Research date: 2026-08-28. This is a feasibility specification, not an implementation contract.

## Evidence and confidence

- **Confirmed (installed game):** verified against the installed Stardew Valley `1.6.15.24356` assemblies and selectively unpacked installed assets/data. Relevant classes were decompiled from `Stardew Valley.dll`; data models came from `StardewValley.GameData.dll`.
- **Confirmed (Fashion Sense source):** verified against Fashion Sense `7.5.0`, commit `39e9e9e13c9f9a78416172e73a229cf8703ddb59` (released 2026-03-12), including its content loader, renderer patches, models, API, example pack, and UI source.
- **Confirmed (documentation):** corroborated with the current [shirt](https://stardewvalleywiki.com/Modding:Shirts), [pants](https://stardewvalleywiki.com/Modding:Pants), [hat](https://stardewvalleywiki.com/Modding:Hats), and [tailoring](https://stardewvalleywiki.com/Modding:Tailoring) pages, plus the [Fashion Sense wiki](https://github.com/Floogen/FashionSense/wiki) and [7.5.0 release](https://github.com/Floogen/FashionSense/releases/tag/v7.5.0).
- **Likely:** follows directly from a confirmed contract but has not been exercised in-game by this project.
- **Untested:** needs an installed-mod proof of concept or multiplayer test before it can be promised.

The requested toolbox catalog, now located at `docs/TFWR_CODEX_MOD_TOOLBOX_INDEX.md`, was read first. Its clothing-relevant entries support Content Patcher for data/asset delivery and upstream source inspection for verification. It does not list a clothing renderer that replaces Fashion Sense, so current Fashion Sense was studied separately. Deleted local mod-source folders were not assumed to exist.

Installed-data audit snapshot: `Data/Shirts` has 303 entries (sprite indices 0–301), `Data/Pants` has 18 entries (sprite indices 0–15), `Data/Hats` has 122 entries, and `Data/TailoringRecipes` has 322 entries. These counts describe the installed 1.6.15 data and are evidence, not exporter limits.

# Native Stardew

## Shared player-rendering contract

- **Directions:** Stardew uses `0 = back/up`, `1 = right`, `2 = front/down`, `3 = left`.
- **Logical pixels:** all source rectangles and feature offsets are integer pixels. The game normally draws player art at scale 4 with point-sampled pixel art. Native assets therefore fit a one-source-pixel-to-one-logical-pixel authoring model.
- **Animation:** the farmer uses a 16x32 logical source rectangle and many animation frames. Shirts and hats select a static direction sprite, then follow per-farmer-frame feature offsets. Pants are a frame-aligned overlay atlas and therefore contain art for the farmer animation frames themselves.
- **Relevant layer order:** the installed renderer defines, in part, Base, Pants, FaceSkin, Eyes, Shirt, under-hair accessory, ArmsUp, HatMaskUp, Hair, Accessory, Hat, Tool, Arms, and later special layers. Shirts normally cover pants; arms/sleeves are separate from the shirt tile; hats normally cover hair/accessories.
- **Registration:** 1.6 uses qualified item IDs: `(S)` shirts, `(P)` pants, and `(H)` hats. Shirts and pants are model entries; hats remain slash-delimited data. Content Patcher can edit these assets without replacing XNB files.
- **Multiplayer:** equipped clothing is regular item/equipment state and is synchronized by the game. All players still need the modded data and textures to resolve custom IDs consistently. This project's custom-content behavior is untested in multiplayer.

## Shirts

- **Exact file structure:** a PNG loaded as a game content asset (default `Characters/Farmer/shirts`) plus an entry in `Data/Shirts`.
- **Exact JSON/data structure:** a string-keyed `ShirtData` model with `Name`, `DisplayName`, `Description`, `Price`, `Texture`, `SpriteIndex`, `DefaultColor`, `CanBeDyed`, `IsPrismatic`, `HasSleeves`, `CanChooseDuringCharacterCustomization`, and `CustomFields`.
- **Sheet dimensions:** custom shirt sheets must be exactly 256 pixels wide; height may contain any number of 32-pixel rows. The installed vanilla sheet is 256x608.
- **Logical frame dimensions:** each direction is 8x8. Each item consumes an 8x32 block in the left 128-pixel half and an aligned 8x32 dye-mask block in the right half.
- **Sprite addressing:** `x = (SpriteIndex * 8) % 128`; `y = floor(SpriteIndex * 8 / 128) * 32`. The dye mask uses `x + 128`.
- **Supported directions:** within the 8x32 block, front/down at `y+0`, right at `y+8`, left at `y+16`, back/up at `y+24`.
- **Body anchor/offset system:** the renderer places the 8x8 shirt at its fixed torso anchor and adds the farmer frame's integer feature offsets. There is no per-item anchor field.
- **Animation behavior:** no independent shirt frames or timing. The same directional tile rides all walking/tool/action frames through native offsets.
- **Color/dye support:** base sprite is drawn normally; its corresponding mask is drawn tinted by the equipped shirt color. `DefaultColor`, `CanBeDyed`, and `IsPrismatic` control item behavior. Only one user-selectable dye color exists.
- **Sleeves:** `HasSleeves=true` uses colors sampled from the shirt art to recolor the farmer's native arm/sleeve pixels. `HasSleeves=false` leaves skin-colored arms. Shirts do not supply independently shaped sleeve sprites.
- **Layering:** shirt tile above native pants and body, with native arms/tool layers handled separately.
- **Item/equipment integration:** complete native shirt-slot integration, inventory icon (front 8x8 tile), tailoring output, shops/item queries, save state, and character customization opt-in.
- **Controller/player UX:** native inventory/equipment, sewing machine, and dye UI are controller-aware. No new clothing browser is provided.
- **Limitations:** only 8x8 per direction, fixed anchor, fixed draw layer, one dye channel, no garment-specific animation, no oversized silhouette, and severe competition for a few readable pixels. Long coats and dresses cannot be represented faithfully by the shirt layer alone.
- **Automation feasibility:** **confirmed high** for T-shirts, sweaters, compact jackets, collars, ties, bibs, and small front/back motifs. **Likely medium** for dense layering. Unsafe for large silhouettes.

Minimal 1.6 data shape:

```json
{
  "Example.Mod/Shirt": {
    "Name": "Example.Mod/Shirt",
    "DisplayName": "Example Shirt",
    "Description": "A generated logical-pixel shirt.",
    "Price": 100,
    "Texture": "Mods/Example/Shirts",
    "SpriteIndex": 0,
    "DefaultColor": "255 255 255",
    "CanBeDyed": true,
    "IsPrismatic": false,
    "HasSleeves": true
  }
}
```

## Pants

- **Exact file structure:** a PNG content asset (default `Characters/Farmer/pants`) plus an entry in `Data/Pants`.
- **Exact JSON/data structure:** a string-keyed `PantsData` model with `Name`, `DisplayName`, `Description`, `Price`, `Texture`, `SpriteIndex`, `DefaultColor`, `CanBeDyed`, `IsPrismatic`, `CanChooseDuringCharacterCustomization`, and `CustomFields`.
- **Sheet dimensions:** the installed sheet is 1920x1376. A style occupies a 192x688 block: a 96x688 masculine overlay on the left and a 96x688 feminine overlay on the right. The renderer hardcodes 10 styles per row. A one-style 192x688 texture at index 0 is valid by the observed addressing; multi-row output should preserve the 1920-wide/10-style convention.
- **Logical frame dimensions:** not one small direction tile. Pants reuse the farmer's current source rectangle, usually 16x32, at the same frame coordinate inside a 96x688 half-atlas.
- **Sprite addressing:** add `(SpriteIndex % 10) * 192` to X and `floor(SpriteIndex / 10) * 688` to Y; add 96 to X for the feminine half.
- **Supported directions:** all directions and player animation frames represented by the farmer atlas layout.
- **Body anchor/offset system:** exact alignment to the native farmer source rectangle. There is no per-item anchor.
- **Animation behavior:** complete walking/action compatibility is possible because the overlay follows every farmer frame, but the garment must be authored for the relevant atlas pixels.
- **Color/dye support:** the entire pants overlay is tinted with the pants color. `CanBeDyed`, `DefaultColor`, and `IsPrismatic` apply. There is one color channel, not a separate mask half.
- **Layering:** native Pants layer above the base body and below shirt/most upper layers. Pants may cover legs and lower torso where the overlay has pixels.
- **Item/equipment integration:** complete native pants-slot integration. The icon is a 16x16 region at block `y+672`.
- **Controller/player UX:** native equipment, tailoring, and dye UX.
- **Limitations:** very large authoring surface, masculine/feminine halves, hardcoded atlas geometry, action-frame edge cases, one whole-overlay tint, and no item-specific timing. A static-looking skirt can still fail while tools, sitting, swimming, or special animations run.
- **Automation feasibility:** **confirmed technically possible, but medium-to-low reliability** until a frame-coverage validator exists. Straight pants/shorts that closely follow native legs are safer than long skirts, dresses, wide hems, or asymmetric lower garments.

## Hats

- **Exact file structure:** a PNG content asset (default `Characters/Farmer/hats`) plus an entry in `Data/Hats`.
- **Exact JSON/data structure:** `Data/Hats` is still a string-to-slash-delimited-string lookup: `name/description/hair draw type/ignore hair offset/tags/display name/sprite index/texture asset`.
- **Sheet dimensions:** any dimensions evenly divisible by 20 horizontally and 80 vertically. The installed vanilla sheet is 240x880.
- **Logical frame dimensions:** 20x20 per direction; 20x80 per hat.
- **Supported directions:** front/down, right, left, back/up from top to bottom.
- **Body anchor/offset system:** fixed head anchor plus the farmer frame offset and optional hairstyle-specific hat offset. The data can ignore that hairstyle offset, but cannot provide a custom numeric anchor.
- **Animation behavior:** static direction sprites; native frame offsets move them with the head. No independent frames.
- **Color support:** no normal dye channel. The legacy `Prismatic` hat tag enables cycling tint.
- **Layering:** normally above hair. Names containing `Mask` use special split rendering for back-facing mask behavior. Hair draw mode can show full hair, use hat-adapted/obscured hair, or hide hair.
- **Item/equipment integration:** complete native hat-slot integration, item registry, shops, tailoring, save state, and inventory icon.
- **Controller/player UX:** native equipment and sewing-machine UX.
- **Limitations:** fixed head anchor, no normal dyeing, no independent animation, legacy data format, and possible hairstyle clipping. Oversized 20x20 art is possible within the tile but cannot extend beyond it.
- **Automation feasibility:** **confirmed high** for compact hats, bows, bands, masks, and glasses-like head items. **Medium** for brimmed/tall hats because hair and side/back silhouette interactions require testing.

## Tailoring / sewing machine

### Confirmed resolution architecture

```text
left item context tags + right item context tags
    -> scan Data/TailoringRecipes in data order
    -> first recipe whose required left tags all match
       and whose required right tags all match
    -> choose feminine override, random output list, or fixed output
    -> ItemRegistry.Create(qualified ID)
    -> optionally dye created Clothing from the right ingredient
```

- `TailorItemRecipe` fields are `Id`, `FirstItemTags`, `SecondItemTags`, `SpendRightItem`, `CraftedItemId`, `CraftedItemIds`, and `CraftedItemIdFeminine`.
- Both tag lists must be nonempty. Matching is **all required tags**, not any-tag matching.
- Recipe order is semantic: the first matching recipe wins. Overlapping recipes need a collision/order validator.
- `CraftedItemIds` is a uniform random output list when present. The feminine override takes precedence for a feminine player.
- The installed 1.6.15 data has 322 recipes. Expanding fixed, feminine, and random output fields yields 276 shirt IDs, 16 pants IDs, 33 hat IDs, and one object ID (with duplicates possible); the prismatic recipe contributes one five-item random list. Every result is an existing registered item. Tailoring does not synthesize PNG pixels.
- Dyeing is separate from recipe selection. Color may come from a colored object or item context-color tags; dye strengths include weak 0.25, medium 0.5, and strong 1.0. Prismatic input is special.
- **Reusable design pattern:** semantic tags, deterministic filter/order rules, qualified output IDs, an optional random result set, and post-selection color application.
- **Not reusable as-is:** it cannot generate art or validate visual compatibility. It should inspire the future recipe resolver, not serve as the pixel builder.

## Random cosmetic selection

The installed `Utility.getRandomCosmeticItem(Random)` does **not** discover all registered cosmetics or build a dynamic validity pool.

- First roll: 20% furniture branch. A small special chance yields `(F)1369`; otherwise a hardcoded furniture family/range is selected. Exceptions fall back to `(F)1369`.
- If the first branch is not taken, an independent 25% roll selects from a hardcoded 22-hat allowlist. Overall probability: 20%.
- Otherwise it selects a shirt in integer range 1112–1290 and rerolls a hardcoded exclusion set. Overall probability: 60%.
- Pants and boots are absent.
- Randomness is injected through the method's `Random` argument, which makes deterministic testing possible.

**Reusable pattern:** weighted category selection, explicit allowlists/ranges, rejection filters, deterministic RNG injection, and a safe fallback. **Do not reuse the hardcoded IDs or describe the vanilla function as registry-aware.** A future RNG reward system should build its own validated candidate pool from generated metadata, then apply this selection pattern.

# Fashion Sense

## Shared content-pack contract

- **Dependency status:** Fashion Sense itself is a SMAPI mod; current 7.5.0 requires Stardew 1.6.14 or later and lists Content Patcher as optional. This feasibility project does not add it as a dependency.
- **Manifest:** a normal content-pack manifest with `ContentPackFor.UniqueID = "PeacefulEnd.FashionSense"`. Each appearance lives under its type folder.
- **Exact folders/files:** `Hairs/<appearance>/hair.json|png`, `Accessories/.../accessory.json|png`, `Hats/.../hat.json|png`, `Shirts/.../shirt.json|png`, `Sleeves/.../sleeves.json|png`, `Pants/.../pants.json|png`, `Shoes/.../shoes.json|png`, and `Bodies/.../body.json|png` (bodies may also use `eyes.png`). Packs may include `conditions.json` and `preset_outfits.json`.
- **Root JSON model:** an appearance file is an `AppearanceContentPack` subtype. Common author-facing fields include required `Name` (or CP-only `FromItemId`), optional `Format`, `Author`, `Tags`, `IsLocked`, optional `Item`, and the type's direction objects. CP-supplied models additionally use `Id`, `PackId`, `PackName`, and `TexturePath`; normal folder packs derive ownership/path information from their manifest and files.
- **Canvas:** the layout is freeform and documented as under 16384x16384, but this is only a texture ceiling, not a recommended design size. Every direction model declares an integer source `StartingPosition` and integer `*Size { Width, Length }`; output should use the smallest logical canvas that contains its frames.
- **Directions:** content objects expose `Front*`, `Right*`, `Left*`, and `Back*`; source mapping is the same `0 back, 1 right, 2 front, 3 left` contract as Stardew. Every used direction needs a model with source position, anchor, and size. Current source falls back to the corresponding vanilla appearance when the selected Fashion Sense direction model is null. The generator should nevertheless require all four directions to prevent an accidental mixed custom/vanilla garment.
- **Anchors:** head types use integer `HeadPosition`; body types use integer `BodyPosition`. These are the sprite-batch origin within the selected source rectangle. Bodies instead provide body/feature offsets. `StartingPosition` is the source rectangle's top-left, not a screen offset.
- **Scale:** model default is 4.0. Generated assets should keep scale 4 and integer logical coordinates. Arbitrary scale exists but is outside the strict logical-pixel contract.
- **Frames:** `UniformAnimation`, `IdleAnimation`, and `MovementAnimation` are lists of frame records. Frames advance horizontally in `*Size` increments unless source behavior is overridden. Records support `Frame`, millisecond `Duration` (including random choice/range), `Offset`, conditions, `EndWhenFarmerFrameUpdates`, subframes, light data, and per-frame `DrawOrderOverride`. `AppearanceSyncing` can synchronize animation state to another appearance type.
- **Color:** by default the framework grayscale-colors the whole sprite. `DisableGrayscale=true` preserves authored colors. `ColorMasks` defines a single replaceable set; `ColorMaskLayers` gives named independent color regions with `Values`, optional `DefaultColor`, and `IgnoreUserColorChoice`. `SkinToneMasks`, prismatic color, and type-specific shirt/sleeve tone handling are available. Mask colors should be disjoint and validation should reject overlap.
- **Layering:** current 7.5.0 source is authoritative. Its default front-facing sequence is Player, Shoes, Pants, Shirt, Hair, Accessories, Sleeves, Hat. Back-facing and type-specific flags can move sleeves/accessories. The older wiki list places Pants before Shoes and Sleeves before Accessories; it is stale. Generic `DrawOrderOverride { Preposition, AppearanceType }`, type flags, and animation-frame overrides can reposition layers.
- **Visibility:** shared properties include `HidePlayerBase`, `HideWaterLine`, swimming/bathing-suit visibility, `UseBaldHead`, `HideSleeves`, `DisableNativeOffset`, scale, and prismatic settings.
- **Unlocking:** `IsLocked` hides an appearance from normal Hand Mirror selection. Content Patcher can edit Fashion Sense's exposed appearance-data assets; the public API has `SetAppearanceLockState`. Preset outfits can expose coordinated sets.
- **API:** public 7.5.0 methods can set/clear and color hair, accessory slots, hat, shirt, pants, sleeves, and shoes; query current IDs/colors; get/set/reset raw appearance textures; manage outfits; lock appearances; register draw overrides; and observe sprite-dirty events. IDs are `PackId/Type/Name`. Direct raw-texture mutation and draw overrides are unnecessary for this generator and should be avoided.
- **Body API caveat:** the enum contains `Player`, but `GetAppearanceModDataKey` does not map it. Direct generic body set/clear is therefore **not a confirmed public capability in 7.5.0**. Bodies are selectable through content/UI/outfit mechanisms.
- **Content Patcher integration:** Fashion Sense exposes `Data/PeacefulEnd/FashionSense/AppearanceData` and per-type data assets. `FromItemId` handling is confirmed in current source for Hat and Shirt only. The CP appearance token reports equipped IDs for supported non-body types.
- **Item integration:** an `Item` block adds a wearable item only for Hat, Shirt, Pants, or Shoes. It needs `SpritePosition` and `SpriteSize`; optional fields are `Id`, `DisplayName`, `Description`, `Price`, and `InventoryScale`. The framework adds the corresponding native data entry and maps equip/unequip to the Fashion Sense appearance. Hair, accessories, sleeves, and bodies are not item-backed by this contract.
- **Controller/player UX:** Hand Mirror, search, and outfit menus implement clickable-component/snappy-menu navigation and explicit gamepad buttons. Triggers cycle appearances; shoulder buttons rotate the preview. A Hand Mirror is purchased/used unless configuration allows a quick menu. Multiple mask layers add additional color choices, so excessive layers increase controller friction.
- **Multiplayer:** appearance IDs and colors are stored in farmer `modData`, and current source updates all farmers and sends selected color/vanilla-equipment messages. This confirms a synchronization mechanism. **Untested:** visual behavior when a peer lacks the exact content pack; the safe requirement is that every peer installs Fashion Sense and the same generated pack.
- **Debugging:** `fs_reload` reloads packs without restarting. Current source also has frame/movement display and animation record/play commands. These are valuable POC test tools, not generator dependencies.
- **Large garments:** there is no separate “large garment” type. Oversized shirts, pants, sleeves, or accessories can exceed 16x32 and can be coordinated through presets. This is supported, but long coats/dresses spanning layers remain a validation problem.

Minimal static shirt shape:

```json
{
  "Name": "Example Shirt",
  "FrontShirt": {
    "StartingPosition": { "X": 0, "Y": 0 },
    "BodyPosition": { "X": 0, "Y": 0 },
    "ShirtSize": { "Width": 8, "Length": 8 }
  },
  "RightShirt": {
    "StartingPosition": { "X": 8, "Y": 0 },
    "BodyPosition": { "X": 0, "Y": 0 },
    "ShirtSize": { "Width": 8, "Length": 8 }
  },
  "LeftShirt": {
    "StartingPosition": { "X": 16, "Y": 0 },
    "BodyPosition": { "X": 0, "Y": 0 },
    "ShirtSize": { "Width": 8, "Length": 8 }
  },
  "BackShirt": {
    "StartingPosition": { "X": 24, "Y": 0 },
    "BodyPosition": { "X": 0, "Y": 0 },
    "ShirtSize": { "Width": 8, "Length": 8 }
  }
}
```

The exact anchor values must be established from a current template or in-game overlay test; zero is shown only as JSON structure, not a certified garment anchor.

## Shirts

- **Files/data:** `Shirts/<name>/shirt.json` and `shirt.png`; root object contains metadata and `FrontShirt`, `RightShirt`, `LeftShirt`, `BackShirt` models.
- **Canvas/frame:** arbitrary compact canvas; each direction has its own integer `StartingPosition`, `BodyPosition`, and `ShirtSize`. Art can exceed the native 8x8/16x32 body.
- **Directions/animation:** four direction models; uniform, idle, and movement animation supported.
- **Color:** shared full-sprite/mask-layer color system plus `SleeveColors` for native sleeve recoloring.
- **Layering:** normally after pants and before hair; generic and frame-specific overrides. Can hide native sleeves/player base.
- **Equipment:** optional `Item` creates a shirt-slot item. `FromItemId` is confirmed for CP-supplied existing shirts.
- **Unlock/API:** Hand Mirror, presets, CP `IsLocked`, API set/clear/color/lock.
- **UX/multiplayer:** controller-aware Hand Mirror; item-backed form offers native equip UX. Same-pack peer requirement remains.
- **Limitations:** separate sleeves or action-aware oversized shapes are needed for coats/robes; arbitrary size can clip surrounding layers.
- **Procedural realism:** **high** for static compact tops; **medium** for layered/animated tops; **low initially** for robes/coats.

## Sleeves

- **Files/data:** `Sleeves/<name>/sleeves.json` and `sleeves.png`; four `*Sleeves` models.
- **Canvas/frame/anchors:** freeform integer canvas; per-direction `StartingPosition`, `BodyPosition`, `SleevesSize`.
- **Directions/animation:** four directions and all shared animation modes/subframes.
- **Color:** shared masks plus `UseShirtColors` and `ShirtToneMask`; can coordinate with a Fashion Sense or vanilla shirt.
- **Layering:** normally its own arms layer; `DrawBeforeShirt`, `DrawBehindHead`, generic overrides, and animation overrides.
- **Equipment:** no `Item` contract. Selection is by Hand Mirror, preset, CP lock state, or API.
- **UX/multiplayer:** adds a separate appearance decision and color UI; synced through farmer modData when peers share the pack.
- **Limitations:** tool, arm, slingshot, and facing motion make sleeves substantially harder than static torso art. Shirt/sleeve compatibility must be validated as a pair.
- **Procedural realism:** **medium after a frame-safe sleeve template library exists; risky as a first target**.

## Pants

- **Files/data:** `Pants/<name>/pants.json` and `pants.png`; four `*Pants` models.
- **Canvas/frame/anchors:** freeform integer source rectangles with `BodyPosition` and `PantsSize`; no 1920x1376 native atlas requirement.
- **Directions/animation:** four directions plus shared idle/movement/uniform animations.
- **Color:** full sprite or multiple named mask layers; skin masks; prismatic.
- **Layering:** normally over shoes/player and under shirt; `HideLegs` and `HideShadow`; generic overrides.
- **Equipment:** optional pants-slot `Item`; no current-source `FromItemId` shortcut confirmed.
- **Unlock/API:** Hand Mirror, presets, locks, and direct pants API.
- **UX/multiplayer:** item-backed output has native equip semantics; otherwise Hand Mirror. Same-pack peer constraint.
- **Limitations:** leg motion, long hems, sitting/swimming, and upper/lower garment overlap. Oversized dresses may need a paired shirt and explicit draw rules.
- **Procedural realism:** **medium** for fitted trousers/short skirts using tested templates; **low** for long or wide hems initially.

## Hats

- **Files/data:** `Hats/<name>/hat.json` and `hat.png`; four `*Hat` models.
- **Canvas/frame/anchors:** arbitrary integer rectangles using `HeadPosition` and `HatSize`; larger than native 20x20 is supported.
- **Directions/animation:** four directions and full shared animation system.
- **Color:** full sprite, named mask layers, skin tone masks, or prismatic.
- **Layering:** normally topmost; `HideHair`, visibility properties, and draw overrides.
- **Equipment:** optional hat-slot `Item`; `FromItemId` is confirmed for CP-supplied existing hats.
- **Unlock/API:** Hand Mirror/presets/CP locks/API.
- **UX/multiplayer:** item-backed hats are intuitive; multiple color layers add Hand Mirror steps.
- **Limitations:** large brims, hair clipping, and animated appendages require per-direction tests.
- **Procedural realism:** **high** for compact hats/accessories; **medium** for large/animated hats.

## Accessories

- **Files/data:** `Accessories/<name>/accessory.json` and `accessory.png`; four `*Accessory` models. The modern system supports multiple accessory slots; legacy primary/secondary/tertiary API types are deprecated.
- **Canvas/frame/anchors:** arbitrary integer rectangles using `HeadPosition` and `AccessorySize`. Despite the name, accessories can be body-sized (the example pack includes capes/scarves).
- **Directions/animation:** four directions and full shared animations.
- **Color:** all shared coloring/mask features.
- **Layering:** `DrawBehindHead`, `DrawAfterPlayer`, `DrawAfterSleeves`, generic overrides, and per-frame overrides.
- **Equipment:** no native `Item` linkage. Use Hand Mirror, accessory-slot API, presets, or lock/unlock rules.
- **UX/multiplayer:** accessory slot selection is additional UX; API has explicit slot set/clear/color. Synced modData, common-pack requirement.
- **Limitations:** “accessory” is semantically broad, so generator metadata must distinguish face, head, neck, back, waist, and body-overlay bounds. Capes/scarves need motion-aware frames.
- **Procedural realism:** **high** for glasses, pins, small bows; **medium/low** for capes, bags, and scarves.

## Hairstyles

- **Files/data:** `Hairs/<name>/hair.json` and `hair.png`; four `*Hair` models.
- **Canvas/frame/anchors:** arbitrary integer rectangles using `HeadPosition` and `HairSize`.
- **Directions/animation:** four directions plus shared animation modes.
- **Color:** shared masks, multiple layers, skin masks, and authored-color opt-out.
- **Layering:** normally around the hair position; bald-head and draw overrides support replacement styles.
- **Equipment:** no native item. Hand Mirror, presets, API, and lock rules.
- **UX/multiplayer:** controller-aware hair browsing and color choice; synced appearance ID/colors.
- **Limitations:** hairstyle/hat compatibility and head-shape coverage. It is outside the first clothing-generator scope.
- **Procedural realism:** **possible but risky and not recommended for early work**.

## Shoes

- **Files/data:** `Shoes/<name>/shoes.json` and `shoes.png`; four `*Shoes` models.
- **Canvas/frame/anchors:** arbitrary integer rectangles using `BodyPosition` and `ShoesSize`.
- **Directions/animation:** four directions plus shared animations.
- **Color:** shared full/multi-mask/prismatic system.
- **Layering:** native sequence near player/pants; `DrawBeforePants` and generic overrides.
- **Equipment:** optional Boots/footwear `Item`; direct API and Hand Mirror are supported.
- **UX/multiplayer:** item-backed form is easiest; same-pack peer requirement.
- **Limitations:** tiny readable area and leg-frame alignment. Shoe automation adds little style payoff before shirts/pants work.
- **Procedural realism:** **medium-high** with fixed templates, but low priority.

## Bodies

- **Files/data:** `Bodies/<name>/body.json`, `body.png`, and optionally `eyes.png`; four `*Body` models and optional portrait data.
- **Canvas/frame/anchors:** arbitrary integer body rectangles. Body models do not use `BodyPosition`; they provide `BodySize`, eye/background positions, `HeightOffset`, and optional accessory/head/leg/shoe/body/arms offsets that move all other equipped layers.
- **Directions/animation:** four directions, extensive animation data, eye/player offsets, and subframes.
- **Color:** shared masks plus skin-tone model/masks.
- **Layering:** replaces or augments Player and controls offsets of every garment class.
- **Equipment:** no wearable `Item`. Hand Mirror/presets/content data support it. Direct generic API setting is not working by the inspected 7.5.0 key map.
- **UX/multiplayer:** body choice is present in the Hand Mirror UI; preset outfits can include it. Cross-peer behavior untested.
- **Limitations:** the highest compatibility surface—eyes, skin, all farmer animations, portraits, and every garment anchor. A custom body multiplies rather than reduces garment validation work.
- **Procedural realism:** **low and out of scope**. Generate against Fashion Sense's default/native body contract first.

## Larger garments and coordinated outfits

- There is no dedicated coat/dress/robe appearance type.
- Oversized source rectangles are confirmed for all Fashion Sense types. A coat can be a large shirt plus sleeves; a dress may combine shirt and pants; a cape may be an accessory.
- `preset_outfits.json` can present a coordinated set. `AppearanceSyncing` can coordinate animation state. Draw-order overrides can keep sections together.
- **Likely capability:** reliable generated larger garments after a tested multi-part template and collision matrix exist.
- **Untested capability:** automatic cross-type fitting without hand-authored templates. This is the riskiest part of the proposal.

# Reusable functions, models, and contracts

## Use directly at runtime/export boundaries

- Native `Data/Shirts`, `Data/Pants`, `Data/Hats`, qualified item IDs, `ItemRegistry`, and Content Patcher asset edits.
- Native direction mapping and `FarmerRenderer` frame/feature-offset behavior for vanilla exporters and test fixtures.
- Native `Data/TailoringRecipes` for semantic inputs to already registered outputs.
- Fashion Sense's JSON content models, `StartingPosition`, `HeadPosition`/`BodyPosition`, `*Size`, animation models, color-mask layers, draw-order overrides, item blocks, presets, lock state, and public API.
- Fashion Sense Hand Mirror/controller UX and renderer. The future generator should emit input for it, not copy its draw code.

Confirmed game methods/contracts useful for verification are `Farmer.GetDisplayShirt`, `Farmer.GetDisplayPants`, `Farmer.GetShirtColor`, `Farmer.GetPantsColor`, `Farmer.ShirtHasSleeves`, `TailoringMenu.GetRecipeForItems`, `TailoringMenu.CraftItem`, and `Utility.getRandomCosmeticItem(Random)`. They are game implementation points, not code to vendor.

Fashion Sense internally already implements each content pack's `Get*FromFacingDirection`, source-rectangle/animation selection in `AppearanceHelpers`, layer sorting in `LayerManager`, item registration/equip patches, and anchoring/drawing in `DrawManager`. These confirm the framework owns the problem. Except for the documented public API, they are internal contracts and should not be called by the generator.

## Use as design patterns, not external APIs

- `TailoringMenu.GetRecipeForItems`: all-tag matching, ordered first match, registered output ID.
- `Utility.getRandomCosmeticItem`: weighted category branch, allowlist/range, rejection exclusions, injected RNG, fallback.
- Fashion Sense internal unlocked-appearance selection: filter locked models, then uniform random choice. It is internal, not a supported external API.
- The Sailor reference pack's `RANDOM_ITEMS` + `PerItemCondition`, keyed Content Patcher random choices, and paired top/bottom keys demonstrate data-driven pool filters and coordinated output variants.

## Do not copy or depend on

- Decompiled game implementation as a redistributed dependency.
- Fashion Sense internal managers or renderer patches.
- Fashion Sense raw-texture mutation/draw override API for normal generated garments.
- The Sailor pack's assets, IDs, or outfit-specific pixel arrangements.

# Logical-pixel generation feasibility

## Required invariant

```text
one output PNG pixel = one logical source pixel
```

- Recipe/component coordinates, anchors, bounds, source rectangles, and frame offsets must be integers.
- Rasterization occurs directly into the final logical canvas.
- Preview enlargement may use integer nearest-neighbor only (for example 8x). Preview pixels never return to the source pipeline.
- No high-resolution generative image, resampling, antialiasing, smoothing, fractional transforms, or downscaling is allowed.
- Reference images produce semantic traits only. They never enter the raster compositor.

This is technically realistic because both native assets and Fashion Sense consume discrete PNG source rectangles. The hard problem is not raster format; it is maintaining silhouette, anchor, direction, animation, and layer compatibility.

## Smallest proposed architecture (do not implement yet)

```text
reference observations / named style profile
    -> semantic recipe
       (category, archetype, silhouette, length, fit, collar, sleeve,
        layers, palette role, pattern density, accessories, asymmetry)
    -> compatibility resolver
       (required/excluded tags, anchor/body contract, layer budget,
        direction coverage, animation class, mask-channel budget)
    -> validated logical components
       (integer masks, outlines, seams, collar, trim, shading ramps)
    -> logical-pixel builder
       (transparent integer grid; direct cell writes only)
    -> validators
       (bounds, opaque-pixel budget, direction coverage, anchor,
        color-mask overlap, layer collision, atlas addressing)
    -> exporters
       -> vanilla shirt/pants/hat PNG + Data entries
       -> Fashion Sense PNG + appearance JSON + optional Item/preset
```

Suggested data separation:

1. **Style profile:** reusable weighted trait vocabulary; no item IDs and no rarity.
2. **Semantic garment recipe:** one resolved design intent with explicit constraints and provenance.
3. **Component library:** authored logical templates parameterized by tags and integer bounds.
4. **Compatibility rules:** declarative `requires`, `excludes`, `fits`, direction symmetry, layer order, and color-channel limits.
5. **Build target contract:** vanilla-shirt, vanilla-hat, vanilla-pants, or Fashion-Sense type/version.
6. **Validation report:** machine-readable pass/fail and warnings; never silently clip or resample.

The resolver should copy tailoring's semantic structure—tags to filtered compatible result—but return component templates rather than registered items. Reward selection should then copy the random-cosmetic pattern over only validated finished candidates.

# Final feasibility report

1. **What vanilla supports reliably:** compact four-direction 8x8 shirts with one dye mask; compact static 20x20 hats with hair modes/prismatic option; and fully animated pants overlays when a complete 96x688-per-body atlas is correctly authored. Native item, equipment, tailoring, dye, shop, save, controller, and multiplayer plumbing already exists.
2. **What Fashion Sense adds:** arbitrary logical rectangle sizes, explicit integer anchors, independent sleeves/shoes/accessories/hair/bodies, idle/movement/uniform animation, multiple named color regions, skin masks, draw-order controls, locks, presets, a Hand Mirror UI, item linkage for four types, CP data integration, and a public appearance API.
3. **Existing leverage:** native data/item/tailoring contracts; native direction/frame rules; Content Patcher delivery; Fashion Sense JSON models, renderer, animations, masks, layering, UI, item registration, locks, presets, API, and debug reload tools.
4. **Still required:** reference-to-trait analysis, recipe schema, a small logical component/template library, compatibility resolver, deterministic pixel compositor, palette/shading rules, exporters, static validators, in-game screenshot test harness, and multiplayer acceptance tests.
5. **Technical realism:** **yes, confirmed at the file/renderer-contract level**. End-to-end reliability is still untested. Direct logical-pixel construction is a natural match for both targets.
6. **Safest automation order:** Fashion Sense static shirts; native compact shirts; compact hats; small accessories; then shoes and fitted pants. Color-mask variants are safer than geometric variants.
7. **Risky types:** sleeves during tool animations, native pants atlases, long/wide skirts, full dresses/coats split across layers, capes/scarves, hair, and especially bodies.
8. **Reference -> recipe -> grid viability:** **viable** if references stop at semantic traits and all geometry comes from validated logical templates. An unconstrained image model producing pixels would violate both reliability and the hard rules.
9. **First proof of concept:** one static four-direction **Fashion Sense shirt**, native-scale 8x8 torso coverage (or the smallest verified template bounds), one collar family, one layering option, two palette ramps, and at most two non-overlapping color-mask layers. Also export the same compatible recipe as a vanilla 256-wide shirt sheet to test the exporter boundary, but treat the Fashion Sense form as primary.
10. **Abandon/change criteria:** do not abandon now. Substantially change course if the POC cannot pass all four directions plus walk/tool/swim/bath/UI tests without per-output manual pixel repair; if a verified Fashion Sense default-body anchor template cannot be stabilized; or if multiplayer peers cannot resolve generated IDs deterministically. In that event, narrow scope to curated logical templates with procedural palette/trim/pattern variation rather than freeform garment geometry.

## Gate before implementation investment

The next phase should install Fashion Sense only in an isolated test setup and validate one hand-authored logical fixture—not generated fashion—against front/back/left/right, walk, run, tool use, sitting, swimming/bathing, inventory item, Hand Mirror/controller, save/reload, and two-player sync. Until that passes, animation-heavy and multi-part outputs remain **untested**, not promised capabilities.

# Source index

- Stardew Valley Wiki: [shirts](https://stardewvalleywiki.com/Modding:Shirts), [pants](https://stardewvalleywiki.com/Modding:Pants), [hats](https://stardewvalleywiki.com/Modding:Hats), [tailoring recipe data](https://stardewvalleywiki.com/Modding:Tailoring), and [1.6 migration notes](https://stardewvalleywiki.com/Modding:Migrate_to_Stardew_Valley_1.6).
- Installed Stardew Valley `1.6.15.24356`: `Stardew Valley.dll`, `StardewValley.GameData.dll`, `Characters/Farmer/{shirts,pants,hats}`, and `Data/{Shirts,Pants,Hats,TailoringRecipes}`. These local installed files resolved omissions in the public data pages, especially pants atlas geometry and random cosmetic selection.
- Fashion Sense: [7.5.0 release](https://github.com/Floogen/FashionSense/releases/tag/v7.5.0), [source at the inspected commit](https://github.com/Floogen/FashionSense/tree/39e9e9e13c9f9a78416172e73a229cf8703ddb59), [content-pack overview](https://github.com/Floogen/FashionSense/wiki/Creating-a-Content-Pack), [Content Patcher integration](https://github.com/Floogen/FashionSense/wiki/Content-Patcher-Integration), [public API](https://github.com/Floogen/FashionSense/wiki/Fashion-Sense-API), [animation](https://github.com/Floogen/FashionSense/wiki/Animation-Properties), [color-mask layers](https://github.com/Floogen/FashionSense/wiki/Color-Mask-Layers-Property), and [draw-order override](https://github.com/Floogen/FashionSense/wiki/DrawOrderOverride-Property).
- Project-local capability catalog: `docs/TFWR_CODEX_MOD_TOOLBOX_INDEX.md`. Only clothing-relevant entries informed this study.
