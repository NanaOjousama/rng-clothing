# Generator V4 Article Model and Translation Adapters

## Architectural boundary

V4 is a coordinate-free wrapper around a complete V3 design recipe:

```text
style / V3 design concept / rarity
  -> V4 garment article selector
  -> article compatibility adapter
  -> unchanged V3 FS render
  -> renderer-owned article translation
  -> article and cross-rarity validation
```

The V4 semantic model adds `articleType`, `articleIntent`, and `articleFeatures`. It contains no pixels, rows, or coordinates. Logical-cell operations live only in `generator/data/fashionsense/v4_article_grammar.json` and `generator/renderers/fashionsense/article_v4.py`.

This preserves V3's construction, surface composition, directional topology, palette story, rarity budget, body coverage, and art grammar. It also prevents a style profile from acquiring Fashion Sense offsets or article-mask hacks.

## Article adapters

### FITTED_SHIRT

- Compatible base: `BUTTON_SHIRT`.
- Identity: tailored lower torso, shirt closure/collar logic, no outer-shell framing.
- Renderer operation: symmetric one-cell lower inset on rows 10–15, after the proven coverage rows.
- Surface zones: collar, yoke, chest, placket, waist, sleeves.
- Runtime sleeve material: outer shirt fabric through the existing native sleeve ramp.

### SWEATER_TOP

- Compatible base: `SWEATER`.
- Identity: continuous heavier cloth mass and a sweater-specific ribbed or structured termination.
- Renderer operation: preserve the V3 sweater mass; the adapter validates it instead of altering it.
- Surface zones: collar, yoke, chest, waist, hem, sleeves.
- Limitation: sibling sweaters intentionally share an article silhouette; design composition differentiates individual sweaters.

### VEST_TOP

- Compatible base: bounded `BUTTON_SHIRT` construction with overlay-panel layering.
- Identity: outer vest body over a visibly different under-shirt.
- Renderer operation: translate `SLEEVE`, `SHOULDER_CAP`, and `COLLAR` material regions to the palette story's coordinated under-shirt ramp. Native `SleeveColors` use that same under-shirt ramp.
- Surface zones: collar, yoke, vest body, placket, waist, back yoke.
- Limitation: this is a vest **over a shirt**, not a bare-arm vest. The latter is not runtime-proven.

### CROPPED_JACKET

- Compatible base: split-panel `JACKET` with visible inner layer.
- Identity: structured outer shell whose garment bottom ends two HD logical rows above standard short outerwear.
- Renderer operation: remove occupied rows 14–15 and add selective shadow anchors at the new row-13 termination. No full-width dark bar is introduced.
- Surface zones: lapel/collar, panels, inner layer, chest, waist, sleeves, back yoke.
- The shoulder/body envelope remains untouched, so the prior runtime coverage correction is preserved.

### SHORT_OUTERWEAR

- Compatible base: `JACKET`.
- Identity: split/open outer shell, visible inner layer, structured back, and full proven shirt-footprint lower termination.
- Renderer operation: preserve V3 jacket geometry and validate occupancy through row 15.
- This is deliberately called short outerwear. It is not presented as a long coat.

### LONG_OUTERWEAR

- Model status: `EXPERIMENTAL_REJECTED_FOR_V4_OUTPUT`.
- A taller shirt rectangle could load, but coat tails would overlap independently animated legs/pants and require unproven horse, sitting, swimming, tool, and draw-order behavior.
- The validator rejects this article from both V4 collections.

## Article-aware surface translation

V4 does not paste a design onto every article identically:

- a fitted shirt keeps its focal collar/placket or chest design while the lower body becomes tailored;
- a vest reinterprets shoulder/sleeve cloth as the under-shirt and preserves the outer body as a separate material frame;
- a cropped jacket preserves V3 lapel, pocket/motif, panel, and inner-layer systems but terminates their topology at a raised shell hem;
- short outerwear preserves jacket-scale paneling and a full lower shell;
- sweaters retain broad uninterrupted design planes and sweater termination rather than acquiring jacket openings.

V3 topology still controls whether a motif is front-only, paired with the back, wrapped, or construction-bound. The V4 adapter filters removed crop cells from its diagnostics rather than decorating directions independently.

## Rarity parity

V4 does not allocate new decorative pixels by rarity. It inherits V3 rarity floors and ceilings, then changes how each article expresses them:

- Common: one clear surface idea on an attractive readable article.
- Uncommon: a primary surface system plus an article-relevant supporting region.
- Rare: coordinated premium composition plus strong article evidence, without consuming future Legendary/Mythic space.

The cross-article gate compares rendered surface evidence, active systems, and article evidence. It rejects a collection whose Common/Uncommon/Rare averages do not progress. This index is a regression guard, not a beauty score.

## Quality gates

Each render must pass:

- V3 design/surface diagnostics;
- binary-alpha 16×64 texture contract;
- body/shoulder coverage after translation;
- article-specific material, taper, crop, or full-length evidence;
- a name-removed classifier based on rendered evidence;
- Fashion Sense Scale 2, BodyPosition `(0,32)`, four direction frames, and native sleeves.

Collection gates require at least four article types, exact rarity counts, deterministic unique textures, no long outerwear, and increasing cross-article rarity evidence.

