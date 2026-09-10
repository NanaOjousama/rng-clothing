# Generator V4 Multi-Garment Report

## Outcome

V4 materially expands the proven Fashion Sense top pipeline into **five readable upper-garment article adapters**: fitted shirt, sweater, vest-over-shirt, cropped jacket, and short outerwear. Fourteen deterministic garments were generated: six AoT-inspired and eight neutral benchmark pieces. Static technical validation passes with no V3 regression.

This is a successful upper-garment translation milestone, not a complete all-clothing generator. Long coats, capes, pants, skirts, and footwear remain outside the proven runtime envelope.

## What V4 added

- A semantic `articleType` separate from V2/V3 archetype.
- Coordinate-free article intent and feature contracts.
- Shared article selector/adapter architecture above the frozen V3 design engine.
- Renderer-owned fitted, vest-material, crop, and full-shell translation operations.
- Article-specific focal/feature zones and rarity interpretations.
- Name-removed article classification and cross-article rarity/quality gates.
- Exact AoT 2 Common / 2 Uncommon / 2 Rare collection.
- Exact neutral 2 Common / 3 Uncommon / 3 Rare benchmark.

## Working article types

| Article | Result | Critical assessment |
|---|---|---|
| Fitted shirt | **Working** | The persistent lower taper and shirt closure read clearly against the broader articles. The difference is subtle at Scale 2 but survives gameplay footprint. |
| Sweater | **Working** | Heavy uninterrupted mass and termination remain clear. Individual sweaters necessarily share an article silhouette; V3 surface systems distinguish them. |
| Vest-over-shirt | **Working; strongest adapter** | Coordinated inner-shirt shoulders/sleeves and vest body produce an immediate material/layer read in all directions. It is not a bare-arm vest. |
| Cropped jacket | **Working; bounded** | The shell ends two logical rows above standard outerwear while retaining lapels, inner layer, sleeves, and body coverage. It is visibly shorter at gameplay size. |
| Short outerwear | **Working but weakest silhouette adapter** | Jacket opening, split panels, and back construction read as outerwear, but the outside footprint still shares the proven 16×16 shirt boundary. It must not be called a long coat. |
| Long outerwear | **Not viable yet** | No final garment was generated. A static taller shirt would not prove animated coat tails or correct lower-body layering. |

## AoT V4 collection

| Rarity | Article | Garment | Main article evidence |
|---|---|---|---|
| Common | Fitted shirt | Hearthward Work Shirt | tailored taper, disciplined closure |
| Common | Sweater | Mossline Field Knit | heavy field-knit mass, firm termination |
| Uncommon | Vest top | Palisade Vest Shirt | pale under-shirt sleeves/shoulders framed by a darker vest |
| Uncommon | Short outerwear | Crosswall Utility Jacket | full shell, opening/inner layer, shoulder treatment and field badge |
| Rare | Cropped jacket | Rookfield Crop Jacket | raised waist termination, split tan shell, inner field layer, focal crest/panel composition |
| Rare | Short outerwear | Nightward Command Jacket | full dark outer shell, formal opening, distinct back and restrained red cadence |

The set no longer collapses into six similar torso formulas. The clearest role sequence is Palisade vest → Rookfield cropped jacket → Nightward full short outerwear. Family coherence still comes from disciplined military construction, utility geometry, and palette stories—not identical masks.

Rookfield remains the strongest immediate AoT read. Nightward is intentionally a darker formal branch and is distinct, but its article silhouette is less novel than Rookfield's crop. No article required a garment-specific hand-painted exception; each uses a reusable adapter operation.

## Neutral benchmark

| Rarity | Article | Garment | Design family |
|---|---|---|---|
| Common | Fitted shirt | Inkline Dress Shirt | formal/elegant |
| Common | Sweater | Maple Hush Sweater | seasonal soft |
| Uncommon | Vest top | Circuit Tide Shirt | cyber/tech |
| Uncommon | Cropped jacket | Brassfield Short Jacket | military structured |
| Uncommon | Sweater | Moonplum Crystal Knit | witchy/dark |
| Rare | Vest top | Ribbonvale Story Shirt | storybook whimsical |
| Rare | Short outerwear | Emberbolt Layer Jacket | elemental |
| Rare | Sweater | Mosskin Familiar Knit | creature inspired |

This demonstrates that vest, crop, fitted, sweater, and outerwear translation is not AoT-specific. The strongest neutral article reads are Circuit Tide's bright under-shirt/vest relationship and Brassfield's shorter shell. Ribbonvale is visually rich, though its supporting color block can compete with the primary motif; validation retains that warning rather than hiding it.

## Rarity consistency

All Commons remain intentionally calm but designed. Uncommons introduce stronger article/surface coordination. Rares retain the strongest coordinated composition without using future Legendary/Mythic devices.

The static cross-article evidence gate progresses in both collections:

- AoT: Common 28.5 → Uncommon 55.0 → Rare 74.0.
- Neutral: Common 25.5 → Uncommon 54.3 → Rare 68.0.

These figures measure article evidence and visible V3 surface systems; they do not prove beauty. Visual review supports the broad progression, but neutral Uncommon quality has a wide spread and Mosskin's Rare premium read depends more on motif authorship than silhouette novelty.

## Validation

`tools/validate_generator_v4.py` reports **PASS**:

- 14/14 deterministic unique native textures;
- exact 16×64 PNGs, four 16×16 frames;
- binary alpha and encoder filter type 0;
- Scale 2 and BodyPosition `(0,32)`;
- direction starts 0/16/32/48;
- native `SleeveColors`, including the vest under-shirt ramp;
- no body-coverage regressions;
- exact requested rarity counts and pack counts;
- all name-removed article classifiers match;
- `LONG_OUTERWEAR` absent/rejected.

The independent Generator V3 validator also remains the required regression check. Runtime beauty and motion review of the new crop/vest operations is still recommended before treating V4 as production-ready.

## Direct answers

1. **Which articles work?** Fitted shirts, sweaters, vest-over-shirt tops, bounded cropped jackets, and short outerwear.
2. **Which collapse?** Short outerwear retains the standard shirt-layer outer footprint; its layering distinguishes it, but it is closest to existing top geometry. Same-type sweaters share silhouettes as expected.
3. **Is long outerwear viable?** No—not honestly on the currently proven static 16×16 shirt contract.
4. **Does V4 preserve V3 quality?** Yes. V3 construction, surface, rarity, palette, topology, coverage, and art grammar are unchanged and remain the render source.
5. **Is rarity consistent across articles?** Broadly yes in both static collections, with explicit warnings about neutral Uncommon spread.
6. **Are Rares better than Uncommons?** Yes overall; Rookfield and Ribbonvale/Emberbolt show stronger authored compositions. Not every Rare has a stronger silhouette because rarity is not article size.
7. **Are Commons attractive?** Yes; they are restrained rather than empty, though intentionally quieter.
8. **Does AoT gain silhouette variety?** Yes: fitted, heavy knit, vest-layered, cropped shell, and full short shells are visibly separate.
9. **Strongest adapter?** Vest-over-shirt, because material topology changes torso/shoulder/sleeve perception across every direction.
10. **Weakest adapter?** Short outerwear, because it cannot exceed the shirt footprint safely.
11. **Next milestone?** A dedicated Fashion Sense lower-body/layer-motion audit for a coat-tail companion or coordinated pants layer. Only after walking, tools, horse, sitting, swimming, draw order, and multiplayer equip behavior pass should `LONG_OUTERWEAR` move from experimental.

## Files and test packs

- Recipes: `output/recipes/v4_aot_collection.json`, `output/recipes/v4_neutral_collection.json`
- Native assets/previews: `output/fashionsense/v4/aot/`, `output/fashionsense/v4/neutral/`
- Collection comparisons: `output/fashionsense/v4/V4_*.png`
- Full validation: `output/fashionsense/v4/full_validation.json`
- Test packs: `test-packs/fashionsense/RNG-Clothing-V4-AoT/` and `test-packs/fashionsense/RNG-Clothing-V4-Neutral-Benchmark/`

V4 stops here. It does not integrate TFWR or implement reward distribution.

