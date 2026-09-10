# Fashion Sense — official technical reference (local index)

Gathered **2026-09-08** from the official GitHub `development` branch, which is
the repository's own default branch, plus the official wiki and releases.

| | |
|---|---|
| Repository | https://github.com/Floogen/FashionSense (GPL-3.0) |
| Default / development branch | `development` — last push 2026-03-12 |
| Latest release | **v7.5.0**, 2026-03-12 (30 releases indexed) |
| Wiki | 39 pages, cloned to `wiki-git/` |
| Example Pack | 45 JSON files across 8 categories, mirrored to `examplepack/` |

## Local contents

    meta/repo.json          repository metadata
    meta/releases.json      all 30 releases with changelog bodies
    meta/tree.json          full development-branch file tree
    meta/README.md          development-branch README
    wiki-git/               complete official wiki (git clone)
    examplepack/            every Example Pack JSON, original folder layout
    src/                    the C# appearance models (authoritative defaults)
    converters/             ja2fs (MIT) and SkirtConverter, import references
    property_matrix.json    every documented property, per appearance type
    exporter_gap.json       what our exporters emit vs what FS supports
    BEHAVIOR_MAP.md         behaviour catalogue with generator implications

## Appearance types and their required properties

| Type | Props | Required | Frame folder | Model file |
|---|---|---|---|---|
| Hats | 27 | StartingPosition, HeadPosition, HatSize | `Hats/<name>/hat.json` + `hat.png` | HatModel |
| Shirts | 26 | StartingPosition, BodyPosition, ShirtSize | `Shirts/<name>/shirt.json` | ShirtModel |
| Pants | 26 | StartingPosition, BodyPosition, PantsSize | `Pants/<name>/pants.json` | PantsModel |
| Sleeves | 24 | StartingPosition, BodyPosition, SleevesSize | `Sleeves/<name>/sleeves.json` | SleevesModel |
| Shoes | 24 | StartingPosition, BodyPosition, ShoesSize | `Shoes/<name>/shoes.json` | ShoesModel |
| Accessories | 23 | StartingPosition, HeadPosition, AccessorySize | `Accessories/<name>/accessory.json` | AccessoryModel |
| Hairs | 24 | StartingPosition, HeadPosition, HairSize | `Hairs/<name>/hair.json` | HairModel |
| Bodies | 33 | StartingPosition, EyeBackgroundPosition, EyePosition, BodySize | `Bodies/<name>/body.json` | BodyModel |

17 properties are common to all eight types: `StartingPosition`, `Scale`,
`Flipped`, `DisableGrayscale`, `ColorMasks`, `ColorMaskLayers`,
`DrawOrderOverride`, `IsPrismatic`, `PrismaticAnimationSpeedMultiplier`,
`UniformAnimation`, `IdleAnimation`, `MovementAnimation`,
`RequireAnimationToFinish`, `HideWhileSwimming`,
`HideWhileWearingBathingSuit`, `HideWaterLine`, `Tags`.

## Packaged-example vs current-GitHub differences

The four packs under `generator conent` are CurseForge-era releases declaring
`MinimumVersion` 2.0.0–3.0.3. Current is 7.5.0. Observed differences, current
GitHub behaviour preferred in every case:

* Those packs omit `Format` entirely. `AppearanceContentPack.Format` defaults
  to `Version("1.0.0")`, so they load, but new-format features are not implied.
* They use only `ColorMasks`; `ColorMaskLayers` (multiple colourable sections)
  post-dates them.
* They predate `DrawOrderOverride`; the wiki still references an older
  accessory-only `DrawBeforeHair` in one prose line, which the current property
  tables no longer list. Treat `DrawOrderOverride` as the current mechanism.
* None declare `Scale`, so all inherit the 4.0 default.
