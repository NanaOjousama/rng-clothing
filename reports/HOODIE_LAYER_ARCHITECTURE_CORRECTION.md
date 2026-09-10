# Hoodie Layer Architecture Correction

> **Historical architecture report:** live gameplay subsequently proved that the custom Scale-2 Sleeves layer detached below the Farmer. Version 1.1 removes custom Sleeves and Accessory appearances from the preset, uses native animated sleeves through the Shirt's `SleeveColors`, and integrates drawstrings into the Shirt. The authoritative correction is documented in `HOODIE_RUNTIME_ANCHOR_FAILURE_FIX.md`.

## Outcome

The corrective batch now models a hoodie as one semantic garment assembled from coordinated Fashion Sense appearances:

```text
semantic hoodie recipe
    -> 16x16 Scale-2 Shirt torso shell
    -> full-motion Scale-2 Sleeves atlas
    -> Scale-2 Hat hood
    -> optional Scale-2 drawstring Accessory
    -> one preset that equips the complete garment
```

Static validation passes. Runtime status remains **EXPERIMENTAL / NOT TESTED**. This work does not claim that static PNG validity proves in-game success.

## What was wrong before

V5C2 and V5D treated the hood primarily as a shaped region inside the 16x16 Shirt frame. That improved an isolated torso preview, but the region could only imply a hood at the neck. It could not control the visible volume around the Farmer's head, the relationship with hair, or direction-specific placement behind the player.

The isolated sheets also favored the old design: no head, hair, skin, pants, moving arms, or gameplay background competed with the Shirt. In game, the small torso hood ring became just another collar while the body read as a sweater, zip top, or generic shirt.

The correction separates two responsibilities:

- **neck bridge:** a small Shirt construction that connects torso cloth to the hood;
- **hood volume:** a real Hat appearance positioned relative to the head and ordered correctly against hair/player layers.

The old Shirt-level hood mass is restored to the underlying sweater cloth before the smaller bridge is authored. This avoids drawing two hoods on top of one another.

## Mandatory reference-pack study

The unpacked `hoodie.zip` corpus contains more than finished PNG designs. Its strongest technical example, `[FS] Hoods & Hoodies`, separates the system into:

- Hat appearances for **Hood Up**, **Hood Down**, **Hood Down (Static)**, and dynamic hood states;
- Accessory appearances for hoodie torso shells and separate pullstrings;
- a full animated Fashion Sense Sleeves appearance;
- `conditions.json` groups for outdoor and precipitation state;
- a companion Content Patcher pack that edits loaded Fashion Sense appearance data.

The relevant reference contracts are:

- **Hood Up:** 16x16 Hat frames at default Scale 4, hair hidden, three unique direction frames with left mirrored.
- **Hood Down (Static):** 8x16 Hat frames at default Scale 4. Its front frame is intentionally empty; the visible lowered hood is a side/back mass. Side views draw before the Player and the back view draws before Hair.
- **Pullstrings (Static):** 8x8 Accessory direction frames at default Scale 4.
- **Hoodie Sleeves:** a full movement-aware Sleeves atlas, not torso pixels stretched onto moving arms.

Only those generalized contracts were used. Reference pixels, motifs, palettes, and completed outfit layouts are not loaded by the renderer.

## What the supplied `content.json` does

The companion Content Patcher file targets:

`Data/PeacefulEnd/FashionSense/AppearanceData`

It updates already loaded Fashion Sense hood models for location/weather changes. In particular it:

- changes `HideHair` when a dynamic hood moves up or down;
- adds or removes `DrawOrderOverride` so a lowered side hood can sit before the Player and a lowered back hood can sit before Hair;
- applies those edits on day start and location change for outdoor/precipitation conditions.

This proves that dynamic hood identity can require both an independent Hat appearance and runtime layer-state changes. It does **not** imply that every generated hoodie needs weather behavior.

The correction pack therefore uses static generated hood states and native Fashion Sense draw-order properties. It does not contain `content.json`, does not require Content Patcher, and does not mutate Fashion Sense's data asset.

## Fashion Sense 7.5.0 source findings

The inspected 7.5.0 source confirms:

- Hat positioning uses `HeadPosition`; Shirt and Sleeves use `BodyPosition`.
- Hat models own `HatSize` and `HideHair`.
- Accessory models own `AccessorySize`, `HeadPosition`, `DrawBehindHead`, `DrawAfterPlayer`, and `DrawAfterSleeves`.
- `DrawOrderOverride` is honored by the general layer manager.
- presets can coordinate `ShirtId`, `SleevesId`, `HatId`, and three `AccessoryIds`.
- `GetScaledPosition` adds its scale compensation only for UI drawing; appearance origin values are still applied as logical coordinates multiplied by the appearance scale.

The higher-density component contracts preserve the approximate Scale-4 reference footprint by doubling logical dimensions and offsets while drawing at Scale 2:

| Component | Reference-style contract | Generated contract |
|---|---:|---:|
| Shirt | existing project backend | 16x16, Scale 2, BodyPosition `(0,32)` |
| Raised hood | 16x16, Scale 4 | 32x32, Scale 2 |
| Lowered hood | 8x16, Scale 4 | 16x32, Scale 2 |
| Drawstrings | 8x8, Scale 4 | 16x16, Scale 2 |
| Animated Sleeves source cell | 16x32, Scale 4 reference | 32x64, Scale 2 project contract |

The raised-hood `HeadPosition` values are the doubled reference topology: front `(-4,-4)` and back/sides `(-4,-6)`. The lowered-hood positions are front `(0,0)`, right `(-6,-32)`, left `(-18,-32)`, and back `(-12,-34)`. These are shared renderer contracts, not per-garment corrections.

## Permanent hoodie layer policy

### Shirt + Sleeves only

Limited. This may be adequate when a recipe intentionally wants only a hood-like neckline, but it is not accepted for a garment whose primary identity must survive as a hoodie in gameplay. None of the six final corrections use this alone.

### Shirt + Sleeves + Hood/Hat

Supported now. This is the minimum runtime-readable hoodie assembly. The Shirt owns torso construction; the Hat owns head-relative hood volume.

### Shirt + Sleeves + Hood/Hat + Accessory

Supported when a small front cue is useful. The correction uses one Accessory only for drawstrings. It does not stack decorative accessories merely because slots exist.

### Preset assembly

Required for this batch. All six have a preset so the player selects one named hoodie rather than guessing which components belong together.

## Hair and draw-order policy

- **Hood up:** `HideHair: true`; native Hat order; hidden while swimming or wearing a bathing suit.
- **Hood down:** `HideHair: false`; front Hat frame empty; side hood before Player; back hood before Hair; hidden while swimming or wearing a bathing suit.
- **Drawstrings:** draw after Sleeves and hide for swimming/bathing states.

This is intentionally static. A future weather-reactive feature could generate CP edits, but that is outside this correction and would add a dependency with no benefit to the immediate readability test.

## Corrected batch

| # | Garment | Rarity | Shirt | Sleeves | Hood/Hat | Accessory | Preset |
|---:|---|---|---|---|---|---|---|
| 1 | Harbor Haze Pullover | Common | yes | generated long | lowered, hair preserved | drawstrings | yes |
| 2 | Rainline Zip Hoodie | Uncommon | yes | generated fitted long | compact lowered, hair preserved | none | yes |
| 3 | Cloudberry Pouch Hoodie | Uncommon | yes | generated layered long | lowered contrast, hair preserved | drawstrings | yes |
| 4 | Tidecap Contrast Hoodie | Common | yes | generated long | raised contrast, hair hidden | none | yes |
| 5 | Sproutwing Cropped Hoodie | Rare | yes | generated layered long | raised contrast, hair hidden | drawstrings | yes |
| 6 | Nightgarden Crest Hoodie | Rare | yes | generated layered long | lowered baggy, hair preserved | none | yes |

## Reference-target reconstruction

### `hoodie_design1.png`

The source collage repeatedly emphasizes soft sweatwear, long drawstrings, a relaxed/cropped form, and a small asymmetric cute graphic. Sproutwing translates those broad traits into an original green family, a raised contrast-lined hood, separate strings, compact pouch seam, ribbing, and a small original sprout-wing charm. It does not reproduce the chicken graphic or any source garment layout.

### `hoodie_design2.png`

The reference is predominantly oversized crew sweatshirts with restrained monochrome color and a broad tonal center graphic. Nightgarden deliberately adapts that sweatshirt appeal into a true hoodie: baggy torso mass, a lowered hood layer, broad ribbing, and an original tonal garden/constellation crest. The motif and pixel placement are newly generated.

## Why the new previews are more honest

The isolated sheet remains available because it is useful for examining Shirt construction. It is no longer treated as the decisive quality view.

The assembled preset sheets show generated Shirt + Hood + optional strings at exact relative diagnostic scale. They are explicitly labeled as schematics because the project still cannot produce a reliable authoritative Farmer composite offline. A fake head/hair/body would conceal the runtime uncertainty this task is meant to test.

The raw Hat PNG contains grayscale dye-mask pixels. Preview generation separately applies the declared default color so the human review does not mistake mask gray for the in-game palette. The authoritative game PNG remains unchanged.

## In-game readability expectations

- A raised hood should provide the strongest immediate silhouette and should no longer be mistaken for a sweater collar.
- A lowered hood should become visible on side/back views without hiding hair; its front identity must come from the Shirt neck bridge plus zip, pouch, or strings.
- The Rainline zip variant is the most demanding test because its front can still resemble a light zip jacket if the lowered hood is obscured by hair.
- The Sproutwing preset uses all four component types and is the strongest architecture demonstration.

Detailed per-item checks are in `output/fashionsense/hoodie-layer-correction/IN_GAME_READABILITY_NOTES.md` and the test-pack README.

## Strongest and weakest corrected hoodie

**Provisional strongest: Sproutwing Cropped Hoodie.** The raised hood changes the head silhouette, while strings, crop, pouch seam, cuffs, and a restrained motif keep the torso authored. Its identity does not depend on one collar cluster.

**Provisional weakest: Rainline Zip Hoodie.** The compact lowered hood is correct architecture, but the front deliberately has no Hat pixels and no string Accessory. Its front still risks reading as a zip jacket when hair obscures the side/back hood. Runtime review should decide whether that conservative variant survives; it has not been artificially promoted.

## Validation result

`tools/validate_hoodie_layer_correction.py` passes:

- deterministic direct logical-pixel output;
- binary alpha for every game texture;
- six 16x64 Shirt sheets with 16x16 Scale-2 frames and BodyPosition `(0,32)`;
- six complete 384x1344 generated Sleeves atlases;
- four lowered 16x32 Scale-2 Hat contracts;
- two raised 32x32 Scale-2 Hat contracts;
- three 16x16 Scale-2 drawstring Accessory contracts;
- six complete preset references;
- correct raised/lowered hair policy;
- direction-specific lowered-hood draw order;
- no Content Patcher dependency;
- no renderer access to reference pixels;
- `EXPERIMENTAL / NOT TESTED` promotion state.

Static validation cannot verify hairstyle intersections, tools, movement, horse, sitting, or multiplayer. Those remain manual runtime gates.

## Critical assessment

This is a material architecture correction, not proof of final art quality. The generated hood now occupies the correct conceptual layer and has enough logical resolution to frame the head. The raised-hood silhouettes are much harder to confuse with ordinary sweaters in the assembled diagnostic.

The largest remaining risk is the lowered hood: its correctness depends on actual hair/player draw order, and different hairstyles may obscure more or less of it. The second risk is visual scale around the real Farmer head; the 32x32 Scale-2 raised hood follows the same approximate footprint as the studied 16x16 Scale-4 contract, but only an in-game test can confirm the generated internal opening and face alignment.

No other garment category or global architecture was changed.
