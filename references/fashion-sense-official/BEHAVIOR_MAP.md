# Fashion Sense behaviour map

Each entry: **what it does · applies to · controlled by · official source ·
do we support it · change needed · safe default for the generator.**

Sources are the `development` branch (default branch, last push 2026-03-12),
release v7.5.0, the wiki clone in `wiki-git/`, and the C# models in `src/`.
Where the wiki and the C# disagree, the C# is authoritative and is cited.

---

## A. Corrections to conventions we had inferred wrongly

### A1. `Scale` is per-direction, not top-level — and it is not ignored
* **What** Scales the appearance when drawn. Default `4.0`, matching the game.
* **Applies to** all eight types.
* **Controlled by** `Scale`, a float **inside each direction model**.
* **Source** `src/AppearanceModel.cs:35` `public float Scale { get; set; } = 4f;`
  and `wiki-git/Scale-Property.md`.
* **Do we support it** No — and worse, we recorded a false finding. Our
  `authored/fit.json` states *"Fashion Sense ignored a top-level Scale field:
  soft_cap drawn at Scale 3, 4 and 5 rendered identically"*. That experiment
  put `Scale` at the top level of `hat.json`, where it is not a property of any
  model. FS did not ignore `Scale`; we never set it. **Runtime scaling IS
  available.**
* **Change needed** Yes. Emit `Scale` per direction; correct `fit.json`.
* **Safe default** Omit (inherit `4.0`) unless the art is authored at a
  different pixel grid, in which case `Scale = 4 / (art_pixels_per_game_pixel)`.

### A2. Missing directions draw nothing — there is no mirroring or fallback
* **What** Each facing is looked up directly; a null model draws nothing.
* **Applies to** all types.
* **Controlled by** presence of `FrontX` / `RightX` / `LeftX` / `BackX`.
* **Source** `src/HatContentPack.cs` `GetHatFromFacingDirection` — a plain
  switch over facing 0=Back, 1=Right, 2=Front, 3=Left returning `null` with no
  fallback branch.
* **Do we support it** Yes by accident: we always emit four directions.
* **Change needed** No, but make it an explicit invariant and validate it.
* **Safe default** Always emit all four. Never rely on inference.

### A3. `Flipped` — FS can mirror for us
* **What** Draws the sprite mirrored; the wiki says explicitly this is "useful
  for `LeftHat`/`RightHat`".
* **Applies to** all types.
* **Controlled by** `Flipped` (bool, default false).
* **Source** `wiki-git/Hat-Model-Properties.md`; `src/AppearanceModel.cs:22`.
* **Do we support it** No. We bake a mirrored Right frame into the atlas,
  which costs sheet space and lets Right drift from Left.
* **Change needed** Optional but recommended: point Right at the Left region
  with `Flipped: true`.
* **Safe default** Keep authoring both while our art is small; adopt `Flipped`
  when importing sources that only supply one side.

### A4. `Position` is integer — the cause of our silent whole-pack failure
* **What** `StartingPosition`, `HeadPosition`, `BodyPosition` are `int X, Y`.
* **Source** `src/Position.cs:5-6`.
* **Do we support it** Yes, empirically — we found that a float made FS reject
  the model and load zero hats. Now explained rather than merely observed.
* **Safe default** Emit ints; assert integrality before writing.

### A5. `Format` exists and we never emit it
* **What** Content-pack format version, a `Version`. Defaults to `1.0.0`.
* **Source** `src/AppearanceContentPack.cs:19`; examples declare `"Format":
  "5.3.0"` / `"6.3.0"`.
* **Change needed** Yes — declare the format we author against so future
  format-gated behaviour resolves correctly.
* **Safe default** `"Format": "7.5.0"`.

### A6. `fs_reload` removes the restart requirement
* **What** `fs_reload` reloads all packs live; `fs_reload_continuous` every 2s;
  `fs_freeze_self` freezes the player; `fs_display_movement` shows debug state.
* **Source** `wiki-git/SMAPI-Commands.md`.
* **Do we support it** No. Our QC watcher waits for a full game restart, and
  three capture runs were lost to that assumption — including one that captured
  empty frames because FS still held cached textures.
* **Change needed** Yes. The QC Bridge should issue `fs_reload` and re-list
  appearances instead of waiting for a restart.
* **Safe default** `fs_reload`, verify the pack's hats are listed, then capture.
* **LIMIT, measured the hard way.** `fs_reload` refreshes content packs the
  game already knows about. A pack FOLDER created after startup is not
  registered with SMAPI, so Fashion Sense lists its appearance names -- they
  show up in `list_hats` -- but never loads its textures. The hats equip and
  draw nothing, which is indistinguishable from art that failed. Every pack
  that existed before its session captured correctly; the one installed
  mid-session did not, and produced a full batch of frames containing only
  hair. **A new pack still needs a restart; only edits to an existing pack are
  hot-reloadable.** `qc.refresh()` now refuses to proceed when it detects this.

---

## B. Hat / head / hair interaction — directly relevant to the soft_cap problem

### B1. `HideHair` and `UseBaldHead`
* **What** `HideHair` hides the hairstyle entirely. `UseBaldHead` swaps the
  farmer to the game's bald sprite, so the *head silhouette itself* shrinks.
* **Applies to** `HideHair`: Hats, Bodies. `UseBaldHead`: Hats, Hairs.
* **Source** `wiki-git/Hat-Model-Properties.md`; `src/HatModel.cs:9`,
  `src/AppearanceModel.cs:28`.
* **Do we support it** We emit `HideHair: false` and never considered
  `UseBaldHead`. **This is a material omission**: the entire soft_cap
  investigation — the cap reading as buried under the hairstyle — was fought
  purely as a silhouette problem, when the framework offers two direct levers
  for exactly that.
* **CORRECTION to an earlier claim in this document.** A first draft said a
  snug cap "is usually authored with hair hidden or the bald head forced".
  The source library does not support that. Measured over its 116 hats:
  **114 declare nothing (hair kept), 2 declare `HideHair` (Headscarf 1,
  Plague Doctor Mask — both enclose the whole head), 0 use `UseBaldHead`.**
  Hiding hair is the rare exception, not the convention for close-fitting hats.
* **Change needed** Yes. Expose per-base, per-direction hair policy:
  `KEEP` / `HIDE` / `BALD`. Implemented in `v5/hairpolicy.py`.
* **Safe default** **`KEEP` for everything**, because that is what authors
  ship. `HIDE`/`BALD` are opt-in per base, justified by construction and
  confirmed by eye — never adopted because an overspill metric improved.

### B2. `HidePlayerBase`, `HideSleeves`
* **What** Hide the farmer's base sprite / the arms and sleeves.
* **Applies to** `HidePlayerBase`: all but Bodies. `HideSleeves`: all but Sleeves.
* **Safe default** false; only for full-body or costume appearances.

---

## C. Layering

### C1. Default draw order
* **Order** Pants → Shoes → Shirts → **Hair** → Sleeves → Accessories → Hat,
  each drawing over the previous.
* **Source** `wiki-git/Creating-a-Content-Pack.md`, "Default Draw Order".
* **Note** Hats draw over hair by default, so a hat that still reads as *under*
  the hair is a silhouette/coverage problem, not a layering one — which
  retrospectively confirms the soft_cap diagnosis, and means B1 is the lever.

### C2. `DrawOrderOverride`
* **What** Moves an appearance before/after another type.
* **Controlled by** `DrawOrderOverride: {Preposition: Before|After,
  AppearanceType: Hair|Accessory|Hat|Shirt|Pants|Sleeves|Shoes|Player}`.
* **Source** `wiki-git/DrawOrderOverride-Property.md`; Example Pack
  `Accessories/Priestess`.
* **New in v7.5.0** animations may override draw order *per frame*.
* **Safe default** omit; use for back-layer pieces (capes, long hair ribbons)
  which must sit behind hair or the player.

---

## D. Colour and recolour

### D1. Grayscale is ON by default
* **What** With no masks declared, **the whole sprite** is tinted by the
  player's colour choice.
* **Source** `wiki-git/Color-Masks-Property.md`.
* **Implication** Our source library is greyscale precisely because of this —
  it is authored as a tint mask. This is why multiplicative tinting is the
  faithful recolour and luminance-mapping washed the assets out.
* **Safe default** For generated items where we bake final colour:
  `DisableGrayscale: true` (what we already do). For items we want the player
  to recolour: leave grayscale on and ship greyscale art.

### D2. `ColorMasks` vs `ColorMaskLayers`
* **What** `ColorMasks` = one colourable section keyed on exact RGB values.
  `ColorMaskLayers` = **several independently colourable sections**.
* **Do we support it** Neither. Our pipeline bakes colour.
* **Change needed** Worth adopting: exporting `ColorMaskLayers` would let a
  player recolour body/trim/accent separately, which maps exactly onto the
  semantic roles we already derive.
* **Safe default** bake colour now; treat mask-layer export as the next step.

### D3. `SkinToneMasks`, `DisableSkinGrayscale`
* Three RGB values replaced by the player's skin shades. For appearances that
  expose skin (off-shoulder tops, sandals). Not supported by us; default null.

### D4. `IsPrismatic`, `PrismaticAnimationSpeedMultiplier`
* Cycles colours like the prismatic slime. Default false / 1.0.

---

## E. Animation

* **Frame formula** `StartingPosition + Size * Frame` — frames advance
  horizontally. Source: `wiki-git/Animation-Properties.md` footnote 1.
* **Three types** `UniformAnimation` (always), `IdleAnimation` (still),
  `MovementAnimation` (moving). **Uniform is ignored if either of the other
  two is given.**
* **Frame properties** `Frame`, `Duration` (ms, default 1000), `Conditions`,
  `Offset`, `Light`, `OverrideStartingIndex`, `EndWhenFarmerFrameUpdates`.
* **`EndWhenFarmerFrameUpdates`** ties a frame to the farmer's own sprite
  updates instead of a fixed duration — the wiki calls this out as the right
  approach for **sleeves and pants**, which must track walking/tool frames.
  Note it plays indefinitely while the farmer's sprite does not update, e.g.
  riding a horse.
* **`RequireAnimationToFinish`** prevents a movement animation cutting off
  when the player stops.
* **`AppearanceSyncing`** syncs one appearance's animation to another's
  (e.g. shoes to pants).
* **Do we support it** No — every appearance we emit is a single static frame.
* **Safe default** static (frame 0); no animation keys emitted.

---

## F. Conditions

* Frames may carry `Conditions`; a failing frame is **skipped**.
* Fields: `Name`, `GroupName`, `Value`, `Operator`, `Independent`.
* ~45 condition names, including `IsRaining`, `IsSnowing`, `IsDarkOut`,
  `IsSwimming`, `IsInBathingSuit`, `IsSitting`, `IsWalking`, `IsRunning`,
  `RidingHorse`, `IsCarrying`, `IsUsingHeavyTool`, `IsWatering`, `IsFishing`,
  `IsReeling`, `ToolChargeLevel`, `CurrentFarmerFrame`, `HealthLevel`,
  `StaminaLevel`, `IsOutdoors`, `IsInMines`, `RandomChance`, `GameStateQuery`.
* v7.5.0 added the `IsMoving` condition and the `NotEqualTo` operator.
* Example Pack `Hats/HatThatAppearsInRain` demonstrates weather-gated hats.
* **Safe default** no conditions.

---

## G. Special player states

| Property | Applies to | Default | Note |
|---|---|---|---|
| `HideWhileSwimming` | all | false; **true for Shirts** | per-type defaults differ |
| `HideWhileWearingBathingSuit` | all | false; **true for Shirts** | v7.5.0 changed this to override bathing skin when false for shirts/pants/shoes |
| `HideWaterLine` | all | false | hides the swimming water line |

The differing per-type defaults are a real trap: a hat and a shirt with the
same JSON behave differently while swimming.

---

## H. Type-specific behaviour worth knowing

* **Sleeves** `UseShirtColors` makes sleeves follow the shirt's colours —
  the normal way to keep a shirt and its sleeves consistent. `SleeveColors` on
  the *shirt* declares those colours. `DisableNativeOffset` (Sleeves only)
  turns off the framework's built-in arm offset.
* **Pants** `HideLegs`, `HideShadow`. v7.5.0 added a "Simple Pants Template"
  that matches the game's own pants layout — the right starting point for
  pants/skirt import.
* **Bodies** by far the largest model (33 properties): `EyePosition`,
  `EyeBackgroundPosition`, `SkinTone`, `Portrait`, and per-part offsets
  (`HeadOffset`, `ArmsOffset`, `LegOffset`, `ShoeOffset`, `AccessoryOffset`).
* **Hats/Shirts/Pants/Shoes** support `Item`, which registers the appearance as
  a real wearable in-game item.
* **`FromItemId`** (Hats, Shirts) links to an existing item and auto-populates
  the required fields — for Content Patcher use.
* **`IsLocked`** hides an appearance from the Hand Mirror.

---

## I. Pack-level facts

* Folder names under a category folder are arbitrary; nesting is allowed.
* `manifest.json` must declare `ContentPackFor.UniqueID =
  "PeacefulEnd.FashionSense"`.
* `Author` on the content pack is what the Hand Mirror displays — the correct
  place to carry source attribution for imported art.
* Texture must be under 16384×16384; sprite size is otherwise unconstrained.
* `preset_outfits.json` ships curated whole outfits; `conditions.json` holds
  reusable condition groups.

---

## J. Ranked generator work

1. **`UseBaldHead` / `HideHair` policy per base** (B1) — the outstanding
   soft_cap problem, and a framework feature we simply had not found.
2. **`fs_reload` in the QC Bridge** (A6) — removes the restart cycle that has
   cost several capture runs.
3. **Emit `Format`, and `Scale` per direction** (A1, A5); correct the false
   "Scale is ignored" note in `authored/fit.json`.
4. **Validate all four directions and integer positions before writing** (A2, A4).
5. **`ColorMaskLayers` export** (D2) — maps onto roles we already derive.
6. **Per-type swimming/bathing defaults** (G) — do not copy a hat's JSON shape
   to a shirt.
7. Animation and conditions (E, F) — real capability, no current need.
