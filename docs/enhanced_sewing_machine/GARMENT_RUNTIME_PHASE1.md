# Enhanced Sewing Machine — Garment Runtime Phase 1

Status: **compiled/static-tested; live runtime QC pending**

Scope: hat-only proof of source-resolution-independent worn rendering.

## Goal

Prove that Enhanced Sewing Machine can output a **real Stardew hat item** while our runtime renders higher-density worn art independently of the source PNG's raw dimensions.

The proof separates:
- **item identity/equipment** — vanilla Stardew `Hat`;
- **worn artwork resolution** — our garment definition;
- **physical worn size** — `RenderScale`;
- **head seating** — anchor + directional offset metadata.

The target is a 32×32 logical frame kept 32×32 on disk but drawn at `RenderScale = 0.5`, so each source pixel is 2 display pixels at normal farmer scale instead of vanilla's 4.

```text
vanilla-density 16px art: 16 × 4 × 1.0 = 64 display px
high-density 32px art:    32 × 4 × 0.5 = 64 display px
```

This avoids destructively shrinking good 24–32px source art just to make it wearable.

## Phase 1 non-goals

Not in this milestone:
- sewing-machine UI;
- RNG generation;
- runtime Python/image generation;
- shirts, sleeves, pants, shoes;
- dyeing, salvage, rarity, Inspiration items, Fashion Fragments;
- production art;
- Fashion Sense content-pack loading or wardrobe UI.

## Dependency decision

**Fashion Sense is not a runtime dependency for Phase 1.**

Fashion Sense remains a technical reference for concepts already proven useful:
- per-direction appearance selection;
- head-position style offsets;
- left/right mirroring;
- source rectangle and draw scale as separate concepts.

No Fashion Sense source code is copied into this mod. The implementation is written directly against Stardew/SMAPI/Harmony and the installed Stardew 1.6.15 behavior.

If later milestones would require recreating substantial FS systems, dependency cost should be re-evaluated instead of automatically reimplementing them.

## Confirmed vanilla 1.6.15 findings

Installed assembly: Stardew Valley 1.6.15.24356.

`FarmerRenderer.drawHairAndAccesories(...)` owns the normal worn-hat draw. Vanilla:
- selects a 20×20 hat source frame;
- uses `4f * farmerScale` as source-pixel draw scale;
- selects direction by offsetting the 20px source frame;
- applies current Farmer feature X/Y offsets;
- applies hairstyle hat offset unless the hat ignores it;
- draws at `FarmerSpriteLayers.Hat`.

`Data/Hats` remains a string dictionary. Relevant fields:

```text
0 internal name
1 description
2 hair display mode
3 ignore hairstyle offset
4 tags
5 display name
6 sprite index
7 texture asset
```

The proof registers a custom carrier item in this data and points its vanilla texture at a fully transparent 20×80 atlas.

## Why a transparent vanilla carrier

The carrier is still a genuine `(H)` item, so Stardew owns inventory behavior, the hat equipment slot, save serialization, normal item identity, and normal hat hair-mode state.

Vanilla draws the transparent carrier normally. A Harmony **postfix** then adds our high-density worn layer for that carrier only.

This avoids replacing the whole Farmer draw method and avoids suppressing unrelated hats, hair, accessories, shirts, or controls. If our definition, texture, or patch is unavailable, the custom overlay simply doesn't draw and normal Stardew rendering remains intact.

## Current metadata contract

`mods/EnhancedSewingMachine/assets/garments/dev_proof32.json` (moved into the generic registry in Phase 2):

```json
{
  "ItemId": "RNGClothing.ESM.ProofHat",
  "WornTexture": "assets/proof_hat_32.png",
  "FrameWidth": 32,
  "FrameHeight": 32,
  "RenderScale": 0.5,
  "VanillaReferenceAnchor": { "X": 10, "Y": 16 },
  "Directions": {
    "Front": { "SourceX": 0, "SourceY": 0, "AnchorX": 16, "AnchorY": 25 },
    "Right": { "SourceX": 0, "SourceY": 32, "AnchorX": 12, "AnchorY": 25 },
    "Back":  { "SourceX": 0, "SourceY": 64, "AnchorX": 16, "AnchorY": 25 },
    "Left":  { "MirrorOf": "Right", "AnchorX": 20, "AnchorY": 25, "FlipX": true }
  }
}
```

Definitions support authored frames or a mirrored source view. Left currently reuses Right specifically to prove the mirror contract.

## Placement model

Two coordinate systems are intentionally separated.

**Source anchor:** `AnchorX/Y` is measured in that garment's source pixels. It is the pivot inside the 16–32px worn frame. Changing source resolution therefore does not force a matching change to the world-space placement model.

**Direction offset:** `OffsetX/Y` is measured in vanilla logical pixels. At normal farmer scale, one offset unit moves four display pixels regardless of whether the source frame is 16, 20, 24, or 32 pixels. This keeps fitting values consistent across source densities.

The runtime reconstructs the same vanilla hat pivot inputs: farmer draw position/origin, animation position offset, `featureXOffsetPerFrame`, `featureYOffsetPerFrame`, `hairstyleHatOffset`, renderer height offset, and current animation flip.

It then maps `VanillaReferenceAnchor` through vanilla 4× density to create a stable head reference point. The garment's own anchor is passed to `SpriteBatch.Draw` with:

```text
drawScale = 4 × farmerScale × RenderScale
```

Physical size is therefore independent from the PNG's frame dimensions.

## Proof assets

Built by:

```bash
python3 tools/build_esm_proof_assets.py
```

The script uses only deterministic geometric pixel rules. It creates:
- `carrier_hat_20x80.png` — fully transparent vanilla carrier texture;
- `proof_hat_32.png` — original debug cap shapes, 32×32 Front/Right/Back cells; Left mirrors Right at runtime.

These pixels are project-owned diagnostic art. No Stardew, Fashion Sense, or third-party art is copied.

## Debug command

After loading a save, `rng_garment_hat` adds the proof carrier to inventory. `rng_garment_hat equip` equips it immediately, first preserving the currently worn hat in inventory if space exists.

## Static proof completed

`EnhancedSewingMachine.csproj` builds Release successfully.

`EnhancedSewingMachine.Tests` verifies:
- `.5` render scale produces 2 display pixels per 32px source pixel;
- 32×.5 and 16×1.0 have equal nominal physical width;
- vanilla pivot baseline math;
- vanilla reference-anchor mapping;
- direction offsets use vanilla logical units;
- Left can reuse Right's source rectangle;
- mirrored Left keeps its own anchor;
- all four directions resolve.

## Live QC gate — REQUIRED before calling Phase 1 proven

The game was not running while this milestone was implemented. No runtime PASS is claimed yet.

Run Stardew through SMAPI, load a save, then:
1. confirm the mod loads with no SMAPI errors;
2. run `rng_garment_hat equip`;
3. capture **Front / Right / Back / Left** at normal gameplay scale;
4. confirm all four are actually the 32px proof art, not a stale/vanilla hat;
5. confirm the physical width is in the normal vanilla-cap range;
6. confirm no face-covering / giant-hat failure;
7. confirm hat follows idle/walk head bob without obvious detachment;
8. confirm Right→Left mirroring is correct;
9. equip an ordinary vanilla hat and confirm it is completely unaffected;
10. remove the proof hat and confirm ordinary hair/equipment behavior returns.

### Calibration rule

If seating is wrong but physical scale is correct, tune only `VanillaReferenceAnchor`, per-direction `AnchorX/Y`, or per-direction `OffsetX/Y`.

**Do not resize the 32×32 PNG to solve seating.**

If physical size is wrong, tune `RenderScale` independently.

## Risks still unproven

- non-zero farmer rotation/action frames;
- swimming/bathing transitions beyond the explicit hide check;
- horse alignment;
- multiplayer remote Farmer rendering;
- masks/hair-hiding semantics beyond the proof carrier's basic hair mode;
- UI portrait/menu render equivalence;
- compatibility with mods that fully replace `FarmerRenderer.drawHairAndAccesories`.

Those belong to later gates after the basic four-direction world render passes.
