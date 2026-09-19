# Enhanced Sewing Machine — Generic Garment Runtime + Instance System

Status: **implemented and static-tested; live restart gate pending**

This milestone covers the two steps immediately after the 32px Phase 1 proof:

1. turn the hardcoded proof renderer into a reusable garment registry/runtime;
2. make generated garments real item instances whose identity survives normal
   Stardew item copying, save serialization, and network sync through item modData.

## Generic garment registry

Definitions now live under mods/EnhancedSewingMachine/assets/garments/.

The explicit index currently loads:
- dev.proof32 — 32×32 frames at RenderScale 0.5;
- dev.proof16 — 16×16 frames at RenderScale 1.0.

Both have the same nominal 64 display-pixel width at normal farmer scale.

The runtime is no longer tied to one proof JSON or one frame size. Each
definition supplies a stable garment ID, category, definition version, worn
texture path, frame size, render scale, vanilla reference anchor, directional
frames or one-hop mirror, per-direction source anchor and logical offset, plus
family/construction/material/palette/motif metadata.

GarmentRegistry loads each entry independently. One invalid definition is
rejected without disabling the rest of the registry.

Validation rejects unsupported categories, invalid dimensions/scales, missing
directions, mirror chains, out-of-bounds source rectangles, unsafe asset paths,
excessive offsets, and duplicate IDs.

The renderer still only patches our carrier hats. Vanilla hats remain untouched.

## Resolved garment item instance

The main carrier is (H)RNGClothing.ESM.GeneratedHat.

The old Phase 1 proof carrier is still registered temporarily so a dev save
that already contains it does not become an error item.

Every newly created generated hat gets an instance payload in item modData.

The payload stores:
- SchemaVersion;
- GarmentId;
- GenerationVersion;
- Seed;
- Category;
- Family;
- Construction;
- Material;
- Palette;
- Motif;
- a resolved render snapshot with DefinitionVersion, WornTexture, frame size,
  RenderScale, VanillaReferenceAnchor, resolved Front/Right/Back/Left frames,
  and AppearanceDigest.

The important rule is that the item stores the **resolved render snapshot**, not
only the seed or registry ID.

That prevents a later change to generator logic, mirror rules, scale, anchors,
or metadata from silently recomputing an existing garment into something else.

Production generated texture paths still need to be immutable. The instance
stores an appearance digest and warns once if the installed registry definition
for the same garment ID has drifted.

## Why item modData is a strong vanilla-first persistence base

This was checked against the installed Stardew 1.6.15 assembly.

StardewValley.Item exposes modDataForSerialization with an XmlElement("modData")
attribute, and its NetFields includes modData, so the data participates in
normal item serialization and multiplayer NetFields.

Item.getOne() calls GetOneCopyFrom(), and GetOneCopyFrom() explicitly copies
every modData entry to the cloned item.

That means the generated identity travels with the actual Hat item instead of
living in one global player setting.

Still required as a live gate: create one generated carrier, save/reload, move
it through inventory/chest/equip flows, and inspect that the same seed and
snapshot return.

## Runtime resolution behavior

When a generated carrier is worn:

1. read and decode its instance payload;
2. take the saved render snapshot;
3. load the referenced texture;
4. validate the snapshot against the actual texture;
5. select Front/Right/Back/Left;
6. apply farmer feature offsets / hairstyle offset;
7. draw at 4 × farmerScale × RenderScale.

The registry is needed to create new garments, but a previously saved item can
still render from its own snapshot if the registry entry is no longer listed,
provided its referenced texture remains installed.

Malformed item data fails open and logs only once per bad payload rather than
spamming every render frame.

## Current dev commands

After the next game restart:

~~~
rng_garment list
rng_garment give dev.proof32 12345
rng_garment equip dev.proof32 12345
rng_garment equip dev.proof16 54321
rng_garment inspect
~~~

rng_garment_hat remains a temporary alias for equipping dev.proof32.

These are development commands only. The Enhanced Sewing Machine UI will later
be the normal player path for creating garment instances.

## Static validation completed

Release build:
- EnhancedSewingMachine: success;
- 0 warnings;
- 0 errors.

C# tests: **17/17 PASS**.

They cover 32@0.5 and 16@1.0 physical-scale equivalence, vanilla hat
pivot/reference math, logical offsets, right-to-left mirroring, source-bound
validation, mirror-chain rejection, snapshot independence from later
definition edits, instance JSON round-trip, and malformed payload rejection.

Offline registry validator:
- PASS dev.proof32;
- PASS dev.proof16;
- PASS 32@0.5 == 16@1.0 nominal width;
- 2/2 definitions valid.

Tool: python3 tools/validate_esm_garments.py

## Live gate after restart

The currently running Stardew process loaded the previous DLL before this
milestone was built, so the new generic commands/runtime have not been claimed
as live-proven yet.

After restart:

1. rng_garment list must show both definitions;
2. equip dev.proof32 seed 12345;
3. capture Front/Right/Back/Left and confirm Phase 1 geometry did not regress;
4. rng_garment inspect must report seed 12345 and the 32px snapshot;
5. equip dev.proof16 seed 54321;
6. confirm it renders through the same generic code path at vanilla-like size;
7. save the game with one generated hat equipped or in inventory;
8. reload the save;
9. inspect it again and verify garment ID, seed, metadata, digest and render
   snapshot are unchanged;
10. move/clone it through normal item flows and ensure modData is preserved;
11. equip a normal vanilla hat and confirm it is unaffected.

Only after that live persistence gate should this instance system be treated as
fully proven.

## Not started yet

Still intentionally deferred:
- dynamic generated inventory icons/names;
- generator-to-registry export bridge;
- sewing-machine UI;
- Textile / Inspiration / Fashion Fragment gameplay;
- shirts/pants;
- runtime procedural composition;
- production Dad Cap promotion.

The immediate next implementation after the live gate is the
**existing-generator → compiled garment registry bridge**.
