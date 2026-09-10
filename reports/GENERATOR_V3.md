# Generator V3 Completion Report

Generator version: `3.0.0`  
Controlled seed: `2026082903`  
Scope: exactly 12 optional Fashion Sense shirts/tops; 4 Common, 4 Uncommon, 4 Rare.

## 1. Architectural additions

V3 adds a design-concept engine, surface-design engine, semantic directional topology, original palette stories, rarity surface budgets, shading-independent design-interest checks, and batch diversity rejection. V2 remains the construction authority and the permanent Fashion Sense art grammar remains the structure/shading authority. V3 is an additive semantic and compositional layer, not a replacement renderer.

## 2. What Shirts.zip taught us

The corpus contains 149 appearances and 596 directional frames: 123 compact 8×8 shirts and 26 oversized-canvas thematic definitions. Its transferable strength is not raw resolution. It is the use of a dominant focal system, large torso divisions, repeated trim rhythm, symbolic motifs, deliberate color stories, and quieter related side/back views.

No benchmark pixel, coordinate, palette, silhouette, motif layout, or shirt was copied. The full boundary and metrics are in `reports/SHIRTS_ZIP_DESIGN_GRAMMAR.md`.

## 3. Supported design families

V3 formally supports beach/casual, seasonal soft, formal/elegant, floral/romantic, dessert/cute, witchy/dark, cyber/tech, military/structured, celestial/fantasy, storybook/whimsical, elemental, and creature-inspired concepts. Surface grammar includes 10 color-block types, 10 trim types, 13 motif families, eight pattern types, and multiple focal/topology choices. The controlled set does not claim to exhaust their combinations.

## 4. Rarity now affects design

Common uses one active surface system and one clear idea. Uncommon adds one subordinate support system. Rare coordinates three systems and requires wider directional theme survival. The final average visible surface cells per direction are 7.062 Common, 11.375 Uncommon, and 21.562 Rare, but count is only a consequence: hierarchy, topology, and color-role budgets remain the controlling rules.

## 5. Extra FS resolution use

The 16×16 Scale-2 cells now carry readable stripes, collar/cuff/hem rhythms, yoke and side blocks, focal symbols, paired back cues, and reduced side continuations in addition to the existing construction and shading improvements. The output is directly authored at 16×16 with binary alpha. No resampling or high-resolution source artwork exists in the pipeline.

## 6. Controlled benchmark garments

| # | Rarity | Garment | Family | Primary idea |
|---:|---|---|---|---|
| 1 | Common | Tideglass Sail Top | beach/casual | wrapped double-stripe trim |
| 2 | Common | Maple Hush Sweater | seasonal soft | sparse paired knit repeat |
| 3 | Common | Inkline Dress Shirt | formal/elegant | restrained collar trim around a tailored placket |
| 4 | Common | Meadowbud Top | floral/romantic | small asymmetric flower accent |
| 5 | Uncommon | Berry Parfait Top | dessert/cute | cake-like focal cluster with scalloped hem rhythm |
| 6 | Uncommon | Moonplum Crystal Knit | witchy/dark | crystal focal with coordinated cuffs |
| 7 | Uncommon | Circuit Tide Shirt | cyber/tech | bright technical center panel plus glyph cue |
| 8 | Uncommon | Brassfield Short Jacket | military/structured | shoulder block supporting a lapel-led outer shell |
| 9 | Rare | Gilded Nightfall Top | celestial/fantasy | star focal, yoke piping, and diamond rhythm |
| 10 | Rare | Ribbonvale Story Shirt | storybook/whimsical | ribbon focal, yoke block, and scalloped termination |
| 11 | Rare | Emberbolt Layer Jacket | elemental | asymmetric lightning focal with side-panel/lapel support |
| 12 | Rare | Mosskin Familiar Knit | creature-inspired | creature-face cluster with repeat and hem coordination |

At exact gameplay footprint, the set does not collapse into a center-stripe family. Batch metrics show 12 theme families, four archetypes, six composition types, six focal areas, three symmetry biases, five color-block types, eight trim types, nine motif values (including `none`), three pattern values, and 12 palette stories. Maximum pairwise semantic similarity is 0.5833; maximum color-independent surface-mask Jaccard is 0.2604.

## 7. Strongest examples

**Circuit Tide Shirt** is the clearest proof of V3's missing layer: its technical identity comes from a large center treatment and small glyph relationship, not from shading. **Gilded Nightfall Top** demonstrates Rare coordination across a broad yoke, focal star, trim, and back/side simplification. **Emberbolt Layer Jacket** uses asymmetry without losing outerwear construction. **Brassfield Short Jacket** proves that a themed jacket can remain readable without copying the prior AoT silhouette. **Mosskin Familiar Knit** is a useful playful/creature test with a distinct hem rhythm.

## 8. Weaknesses and human judgment

- Meadowbud is attractive as a Common but its five-cell flower reads more like a floral brooch at gameplay size; explicit flower recognition is not guaranteed.
- Berry Parfait reads as cute/designed, but “dessert” is less immediate than cyber, celestial, military, or elemental. Symbol selection and focal placement still need human review.
- Ribbonvale is visually rich and clean, but its tailored vertical structure can skew technical until the ribbon and pink terminations are noticed.
- Fixed surface colors do not recolor with the primary Fashion Sense dye channel. Extreme player dyes can weaken a planned relationship.
- Static sheets cannot certify appearance against every Farmer body mod, gameplay background, or animation state. The existing anchor/coverage/runtime behavior is preserved, but this 12-item pack still needs in-game desirability review.
- Theme vocabulary, palette authorship, and final batch curation remain artistic decisions. The engine rejects obvious failure; it cannot prove taste.

## 9. Validation

Result: **PASS_GENERATOR_V3_FULL_VALIDATION**, with zero errors and zero warnings.

- exactly 12 deterministic recipes and garments;
- exact 4/4/4 rarity distribution;
- 16×64 RGBA8 textures containing four direct 16×16 frames;
- binary alpha and explicit unfiltered scanlines;
- Scale 2 and BodyPosition `(0,32)` in all directions;
- preserved body-coverage envelope and native animated `SleeveColors`;
- protected darkest construction anchors are not overwritten;
- all active surface systems survive their required topology;
- per-rarity surface/color/motif/pattern budgets pass;
- every garment passes the shading-independent design-interest gate;
- test-pack textures are byte-identical to approved outputs;
- existing V2 vanilla recipes and four permanent V2 FS-HD controls still render successfully;
- generation code is isolated from benchmark assets.

Machine-readable results: `output/fashionsense/v3-benchmark/validation.json` and `full_validation.json`.

## 10. Test pack

Copy the entire folder:

```text
test-packs/fashionsense/RNG-Clothing-V3-Benchmark/
```

into `Stardew Valley/Mods/`, with Fashion Sense 7.5.0 installed separately, then restart SMAPI. Run `fs_add_mirror` if a Hand Mirror is needed and select the items in Fashion Sense's Shirts category. Nothing was installed automatically.

## 11. Critical V3 versus V2 result

V3 is a material design-variety improvement. V2 could distinguish construction; V3 can now distinguish why a garment exists visually even when silhouette and shading are held within the same permanent backend. The 12-way exact-footprint sheet shows multiple focal areas, horizontal and vertical rhythms, asymmetry, motifs, blocks, and theme families rather than jacket/shirt recolors.

This is not community-quality parity by metric. Five designs are strong enough for an immediate in-game reward-quality review, four are solid tier-appropriate garments, and three remain useful but need a human call on theme legibility. The architecture succeeds; the entire uncurated output space is not automatically guaranteed beautiful.

## 12. Recommended next step

Test this exact pack in game at normal zoom and collect visual accept/reject notes by garment and direction. If the strong/weak ranking survives runtime, the next engineering step should be a bounded style-profile-to-V3 adapter plus curated theme-specific motif libraries—not more global surface categories, higher rarity, or reward-system integration yet.

## Stop condition

V3 stops here. No TFWR modification, reward/gacha logic, pants, hats, accessories, Legendary/Mythic rarity, GUI, machine learning, or automatic Mods installation was added.
