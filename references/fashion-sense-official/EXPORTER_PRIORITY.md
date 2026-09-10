# Exporter gap — classified, not a checklist

27 hat properties and 26 shirt properties exist. We emit 6 and 5. Implementing
the rest blindly would be work without a reason, so each is placed in one of
four bands and the first two are the only ones that justify code now.

---

## 1. REQUIRED FOR CORRECTNESS
Absence produces a wrong or silently broken item.

| Property | Why | Status |
|---|---|---|
| all four direction models | a missing facing draws **nothing**; no fallback exists (A2) | **DONE** — exporter raises if any direction is absent |
| integer `Position` values | a float makes FS reject the whole appearance silently (A4) | **DONE** — exporter asserts before writing |
| `Format` | defaults to `1.0.0`; format-gated behaviour resolves against the wrong version (A5) | **DONE** — emits `7.5.0` |
| per-type `HideWhileSwimming` / `HideWhileWearingBathingSuit` defaults | default **false for hats, true for shirts**; copying a hat's JSON shape to a shirt changes behaviour (G) | **TODO** — resolve defaults per appearance type |
| `Scale` per direction | ours is authored at 4x so the default is right today, but the Envelope must carry it per direction, and our recorded "Scale is ignored" note was wrong (A1) | **PARTIAL** — note corrected; emission still TODO; **untested in-game** |

## 2. REQUIRED FOR SOURCE FIDELITY
An imported item must behave the way its original author made it behave.

| Property | Why | Status |
|---|---|---|
| `HideHair` / `UseBaldHead` | 2 of 116 source hats declare `HideHair`; an item generated from that art must keep doing so (B1) | **DONE** — `v5/hairpolicy.py`, `from_source()` reads the source declaration |
| `DisableGrayscale` | source packs rely on FS tinting; we bake colour, so we must opt out explicitly | **DONE** |
| provenance in `Tags` + pack `Author` | `Author` is what the Hand Mirror shows; it is the correct carrier for attribution | **DONE** — plus `CREDITS.txt` |
| `ColorMasks` passthrough | a source that declares masks expects those exact RGB values to remain keyable | **TODO** — only matters once we ship recolourable output |
| source `DrawOrderOverride` | if an author layered a piece behind hair, dropping it changes their art | **TODO** — none in the current library, so no urgency |

## 3. USEFUL GENERATOR FEATURE
Real capability, no correctness risk in deferring.

| Property | Value | Note |
|---|---|---|
| `ColorMaskLayers` | player-recolourable sections mapped to our semantic roles | **BLOCKED — see below** |
| `Flipped` | Right can point at the Left region instead of duplicating pixels | saves sheet space; also removes a class of left/right drift |
| `Item` | the appearance also becomes a wearable in-game item | wanted eventually for generated wardrobes |
| `IsPrismatic` | a novelty finish that costs one boolean | cheap tier-differentiator for legendary output |
| `Tags` | Hand Mirror search | already emitted; could carry style tags |

### Why `ColorMaskLayers` is blocked, not merely deferred

It is the highest-value item on this list — it maps almost exactly onto the
body/trim/accent/hardware roles the source pipeline already derives. Two things
must be true first, and one of them is currently false:

1. **`DisableGrayscale: true` disables all colour masks.** Baked colour and
   recolourable layers are mutually exclusive per model. Adopting layers means
   *stopping* baking colour for those items, not adding a field. This is stated
   in `Color-Mask-Layers-Property.md` and would otherwise have silently no-oped.
2. **The semantic mapping must reproduce the source cleanly first.** Per the
   instruction not to implement until confirmed: our vocabulary → role mapping
   is proven only for pure-greyscale families. `BoaterHat` and `SunHat` build a
   vocabulary that interleaves greys and colours and then assigns
   outline/shadow/mid/light by luminance **across different materials** — a
   straw crown and a coloured band land in one ramp. Emitting mask layers off
   that mapping would hand players sliders that recolour the wrong pixels.

**Gate:** implement `ColorMaskLayers` only after a material split separates
cloth / metal / coloured trim before roles are assigned, and after a
round-trip test shows layer-based output reproducing the source.

## 4. ADVANCED / DEFER
Capability we have no current use for.

* Animation — `UniformAnimation`, `IdleAnimation`, `MovementAnimation`,
  `RequireAnimationToFinish`, `EndWhenFarmerFrameUpdates`, `AppearanceSyncing`.
  Everything we generate is a single static frame. `EndWhenFarmerFrameUpdates`
  becomes relevant if we ever generate sleeves or pants.
* Conditions — ~45 of them. Weather-gated or tool-gated appearances are a
  content idea, not a pipeline gap.
* `SkinToneMasks` / `DisableSkinGrayscale` — needed only for garments that
  expose skin.
* `HidePlayerBase`, `HideSleeves`, `HideWaterLine`, `HideLegs`, `HideShadow` —
  full-body and costume work.
* `FromItemId`, `IsLocked`, `Light`, Bodies (33 properties), Hairs, Shoes.

---

## Order of work

1. Per-type swimming/bathing defaults (band 1, small, currently wrong).
2. `Scale` emission plus an in-game test that actually validates A1.
3. Material split in the semantic mapping — unblocks `ColorMaskLayers`.
4. `Flipped`, once importing sources that ship only one side.
