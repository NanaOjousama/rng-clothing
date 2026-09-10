# Hoodie Runtime Anchor Failure Fix

> Follow-up runtime evidence supersedes this report's earlier Hat conclusion: the Shirt/native sleeves/strings pass, but the Hat hood alone remained 64 display pixels low. See `reports/HOOD_ONLY_ANCHOR_FIX.md` for the version 1.2.0 correction.

## Result

The broken over-assembled preset has been replaced with the smallest supported runtime assembly:

```text
semantic hoodie recipe
    -> Fashion Sense Shirt (16x16, Scale 2, BodyPosition 0,32)
       -> native animated Farmer sleeves colored by Shirt SleeveColors
       -> drawstrings integrated into Shirt when requested
    -> Fashion Sense Hat/Hood (head-relative)
    -> one preset
```

The corrected pack contains no custom Fashion Sense Sleeves appearances and no Accessory appearances. Static validation passes. Runtime promotion remains **EXPERIMENTAL** pending the user's retest.

## Runtime evidence and component identification

The live result showed the Shirt/upper garment and Hood on the Farmer while separate arm-shaped pieces appeared below the feet.

That identifies the detached arm geometry as the generated custom **Sleeves** appearance:

- the Shirt texture has no detached animation atlas or arm-shaped source cells;
- the Hat contains only raised/lowered hood geometry and remained head/body-adjacent;
- only the custom Sleeves atlas contains complete separate arm frames;
- every previous preset explicitly equipped that Sleeves ID.

Three presets also equipped a small drawstring Accessory. The runtime description does not independently prove whether those few pixels detached too, but that layer was unnecessary and shared the same broad problem: a torso detail was assigned to a head-relative category. It has been removed conservatively rather than preserved without evidence.

## Fashion Sense 7.5.0 draw-contract audit

### Shirt

- Category: `Shirt`
- Frame: 16x16 logical pixels
- Scale: 2
- `BodyPosition`: `(0,32)`
- Direction rows: front 0, right 16, left 32, back 48
- Anchor behavior: body-relative with Shirt-specific native feature offsets
- Runtime result: aligned on the Farmer
- Decision: **keep unchanged**

The Shirt declares `HideSleeves: false`, three `SleeveColors`, and a color-mask layer. With no custom Sleeves equipped, Stardew/Fashion Sense retains the native animated arm drawing and uses the Shirt's color ramp.

### Previous custom Sleeves — blocking failure

- Category: `Sleeves`
- Source cell: 32x64 logical pixels
- Scale: 2
- `BodyPosition`: `(0,0)`
- `DisableNativeOffset`: true
- Atlas: 384x1344 with a full pose mapping
- Anchor behavior: custom Sleeves draw path, not the Shirt draw path
- Runtime result: separate arm geometry below the Farmer
- Decision: **remove from hoodie presets and pack**

The underlying incorrect assumption was that doubling a working 16x32 Scale-4 reference sleeve cell into 32x64 Scale 2 would preserve the same live origin automatically. It preserved nominal screen-space pixel density, but not the category-specific drawing contract.

Fashion Sense's `DrawSleevesCustom` draws the selected source rectangle using:

- the Farmer draw position plus `armOffset`;
- the shared Farmer draw origin;
- the Sleeves `BodyPosition` as its origin adjustment;
- the Sleeves scale;
- no Shirt-specific direction offset.

The generated atlas set `DisableNativeOffset: true` and `BodyPosition: (0,0)`. The larger logical source cells therefore had no runtime-calibrated origin correction. Static bounds and preview extraction could not expose that error because neither executes the live Farmer draw path.

A calibrated custom Sleeves backend could be a separate future R&D task, but retaining it here would make hoodie correctness depend on another unproven system. Native sleeves already provide the required animation safely.

### Hat/Hood

- Category: `Hat`
- Raised frame: 32x32, Scale 2, head-relative
- Lowered frame: 16x32, Scale 2, head-relative
- `HeadPosition`: direction-specific
- Raised hood: `HideHair: true`
- Lowered hood: `HideHair: false`, side before Player, back before Hair
- Runtime result: hood/upper component remained near the player
- Decision: **keep unchanged**

Hat is the correct category for geometry surrounding or sitting behind the head. Moving it into Shirt art would recreate the original weak-hood problem.

### Previous drawstring Accessory

- Category: `Accessory`
- Frame: 16x16, Scale 2
- `HeadPosition`: `(-8,-26)`
- Anchor behavior: head-relative Accessory feature path
- Design role: tiny body-relative torso lines
- Decision: **remove; integrate into Shirt**

Even if its doubled reference offset were correct, the separate layer provides no essential capability. The strings fit cleanly into the Shirt frame, should move with the torso, and do not need hair/head ordering. Removing it eliminates an anchor contract and an outfit slot.

### Preset

Previous preset:

```text
Shirt + custom Sleeves + Hat + optional Accessory
```

Corrected preset:

```text
Shirt + native sleeves through SleeveColors + Hat
```

Every corrected preset now has:

- `ShirtId`: generated hoodie Shirt;
- `HatId`: matching generated Hood;
- `SleevesId`: `None`;
- `AccessoryIds`: `None`, `None`, `None`.

## Shared fix versus per-garment patches

The correction is entirely shared:

- all six recipes select `native_sleeve_colors`;
- all custom Sleeves IDs are removed;
- all Accessory IDs are removed;
- drawstrings are rendered by the reusable Shirt neck-bridge program;
- Hat contracts remain shared by hood-up or hood-down state.

No garment received a compensating position number. The generated Sleeves and Accessory directories were removed from the old test pack, and the exact generated output/test-pack folders were rebuilt cleanly so stale broken appearances cannot continue loading.

## Corrected assets and validation

The replacement pack version is `1.1.0`.

Static validation now requires:

- six deterministic Shirts and six deterministic Hats;
- six Shirts with `HideSleeves: false` and a complete three-color `SleeveColors` ramp;
- six presets with `SleevesId: None`;
- six presets with three `None` Accessory slots;
- no `Sleeves/` directory in the pack;
- no `Accessories/` directory in the pack;
- unchanged Shirt scale/body anchor;
- unchanged Hat scale/head anchor, hair policy, and lowered-hood draw order;
- binary alpha and declared hood mask values;
- `EXPERIMENTAL / NOT TESTED` status.

`tools/validate_hoodie_layer_correction.py` passes these checks. The V5C2 baseline validator also remained clean before this shared simplification.

## What still requires runtime proof

This correction removes the components that could produce detached arm/accessory geometry. It does not claim a runtime pass before retesting.

The required checks are recorded in `reports/HOODIE_RUNTIME_ANCHOR_RETEST_CHECKLIST.md`, with particular attention to:

- front/right/back/left standing;
- walking;
- tool hold/use;
- native sleeves remaining attached and correctly colored;
- raised/lowered hood alignment and hair behavior;
- no pixels appearing below the Farmer.

No broader design work or garment architecture was changed.
