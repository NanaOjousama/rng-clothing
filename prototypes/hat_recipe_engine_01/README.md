# Hat recipe engine — prototype 01 (crown_brim)

Template-first proof: **one family recipe, parameters only**, builds 4-view
construction templates (bucket / fisherman / sun hat) directly on the 20x20
grid. No AI in pixel construction, no downscaling, no anti-aliasing,
stdlib-only. Isolated from the frozen generator, the trucker solvers and the
Zero123/SDXL experiments.

    python3 prototypes/hat_recipe_engine_01/build.py     # build + validate + previews; non-zero exit on hard failure

| File | Role |
|---|---|
| `engine.py` | generic construction: crown rows, brim lip + lobes, outline, cast, view rules |
| `recipes/crown_brim.json` | family recipe: defaults, parameter docs, 3 variants (params + identity notes) |
| `validate.py` | hard checks, helmet metric with in-run calibration, nearest-reference retrieval |
| `preview.py` | preview-only palettes, contact sheet, offline worn composite |
| `out/` | `*.template.json` (region + role maps per view), strips, sheets, `validation.json` |

## Template format

Per view (front/right/left/back, the vanilla hats.png order), two 20-char x 20-row maps:
- **region**: `c` crown, `b` band, `t` brim_top, `u` brim_under, `x` cast, `.` empty
- **role**: `O` outline, `S` shadow, `M` mid, `L` light, `H` highlight, `C` cast

View rules: `left = mirror(right)` exactly; `back` = same silhouette as front, with different
interior roles and no cast. Family exceptions are meant to go in as explicit recipe keys
(`back_rule`).

## Construction grammar learned from the references

Measured pixel by pixel from vanilla Fishing Hat 55, Straw Hat 4 and Bucket Hat 102, and plurffle's
Sun, Straw and Boater hats. Each rule is a recipe parameter or an engine rule, never pixels copied
from a reference:

- **Disc brim, front view** = a short central **lip** (high, cast shadow under it) plus two **lobes**
  (the brim's sides seen edge-on; the lobe top stays level and only the underside drops). A uniform
  drooping strip gave thin outline "claws".
- **Wide brims are an ellipse** seen from slightly above: the far edge shows beside the crown and the
  tips taper (`brim_far`, `brim_near`). A soft brim flips up on one side (`brim_curl`, plurffle Sun Hat).
- **Brim top faces the light**: lit top surface, shadow only where the lobe turns under. Mid/shadow
  fills made every brim muddy.
- **Skirt brim** (bucket): angled down all round, built row by row as a trapezoid, with a stitched seam row.
- **Back-view exception `bowl`** (55, 4, 98, plurffle Sun/Straw): the brim is seen from above and
  behind; the crown continues ~2 rows down into the bowl, then a shadow band, mid, a lit rim and the
  outline. Same width and top as the front, but deeper.
- The highlight is a small cluster on the light side, not a full-width stripe; the crown base flares
  (`base_flare`).

## Status at this checkpoint (v2, visual iteration)

Judged at 1x / 2x / 6x beside matched-palette references (`WORN_PREVIEW.png`, `COMPARE_6X.png`).
Hard checks pass for all three. Retrieval now matches the intended reference for every variant:
bucket → vanilla Bucket Hat, fisherman → vanilla Fishing Hat, sun → plurffle Straw Hat / Sun Hat.

Not proven / known gaps:
- Offline worn composite, not a QC Bridge capture.
- Hair pokes past the crown sides with hairstyle 0 at full hair (vanilla does the same here).
- Every variant uses the same crown shading pattern; there is no material micro-texture (the
  generator's job) and no deliberate hand irregularity.
- Bucket side view is almost its front view (a round hat; acceptable but plain).
- bucket~fisherman silhouette IoU 0.835 is close to the 0.85 distinctness limit; their brim
  construction and interior differ, but the outlines are similar.
- "<20 manual edits" is not measured by a person.
- Not yet run through the frozen generator.
