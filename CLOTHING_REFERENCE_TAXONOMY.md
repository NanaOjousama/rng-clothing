# Clothing Reference Taxonomy

## Record unit

A record represents one genuinely useful construction or surface-design lesson. Multiple recolors share a record. A named pack does not earn a record until an asset is routed as garment evidence.

Every accepted record contains:

1. source, creator, local path/URL, license note, reference-only flag;
2. family, subtype, gender grammar where relevant, and use identity;
3. structural fields: silhouette, shoulder, neckline, collar, lapel, opening, torso mass, waist, hem, sleeve, cuff, pockets/panels, layering, asymmetry, side and back reconstruction;
4. surface fields: color-block topology, trim, motif, pattern/material implication, focal hierarchy;
5. gameplay fields: front/side/back clarity, silhouette strength, cues, approximate complexity.

## Families

| Tier | Families and subtypes |
|---|---|
| Basics | fitted tee, relaxed tee, henley, button/work shirt, sailor top |
| Knit | crewneck, textured sweater, cardigan |
| Layered | sweater vest, formal waistcoat, utility vest, overalls/bib top |
| Midweight | windbreaker, cropped bomber, moto jacket, cropped structured/fashion jacket |
| Outerwear | work/field jacket, blazer, period coat-top, mandarin coat-top |
| Statement | true hoodie, asymmetric wrap, tunic, tabard, armor overlayer, ceremonial, streetwear, gothic cloak-top |
| Surface-only evidence | motif-led and panel/trim-led compositions whose source silhouette is not adopted |

## Construction vocabulary

- Silhouette: compact, fitted, relaxed, boxy, rounded, elongated-safe, tapered, layered, guarded.
- Shoulder: standard, set-in, soft, dropped, collar-broadened, tailored, capped, asymmetric.
- Neckline/collar: crew, wide crew, split neck, V, open, high; work fold, sailor, ribbed, stand, notched, hood, ceremonial.
- Opening: none, short henley, full placket, center zip, open frame, split shell, diagonal zip/wrap, offset, double-breasted.
- Waist/hem: subtle taper, ribbed/gathered band, pointed vest, crop, structured waist, belt/sash, tabard termination, safe period split.
- Layering: single material; outer/inner; vest/shirt; knit/inner; tabard/underlayer; armor/cloth; coordinated hoodie layers.
- Direction: side views compress physical depth and terminate front features at seams; backs preserve collar/yoke/band/material identity while reducing front-only detail.

## Taxonomy safeguards

- Gender grammar describes visible construction, not a color or creator label.
- Masculine does not mean dark, broad, or plain. The permanent `Mixed_` routing policy remains binding.
- “Fancy,” “cool,” “premium,” and rarity labels are not garment grammars.
- A decorative motif cannot change a tee into a jacket.
- An extended name cannot make a runtime-safe Shirt rectangle into a true long coat.
- Separate grammars that share a topology must still differ in at least three high-salience structural axes and pass the worn-Farmer gate.

## Coding confidence

- `ACCEPTED_STRUCTURAL`: repeated or very clear evidence, safe to inform grammar.
- `ACCEPTED_SURFACE_ONLY`: may inform composition or craft, not silhouette.
- `CONDITIONAL`: useful only for a named gender/style branch or bounded FS layer contract.
- `EXCLUDED`: recolor, UI/non-garment, ambiguous Mixed asset, prohibited identity/layout, or unreadable at gameplay scale.

The current corpus has 23 accepted structural records and two surface-only records. These records support 22 project-owned structural grammars; counts are deliberately lower than raw asset counts.
