# Generator V5A Unified Garment Expansion Report

## Outcome

V5A adds reusable semantic and renderer adapters for **Dress**, **One-Piece/Costume**, and **Bounded Long Outerwear** without changing frozen V3 design generation, V4 upper garments, the vanilla backend, or archived V4.6 lower-body research.

Nine deterministic Fashion Sense appearances were generated and pass static validation. They are all **EXPERIMENTAL**. The extended hem is not leg-articulated, so runtime testing is the promotion gate.

## Architecture

```text
V3 Design Concept / Surface Design / Rarity
  -> V5A article + sleeve intent
  -> article-specific semantic lower regions
  -> article-aware surface targets
  -> existing FS-HD upper construction
  -> bounded taller Fashion Sense Shirt frame
  -> static article/quality validation
```

The V5A recipe adds only semantic intent. All row bounds, masks, frame height, Fashion Sense positions, shading roles, and directional reconstruction remain renderer-owned.

## Article adapters

### Dress

Builds a continuous neckline/bodice/waist/lower-mass sequence. A-line, pinafore, and soft-flare rules change width progressively rather than appending a rectangular skirt. Front/back keep a unified hem; sides use a narrower reconstructed mass and their own fold rhythm.

### One-Piece / Costume

Builds a coordinated upper garment, belt/sash, lower panel system, and article-specific termination. Work-apron, academy-uniform, and split-tabard forms use different taper, split, and surface cadence. They are not four independently decorated sprites.

### Bounded Long Outerwear

Extends open outer panels from the proven jacket/cardigan construction. Front views preserve separate outer panels and either a gap or visible inner layer; backs use a bounded panel with split/rounded/layered terminations; sides use a one-mass outer panel with a subordinate opening cue. The height ceiling is 24 logical pixels—this is not a floor-length coat system.

## Sleeve grammar

V5A introduces semantic sleeve intent independently of article type. The prototype batch uses sleeveless, short-sleeve, and fitted-long-sleeve intents. Sleeveless maps to `HideSleeves` plus removal of shirt-owned sleeve cells. The other two preserve the existing `SleeveColors` integration with Fashion Sense's animated sleeve layer.

Loose, oversized, off-shoulder, and one-shoulder intents are defined but rejected from output because they require a separately equipped, full animation-aware Fashion Sense Sleeves atlas. V5A does not disguise that missing runtime work as torso art.

## Nine diagnostic garments

| Rarity | Article | Garment | Logical frame | Main article/design evidence |
|---|---|---|---:|---|
| Common | Dress | Meadowline Day Dress | 16×20 | clean A-line mass, natural waist, quiet front focal |
| Uncommon | Dress | Berryglass Pinafore Dress | 16×22 | sleeveless buttoned bodice, high contrast waist, layered/scalloped hem |
| Rare | Dress | Gilded Starfall Dress | 16×22 | soft flare, belt geometry, connected celestial bodice/hem composition |
| Common | One-Piece | Mapleforge Work One-Piece | 16×20 | work-apron torso, utility tabs, short divided termination |
| Uncommon | One-Piece | Circuit Cadet Uniform | 16×22 | structured yoke/placket, single waist band, tapered uniform panels |
| Rare | One-Piece | Ribbonward Story Costume | 16×24 | premium upper focal, sash, staged flare, split tabard, sparse lower cadence |
| Common | Long Outerwear | Slateway Long Cardigan | 16×19 | quiet open front, hip extension, rounded termination |
| Uncommon | Long Outerwear | Brasswatch Field Coat | 16×22 | structured field collar, visible inner layer, panel seams, split back |
| Rare | Long Outerwear | Rookwatch Field Long Jacket | 16×24 | AoT-inspired tan field shell, dark inner layer, chest geometry, long panel trim, restrained back mark |

## Extra-resolution use

The frames remain 16 logical pixels wide at Scale 2, but extend to 19–24 logical rows. The new logical cells are spent on:

- waist-to-hip transitions;
- staged flare/taper instead of block scaling;
- dress folds and unified hems;
- one-piece belt, panel, notch, and tabard structure;
- outerwear panel openings and bounded back splits;
- one-cell piping/seams and small connected utility clusters;
- article-aware surface continuation into the lower mass;
- separate right/left/back reconstruction.

No sprite is generated large and downsampled. Native textures use direct integer logical cells, binary alpha, and zero PNG filtering. Enlarged outputs are nearest-neighbor previews only.

## Static quality review

- **Article identity:** Pass in garment-only static sheets. Dress has a unified lower mass; One-Piece uses belt/panel/split construction; Long Outerwear keeps open outer panels.
- **Silhouette variety:** Seven unique hem signatures across nine items. The strongest separations are Gilded Starfall, Mapleforge, Slateway, and Rookwatch.
- **Surface translation:** Pass. V3 focal design remains upper-body-led where appropriate; waist, hem, utility, lower-panel, and back systems move to article-relevant regions.
- **Rarity:** The visual progression is credible inside each family. Rare designs coordinate three targets but remain below a future Legendary/Mythic ceiling.
- **Weakest family:** One-Piece. Its static identities are improved, but its divided lower forms have the highest chance of looking rigid during stride because the Shirt layer does not own leg animation.
- **Strongest family:** Dress in static article readability. Bounded Long Outerwear has the strongest fashion/theme payoff but also the highest sitting/horse clipping risk.
- **Strongest individual:** Rookwatch Field Long Jacket for theme and construction. Gilded Starfall is the clearest dress reward.
- **Remaining art caveats:** Berryglass uses a strong dark center opening that may be harsh in-game; Meadowline's broad upper neckline still exposes its Sailor-top ancestry; Brasswatch and Rookwatch deliberately share fieldwear language and need runtime gameplay-size comparison to ensure sufficient separation.

## Fashion Sense limitations and runtime risks

- There is no Dress/One-Piece/Coat category; all nine appear in the Shirt mirror category.
- Extended Shirt geometry follows torso offsets, not leg articulation.
- Standing source rectangles validate, but walk/tool/sit/horse behavior is not proven.
- Fitted-long-sleeve intent colors animated sleeves but does not independently select a sleeve silhouette.
- Sleeveless hides sleeves but still needs in-game skin/shoulder inspection.
- Swimming/bathing is intentionally hidden by framework properties.
- Multiplayer sync is untested.
- No companion Pants, Accessory, Body, or Sleeves pack is silently required.

## Validation and regression

`tools/validate_generator_v5a.py` reports `PASS_STATIC`:

- 9/9 deterministic unique textures;
- exact 3 Dress / 3 One-Piece / 3 Long Outerwear;
- exact 3 Common / 3 Uncommon / 3 Rare;
- 16-pixel width and correct 19/20/22/24 frame heights;
- correct Front/Right/Left/Back source rows;
- Scale 2 and BodyPosition `(0,32)`;
- binary alpha and direct logical pixels;
- valid Fashion Sense 7.5.0 content-pack contract;
- no garment promoted beyond `EXPERIMENTAL`.

Independent V3 and V4 validators still pass. The archived V4.6B lower-body validator also remains static-pass/runtime-untested. TFWR, vanilla rendering, pants, shoes, Legendary/Mythic, and reward systems were not changed.

## Critical conclusion

V5A proves that the existing design system can create visibly different extended garment silhouettes in static Fashion Sense assets. It does **not** yet prove that a torso-attached lower mass is acceptable through Stardew's full animation set.

The correct next action is manual runtime testing of these nine assets. If dresses and coats remain coherent during walking but fail sitting/horse, the next milestone should add bounded pose overrides or narrowly scoped companion-layer research. V5B coordinated outfits should not begin until that evidence exists.
