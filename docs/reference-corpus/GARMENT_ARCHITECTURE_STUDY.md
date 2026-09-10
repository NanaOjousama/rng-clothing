# Garment Architecture Study

## Central finding

Human-made garments achieve variety by changing a few large structural decisions that survive Farmer compositing. The decisive variables are the outer mass, neck/collar mass, opening topology, layer relationship, sleeve relationship, and hem termination. Small motifs improve an already readable garment; they do not create an article.

The most common procedural failure—fitted torso, short jacket outline, bright central insert—collapses several real constructions into one topology. An inner shirt, zipper, button placket, open cardigan gap, vest V, and tabard panel are not interchangeable center marks. Each requires a different surrounding mass.

## Family findings

### Tees, polos, henleys, and woven shirts

- A tee is defined by a quiet shoulder-to-short-sleeve transition and bound neck, not by its graphic.
- A polo requires collar mass plus a *short* placket. Removing either produces a tee or henley.
- A henley is collarless; the partial placket ends high and must not become a full-height center stripe. Corpus support is thinner than for polos/button shirts.
- A button shirt uses a folded collar, full placket, and optionally a chest pocket or rear yoke. Rolled cuffs can materially change its read.
- An open shirt has two outer leaves surrounding a broad inner tee. A thin contrasting strip is insufficient and reads as a zipper.
- An overshirt adds shell weight: boxier torso, firmer hem, cuffs, and larger pocket rhythm.

### Knitwear, sweatwear, and cardigans

- Crewneck sweatshirts depend on three related terminations: neck rib, cuffs, and gathered/ribbed waist.
- Knitwear becomes distinct through coherent material rhythm—ribbing and controlled repeats—not random texture noise.
- A turtleneck needs visible height and rear depth in every direction; a single light neck pixel is not a collar.
- Cardigans are soft open outer layers. Their two front edges, inner garment, knit cuff/hem, and optional patch pockets separate them from open shirts and blazers.

### Vests and waistcoats

- Sweater vests are knit masses with bound armholes and neckline, visibly layered over native sleeves.
- Formal waistcoats use a deep V, buttons, tailored taper and shaped lower points. The rear should simplify to a tailored back/adjuster rather than repeat front buttons.
- Utility vests are boxier, have strong practical pocket topology, and expose a clear undershirt-sleeve relationship.
- Hiding or leaving native arms blank destroys vest identity. Sleeve presence is a body-coverage contract, not optional decoration.

### Hoodies and sport shells

- A hoodie requires real hood mass connected to neck and shoulders; drawstrings or a hood-colored neck patch cannot substitute for it.
- Track jackets use stand collars, full zips, sport bands, and sleeve/shoulder stripes. If the stripe and zipper are removed, shell construction must still read.
- Bombers are shorter and rounder than track jackets, with a gathered waist and ribbed terminations.
- Varsity identity comes from snap front, contrast sleeve/body construction, and striped ribbing; it cannot be a bomber with an emblem swap.

### Workwear and outerwear

- Work jackets are boxy with large patch pockets, firm straight hems, practical collars, and broad rear yokes.
- Field jackets use more disciplined shoulder/yoke structure, chest utility pockets, guarded openings, cuffs, and controlled waist/hem treatment.
- Cropped fashion jackets require a true independent outer-shell termination and visible inner relationship. Cropping the same torso block is not enough.
- Moto jackets require an actual asymmetric overlap/lapel mass; drawing a diagonal stripe on a field jacket does not create one.

### Formal, period, uniform, and statement garments

- Blazers use broad lapel masses, button stance, tailored waist, pockets, rear collar and back seam/vent logic.
- Double-breasted tops change front overlap and paired-button topology, not merely button count.
- Period coat-tops combine collar/cravat/waistcoat/outer-edge hierarchy and stronger cuffs. Rigid tails over moving legs remain a runtime risk and are not encoded as safe shirt geometry.
- Officer/uniform tops use upright shoulders, high collars, disciplined closures, cuffs, and yokes. Logos and copied insignia are never structural requirements.
- Wrap garments use true overlapping panels and a waist continuation; a diagonal decorative line is not a wrap.
- Tunics use belt/waist division, lower torso termination, and side-split implication. Tabards use a broad over-panel over an underlayer, not a narrow center stripe.
- Traditional offset closures use band collars and coherent offset fastening paths. They require culture-neutral abstraction unless a source is licensed and intentionally targeted.

## Structural axes the generator currently underrepresents

1. **Torso mass:** fitted, regular, boxy, rounded, tapered, layered-open, and longer-looking safe upper proportions.
2. **Opening topology:** none, partial placket, full placket, zipper, two open leaves, wrap, overlap, double-breasted, offset closure.
3. **Collar mass:** bound neck, folded collar, broad sailor collar, shawl edge, lapels, stand/high collar, hood junction.
4. **Hem topology:** clean, tucked, straight heavy, ribbed/gathered, shaped, cropped shell, sash-bound, split implication.
5. **Layer topology:** single fabric mass, visible undershirt wedge, broad inner shirt, vest-over-shirt, tabard-over-underlayer, formal nested layers.
6. **Rear carrier:** neck binding, yoke, rear collar, hood, knit field, tailored seam/vent, sash, rear panel.

These need to become first-class grammar choices. Palette and motif selection must occur only after topology is fixed.
