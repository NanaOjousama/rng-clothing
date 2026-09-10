# Rarity Renderer Architecture

The semantic rarity vocabulary remains Common, Uncommon, and Rare. Rarity now also selects the maximum renderer capability available to the design; it does not inject renderer coordinates into recipes.

| Rarity | Renderer route | Capability ceiling |
|---|---|---|
| Common | Vanilla Stardew clothing renderer | One native article, disciplined low-density design |
| Uncommon | Fashion Sense HD simple-article renderer | One generated 16×16 Scale-2 appearance; native SleeveColors may support it |
| Rare | Fashion Sense RarePlus coordinated-garment renderer | Shirt plus native animated sleeves, optional Hat/Accessory, preset assembly, and bounded state/weather behavior |

`RarePlus` is a renderer capability class, not a newly implemented semantic rarity. Current Rare recipes route to it. Legendary and Mythic remain unimplemented and retain their reserved design space.

Multiple Fashion Sense appearances are valid only on the RarePlus route and require a coordinated preset. Common cannot silently acquire Fashion Sense as a dependency. Uncommon cannot silently become a multi-layer outfit.

The hoodie is the reference implementation for RarePlus complex layers:

- one semantic recipe;
- high-detail Shirt;
- native animated sleeves through `SleeveColors` (`NATIVE_ANIMATED_SLEEVES_V1`);
- optional Hat/Hood;
- optional Accessory only when the detail cannot safely belong to Shirt/Hat;
- preset assembly when more than one appearance is generated;
- optional Fashion Sense state conditions and narrowly scoped Content Patcher policy edits.

The architecture is **locked pending final runtime confirmation**, not yet falsely marked production-frozen. The complete final hoodie checklist must confirm the micro-polished art, direction order, centered lowered fold, and `PreserveFrontOnly` side/back hiding before `RARE_PLUS_COMPLEX_LAYER_GARMENT_V1` changes from `EXPERIMENTAL` to a frozen runtime template.

Live hoodie and V5E tests both rejected the prior 32×64 Scale-2 custom Sleeves atlas. No current production/test route may export that contract. A future custom-sleeve backend needs its own calibrated runtime proof and new named contract.

Post-V5E upper garments also pass the reusable gameplay art-polish stage after article construction. It reinforces selective contour anchors, controlled light/shadow edges, and optical weight while preserving every alpha cell and all Fashion Sense runtime fields.
