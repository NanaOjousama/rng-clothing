# Farmer Preview Quality Gate

## Authority

The worn Farmer at actual gameplay footprint is the approval surface. The installed 1.6.15 Farmer atlas is authoritative. Wiki orientation confirms that clothing, hair, hat, and arms are separate layers and that animation controls placement; left is a mirrored right-facing Farmer frame in vanilla ([Modding: Farmer sprite](https://stardewvalleywiki.com/Modding:Farmer_sprite)). Fashion Sense 7.5.0 remains authoritative for appearance anchors, source rectangles, and layer order.

## Required composites

Every candidate must render onto the installed Farmer in this exact review order:

`FRONT / DOWN | RIGHT | BACK / UP | LEFT`

Standing source baseline is Farmer frame 0 front, 6 right/left, and 12 back, with the left-facing composite mirrored from the right Farmer frame while garment direction ownership remains explicit. Use the real native sleeves/arms and equipped-layer ordering. Show:

1. exact gameplay-size composite without smoothing;
2. integer nearest-neighbor diagnostic enlargement;
3. isolated alpha silhouette only as a diagnostic, never as approval evidence;
4. optional no-shading flat-material composite for the design-interest test.

## Review gates

| Gate | Pass condition | Hard failure |
|---|---|---|
| Article read | label-blind reviewer identifies intended family immediately | identity depends on item name |
| Silhouette | worn mass differs meaningfully from related accepted garments | another fitted top/short jacket |
| Construction | collar/opening/layering/hem remain legible | flat torso plus decoration |
| Side | physical forward edge and depth are reconstructed | cropped/mirrored front |
| Back | topology carrier remains clear but quieter | generic blank/recolored back |
| Palette | structural values separate at gameplay size | muddy role collision or bright center-only read |
| Design interest | flat/no-shading design remains authored | shading does all the work |
| Beauty | clean, coherent, collectible on the Farmer | technically valid but unattractive |
| Diversity | structurally distinct from accepted library and batch | palette-only distinction |

## Pairwise metrics as guardrails

Metrics cannot prove beauty, but they can force review:

- Structural fingerprint overlap above 0.65: mandatory reject/rework review.
- Same topology plus Farmer silhouette IoU at or above 0.90 in two or more views: reject unless the article is intentionally the same subtype and visibly differs on at least four construction axes.
- Same opening, collar, hem, focal zone, and side reconstruction: reject regardless of palette.
- Fewer than four differing visible axes out of silhouette, shoulder, neckline, opening, proportion, hem, layering, dominant gesture, side, back: reject.
- Palette comparison is evaluated only after structural acceptance.

These are tripwires. A human reviewer may reject below them, but may not auto-approve above them.

## Hard rejection language

Reject if the actual Farmer looks like another fitted top, another short jacket, another dark torso with a bright center, a recolor, an identity that exists only in the name, or a design that works only enlarged. The gameplay result overrides the semantic recipe.

## Required evidence record

Each reviewed candidate must store:

- recipe and grammar IDs;
- Farmer/game version and FS version;
- direction mapping and source frames;
- structural fingerprint and topology group;
- pairwise nearest accepted designs;
- article-read label-blind result;
- per-view silhouette/construction/beauty judgments;
- palette/value judgment;
- `ACCEPT`, `REWORK`, or `REJECT` with written reason.

## Later runtime gate

Static acceptance only permits a runtime candidate. Movement, tools, sitting, horse, water/special states, recolor, UI, and multiplayer remain separate runtime evidence. Static validation can never promote `RUNTIME_PASS`.
