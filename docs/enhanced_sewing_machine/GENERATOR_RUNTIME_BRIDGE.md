# Enhanced Sewing Machine — Existing Generator → Runtime Bridge

Status: **implemented/static-verified; live generated-garment QC pending one restart**

## Purpose

The existing Python clothing generator remains the authoring/generation engine.
Stardew does not run Python.

Instead, an offline compiler resolves generator seeds into immutable runtime assets:

```text
V5 authored generator
       ↓
seeded Garment
       ↓
compile_esm_garments.py
       ↓
content-addressed PNG + runtime JSON
       ↓
GarmentRegistry
       ↓
real Stardew GeneratedHat item
```

This keeps generation and game runtime separate. The sewing machine can later select from a compiled pool without embedding Python or image-generation logic inside Stardew.

## Compiler

Tool:

```bash
python3 tools/compile_esm_garments.py
```

Optional:

```bash
python3 tools/compile_esm_garments.py --seeds 1000,1003,1014
python3 tools/compile_esm_garments.py --dry-run
```

The first integration batch intentionally covers the four current `PRODUCTION` HEAD bases with two deterministic rolls each:

- soft_cap: 1000, 1007
- knit_cap: 1003, 1004
- wide_brim_hat: 1002, 1016
- felt_hat: 1005, 1014

These are integration fixtures, not a final curated player pool.

## Safety / provenance gate

The bridge refuses any output whose base classification is not `PRODUCTION`.

That means current source-backed/reference-only Beret/Baseball/Snapback masters cannot accidentally enter the shippable compiled runtime pool through this tool. They remain useful for architecture/QC only until their redistribution status changes.

The compiler also refuses a roll if the authored renderer reports dropped cells.

## Immutable generated assets

Compiled textures are written under:

```text
mods/EnhancedSewingMachine/assets/generated/authored_v5/
```

Runtime definitions are written under:

```text
mods/EnhancedSewingMachine/assets/garments/generated/
```

IDs include generator seed, construction, and a digest of the resolved pixels, for example:

```text
gen.v5.1003.knit-cap.91040e663c58
```

The compiler **never deletes old generated textures/definitions**.

If a future generator change makes the same seed produce different pixels, the new pixel digest creates a new garment ID/path. Old saved items can therefore keep resolving the old immutable texture referenced by their saved render snapshot.

The active pool is listed in:

```text
mods/EnhancedSewingMachine/assets/generated/COMPILED_CATALOG.json
```

and the normal GarmentRegistry index points at the active generated definitions.

## Metadata carried across the bridge

Each compiled runtime definition carries:

- family;
- construction/shape;
- material/treatment when the generator supplied one;
- palette;
- motif classes;
- style;
- quality tier when present;
- exact decal names;
- source classification;
- `GeneratorId = v5.authored`;
- generator bridge version;
- original generator seed.

When a real Stardew Hat item is created, this provenance is copied into `GarmentInstanceData` alongside the sewing/item seed and resolved render snapshot.

This deliberately keeps two concepts separate:

- **generator seed** = what produced the garment pixels;
- **item/sewing seed** = the future transaction/RNG event which selected or awarded that compiled garment.

## Current compiled bridge batch

8 generated hats are active. All use the existing V5 authored 20×20 frame contract, preserved at native logical density with `RenderScale = 1.0`.

No PNG is resized by the bridge.

The atlas is the generator's existing four-view order:

```text
Front
Right
Left
Back
```

and the runtime definition maps those source rows directly.

## Validation

`tools/validate_esm_generator_bridge.py` regenerates every active compiled seed through the current generator and checks:

- regenerated garment ID;
- regenerated pixel digest;
- on-disk texture pixel digest;
- definition ID and texture path;
- exact generator seed/version;
- `PRODUCTION` classification;
- frame dimensions.

Current result:

```text
ALL 8 COMPILED GENERATOR GARMENTS REPRODUCE EXACTLY
```

The generic runtime validator currently reports:

```text
10/10 garment definitions valid
```

(2 renderer regression definitions + 8 actual generator outputs.)

C# item/runtime tests remain:

```text
17/17 PASS
```

The wider historical `v5.tests.test_authored` suite currently has pre-existing failures caused by newer source-backed/four-view library entries being visible to assertions written for the older three-view-only library. The targeted generator calls used by this bridge are deterministic and the bridge's exact regeneration validator passes; those stale historical tests were not silently treated as green.

## Dev workflow

After the next DLL restart:

```text
rng_garment list
rng_garment equip <compiled-id> 777
rng_garment inspect
```

A new command is also available:

```text
rng_garment reload
```

Once this DLL is loaded, future **asset-only** bridge recompiles can reload the GarmentRegistry without restarting Stardew again.

## Live gate

After one restart:

1. registry must load 10 definitions;
2. equip one compiled Soft Cap;
3. equip one compiled Knit Cap;
4. equip one compiled Wide-Brim Hat;
5. equip one compiled Felt Hat;
6. capture all four directions at normal scale;
7. confirm seating/readability and no renderer regression;
8. inspect each item and confirm generator ID + original generator seed + palette/decal metadata survived into the real Hat item;
9. verify a vanilla hat remains unaffected.

Any seating issue should be fixed in the runtime definition/bridge placement contract, never by destructively resizing the generated PNG.

## Next after the live gate

The next subsystem is the **tailoring selection service**: give Textile, Inspiration and a sewing RNG seed to a query layer which filters/scores the compiled garment pool and returns a garment ID. That service becomes the seam between the generator catalog and the future Enhanced Sewing Machine UI.
