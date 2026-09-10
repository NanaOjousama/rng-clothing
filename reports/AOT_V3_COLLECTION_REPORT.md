# Generator V3 AoT-Inspired Collection Report

Status: **static generator, texture, diversity, and Fashion Sense pack validation passed**. In-game aesthetic review of this exact six-item pack remains required. Automated gates are guardrails, not a beauty verdict.

Art-direction update: the collection has been rerendered under bounded AoT rarity-art profiles which allow modest original crest/insignia geometry. The authoritative correction details are in `reports/AOT_V3_RARITY_ART_CORRECTION.md`.

## Outcome

Generator V3 accepted a curated external style profile without changing the frozen renderer or global V3 architecture. It produced exactly six visible concepts—two Common, two Uncommon, and two Rare—with no hidden candidate pool. The set is coherent through compact fits, disciplined collars/yokes, waist emphasis, field olive/tan/charcoal stories, and restrained utility geometry. It is not six recolors of one jacket.

The result is strongest when the references provide a compound construction signature. **Rookfield Crop Jacket** is the clearest success. The quieter pieces establish a believable clothing world, but their standalone franchise recognition is intentionally lower.

## The six designs

| ID | Garment | Tier / branch | Construction identity | Surface plan | Recognition |
|---|---|---|---|---|---|
| `aot-v3-01` | Hearthward Work Shirt | Common / civilian | fitted button shirt, folded collar, single layer, plain hem | collar-led dark trim only | Low |
| `aot-v3-02` | Mossline Field Knit | Common / practical fieldwear | compact crew knit, uninterrupted cloth mass, ribbed waist | wrapped dark shoulder block | Moderate in collection; low-to-moderate alone |
| `aot-v3-03` | Palisade Vest Shirt | Uncommon / military core | fitted yoke shirt with overlay-panel logic | pale front/back center inset framed by taupe vest mass; front collar piping | Moderate |
| `aot-v3-04` | Crosswall Utility Pullover | Uncommon / practical fieldwear | structured yoke pullover with no jacket closure | field-olive side panels plus small asymmetric regiment-style badge | Moderate–strong in collection |
| `aot-v3-05` | Rookfield Crop Jacket | Rare / military core | open split tan shell, wide collar, visible olive inner layer, structured cropped waist | shoulder block, dark lapel trim, modest original split-wing crest | Strong |
| `aot-v3-06` | Nightward Command Jacket | Rare / dark formal | closed center placket, small folded collar, contrast waist | charcoal side panels, pale collar trim, restrained burgundy waist cadence | Strong as a dark officer branch; less immediate than Rookfield |

Every recipe has a separate `DesignConcept` record containing garment role, rarity, branch, silhouette goal, primary/secondary gesture, focal area, composition type, color story, symmetry, density, recognition target, and uniqueness target. No Fashion Sense coordinates or pixels occur in profile recipes.

## Rarity progression

- Common activates one surface system. Hearthward spends it on collar discipline; Mossline spends it on a wrapped shoulder block. Both remain deliberately simple, but their construction and palettes are intentional rather than degraded filler.
- Uncommon activates one primary and one support system. Palisade combines a broad vest/shirt color relationship with collar piping. Crosswall combines side utility panels with cuff termination.
- Rare activates three controlled systems within both richness floors and complexity ceilings. Rookfield uses upper-shell blocking, lapel trim, and a modest asymmetric crest. Nightward uses side-panel composition, collar trim, and a waist-level cadence. Neither uses the multi-layer, dominant-back-emblem, animation, or VFX space reserved for future tiers.

The no-shading diagnostic passes for every garment. Each Uncommon and Rare retains a readable surface composition when shading is replaced by a neutral base.

## Revision record—no hidden concepts

There were always exactly six semantic concepts. Two of those same concepts were revised after the first render gate:

1. Palisade’s first yoke block and construction-bound piping overfilled its back surface budget and still looked too quiet on the front. It was corrected to a broad pale center inset with front-specific piping and a quieter coordinated back inset. This made the intended vest-over-shirt relationship visible without changing its role, rarity, or renderer.
2. Nightward’s first chevron plan placed almost all of its pattern on the back. It was corrected to a restrained front/back waist cadence and construction-bound collar trim. Its deterministic collection seed was also advanced so the frozen compatible-side selector chose a lapel-led side while Rookfield retained a layered side. No mask, renderer rule, or pixel coordinate was added.
3. The rarity-art correction replaced Crosswall’s quiet cuffs with a small original badge, and replaced Rookfield’s paired repeat with a nine-cell split-wing crest plus two-cell right-side continuation. Exact copied insignia remains prohibited; compact homage-style emblem geometry is permitted.

These were revisions of exposed concepts, not replacement candidates selected from a concealed batch.

## Critical answers

### 1. Did V3 produce a coherent AoT-inspired collection?

Yes, at collection level. The tan cropped shell, fitted vest/shirt, olive field underlayers, disciplined waist/collar structure, and dark formal branch read as one visual world. The relationship comes from construction and surface vocabulary, not one brown palette formula.

### 2. Are all six genuinely distinct?

Yes in semantic role and static rendering. There are three archetypes, four branches, five palette stories, three composition types, and four focal areas. No pair exceeds 0.583 semantic similarity; maximum rendered surface overlap is 0.509.

### 3. Are construction differences visible?

Yes. Hearthward is a narrow-placket shirt; Mossline is an uninterrupted crew knit; Palisade has a broad vest/shirt center relationship; Crosswall is a closure-free utility pullover; Rookfield is an open layered shell; Nightward is a closed formal jacket.

### 4. Are surface-design differences visible?

Yes, especially from Uncommon upward. Focal systems vary among collar trim, shoulder mass, center inset, side panels/cuffs, lapel/utility composition, and formal side-panel/waist composition. Common remains intentionally sparse.

### 5. Did 16×16 materially improve thematic detail?

Yes. Rookfield’s paired chest geometry, shoulder tabs, lapel edge, visible inner layer, cropped termination, and directional continuity would compete for too few cells in vanilla 8×8. Palisade’s narrow piping and vest frame, Crosswall’s cuff/side termination, and Nightward’s collar/waist cadence also benefit. Extra cells are not used for texture noise.

### 6. Are Commons attractive rather than filler?

They are acceptable everyday rewards, but the weakest visual tier by design. Hearthward is clean and warm rather than exciting; Mossline is more distinctive through olive shoulder/waist structure. Neither is intentionally ugly. Runtime wardrobe review should decide whether Hearthward needs a stronger palette relationship in a later profile iteration—not a renderer change.

### 7. Are Uncommons clearly more designed than Commons?

Yes. Palisade’s vest/shirt inset is an immediate large-area design, and Crosswall coordinates its side mass with cuff termination. Both activate two coherent systems and survive the no-shading test.

### 8. Are Rares clearly more sophisticated than Uncommons?

Yes structurally and compositionally. Rookfield is the largest jump: open shell, contrasting underlayer, collar/lapel, shoulder blocks, paired chest rhythm, and cropped waist work together. Nightward is subtler, but its closed formal architecture, dark framing, pale collar accents, and waist cadence remain coordinated rather than cluttered.

### 9. Does Rare 1 immediately evoke the iconic cropped field-jacket language?

**Yes in static review.** It presents a compact tan shell, split opening, olive fitted center, high dark lapel rhythm, shoulder construction, short structured waist, and a modest original cream/gold split-wing crest. It reproduces no supplied insignia pixels. This is the collection’s strongest recognition result and most likely keeper.

### 10. Does Rare 2 remain distinct?

Yes. Nightward uses charcoal rather than tan, a closed placket rather than an open inner layer, small collar rather than broad lapels, side-panel framing rather than shoulder blocking, a contrast lower termination, and a lapel-led side instead of Rookfield’s layered side. Its AoT recognition is less iconic and more dependent on the dark formal/officer sub-branch.

### 11. Which reference traits survived best?

Compact waist termination, strong collar/lapel structure, visible fitted underlayers, vest-over-shirt framing, shoulder/upper-chest organization, dark leather-like values, restrained utility geometry, regiment-patch placement, olive field layers, and dark formal tailoring.

### 12. Which traits required simplification?

Pocket flaps became short utility anchors; epaulettes became shoulder blocks; harness networks became one waist/chest rhythm; supplied faction insignia became an original compact split-wing crest; cuffs became tiny terminations; long coats became fuller/darker torso treatment. Exact logos, strap maps, full equipment, pants, capes, and footwear remain omitted.

### 13. Did any garment require a renderer-specific hack?

No. The renderer and global surface grammar were unchanged. All changes were semantic selections from existing V3 construction, color-block, trim, pattern, topology, palette, and deterministic side-template capabilities. The pack preserves 16×16 frames, Scale 2, `BodyPosition (0,32)`, body coverage, and native `SleeveColors`.

### 14. Did V3 provide enough surface vocabulary?

Yes for this six-top test. It supported the iconic jacket, fitted vest/shirt, utility knit, civilian shirt, and dark formal branch without a new global category. The current limit is not missing pixels but specificity: literal long-coat length, complex equipment, and exact pocket anatomy remain outside a shirt-only 16×16 backend.

### 15. Which garments are worth keeping?

- **Keep:** Rookfield Crop Jacket. It is the strongest reward and recognition proof.
- **Keep:** Palisade Vest Shirt. It provides the essential non-jacket military layer and strong collection differentiation.
- **Keep provisionally:** Nightward Command Jacket. It is desirable and distinct, but needs in-game review to confirm its muted burgundy waist cadence while moving.
- **Keep:** Crosswall Utility Pullover as an Uncommon field underlayer; it broadens the pool without copying the jacket.
- **Keep as Common support:** Mossline Field Knit.
- **Borderline:** Hearthward Work Shirt. It is clean and coherent, but least exciting; its value is as a quiet civilian Common rather than a showcase item.

## Validation evidence

- Exact visible concepts: 6; hidden candidates: 0.
- Rarity distribution: Common 2 / Uncommon 2 / Rare 2.
- Native textures: 16×64 RGBA8, four 16×16 direction frames.
- Alpha: binary only; PNG scanlines use explicit filter 0.
- Rendering: deterministic direct logical pixels; no resize/downsample path.
- Fashion Sense contract: 7.5.0; Scale 2; `BodyPosition (0,32)`; starts at Y 0/16/32/48; native sleeves retained.
- Body coverage: no missing required cells in any direction.
- Maximum semantic similarity: 0.5000.
- Maximum rendered surface overlap: 0.5000.
- Maximum side-surface overlap: 0.3846.
- Rare side templates: `layered_side` and `lapel_led`.
- Dedicated validation: `PASS_AOT_V3_COLLECTION_FULL_VALIDATION`.

## Final judgment

This is a successful first V3 external-profile integration **subject to in-game aesthetic confirmation**. It proves a curated profile can drive collection coherence, rarity progression, and large surface differences through the frozen engine. It does not prove every Common is exciting or the dark-formal branch is as instantly recognizable as the iconic tan jacket. Rookfield is the decisive success; Hearthward is the clearest remaining quality risk.

No TFWR integration, reward logic, new rarity, additional garment type, or global renderer change was made.
