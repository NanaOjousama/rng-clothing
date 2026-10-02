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

## Construction grammar learned from vanilla (evidence: Fishing Hat 55, Straw Hat 4, Bucket Hat 102)

The decisive finding: in the front view a brim is **not** one strip. It is a short
central **lip** (the part in front of the face: high, with the cast shadow under it)
plus two **lobes** (the brim's sides seen edge-on, hanging lower, separated from the
lip by a turn-under line). The lobe top stays level and only the underside drops.
Modelling the brim as one drooping strip gave thin outline "claws" (iterations 1–4);
lip + lobes fixed it.

## Status at this checkpoint

Hard checks pass for all 3 variants: grid/codes, left mirrors right, back silhouette
matches front, closed outline, no orphan pixels, front/side height agreement, seating
inside the measured vanilla range (lip bottom 10–12), regions/roles present, not a
helmet. Family checks: variants distinct (silhouette IoU < 0.85), and the helmet metric
calibration (vanilla brimmed hats pass, head-shell strawmen fail).

Nearest-reference retrieval (silhouette IoU over 4 views, vanilla + plurffle):
bucket → vanilla Bucket Hat ✔; sun → plurffle Straw Hat / Sun Hat ✔;
fisherman → Straw Hat first, Fishing Hat only third ✘ (soft check).

Not proven / known gaps:
- **Worn preview is an offline composite** (farmer_base + hairstyle 0, hat at −2,−2),
  not a QC Bridge capture. The bridge was not running.
- Hair pokes past the crown sides with hairstyle 0 at full hair. Vanilla Bucket Hat
  does the same in this composite. No hat-hair or `HairMode` setting has been tested.
- Back view follows the default rule. Vanilla brimmed backs are a slightly
  top-down "bowl" (more brim visible, ~1 row lower). That is a candidate `back_rule`
  exception with recurring evidence (55, 98, 4, 102, plurffle Sun Hat).
- "<20 manual edits" is an estimate only; it has not been measured by a person.
- The sun and fisherman hats are the closest pair (IoU ≈ 0.76).
- Not yet routed through the frozen generator; the 4 palettes are preview-only ramps.
