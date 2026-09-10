# V4.6 Lower-Body Report

## Outcome

V4.6 establishes a reusable full-frame runtime-test foundation for fitted Pants and Footwear. It replaces V4.5's four synthetic movement phases with installed Fashion Sense developer contracts and per-frame coverage envelopes. Exactly four development appearances were generated and packaged.

Static result: **PASS_STATIC_CONTRACTS_RUNTIME_NOT_TESTED**.

Promotion result:

| Article | State |
|---|---|
| Fitted Pants | EXPERIMENTAL |
| Footwear | EXPERIMENTAL |

No runtime or art promotion is claimed.

## Architecture delivered

- Full lower-body data map: `generator/data/fashionsense/v46/lower_body_frame_contracts.json`.
- Pants motion semantics: `pants_motion_grammar.json`.
- Footwear motion semantics: `footwear_motion_grammar.json`.
- Coordinate-free four-item fixture engine: `generator/v46/engine.py`.
- Reusable full-atlas renderer: `generator/renderers/fashionsense/lower_body_v46.py`.
- Static generator/pack validator: `tools/validate_generator_v46.py`.
- Installed-example contract builder: `tools/build_v46_frame_contracts.py`.
- Generation and preview tool: `tools/generate_v46_lower_body_runtime.py`.
- Fashion Sense built-in live diagnostics documented in the pack README and checklist.

The semantic recipes contain article zones, rarity, and palette stories but no source-frame coordinates. Frame geometry lives only in the lower-body adapter/contracts.

## Four prototypes

| Appearance | Article | Rarity | Design intent | Current state |
|---|---|---:|---|---|
| Wayfarer Field Trousers | Fitted Pants | Common | fitted mass, clean waistband, ankle termination | EXPERIMENTAL |
| Crossline Scout Trousers | Fitted Pants | Rare | side/knee panels and one utility rhythm | EXPERIMENTAL |
| Trailguard Field Shoes | Footwear | Common | compact vamp and clear sole | EXPERIMENTAL |
| Rampart Scout Boots | Footwear | Rare | compact shaft, cuff/sole, one strap accent | EXPERIMENTAL |

Rare is visibly more structured than Common in generated diagnostic frames, but rarity-quality parity is not yet an art PASS. The full-frame masks are intentionally conservative and still look template-like in some special poses.

## Validation result

`tools/validate_generator_v46.py` verifies:

- deterministic semantic and pixel output;
- exactly two Pants and two Shoes appearances;
- exact 16×32 source frames and expected 96-pixel atlas width;
- Pants 96×688 and Shoes 96×672 atlas heights;
- every referenced animation frame remains in bounds;
- binary alpha and PNG filter type 0;
- Scale 4, integer anchors, and disabled native offsets;
- explicit water/bathing hide behavior;
- one valid FS color-mask layer;
- unsupported Skirt/Accessory/Mantle/Coat-Tail/Shirt content cannot leak into the pack;
- all promotion states remain `EXPERIMENTAL`.

The validator explicitly sets every runtime claim to false.

## Required answers

1. **Did Pants survive required Farmer motion states?** NOT TESTED. The source-frame architecture covers the official Farmer atlas, but generated pixels need in-game evidence.
2. **Did Footwear survive required Farmer motion states?** NOT TESTED. The official FS conditional map is installed, but visual alignment needs evidence.
3. **Which states remain problematic?** Unknown. Highest risks are sitting, horse, extreme tool/special frames, and Rare boot shaft overlap.
4. **Does sitting work?** NOT TESTED.
5. **Does riding work?** NOT TESTED.
6. **Does tool use work?** NOT TESTED.
7. **Does swimming work?** Source confirms the pack will request hidden visibility. Entry/exit/restoration is NOT TESTED.
8. **Does FS recolor/equip work?** The schema and mask path are valid. UI/runtime is NOT TESTED.
9. **Multiplayer?** NOT TESTED. Remains unverified.
10. **Is the fitted-pants adapter reusable?** Structurally yes: it consumes coordinate-free waistband/panel/knee/seam/accent semantics and applies them inside frame-specific coverage. Production reuse depends on runtime results.
11. **Is the footwear adapter reusable?** Structurally yes: it exposes toe/vamp/ankle/shaft/cuff/sole/strap/material zones. Its compact shaft extension needs runtime proof.
12. **Can V3 semantics translate without becoming template-like?** The zone/palette/rarity semantics translate, but final art still inherits tight official coverage. Runtime safety is intentionally prioritized, so this milestone does not yet prove V3/V4 art-quality parity.
13. **Does Rare visibly exceed Common?** In static diagnostics, yes through article-specific panels/utility/cuff/strap features. Gameplay desirability remains unreviewed.
14. **Which article is safe to promote first?** None yet. Footwear remains the likely first candidate after the checklist because its area and layer interaction are smaller.
15. **What happens next?** Install the isolated pack, complete `V46_RUNTIME_TEST_CHECKLIST.md`, and attach screenshots/frame numbers for failures. Promote only the passing article to `RUNTIME_PASS`; then refine a lower-body-specific art grammar and rarity review.

## Deferred by design

No skirt, mantle, cape, coat tail, long outerwear, coordinated outfit system, Emily integration, reward system, Legendary/Mythic tier, or TFWR integration was started. Lower-body art-quality grammar is also deferred until runtime-safe masks are demonstrated.

## Installation

Copy this exact folder into the game's `Mods` folder:

`test-packs/fashionsense/RNG-Clothing-V46-LowerBody-Runtime/`

Resulting path should be:

`Stardew Valley/Mods/RNG-Clothing-V46-LowerBody-Runtime/manifest.json`

Fashion Sense 7.5.0 must be installed separately. Start through SMAPI, run `fs_add_mirror`, then equip the four appearances from Pants/Shoes. Nothing was installed automatically.
