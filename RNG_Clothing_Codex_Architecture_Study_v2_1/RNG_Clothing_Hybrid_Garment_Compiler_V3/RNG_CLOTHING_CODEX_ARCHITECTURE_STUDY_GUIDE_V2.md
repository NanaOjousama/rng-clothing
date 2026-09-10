# RNG Clothing — Codex Garment Architecture Study Guide v2

## What this guide fixes

The generator must stop *guessing* what clothing looks like.

A garment is generated from a reproducible, versioned chain:

**Rarity → garment family → architecture definition → design concept → fit → physical construction → directional garment model → material behavior → pixel compression → palette → rarity polish → proven V5/HD renderer → Farmer quality gate**

The generated flat/schematic examples are **teaching aids only**. They are NOT visual ground truth.  
The source of truth for physical construction is:

1. the architecture record in this guide; and
2. the linked real-world / fashion-tech-pack examples.

Codex must never copy a reference garment pixel-for-pixel or reproduce logos. It extracts construction facts and produces an original design.

---

# PART I — GENERATOR FORMAT

## 1. Rarity is rolled first

Rarity controls the **design/architecture budget**, not just color and decoration.

### COMMON
Clean everyday designs. Simple construction budget. Artwork must still be polished.

### UNCOMMON
More construction variation, layering, material options, and garment families.

### RARE
Premium but restrained. Better design sophistication, fit, proportion, material treatment and finishing. Rare is **not Legendary-lite** and should not become noisy.

### LEGENDARY
Signature design identity. Strong silhouette/construction/theme. Coordinated or spectacular features are allowed when they genuinely support the concept.

Rarity must NEVER mean:
- Common = bad pixel art;
- Rare = black/gold/purple;
- Legendary = random extra trim.

---

## 2. Roll a garment family

Example:

`UNCOMMON → POLO_SHIRT`

The generator then loads the versioned `POLO_SHIRT` architecture definition. It does not ask an LLM to remember what a polo is.

---

## 3. Architecture composition

Example:

`POLO_SHIRT = T_SHIRT/KNIT_BODY + FOLDED_COLLAR + SHORT_CENTER_PLACKET`

This inheritance/composition system is preferred because it is reproducible.

A polo inherits the torso/sleeve/hem rules of a knit shirt, then adds/overrides the collar and placket architecture.

---

## 4. Real-world / technical-flat study

Real examples are used as **construction truth**:

- where the collar attaches;
- how long a placket actually runs;
- whether a belt wraps around the side/back;
- how armholes cut into a vest;
- what exists on the back versus the front;
- how a storm flap/yoke/lapel/hood physically behaves.

The generator does not redraw the example. It extracts architecture.

---

## 5. Design-concept roll

Within one family, roll compatible variants.

For a polo, examples include:
- straight classic polo;
- athletic fitted polo;
- relaxed boxy polo;
- cropped polo;
- contrast-collar polo;
- long-sleeve polo.

These are examples, not a fixed exhaustive list.

---

## 6. Fit profile

Fit is independent of palette and gender.

Possible dimensions:
`masculine | feminine | unisex`
+
`fitted | regular | relaxed | boxy | cropped | longline | tapered`

Male/female tags are tendencies, not restrictions.

---

## 7. Physical-validity pass

Before pixels, every feature must answer:

- What garment region does it attach to?
- Where does it begin/end?
- Which directions can see it?
- Does it wrap around the body?
- Is it structural or decorative?
- Is it compatible with this family/material?

Example for trench:

- lapel → neckline/front opening;
- belt → front + side + back continuity;
- storm flap → upper chest/back;
- cuff strap → sleeve cuff.

A random vertical line with no physical garment role is invalid and must be rejected.

---

## 8. Directional garment model

One architecture model produces four views:

- FRONT
- RIGHT
- BACK
- LEFT

The side view is not a squeezed crop of the front.
The back does not blindly copy the front.

---

## 9. Material behavior

Material affects rendering after construction.

Examples:
- `KNIT`
- `WOVEN_SHIRT`
- `SWEATSHIRT_FLEECE`
- `CARDIGAN_KNIT`
- `DENIM_WORKWEAR`
- `STRUCTURED_OUTERWEAR`
- `TAILORED_FORMAL`

Material controls:
- value spacing;
- edge softness;
- ribbing;
- fold placement;
- seam emphasis;
- stiffness/bulk;
- highlight behavior.

Do not treat material as random noise texture.

---

## 10. Pixel-priority compression

At 16×16, preserve the strongest structural signals first.

Example polo priority:

1. collar;
2. SHORT placket;
3. sleeve/shoulder silhouette;
4. hem;
5. tiny buttons only if pixels remain.

The goal is not to reproduce every real-world seam.

---

## 11. Palette after architecture

Palette is selected only after the garment exists structurally.

Palette cannot be used to fake garment identity.

---

## 12. Rarity polish

Rarity polish happens on top of a physically valid garment.

It may tune:
- sophistication;
- construction harmony;
- material rendering;
- surface composition;
- controlled motif budget;
- finishing.

It does not replace architecture.

---

## 13. Render

Use the proven V5/HD backend.

The renderer executes the semantic recipe.  
It does not independently invent collars, belts, lapels, zippers, pockets, etc.

---

## 14. Farmer gate

Reject when:
- article identity disappears;
- side/back are physically wrong;
- a floating edge/line appears;
- garment converges with accepted designs;
- color is carrying identity instead of structure;
- details only work when enlarged.

Human gameplay-scale visual judgment wins over metrics.

---

# PART II — MALE / FEMALE / UNISEX DIFFERENCES

These are **construction and proportion tendencies**, not stereotypes.

## Masculine/traditional menswear tendencies
- straighter torso;
- less waist suppression;
- longer body common;
- broader shoulder/collar scale common;
- larger/geometric pocket systems common.

## Feminine/traditional womenswear tendencies
- more waist suppression common;
- cropped/shorter bodies more common;
- narrower/softer shoulder line common;
- wider/deeper neckline variants common;
- flare/overlap/curved hems more common.

## Unisex
Architecture first. Mix fit tendencies intentionally.

Never map:
- male → brown/navy/black;
- female → pink/pastel.

---

# PART III — ARCHITECTURE LIBRARY

## T_SHIRT

**Architecture formula:** `KNIT_TORSO + BOUND_NECKLINE + SHORT_SLEEVES + SIMPLE_HEM`

**Masculine fit tendencies:** straighter torso; slightly longer body; broader shoulder/neck proportions common.

**Feminine fit tendencies:** waist shaping more common; cropped lengths more common; wider/deeper neck variants common.

**Front grammar:** neckline; sleeve termination; clean torso field.

**Side grammar:** shoulder-to-sleeve transition; single torso plane; no fake front seam.

**Back grammar:** rear neck band; clean knit field.

**16×16 pixel priority:** neckline > shoulder/sleeve silhouette > hem > one optional surface cue.


## POLO_SHIRT

**Inherits:** `T_SHIRT`

**Architecture formula:** `T_SHIRT + FOLDED_COLLAR + SHORT_CENTER_PLACKET`

**Masculine fit tendencies:** straight/athletic torso; collar may be broader; body often longer.

**Feminine fit tendencies:** fitted/cropped variants common; smaller collar possible; waist shaping more common.

**Front grammar:** two collar leaves; short placket ending upper chest; knit body; short sleeves.

**Side grammar:** one visible collar fold; short sleeve; NO full-length placket; clean torso.

**Back grammar:** shallow rear collar band; uninterrupted knit back.

**16×16 pixel priority:** collar > placket length > sleeve/hem > buttons only if space remains.

**Hard rejects:** placket reaches hem; hard blazer lapels; full button-shirt back logic.

**Real-world / technical references:**
- Men's polo tech pack with construction callouts: https://dlkgolf.co.uk/wp-content/uploads/2024/10/dlk-malepoloshirt-techpack.pdf — study rib collar, collar stand, short placket, cuffs, hem, front/back relationship.
- Polo technical flat — front/back: https://www.etsy.com/uk/listing/1008460582/polo-shirt-fashion-flat-technical — study overall silhouette, front collar/placket, plain back.


## HENLEY

**Inherits:** `T_SHIRT`

**Architecture formula:** `T_SHIRT + COLLARLESS_SHORT_BUTTON_PLACKET`

**Masculine fit tendencies:** straight/relaxed torso common; medium placket.

**Feminine fit tendencies:** fitted/cropped common; wider neckline possible.

**Front grammar:** collarless opening; short placket; knit body.

**Side grammar:** no collar mass; no full placket.

**Back grammar:** plain rear neck; plain knit back.

**16×16 pixel priority:** neck opening > short placket > fit/hem.

**Real-world / technical references:**
- Henley technical-flat family: https://www.gettyimages.com/photos/henley-shirt-technical-fashion-illustration — study collarless neckline, short button placket, plain back.


## BUTTON_SHIRT

**Architecture formula:** `WOVEN_TORSO + FOLDED_COLLAR + FULL_FRONT_PLACKET + CUFFS + OPTIONAL_YOKE/POCKET`

**Masculine fit tendencies:** straighter body; broader yoke/collar; longer shirttail common.

**Feminine fit tendencies:** waist darts/shaping common; cropped variants common; narrower collar possible.

**Front grammar:** collar; full opening; optional chest pocket; woven hem.

**Side grammar:** collar depth; side seam; cuff; shirttail behavior.

**Back grammar:** yoke or clean rear plane; NO copied front placket.

**16×16 pixel priority:** collar > full opening > hem/yoke > pocket.

**Real-world / technical references:**
- Men's button-up product example: https://www.calvinklein.ca/en/men/apparel/tops/tech-stretch-slim-button-down-shirt/4LB149G-UB1.html — study point collar, full button front, barrel cuffs, shirttail hem, slim fit.


## OVERSHIRT

**Inherits:** `BUTTON_SHIRT`

**Architecture formula:** `BUTTON_SHIRT + HEAVIER_MATERIAL + RELAXED_VOLUME + LARGER_POCKETS`

**Masculine fit tendencies:** boxy/relaxed; larger utility pockets; longer body common.

**Feminine fit tendencies:** cropped or oversized forms common; dropped shoulder common.

**Front grammar:** shirt collar/opening; large pocket/panel logic; heavier hem.

**Side grammar:** visible outer-layer depth; pocket/hem cue.

**Back grammar:** broad yoke or clean heavy fabric plane.

**16×16 pixel priority:** volume > collar/opening > large pockets > hem weight.


## SWEATSHIRT

**Architecture formula:** `PULLOVER_KNIT + RIB_NECK + RIB_CUFFS + RIB_HEM`

**Masculine fit tendencies:** straight/relaxed; longer torso common; broad rib terminations.

**Feminine fit tendencies:** cropped or oversized common; waist rib may shape torso.

**Front grammar:** crew neck; broad torso; rib hem.

**Side grammar:** sleeve bulk; simple torso; rib hem.

**Back grammar:** plain back; rear neck band; rib hem.

**16×16 pixel priority:** pullover silhouette > rib terminations > neckline.

**Real-world / technical references:**
- Sweatshirt technical-flat family: https://www.gettyimages.com/photos/sweatshirt-technical-fashion-illustration — study crew neck, pullover body, rib cuffs, rib hem, front/back simplicity.


## HOODIE

**Inherits:** `SWEATSHIRT`

**Architecture formula:** `SWEATSHIRT + HOOD_MASS + OPTIONAL_DRAWSTRINGS + OPTIONAL_KANGAROO`

**Masculine fit tendencies:** roomier torso/hood common; longer body.

**Feminine fit tendencies:** cropped/fitted/oversized all valid; hood size may be smaller or oversized intentionally.

**Front grammar:** hood opening; drawstring optional; kangaroo optional.

**Side grammar:** hood depth MUST exist; outer torso; pocket edge optional.

**Back grammar:** hood mass MUST exist; clean sweatshirt back.

**16×16 pixel priority:** hood > silhouette > pocket > drawstrings.

**Hard rejects:** side/back lacks hood mass.

**Real-world / technical references:**
- Hoodie tech pack guide / flat sketch: https://www.artisancasual.com/blog/Hoodie-Tech-Pack-Template-How-to-Create-a-Production-Ready-Tech-Pack-With-Checklist_b16540 — study hood mass, drawstrings, kangaroo pocket, rib cuffs/hem.


## SWEATER

**Architecture formula:** `KNIT_PULLOVER + KNIT_NECKLINE + RIB_CUFFS + RIB_HEM`

**Masculine fit tendencies:** straight/relaxed; crew/V common.

**Feminine fit tendencies:** cropped/fitted/oversized, varied necklines.

**Front grammar:** knit neckline; broad fabric planes; rib hem.

**Side grammar:** soft knit depth; cuff/hem.

**Back grammar:** coherent knit plane; rear neck.

**16×16 pixel priority:** neckline > knit mass > rib terminations > one restrained texture system.


## SWEATER_VEST

**Inherits:** `SWEATER`

**Architecture formula:** `SWEATER - SLEEVES + CUT_IN_BOUND_ARMHOLES`

**Masculine fit tendencies:** straight/tapered torso; deep V common; shirt layering common.

**Feminine fit tendencies:** cropped/fitted common; armholes may cut in higher; wide/deep neck variants common.

**Front grammar:** V/crew neck binding; cut-in armholes; rib hem; optional inner shirt.

**Side grammar:** SLEEVELESS armhole must be obvious; narrow shoulder strap; NO full shoulder slab.

**Back grammar:** shallow rear neck; bound armholes; clean knit back.

**16×16 pixel priority:** armholes > neck binding > hem > layered shirt.

**Hard rejects:** solid side shoulder slab; floating top-edge band; reads as sleeved top.

**Real-world / technical references:**
- Sweater vest technical illustration — front/back: https://www.vectorstock.com/royalty-free-vectors/sweater-vest-vectors — study cut-in armholes, rib V/crew neck, rib hem, sleeveless side logic.


## CARDIGAN

**Inherits:** `SWEATER`

**Architecture formula:** `SWEATER + OPEN_OR_BUTTON_FRONT`

**Masculine fit tendencies:** straight/relaxed common; V/shawl collar common.

**Feminine fit tendencies:** cropped/waist-shaped variants common; wider necklines common.

**Front grammar:** two knit front edges; open/button topology; optional visible inner layer.

**Side grammar:** one hanging knit edge; collar depth; soft outer-layer read.

**Back grammar:** coherent knit mass; shallow rear neck; no front opening copied.

**16×16 pixel priority:** open front > soft collar/edge > layering > rib terminations.

**Hard rejects:** hard triangular blazer lapels unless explicitly shawl-derived.

**Real-world / technical references:**
- Cardigan technical illustration — V-neck/button front: https://www.gettyimages.com/photos/cardigan-technical-fashion-illustration — study open/button front, rib neck/cuffs/hem, soft knit back.


## WAISTCOAT

**Architecture formula:** `TAILORED_SLEEVELESS + V_FRONT + FULL_OPENING + SHAPED_ARMHOLES`

**Masculine fit tendencies:** longer/straighter tailored torso; deeper V; sharper front quarters.

**Feminine fit tendencies:** waist-shaped/cropped common; narrower armhole/shoulder variants.

**Front grammar:** tailored V; front opening; button line; optional welt pockets.

**Side grammar:** thin tailored layer; shaped armhole; no knit ribbing.

**Back grammar:** tailored back may use different fabric/strap logic.

**16×16 pixel priority:** tailored V > armholes > opening > waist shaping.


## BOMBER_JACKET

**Architecture formula:** `SHORT_OUTERWEAR + FRONT_OPENING + RIB_COLLAR + RIB_CUFFS + RIB_WAIST`

**Masculine fit tendencies:** boxy/blouson common; broader ribs.

**Feminine fit tendencies:** cropped/fitted or oversized forms common.

**Front grammar:** front opening; rib collar; rounded body; rib waistband.

**Side grammar:** blouson depth; rib waist.

**Back grammar:** rounded upper body; rib hem.

**16×16 pixel priority:** rib waistband > rounded volume > collar/opening.


## VARSITY_JACKET

**Inherits:** `BOMBER_JACKET`

**Architecture formula:** `BOMBER_JACKET + CONTRAST_SLEEVES + STRIPED_RIBS + SNAP_FRONT`

**Masculine fit tendencies:** classic athletic boxy fit.

**Feminine fit tendencies:** cropped/oversized common.

**Front grammar:** contrast sleeve/body topology; snap front; striped ribs.

**Side grammar:** contrast sleeve; rib edge; pocket cue.

**Back grammar:** contrast sleeves remain; plain or motif back.

**16×16 pixel priority:** contrast sleeves > ribs > snap opening.

**Hard rejects:** identity depends only on letter/logo motif.

**Real-world / technical references:**
- Varsity jacket technical flat — front/back/side: https://storage.googleapis.com/debnziualblbke/varsity-jacket-template.html — study rib collar/cuffs/hem, contrast sleeves, snap front, side profile.


## WORK_JACKET

**Architecture formula:** `STRUCTURED_SHORT_OUTER + SIMPLE_COLLAR + UTILITY_POCKETS + STRAIGHT_HEM`

**Masculine fit tendencies:** boxy/straight; large pockets.

**Feminine fit tendencies:** cropped or shaped versions valid.

**Front grammar:** simple collar; firm opening; utility pockets.

**Side grammar:** structured outer-layer thickness; pocket/hem cue.

**Back grammar:** clean/yoked workwear plane.

**16×16 pixel priority:** pockets/panels > collar > firm hem.


## DENIM_JACKET

**Inherits:** `WORK_JACKET`

**Architecture formula:** `STRUCTURED_JACKET + POINT_COLLAR + FULL_OPENING + CHEST_POCKETS + YOKE + WAISTBAND`

**Masculine fit tendencies:** straight/boxy; larger chest pockets.

**Feminine fit tendencies:** cropped/fitted common; more waist shaping possible.

**Front grammar:** point collar; chest pockets; button opening; panel seams.

**Side grammar:** collar depth; waistband; side seam/pocket.

**Back grammar:** yoke; panel seams; waist tabs optional.

**16×16 pixel priority:** collar > yoke/pockets > opening > waistband.

**Real-world / technical references:**
- Denim jacket vector technical family: https://www.vectorstock.com/royalty-free-vectors/jean-jacket-front-and-back-vectors — study point collar, yoke, chest pockets, button front, waist tabs.


## BLAZER

**Architecture formula:** `TAILORED_OUTER + LAPELS + SHAPED_FRONT_QUARTERS + STRUCTURED_SHOULDER`

**Masculine fit tendencies:** longer line; broader shoulders/lapels; less waist suppression common.

**Feminine fit tendencies:** waist suppression/cropping common; lapel width highly variable.

**Front grammar:** lapels; tailored opening; pockets; shaped hem/front quarters.

**Side grammar:** jacket depth; lapel/collar continuation; tailored waist.

**Back grammar:** center seam/vents or clean tailored plane.

**16×16 pixel priority:** lapels > tailored silhouette > opening > back seam/vent.

**Hard rejects:** no lapel signal; reads as generic work jacket.

**Real-world / technical references:**
- Blazer technical fashion sketch: https://www.magnific.com/vectors/blazer-technical-fashion-sketch — study notch lapels, tailored front, flap pockets, center-back seam.


## TRENCH_COAT

**Architecture formula:** `LONG_OUTER + LAPELS + DOUBLE/SINGLE_BREASTED_OPENING + BELT + STORM_FLAP + CUFF_STRAPS`

**Masculine fit tendencies:** straighter long body; broader lapel/storm-flap proportions common.

**Feminine fit tendencies:** belt-defined waist/flared lower shape common.

**Front grammar:** lapels; button opening; belt wrapping torso; storm flap; long hem.

**Side grammar:** belt continues; coat depth; long silhouette; cuff strap.

**Back grammar:** storm yoke/flap; belt continues across back; center seam/vent.

**16×16 pixel priority:** long silhouette > lapels > belt continuity > storm yoke.

**Hard rejects:** random cross/vertical trim not tied to real seam/opening; belt vanishes on side/back.

**Real-world / technical references:**
- Trench coat technical drawing — front/back: https://www.artofit.org/image-gallery/908953137412694540/flat-drawing-technical-drawing-trench-coat-front-back/ — study lapels, double-breasted opening, belt, storm flap/yoke, cuff straps, long silhouette.


## SAILOR_TOP

**Architecture formula:** `TOP + BROAD_SAILOR_COLLAR + FRONT_V + REAR_SQUARE_COLLAR_PANEL`

**Masculine fit tendencies:** straighter/uniform-like fit common; broader collar possible.

**Feminine fit tendencies:** cropped/fitted/bloused versions common; tie/ribbon variants common.

**Front grammar:** broad sailor V/collar; closed body.

**Side grammar:** compressed collar depth; sleeve/hem.

**Back grammar:** square/rectangular rear collar panel is mandatory.

**16×16 pixel priority:** collar geometry > rear panel > V inset.


## WRAP_TOP

**Architecture formula:** `TWO_FRONT_PANELS + DIAGONAL_OVERLAP + SIDE/WAIST_CLOSURE`

**Masculine fit tendencies:** straighter robe/workwear-derived overlap valid.

**Feminine fit tendencies:** fitted/cropped/waist-shaped common.

**Front grammar:** one dominant diagonal overlap; side closure.

**Side grammar:** overlap terminates physically; tie/closure optional.

**Back grammar:** clean back unless belt/tie wraps.

**16×16 pixel priority:** diagonal front > waist closure > silhouette.

**Hard rejects:** diagonal becomes random decorative sash.


# PART IV — MACHINE ALGORITHM

```text
seed
 ↓
ROLL_RARITY()
 ↓
RARITY_ARCHITECTURE_BUDGET
 ↓
ROLL_GARMENT_FAMILY(allowed_by_rarity)
 ↓
LOAD_VERSIONED_ARCHITECTURE(family)
 ↓
ROLL_DESIGN_CONCEPT(compatible family variants)
 ↓
ROLL_FIT_PROFILE()
 ↓
ROLL_COMPATIBLE_CONSTRUCTION_FEATURES()
 ↓
VALIDATE_PHYSICAL_ARCHITECTURE()
 ↓
BUILD_DIRECTIONAL_MODEL(front,right,back,left)
 ↓
ROLL_MATERIAL()
 ↓
APPLY_MATERIAL_BEHAVIOR()
 ↓
COMPRESS_TO_PIXEL_PRIORITY()
 ↓
BUILD_SEMANTIC_REGION_MAP()
 ↓
ROLL_PALETTE_STORY()
 ↓
APPLY_RARITY_POLISH()
 ↓
RENDER_PROVEN_V5_HD()
 ↓
COMPOSITE_ON_FARMER()
 ↓
QUALITY_AND_DIVERSITY_GATE()
 ↓
ACCEPT
or
REROLL DESIGN CONCEPT
```

## Determinism

Every accepted garment saves:
- RNG seed;
- rarity;
- family;
- architecture version;
- design concept;
- fit;
- selected construction features;
- material;
- semantic regions;
- palette;
- rarity polish profile;
- renderer route.

The same seed + same versioned data must reproduce the same garment recipe.

# PART V — IMPLEMENTATION LAW

1. Never rely on Codex/model memory for garment anatomy.
2. Never let the renderer invent architecture.
3. Never use generated schematic art as the physical source of truth.
4. Use real-world/technical references to validate architecture.
5. Never copy source artwork/logos.
6. New knowledge modifies semantic design data before it modifies rendering code.
7. Freeze the proven V5/HD backend unless a verified renderer bug exists.
8. A garment must be physically coherent before palette/rarity polish.
9. Front/right/back/left are views of one 3D garment.
10. Farmer-scale visual quality is the final authority.


# PART VI — REAL-WORLD → FLAT TRANSLATION CANVAS

Use `REAL_TO_PIXEL_TRANSLATION_FLAT.png` together with
`real_to_pixel_translation_flat_schema.json`.

This is the missing bridge between real-world references and the pixel renderer.

The flat is deliberately **neutral**. It does not depict a trench coat, polo, vest, blazer, etc.
Codex must fill only features supported by the selected garment architecture and real-world reference.

Example:

`POLO_SHIRT`
→ load `T_SHIRT` body architecture
→ add real folded-collar construction
→ add real short-placket construction
→ place collar/placket on FRONT
→ compress collar depth on RIGHT/LEFT
→ place shallow rear collar band on BACK
→ reject any full-length front opening
→ translate to semantic pixel regions
→ render with proven V5/HD backend.

For a trench coat:
- lapels belong to neckline/front opening;
- belt must continue across side/back;
- storm flap/yoke belongs to upper chest/back;
- cuff straps belong to sleeve cuffs;
- no arbitrary cross-shaped line is allowed because the flat has no decorative marks of its own.

**Important:** generated teaching diagrams are never pasted literally into the sprite.
The generator pastes/places **semantic features** into the flat scaffold, not image pixels.
