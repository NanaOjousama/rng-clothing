# V4.6B Lower-Body Readability Report

## Outcome

V4.6B passes the static article-identity gate. The original Scale-2 build failed
runtime because its shared custom layer was anchored 64 display pixels too low.
The reusable contract has been corrected and rebuilt, but the corrected build
has not been runtime-tested. All six prototypes remain `EXPERIMENTAL`.

## Architecture added

- A coordinate-free semantic contract for `PANTS`, `SHORTS`, and `SKIRT`.
- A shared 126-frame Farmer motion/coverage map derived from installed Stardew
  1.6.15 Farmer bases and the installed Fashion Sense 7.5.0 Pants contract.
- Three article-specific region builders rather than one generic bottoms mask.
- Direct 32×64 logical rendering at Scale 2. The original `(0,-2)` anchor was
  disproven by runtime evidence; the corrected BodyPosition `(0,30)` includes
  Fashion Sense's native Farmer origin and preserves the 16×32 Scale-4 Pants
  display offset.
- Direction blocks for front, back, right, and left so side/back grammar is not
  a cropped front.
- Static identity gates in addition to schema, alpha, frame, and determinism
  checks.

The 16×32 source coverage is motion evidence only. Final 32×64 pixels are
constructed directly; no finished sprite is upscaled or downsampled.

## Six prototypes

| Garment | Article | Rarity | Primary diagnostic idea | Status |
|---|---|---|---|---|
| Harborline Fitted Trousers | Pants | Common | clean long paired channels and inseam | EXPERIMENTAL |
| Ridgeline Panel Trousers | Pants | Rare | tapered legs, knee/outer panels, paired cuffs | EXPERIMENTAL |
| Cedar Day Shorts | Shorts | Common | high separate clean hems | EXPERIMENTAL |
| Bramble Cuff Shorts | Shorts | Uncommon | relaxed openings, rolled hems, utility panels | EXPERIMENTAL |
| Willow A-Line Skirt | Skirt | Common | unified short flare and continuous hem | EXPERIMENTAL |
| Heather Pleat Skirt | Skirt | Rare | medium flare, folds, contrast waist, layered hem | EXPERIMENTAL |

## Static validation

`tools/validate_generator_v46b.py` reports
`PASS_STATIC_ARTICLE_IDENTITY_RUNTIME_NOT_TESTED` with zero errors.

Confirmed statically:

- exactly two appearances per article and no Shoes;
- deterministic semantic recipes and pixels;
- no raw coordinates in recipes;
- 32×64 logical frames, Scale 2, binary alpha, PNG filter 0;
- 192×5504 atlases and valid direction starts;
- 126-frame mappings remain in bounds;
- Fashion Sense 7.5.0 content models and recolor masks;
- Pants use paired cuffs/center construction;
- Shorts terminate above Pants and use paired hems;
- Skirts remain connected, retain a center hem, and contain no inseam;
- six distinct representative front masks;
- every promotion state is still `EXPERIMENTAL`.

Not confirmed: idle, walking, running, tools, sitting, horse, recolor UI, or
multiplayer behavior.

## Critical visual assessment

At the controlled gameplay footprint, article recognition has materially
improved over V4.6: the pants are long paired forms, shorts are clearly shorter
with exposed legs, and skirts are unified flared forms. The Rare pants and Rare
skirt demonstrate useful high-density panel/fold vocabulary without turning
this diagnostic batch into a fashion showcase.

The weakest evidence is the back stride: the Farmer's native separated legs
force a much wider lower silhouette, and a static composite cannot prove it
will look coherent through animation. Side skirts are intentionally compact and
may need art refinement after their motion mask proves safe. The 192×5504 atlas
cost also needs optimization before production.

## Promotion status

| Article | Current status | Reason |
|---|---|---|
| Pants | EXPERIMENTAL | static identity passes; runtime untested |
| Shorts | EXPERIMENTAL | static identity passes; runtime untested |
| Skirts | EXPERIMENTAL | static identity passes; runtime untested |
| Footwear | DEFERRED | explicitly out of V4.6B scope |

The immediate next step is only the Steam Deck runtime checklist. V4.7 must not
begin until the motion evidence is returned.
