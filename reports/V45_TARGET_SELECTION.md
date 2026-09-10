# V4.5 Extended-Garment Target Selection

## Selected test targets

V4.5 selects the smallest set that exercises every useful new Fashion Sense layer without pretending to build a full outfit system.

| Target | Prototype count | Why selected | Status before runtime |
|---|---:|---|---|
| Fitted pants | 2 | First-class FS type; meaningful waistband/panel/cuff/harness semantics; essential to coordinated outfits. | EXPERIMENTAL |
| Short skirt | 1 | Proves a distinct silhouette through the Pants type and official compact-skirt contract. | EXPERIMENTAL |
| Footwear | 2 | First-class FS type, small compatibility surface, useful shaft/cuff/sole vocabulary. | EXPERIMENTAL, lowest risk |
| Mantle/back layer | 1 | Largest new silhouette freedom; uses the documented body-sized Accessory route and tests back focal composition. | EXPERIMENTAL |
| Coat-tail companion | 1 diagnostic | Directly tests whether long outerwear can be decomposed into upper Shirt plus lower Accessory. | NOT READY; not installable |

No new top is generated. The frozen V4 Rookfield cropped jacket is the coordinated upper reference for the same AoT-inspired fieldwear concept.

## Rejected or deferred targets

- **True long outerwear:** rejected until the coat-tail layer passes motion and paired-equipment tests.
- **Standalone belt/waist accessory:** deferred; its useful design language is safer inside Pants.
- **Standalone back emblem:** technically safe when compact, but redundant with the mantle's original back focal treatment.
- **Long/full skirt:** deferred; the short-skirt test must pass sitting/horse/leg occlusion first.
- **Custom sleeves:** not needed for lower-body capability and already known to have a large action-frame burden.

## Shared translation architecture

```text
AoTInspired style profile
  -> shared scout fieldwear Design Concept
  -> Common / Uncommon / Rare art profile
  -> article type
  -> coordinate-free article semantics
  -> FS-specific logical mask grammar
  -> Pants / Shoes / Accessory content model
  -> static validation
  -> manual runtime gate
```

The shared concept provides disciplined paneling, muted tan/olive/cream/charcoal colors, dark leather-like utility accents, and restrained original regiment geometry. Article adapters decide how those ideas translate:

- trousers: waistband, knee/side panel, cuff, one utility rhythm;
- skirt: waistband, pleats, panel split, structured hem;
- footwear: shaft, cuff, strap, sole;
- mantle: shoulder anchor, back mass, border, original split-feather crest;
- coat tail: waist anchor, two tails, central split, lower edge.

No shirt coordinates or V4 article masks are reused in the new renderers.

## Rarity translation fixture

- **Common:** Wayfarer Field Trousers and Trailguard Field Shoes—one readable article gesture each.
- **Uncommon:** Palisade Field Skirt—pleat rhythm with supporting hem border.
- **Rare:** Crossline Scout Trousers, Rampart Scout Boots, and Verdant Regiment Mantle—primary article construction, one support system, and one controlled focal/finish.
- **Rare diagnostic:** Rookfield Coat-Tail Diagnostic—semantically rich enough, but runtime NOT READY.

This proves semantic budgets can be expressed. It does **not** yet prove that a Rare lower-body item matches the desirability of a Rare V3/V4 top. That judgment requires in-game review and a later art-quality pass after motion contracts stabilize.

## Installable boundary

Only the two Pants, one Skirt, two Shoes, and Mantle are included in `test-packs/fashionsense/RNG-Clothing-V45-Extended-Prototypes/`. The coat-tail JSON/PNG remains under output with `DIAGNOSTIC_ONLY_NOT_FOR_INSTALL.json`.

