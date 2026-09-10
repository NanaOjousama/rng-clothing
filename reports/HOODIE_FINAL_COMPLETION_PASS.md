# Final Hoodie Completion Pass

## Outcome

The reusable hoodie architecture is now code-locked as the RarePlus complex-layer freeze candidate. Its final live promotion is deliberately not fabricated: the micro-polished Hat art and new `HideBackOnly` policy require the checklist in `reports/HOODIE_FINAL_RUNTIME_CHECKLIST.md`.

## Hair policy

The CP child now supports `PreserveHair`, `HideBackOnly`, `PreserveFrontOnly`, and `HideHair`. Fashion Sense selects one direction-specific Hat model before evaluating `HideHair`, so each policy remains direction-specific. Hood-down always restores all four to visible.

The follow-up keeps full side Hair and uses the already-topmost raised Hat as a visual mask. The side hood now closes diagonally over the lower/rear hair region while leaving the upper/front opening transparent. `HideBackOnly` is again the default; `PreserveFrontOnly` remains a fallback for hairstyles that escape the visual mask.

## Hood-only micro-polish

No anchors, positions, scales, frame indices, draw order, weather rules, Shirt pixels, sleeve behavior, or drawstrings changed.

The pixel cleanup is intentionally small:

- raised front: removed the spaced outer lining pixels that made the rim look dotted; retained one continuous inner rim;
- raised front: widened only the last two shoulder-connection rows by one logical cell per side;
- raised sides: added a two-row tapered neck termination rather than ending abruptly;
- raised back: changed the alternating two-column center marks into one continuous crease plus restrained connected lining clusters;
- lowered front: widened only the final two fold rows by one logical cell per side and converted the center marks into a coherent two-column fold;
- lowered back: replaced alternating center specks with one crease and one short connected fold edge.

This spends extra resolution on connected fabric structure, not decoration.

## RarePlus template

`RARE_PLUS_COMPLEX_LAYER_GARMENT_V1` defines a coordinated garment generated from one semantic recipe and capable of:

- Shirt;
- optional generated Sleeves or native `SleeveColors`;
- optional Hood/Hat;
- optional Accessory when truly necessary;
- a coordinated preset when multiple appearances are present;
- optional bounded Fashion Sense state behavior;
- optional narrowly scoped Content Patcher weather/hair policy.

Renderer coordinates remain outside semantic recipes. The template is reserved for Rare in the current rarity vocabulary and leaves more ambitious silhouettes, layering, animation, and VFX for future tiers.

## Rarity routing

- Common → vanilla Stardew clothing renderer.
- Uncommon → Fashion Sense HD single/simple-article renderer.
- Rare → Fashion Sense RarePlus coordinated-garment renderer.

Existing historical diagnostic packs are not silently rewritten; the new policy governs future production-facing generation.

## Freeze status

Static status: **PASS** after regeneration and validation.

Architecture status: **LOCKED_PENDING_FINAL_RUNTIME_CONFIRMATION**.

Production freeze is blocked only by the explicit live checklist. Once side Hair is shown to remain visible above/front while the hood covers its lower/rear portion, change the policy/template status to `FROZEN_RUNTIME_PASS`. No further garment system should begin before that decision.
