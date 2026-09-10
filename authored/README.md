# The pre-authored library

Small, hand-drawn, recolour-ready. Nothing here is generated: the combinator
only chooses which authored things go together and which curated harmony
recolours them.

```
authored/
  index.json              the authoring index: exact RGB -> (role, ramp step)
  palettes.json           19 curated harmonies, three 6-step ramps each
  bases/<name>/
    front.png back.png left.png    the three authored views
    base.json                      slot, size, style tags, anchor points
  decals/<name>.png + <name>.json  a small drawn piece + where it attaches
```

## Editing the art

`tools/author_base_assets.py` holds the art as ASCII and writes these PNGs.
Edit the art there and re-run it, or edit the PNGs directly in any pixel
editor — both are valid, the PNGs are what the runtime loads.

Every pixel must be an exact colour from `index.json`, or loading raises. The
index is:

| role | what it is | chars in the authoring script |
|---|---|---|
| body | the garment's own cloth | `1`-`6`, true grayscale |
| trim | a second cloth: collars, bands, cuffs | `a`-`f`, red-tinted |
| accent | small hard punctuation: buttons, buckles | `p`-`u`, blue-tinted |

Six steps per role, deep to highlight. A sprite carries roles and values, never
a hue, which is what makes a palette a lookup rather than a redraw.

## Views

FRONT, BACK and LEFT are authored. **RIGHT is the mirror of LEFT** and is never
drawn — Fashion Sense wants four frames, and a hand-drawn right view is one
more thing that can disagree with its own left. `test_right_is_the_mirror_of_left`
asserts it.

## Anchors

`base.json` gives each anchor a top-left point **per view**, because a view
that is narrower needs a different one — the left view's neck sits a column in
from the front's, and getting that wrong is what made a collar hang off the
shoulder in the first batch.

A decal draws only where the base already has cloth. Anything falling outside
is dropped, not drawn floating: **the base owns the silhouette.**

## Style tags

Every base, decal and palette carries tags. One tag is chosen per garment and
every component must carry it, so coherence is a precondition rather than a
filter applied to whatever was rolled. Current tags: `work`, `casual`, `smart`,
`formal`, `cottagecore`, `festival`.

## Shading vocabulary

Held across every base, and checked by `tools/qc_authored_bases.py`:

| step | what it draws |
|---|---|
| `1` | the rim, deepest shadow, undersides — **outlines are drawn at the bottom of the ramp** |
| `2` | shadowed side, contact rows |
| `3` | the turned side, lower body |
| `4` | the body's base plane |
| `5` | the lit plane |
| `6` | the light patch: 3-5 cells, never a band |

Two failure modes this catches, both measured rather than guessed:

* A rim one step down from the body reads at -33 border-to-interior; the corpus
  runs -44 to -71. Draw rims at step 1.
* An interior as dark as its rim flattens the outline just as surely as a light
  rim does — the *delta* is what reads.
* Art that stops at step 5 measures a luminance span of 132; using step 6 at all
  puts it at 165, against the corpus's 97-209.

## QC

`PYTHONPATH=tools python3 tools/qc_authored_bases.py` renders each base through
eight curated palettes, measures it exactly the way the 194 reference hats were
measured, and prints it beside the corpus family it claims. A base that
misclassifies is a drawing problem, and the row says which number moved.

## Adding a base

1. Draw `front.png`, `back.png`, `left.png` in index colours.
2. Write `base.json`: `name`, `slot` (`HEAD`/`TOP`), `size`, `style`, `anchors`.
3. Run the tests — they check the index, the anchors, the mirror and the tags.

No code change is needed. Adding a garment is authoring.
