# V5D Masculine Art Grammar Report

## Outcome

V5D materially expands the masculine upper-garment vocabulary without redesigning V3, V4, V5B, or the Fashion Sense runtime contract. The batch no longer collapses into “dark shirt → dark vest → dark jacket”: it contains a henley, farm workshirt, patterned knit, street hoodie, open cardigan, formal waistcoat, utility vest, cropped field jacket, blazer, period coat-top, officer jacket, adventurer tunic, armor/tabard, and asymmetric street top.

Static status: **PASS_STATIC / EXPERIMENTAL / RUNTIME_NOT_TESTED**. The result is an art-grammar pass, not runtime promotion.

## Corpus study

The routing policy in `specs/MALE_CLOTHING_BENCHMARK_RULES.md` was applied before research.

Primary non-Mixed evidence came from nine top-level corpus branches (358 raw PNG files before exclusion): Adventurer's Armour and Outfits, Bonestealer, Coats and Jackets, Colourable Basics, Frogwares Sherlock, Gentleman's Collection, Project Hail Mary, TGAAClothing, and Male_Pants. Screenshots, instructions, hair, hats, and unrelated accessories did not become clothing grammar.

The three `Mixed_` branches (241 raw PNG files) were secondary only. Individually reviewed neutral or masculine-suitable examples—such as suspenders/overalls, collared tops, and a restrained fantasy top—could inform construction. Strongly feminine or ambiguous garments contributed only general cluster, color-block, trim, or pattern craft. No Mixed folder established masculine silhouette defaults.

The study extracted aggregate tendencies only. The generator does not read benchmark PNGs, sample source colors, reproduce logos, or copy source coordinates.

## Vanilla study and quality floor

Installed Stardew Valley 1.6.15 remained the technical and readability authority:

- installed `Data/Shirts.xnb`: 303 data entries;
- installed `Characters/Farmer/shirts.xnb`: 256×608;
- re-inspected sample: 54 shirts / 216 directional frames;
- inspected groups included jackets/layers, vests/workwear, formal/blouse, knit/hoodie, uniform/outerwear, pattern/motif, and graphic rhythm.

The useful vanilla lesson is not “draw at 8×8.” It is to let one compact construction gesture establish identity: lapel plus opening for a jacket, a high-contrast V over an inner shirt for a waistcoat, continuous cloth mass plus ribbing for knitwear, or a broad yoke/pocket relationship for workwear. Front detail may simplify on the back, but collar, yoke, band, hem, or material mass must carry the same article. Vanilla also concentrates contrast at necklines, openings, cuffs, and motifs instead of distributing tiny marks evenly.

V5D reconstructs those principles at 16×16 logical resolution. It does not copy vanilla pixels.

## Formal masculine grammar

The coordinate-free findings model is `generator/data/v5d/masculine_art_grammar.json`. It records fourteen branches and their silhouette, shoulder, collar, sleeve, opening, layering, hem, pocket/panel, trim/pattern, color-block, and directional rules.

Key discoveries by family:

| Family | Dominant readable construction |
|---|---|
| Casual | Relaxed torso, short neckline opening, one restrained chest rhythm |
| Workwear/farmwear | Work collar, full placket, pockets/yoke, rolled-cuff practicality |
| Streetwear | Soft/dropped shoulder, hood or graphic opening, bold but bounded block |
| Hoodie/sweatwear | Hood mass and lining, pouch or zip, ribbed termination |
| Knit/cardigan | Continuous knit mass or open knitted edges; bands wrap deliberately |
| Formal/suit | Lapel → shirt → tie value hierarchy, fitted hem, sparse accent |
| Vest/waistcoat | Outer vest frame over a clearly different inner shirt; V or utility blocks |
| Jacket/outerwear | Shell/inner relationship, lapel/opening, pocket and yoke logic |
| Military/fieldwear | High collar, ordered chest geometry, tabs, compact structured waist |
| Period/gentleman | Cravat/high collar, offset closure, restrained brocade or chain rhythm |
| Fantasy/adventurer | Layered V, sash/belt, asymmetric utility gesture |
| Armor/tunic/tabard | Material segmentation, guarded neck, plate-over-cloth hierarchy |
| Uniform | Disciplined repeated construction and consistent directional trim |
| Alt/dark fashion | Asymmetric opening/panel rhythm; identity comes from cut, not black alone |

Masculinity is encoded through construction relationships and garment role, not darkness or exaggerated shoulders. Seven of fourteen outputs use deliberately light or colorful palette stories.

## Article and surface grammar changes

V5D adds a thin, reusable masculine art-grammar layer over the frozen renderer:

- short henley opening instead of a full shirt placket;
- work collar/placket/pocket/back-yoke relationship;
- connected knit bands and deliberate ribbed terminations;
- hood mass plus pouch and bounded sleeve stripe;
- cardigan outer edges framing a broad inner layer;
- waistcoat V, welt pockets, button rhythm, and tailored points;
- utility-vest block pockets and shoulder tabs;
- cropped field shell with side opening and back yoke;
- formal lapel/shirt/tie hierarchy and pocket square;
- cravat, offset closure, brocade edge, and quiet back coat seam;
- ordered field collar/tabs/belt treatment;
- diagonal tunic sash and wrap continuation;
- plate caps, segmented chest, tabard, and original abstract crest;
- asymmetric cross-zip with a non-mirrored far-side resolution.

Surface systems follow topology. Bands wrap; pockets stay front-specific; shoulder structures echo into back yokes; lapels compress into one descending profile gesture; back designs become quieter without becoming unrelated.

## Extra-resolution value

The 16×16 Scale-2 budget is visibly used for two-cell pocket flaps, short plackets, narrow piping, offset buttons, a pocket square, cravat geometry, shoulder tabs, cuffs, ribbing, a diagonal sash, segmented plate fields, and controlled asymmetric openings. These are direct logical pixels. Previews use integer nearest-neighbor scaling only.

Extra resolution still has a limit: Shirt-only previews cannot show the full animated Sleeves silhouette, and a few side openings occupy more visual width than ideal. Those require in-game review, not additional static decoration.

## Fourteen prototypes and human quality review

Scores are manual visual judgments of the gameplay-footprint and enlarged direction sheets, not automated beauty claims. Scale: 1–5.

| # | Garment | Rarity | Read | Silhouette | Construction | Surface | Side/back | Extra res | Appeal |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | Tideglass Henley | Common | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| 2 | Orchard Hand Workshirt | Common | 5 | 4 | 5 | 4 | 4 | 4 | 4 |
| 3 | Skylark Cable Knit | Common | 5 | 4 | 4 | 5 | 5 | 5 | 5 |
| 4 | Neon Harbor Street Hoodie | Uncommon | 5 | 5 | 5 | 4 | 5 | 5 | 5 |
| 5 | Rowan Morning Cardigan | Uncommon | 5 | 4 | 5 | 4 | 5 | 5 | 5 |
| 6 | Silverline Evening Waistcoat | Uncommon | 5 | 4 | 5 | 4 | 4 | 5 | 5 |
| 7 | Brasshook Utility Vest | Uncommon | 5 | 4 | 5 | 5 | 4 | 5 | 4 |
| 8 | Sunfield Scout Jacket | Rare | 5 | 5 | 5 | 4 | 5 | 5 | 4 |
| 9 | Midnight Laurel Blazer | Rare | 5 | 5 | 5 | 5 | 4 | 5 | 5 |
| 10 | Copperwick Gentleman Top | Rare | 5 | 5 | 5 | 5 | 4 | 5 | 5 |
| 11 | Greywatch Officer Jacket | Rare | 5 | 4 | 5 | 5 | 4 | 5 | 5 |
| 12 | Amethyst Wayfarer Tunic | Rare | 5 | 5 | 5 | 5 | 4 | 5 | 5 |
| 13 | Emberward Tabard Armor | Rare | 5 | 5 | 5 | 5 | 5 | 5 | 5 |
| 14 | Berry Static Cross-Zip Top | Rare | 5 | 5 | 5 | 5 | 4 | 5 | 5 |

The Tideglass first pass failed visually because the frozen button-shirt foundation left a full-height dark placket, which read like open outerwear. The reusable casual-shirt rule now replaces the inherited long placket with dominant body cloth and authors only a short henley opening. No sub-4 article/readability/appeal result remains in the included batch.

## Diversity analysis

- Fourteen requested article roles are unique.
- Rarity distribution is exactly 3 Common / 4 Uncommon / 7 Rare.
- Seven pieces prove light/colorful masculine styling.
- Closest semantic pair is the knit and hoodie at Jaccard 0.2143, well below the 0.55 cousin ceiling.
- All fourteen have unique authored structural/surface signatures.
- The sheet remains readable without names: the strongest distinctions come from cardigan opening, hoodie mass/pouch, waistcoat V, formal lapels, cravat, tunic sash, tabard/plate segmentation, and cross-zip asymmetry.

## Old versus new

The old comparison is not just a palette comparison:

- Saltair tee → Tideglass: full-height inherited opening removed; short henley placket and one wrapping band.
- Signalwork shirt → Orchard: collar/placket plus paired work pockets and back yoke.
- Maple knit → Skylark: connected directional knit band and explicit ribbed termination.
- Juniper cardigan → Rowan: broad visible inner shirt, knitted opening edges, pockets, and back-neck cue.
- Duskline waistcoat → Silverline: clearer inner-shirt V, tailored points, welt pockets, and formal button rhythm.
- Relay vest → Brasshook: large utility blocks, tabs, waist structure, and quieter workwear back.
- Rookwing jacket → Sunfield: more explicit crop, lapel path, pocket flaps, and side/back shell logic.
- Gilded blazer → Midnight: clearer lapel/shirt/tie hierarchy, pocket-square focal point, and side lapel reconstruction.

## Strongest and weakest results

Strongest garment: **Emberward Tabard Armor**. Its plate/cloth material hierarchy, guarded neckline, center tabard, restrained crest, and back composition survive every direction.

Weakest included garment: **Tideglass Henley**. It now passes as a clean Common casual shirt, but its deliberate simplicity gives it the least silhouette leverage and depends on Fashion Sense's separate short sleeves to complete the read in game.

Strongest family: **fantasy/adventurer and armor/tabard**. The corpus supplied construction vocabulary that uses the HD budget for material layering instead of generic decoration.

Weakest family: **casual**. The Shirt frame alone offers less article-specific silhouette than hoodies, cardigans, vests, or outerwear, so its appeal must come from excellent proportion and a concise opening/pattern gesture.

## Remaining limitations and runtime risks

- Generated 384×1344 Sleeves atlases are structurally inherited from the proven V5B Fashion Sense 7.5.0 templates, but the thirteen V5D companions remain untested in motion.
- The blazer and period side openings are visually broad in static garment-only views; verify that animated arms make the profile coherent rather than crowded.
- Vest and waistcoat arm visibility must be retested, despite `HideSleeves: false` and valid generated sleeves.
- Back views are intentionally subordinate. Brasshook and Amethyst are the quietest; runtime scale may make them feel under-authored.
- Static sheets cannot prove tools, sitting, horse, multiplayer synchronization, or recolor behavior.
- No garment is promoted beyond `EXPERIMENTAL`.

## Recommended runtime subset

1. Tideglass Henley — built-in short-sleeve path.
2. Neon Harbor Street Hoodie — dropped shoulder plus decorated layered sleeve.
3. Silverline Evening Waistcoat — missing-arm regression coverage.
4. Sunfield Scout Jacket — crop, side opening, and rolled cuff.
5. Emberward Tabard Armor — densest panel grammar and reinforced sleeve.

Use `reports/V5D_RUNTIME_TEST_CHECKLIST.md` and the coordinated Fashion Sense presets.

## Validation results

Independent V5D validation passes with zero errors:

- exactly 14 Shirts, 13 generated Sleeves companions, and 1 Fashion Sense default-short-sleeve preset;
- deterministic rerender equality for Shirt and Sleeves logical pixels;
- 16×16 directional Shirt frames stacked into 16×64 textures;
- Scale 2 and BodyPosition `(0,32)` in every Shirt direction;
- FS row mapping Front 0, Right 16, Left 32, Back 48; preview order Front, Right, Back, Left;
- 384×1344 generated Sleeves atlases with complete 62/28/42/42 front/back/right/left animation maps;
- binary alpha, no body-coverage gaps, `HideSleeves: false`, and no lower-body appearance folders;
- semantic export contains no raw coordinates;
- renderer contains no benchmark-pixel access;
- all appearances remain `EXPERIMENTAL / NOT TESTED`.

Frozen V3, V4, V5B, and V5C2 validators also pass. V4 retains its pre-existing warnings about a few same-article silhouettes and cross-article quality spread; V5D does not modify that frozen output.

## Critical conclusion

The male corpus materially changed generator behavior: the most important improvements are article-specific opening systems, knit/cardigan logic, formal hierarchy, period focal construction, tunic/sash topology, and armor/tabard material separation. This is a clear visual improvement over V5B at static gameplay footprint and demonstrates multiple masculine fashion identities rather than repeated jackets.

It is not yet proof of finished community-pack parity. The batch still needs runtime review, and casual plus some side/back treatments need future refinement. The correct next milestone is the bounded five-item runtime test—not feminine rebalancing, collections, higher rarities, or TFWR integration.
