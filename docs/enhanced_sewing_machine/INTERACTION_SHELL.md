# Enhanced Sewing Machine — Interaction Shell

Status: **live gate started; first pass found a UI-scale hit-test bug, now fixed/static-tested; corrected DLL requires restart for final live craft gate**

## Architecture

The shell is additive around Stardew's existing `TailoringMenu`.

It does **not** replace the vanilla menu class or rewrite vanilla recipes. SMAPI menu/input/render events attach an optional Enhanced mode to the real vanilla menu instance.

Normal mode remains vanilla behavior.

Enhanced mode adds:

- a controller-reachable `Enhanced: ON/OFF` toggle;
- the existing left slot as **Textile**;
- the existing right slot as **Inspiration**;
- a third Enhanced-only **Fashion Fragment** slot;
- hidden-result sewing through the deterministic tailoring selector;
- transactional item creation: construct output first, consume ingredients last.

## Prototype ingredient mapping

Verified against the exported Stardew 1.6.15 `Data/Objects`:

- Cloth `(O)428` → `cotton`
- Wool `(O)440` → `wool`
- Sunflower `(O)421` → `sunflower`
- Frozen Tear `(O)84` → `frozen-tear`
- Ancient Doll `(O)103` → `ancient-doll`

The selector also has a `canvas` development profile, but no player-facing Canvas textile item is mapped yet. That is deliberate rather than pretending vanilla Fiber is Canvas.

## Fashion Fragment

Registered custom object:

```text
(O)RNGClothing.ESM.FashionFragment
```

Prototype cost:

```text
5 Fashion Fragments
```

The current icon intentionally reuses the vanilla Cloth sprite as a temporary development placeholder. No final Fashion Fragment art has been authored yet.

Dev command after restart:

```text
rng_tailor fragments 25
```

## Sewing transaction

Enhanced sewing does:

```text
validate Textile
→ validate Inspiration
→ validate Fragment stack
→ choose sewing seed
→ deterministic GarmentId selection
→ construct real GeneratedHat successfully
→ consume 1 Textile
→ consume 1 Inspiration
→ consume 5 Fashion Fragments
→ place generated garment on cursor
```

Any selection or item-construction failure occurs before consumption, so inputs remain untouched.

The garment's item seed stores the sewing RNG seed; its compiled metadata still stores the separate original generator seed.

## Hidden result

Enhanced mode deliberately hides the exact garment preview before sewing. The player sees only whether the inputs are valid and that the result remains unknown until the stitch succeeds.

## Controller

The Enhanced toggle and Fragment slot are added to the vanilla menu's clickable-component graph. The toggle is reachable from the vanilla start button, and the Fragment slot is linked below the Inspiration slot.

Mouse and Controller A are both handled.

## Localization

All new player-facing shell text is in `i18n/default.json`.

## Compatibility / fail-open

- Vanilla tailoring remains unchanged while Enhanced mode is OFF.
- No global input suppression.
- Input is suppressed only for Enhanced-owned controls or the vanilla Sew button while Enhanced mode is ON.
- Inventory pickup remains Stardew's own implementation. In Enhanced mode the mod owns Textile/Inspiration slot placement so supported Textiles like Wool are not blocked by vanilla tailoring recipe-highlight rules; OFF mode restores vanilla slot behavior and validation.
- Closing the menu returns any item in the custom Fragment slot through Stardew's `Utility.CollectOrDrop`.

## Static verification

Current release build:

```text
0 warnings
0 errors
```

Existing regression suite:

```text
23/23 PASS
```

Plus:

- 10/10 garment definitions valid;
- 8/8 compiled V5 garments regenerate exactly;
- all current Textile/Inspiration bias profiles discriminate over the active pool.

## Live gate

After restart:

1. verify Fashion Fragment registers and can be given with `rng_tailor fragments 25`;
2. open a real sewing machine and confirm the vanilla TailoringMenu is still present;
3. confirm Enhanced toggle appears and normal mode is still vanilla;
4. toggle Enhanced with mouse and controller;
5. place Cloth/Wool in Textile, one supported Inspiration in Inspiration, and Fashion Fragments in the third slot;
6. verify exact output remains hidden before sewing;
7. click Sew and confirm a real GeneratedHat appears;
8. verify only 1 Textile + 1 Inspiration + 5 Fragments were consumed;
9. inspect item seed vs generator seed;
10. close/reopen and verify custom Fragment slot returns leftovers safely;
11. re-run one vanilla tailoring recipe to prove no regression.

Only after this passes should the UI be considered ready for polish/animation and broader ingredient acquisition.
