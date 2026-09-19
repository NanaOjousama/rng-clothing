# Enhanced Sewing Machine — Tailoring Selection Service

Status: **implemented/static-tested; live command QC needs one DLL restart**

## Purpose

This service is the seam between the compiled garment catalog and the future Enhanced Sewing Machine UI.

Input:

```text
Textile + Inspiration + sewing RNG seed
```

Output:

```text
one compiled production GarmentId
```

It does **not** consume ingredients and does **not** draw a sewing-machine menu yet.

## Selection rules

Only garments which are both:

- `Classification = PRODUCTION`;
- generated/compiled (`GeneratorId` is present);

enter the tailoring pool.

That mechanically excludes:

- renderer dev proofs;
- current REFERENCE-only Beret/Baseball/Snapback source-backed assets.

Selection is deterministic for:

```text
Textile ID + Inspiration ID + sewing seed + active compiled pool
```

The selector uses a stable SplitMix64/FNV-based RNG rather than relying on `System.Random` implementation details.

Each eligible garment receives:

```text
Textile BaseWeight
+ Inspiration BaseWeight
+ textile metadata adjustments
+ inspiration metadata adjustments
```

with a minimum positive selection weight of 1.

Bias dimensions supported now:

- family;
- construction;
- material;
- style;
- palette;
- motif class;
- exact decal.

Textile profiles can also optionally hard-allow or hard-deny constructions for future material compatibility rules. Current profiles use soft biases only.

## Current development profiles

These values are **development calibration**, not locked final gameplay balance.

Textiles:

- `cotton`
- `wool`
- `canvas`

Inspirations:

- `sunflower`
- `frozen-tear`
- `ancient-doll`

The bias data is externalized in:

```text
mods/EnhancedSewingMachine/assets/tailoring/biases.json
```

so balancing does not require changing the selection algorithm.

The current 8-garment integration pool is intentionally tiny, so these weights only prove that the axes work. Final balance should happen after the compiled pool is much larger.

## Current dev commands

After the next DLL restart:

```text
rng_tailor profiles
rng_tailor roll cotton sunflower 12345
rng_tailor equip cotton sunflower 12345
rng_tailor reload
```

`roll` reports the selected GarmentId plus the leading candidate weights and Textile/Inspiration adjustments.

`equip` uses the same selection result and creates a real GeneratedHat item with the **sewing seed** stored as the item seed.

The selected garment also still carries its separate original **generator seed**, so the two RNG events remain traceable.

## Tests

C# tests now cover:

- same inputs + same seed are deterministic;
- dev and REFERENCE garments are excluded;
- Sunflower boosts flower/cottagecore metadata;
- Wool + Frozen Tear biases felt/winter metadata;
- unknown profiles fail cleanly;
- optional textile construction gates work.

Bias validator:

```bash
python3 tools/validate_esm_tailoring_biases.py
```

It checks that every current profile actually discriminates within the live compiled pool and prints the top weighted garments for every Textile + Inspiration pair.

Current profile adjustment ranges:

```text
cotton       -35..105
wool         -25..90
canvas       -20..85
sunflower      0..230
frozen-tear    0..190
ancient-doll   0..185
```

## Live gate

After one DLL restart:

1. `rng_tailor profiles` must show 3 Textiles + 3 Inspirations;
2. same `roll` command repeated twice must return the same GarmentId;
3. several different seeds should produce valid compiled garments;
4. `equip` must create/wear the selected real GeneratedHat;
5. `rng_garment inspect` must show:
   - item/sewing seed = the tailoring seed;
   - generator seed = the original compiled-art seed;
   - selected garment metadata unchanged;
6. dev proofs and REFERENCE-only assets must never appear;
7. vanilla hat regression remains unchanged.

## Next after live gate

Once this selector is live-proven, the next implementation is the **Enhanced Sewing Machine shell**:

- hook the vanilla sewing machine/tailoring interaction;
- leave ordinary vanilla recipes untouched;
- enter enhanced mode only for our supported inputs;
- initially expose Textile + Inspiration + Fashion Fragments;
- validate/roll/create the item first;
- consume ingredients **last**, only after item construction succeeds;
- controller-first navigation and i18n from the start.
