# V4.5 Extended-Garment Report

## Executive conclusion

V4.5 produced an honest capability map and seven bounded logical-pixel prototypes. Six have valid Fashion Sense 7.5.0 content-pack contracts and are safe enough for **manual runtime testing**. None of the new article types has been promoted to production PASS because no in-game motion session was performed in this milestone.

The strongest candidates are Footwear and compact Pants. A short Skirt is plausible but has a harder sitting/horse gate. A Mantle is supported as a body-sized Accessory but remains layer/order intensive. The Coat-Tail companion and therefore true Long Outerwear are **NOT READY**.

## Prototype set

| Prototype | Article | Rarity | Static contract | Runtime verdict |
|---|---|---:|---|---|
| Wayfarer Field Trousers | Pants | Common | PASS | EXPERIMENTAL |
| Crossline Scout Trousers | Pants | Rare | PASS | EXPERIMENTAL |
| Palisade Field Skirt | Skirt through Pants | Uncommon | PASS | EXPERIMENTAL |
| Trailguard Field Shoes | Shoes | Common | PASS | EXPERIMENTAL |
| Rampart Scout Boots | Shoes | Rare | PASS | EXPERIMENTAL |
| Verdant Regiment Mantle | Accessory | Rare | PASS | EXPERIMENTAL |
| Rookfield Coat-Tail Diagnostic | Accessory companion | Rare | PASS format only | NOT READY; excluded from pack |

All assets are authored directly on integer logical grids at Scale 4 with binary alpha. They contain original fieldwear geometry and do not copy Fashion Sense example art. Their compact movement phases are original capability fixtures, not complete Farmer animation atlases.

## Shared concept translation

The same AoT-inspired scout-fieldwear concept translated without reusing shirt geometry:

- Common trousers: pale fitted legs, disciplined waistband, dark termination.
- Rare trousers: olive field panels, knee structure, one restrained utility/harness rhythm.
- Uncommon skirt: tan compact silhouette, pleat cadence, structured dark hem.
- Common shoes: compact dark work shoe and contrasting sole.
- Rare boots: taller shaft, cuff, strap, and sole hierarchy.
- Rare mantle: muted green back field, warm edge, clasp, and original paired split-feather crest.
- Coat-tail diagnostic: waist anchor, separated tails, lower border.

This confirms V3/V4 Design Concept semantics can be translated into article-native zones. It does not prove the same art-quality ceiling: these prototypes are deliberately conservative and remain more template-like/programmer-art-like than the best V3/V4 tops.

## Rarity result

Semantic rarity budgets work across articles: Common has one idea, Uncommon has a primary plus support, and Rare has primary/support/focal treatment. The visual difference is clearest between short shoes and tall boots and between Common/Rare trousers.

However, **rarity-quality parity is not yet proven**. Lower-body pieces have less visible area, and motion templates constrain their designs. Crossline trousers are recognizably richer than Wayfarer, but they do not yet match the reward impact of Rookfield Crop Jacket. An art-quality pass should happen only after runtime-safe masks stabilize; beautifying an invalid motion template would waste effort.

## Long-outerwear experiment

The decomposition is technically representable:

```text
V4 cropped/short Shirt
  + body-sized Accessory before Player
  + preset outfit coordination
```

It is not yet a reliable article:

- Shirt and Accessory are separate equip states; a Shirt item cannot atomically equip the tail.
- The tail animation is independent of the upper jacket and native legs unless every condition/frame is authored.
- Sitting, tools, horse, swimming, and body-mod offsets can separate the waist anchor from the jacket.
- Per-direction draw order can place a tail correctly behind the body but does not solve articulation.
- Multiplayer syncs appearance IDs, but the paired-state and missing-pack behavior remain untested.

The diagnostic tail is therefore omitted from the installable pack. A loadable PNG would not justify calling it Long Outerwear.

## Static validation

`tools/validate_v45_extended_prototypes.py` reports `PASS_STATIC_CONTRACTS`:

- exact seven semantic prototypes and six installable appearances;
- exact article mix: two Pants, one Skirt, two Footwear, one Mantle, one diagnostic tail;
- deterministic unique PNGs;
- valid frame bounds and four directions;
- animation indices remain within each texture row;
- authored Scale-4 logical pixels, filter type 0, binary alpha;
- explicit water/bathing visibility;
- Fashion Sense 7.5.0 manifest dependency;
- coat tail cannot leak into the pack.

Warnings intentionally remain: runtime untested, compact phases do not cover special Farmer frames, and mantle draw order needs full review.

Generator V3 and V4 remain frozen. This milestone adds independent V4.5 modules/data/tools and does not alter their recipes or renderers.

## Answers to required questions

1. **Which lower-body articles are genuinely viable?** Fashion Sense genuinely supports Pants and Shoes. For this generator, compact Pants and Footwear are viable candidates but remain EXPERIMENTAL until the checklist passes.
2. **Which are strongest?** Footwear has the lowest compatibility risk. Compact fitted Pants has the strongest design vocabulary/payoff.
3. **Which are experimental?** Both Pants, short Skirt, both Footwear pieces, and Mantle.
4. **Is footwear viable?** Likely yes. The layer, anchor, UI/API, optional item contract, and compact official examples are strong. Runtime pose coverage is still pending.
5. **Is skirt rendering viable?** A short skirt through Pants is plausible. Long/wide skirts are not ready; sitting and horse behavior are decisive.
6. **Are custom pants viable?** Framework yes, generator likely for fitted templates. Full confidence requires many Farmer frames or validated compact overlays.
7. **Is a cape/mantle viable?** As an Accessory, yes experimentally. It needs more layer/hair/tool/horse testing than Pants/Shoes.
8. **Can true long outerwear use multiple FS layers?** It can be represented, but not yet built reliably. Current answer: NOT READY.
9. **What breaks during animation?** Not measured in game. The known structural risk is that compact walk/run phases do not cover tool, horse, sitting, bed, fishing, and special Farmer frames; coat tails can desynchronize from legs/jacket.
10. **What works on horse?** Source conditions can select riding frames, but none of these prototype assets has horse evidence. Status: UNKNOWN/NOT RUN.
11. **What works while sitting?** Source conditions support `IsSitting`; prototypes do not yet author sitting frames. Status: UNKNOWN/likely weak for skirt.
12. **What works during tools?** Full FS templates demonstrate conditional tool frames are possible. Compact V4.5 prototypes have no tool-specific frames. Status: UNKNOWN/NOT RUN.
13. **What works in multiplayer?** Fashion Sense syncs selected IDs/colors through Farmer modData. These exact assets and coordinated layer states have not been tested remotely. Same-pack installation remains mandatory.
14. **Does rarity remain consistent?** Semantic budgets translate, but visual parity with V3/V4 tops is not yet achieved or claimed.
15. **Can V3/V4 concepts translate cleanly?** Yes semantically: palette, panel, trim, motif, focal, and rarity intent all mapped into article-native zones without shirt-specific coordinates.
16. **Next production milestone?** Run the complete checklist on Footwear and fitted Pants first. If both pass, build a reusable full Farmer-frame lower-body template library and quality grammar. Test the Skirt second. Promote Mantle only after layer/hair/horse checks. Do not resume Coat-Tail/Long Outerwear until Mantle passes.

## Outputs

- Capability audit: `reports/V45_EXTENDED_GARMENT_CAPABILITY_AUDIT.md`
- Target selection: `reports/V45_TARGET_SELECTION.md`
- Runtime checklist: `reports/V45_RUNTIME_TEST_CHECKLIST.md`
- Semantic data: `generator/data/v45/article_semantics.json`
- FS grammar: `generator/data/fashionsense/v45_extended_grammar.json`
- Recipes: `output/recipes/v45_extended_prototypes.json`
- Assets/previews: `output/fashionsense/v45-extended-garments/`
- Comparison: `output/comparisons/V45_EXTENDED_ARTICLES.png`
- Validation: `output/fashionsense/v45-extended-garments/full_validation.json`
- Manual test pack: `test-packs/fashionsense/RNG-Clothing-V45-Extended-Prototypes/`

V4.5 stops here. It does not implement a coordinated outfit engine, reward system, or TFWR integration.

