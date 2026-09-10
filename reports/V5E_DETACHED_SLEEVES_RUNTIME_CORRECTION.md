# V5E Detached Sleeves Runtime Correction

## Root cause

V5E exported the earlier experimental V5B custom Sleeves model:

- category: Fashion Sense `Sleeves`;
- frame size: 32×64;
- Scale: 2;
- BodyPosition: `(0,0)`;
- `DisableNativeOffset: true`;
- atlas: 384×1344;
- preset: explicit generated `SleevesId`.

That is the same contract that live hoodie testing had already shown rendering detached arm geometry below the Farmer. The final hoodie did **not** fix it with a new offset. It removed the uncalibrated custom Sleeves layer and returned arm animation to the native Farmer path through the Shirt's `SleeveColors`.

V5E accidentally treated the older V5B static assumption as authoritative instead of inheriting the later runtime correction.

## Corrected V5E contract

Version 1.1 now matches the final hoodie arm mechanics exactly:

- Shirt `HideSleeves: false`;
- exactly three jacket-specific `SleeveColors` in every direction;
- Shirt Scale 2 and BodyPosition `(0,32)` unchanged;
- Shirt native feature offsets remain enabled;
- preset `SleevesId: None`;
- no `Sleeves/` directory or custom arm atlas in the pack.

The torso, lapels, pockets, yoke, palette, anchors, and all jacket pixels are unchanged. The sleeve palette remains jacket-specific. The correction trades the unsupported custom cuff silhouette for proven native arm attachment; pretending the rejected atlas is safe would repeat the same runtime bug.

## Permanent regression guard

`generator/data/fashionsense/runtime_sleeve_contracts.json` records:

- `NATIVE_ANIMATED_SLEEVES_V1` as the live-evidence known-good contract;
- `CUSTOM_32X64_SCALE2_DISABLE_NATIVE_OFFSET` as rejected.

`generator/renderers/fashionsense/runtime_sleeve_contracts.py` provides a reusable validator that rejects any Rare+ pack which:

- contains a custom `Sleeves/` directory under the known-good contract;
- equips a non-`None` Sleeves ID;
- hides native sleeves;
- lacks three Shirt `SleeveColors`;
- changes the proven Shirt scale/body anchor;
- disables native Shirt feature offsets.

The V5E validator now calls this shared guard and writes its result into the rebuilt test pack.

## Runtime status

Static contract validation passes. Runtime status remains **EXPERIMENTAL / RETEST REQUIRED**. No runtime pass is claimed until the rebuilt pack is tested in live Stardew Valley.
