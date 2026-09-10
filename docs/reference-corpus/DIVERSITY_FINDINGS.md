# Diversity Findings

## Ranked sources of worn-scale differentiation

1. **Outer silhouette and volume distribution** — fitted, regular, boxy, rounded, tapered, cropped, open-layered, padded.
2. **Collar/hood mass** — bound neck, folded collar, broad sailor collar, shawl edge, lapel, stand/high collar, true hood.
3. **Opening topology** — closed, short placket, full placket, zip, open leaves, overlap, diagonal wrap, double-breasted, offset closure.
4. **Layer topology** — single mass, broad inner tee, vest over shirt, tabard over underlayer, nested formal layers.
5. **Hem/waist topology** — clean, tucked, straight heavy, gathered/ribbed, shaped, cropped, sash-bound, split implication.
6. **Sleeve relationship** — short/long/rolled, inner-shirt sleeves under vest, contrast sleeves, sport continuation, cuff character.
7. **Large color-block topology** — shoulder/sleeve block, yoke/body, inner/outer, wrap halves, light body/dark frame.
8. **Major panel and pocket topology** — large work pockets, field pockets/yoke, tabard panel, padded divisions.
9. **Directional asymmetry** — genuine wrap/moto/offset closure that changes left/right views.
10. **Back carrier** — hood, sailor collar, yoke, tailored seam/vent, knit field, sash, rear panel.

The first six are structural and should dominate diversity scoring. Large color blocking and major panels support them. Back treatment prevents front-only diversity from collapsing during play.

## Low-value variation that must not count

- palette swaps within identical topology;
- one extra stripe, button, pocket dot, badge or motif;
- moving a small motif from left to right chest;
- changing only shading richness or outline darkness;
- renaming the same fitted top as shirt, tunic, jacket or uniform;
- changing lore/theme tags without worn structural change;
- side/back views that are merely recolored crops;
- adding a custom layer whose visible result is equivalent to shirt pixels.

## Corpus balance

### Strong coverage

- casual shirts and graphic tees;
- sweaters/crewnecks and patterned knitwear;
- cardigans, sweater vests and formal waistcoats;
- track/sport jackets and winter shells;
- blazers, uniform tops, period/formal layers;
- feminine fashion-top neckline, wrap and asymmetry techniques;
- four-direction Fashion Sense shirt construction.

### Moderate coverage

- open shirts/overshirts and work jackets;
- field/military outerwear;
- hoodies and coordinated presets;
- sailor tops, traditional/offset closures, tunics/tabards;
- one-piece/costume coordination.

### Thin or ambiguous coverage

- true henleys;
- clearly documented moto jackets;
- non-character varsity jackets;
- modern long coats with runtime-safe movement;
- diverse masculine pastel/formal-light outerwear;
- custom sleeve silhouettes with broad runtime proof.

The corpus is very large but imbalanced toward feminine packs, graphics/recolors, uniforms, and fitted shirt-sheet constraints. Military/short jackets are not the only references, but they are easy to overlearn if sources are counted by asset rather than structural family.

## Batch diversity gate for future implementation

For each pair, compare: silhouette/volume, collar/hood, opening, layering, hem, sleeve relationship, major panel/pocket layout, side profile, back carrier and color topology. Reject a pair when seven or more dimensions substantially overlap, or when both share silhouette + opening + layering even if decoration differs.

Farmer composites override semantic recipes. A claimed cardigan that wears like an open blazer is a blazer-like duplicate. A claimed tabard that wears like a center-striped shirt is not a tabard. Review at gameplay size in Front | Right | Back | Left before any candidate enters rarity evaluation.

## Five highest-impact anti-convergence rules

1. Lock a distinct structural grammar before palette, motif or rarity polish.
2. Ban the center stripe as a universal substitute for zipper, placket, inner layer, vest opening, tabard or wrap.
3. Require each grammar to own a distinct hem/waist and a distinct rear carrier, not only a front neckline.
4. Score the worn Farmer, not the isolated shirt sheet or recipe name.
5. Treat recolors and decoration swaps as variants inside one grammar; they do not expand the design pool.

## Readiness conclusion

The corpus is sufficiently diverse to proceed to a **grammar implementation review**, not directly to generation. The 33 proposed grammars materially broaden the vocabulary, but provisional henley, varsity and moto families need additional references, and all future implementations must be constrained by current runtime-safe upper-body contracts. No rarity expansion is justified by this study alone.
