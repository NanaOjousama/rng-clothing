# V2 audit of V1 archetype collapse

Audit target: the five V1 shirts selected in `output/recipes/lifestyle_v1_recipes.json`, reconstructed through the V1 renderer at their authoritative 8×8 logical resolution.

## Executive finding

V1 did not fail because 8×8 is inherently unusable. It failed because every selected garment began with the same occupied silhouette and nearly the same shading field, then attempted to communicate archetype through late pixel overlays.

All five selected sprites have exactly the same occupancy in every direction:

| Direction | Occupied cells in every V1 garment | Occupancy difference between archetypes |
|---|---:|---:|
| Front | 62 | 0 |
| Back | 62 | 0 |
| Right | 56 | 0 |
| Left | 56 | 0 |

The selected recipes use `regular` or `relaxed` fit, but those V1 silhouette templates are byte-for-byte identical. Consequently, fit could change shading weight but never garment outline or region organization.

V1's render order was also collision-prone:

```text
shared silhouette and shading
  -> small archetype shade edits
  -> pattern pixels
  -> closure pixels
  -> collar pixels
  -> detail pixels
```

There was no persistent `PLACKET`, `INNER_LAYER`, `YOKE`, or `OUTER_PANEL` ownership. A later detail could overwrite an earlier construction cue, and validation only knew final color roles (`main`, `secondary`, `accent`), not which garment region a cell represented.

## Quantified visual-role convergence

The table below counts cells whose final broad role category (`main`, `secondary`, `accent`, or transparent) differs between each selected pair. It includes decoration, so it is a generous estimate of structural difference.

| Pair | Front | Back | One side | Interpretation |
|---|---:|---:|---:|---|
| T-shirt vs sweater | 16 | 14 | 12 | Difference is overwhelmingly lower-border placement, not garment construction. |
| T-shirt vs button shirt | 19 | 14 | 11 | Front collar/center marks survive; back and side remain close. |
| Sweater vs button shirt | 13 | 12 | 9 | The weakest side-view separation in the selected set. |
| Button shirt vs jacket | 13 | 10 | 13 | Too few changed cells for two supposedly different construction systems; much of the change is color role rather than outer-layer geometry. |
| Jacket vs sailor top | 22 | 28 | 25 | Large collar/yoke regions make this the clearest distinction. |

These counts do not prove similarity by themselves. The decisive fact is that the occupied masks are identical and most differences sit in one-cell lines. The comparison matches the in-game observation that the five items feel like treatments of one shirt body.

## Archetype findings

### T_SHIRT — Bluebell Pin Tee

- V1 applied no archetype-specific structural mask at all.
- Its identity came from a round neckline, a one-cell border treatment, and a two-cell chest accent.
- The border and pin were decorative; removing them leaves the shared V1 shirt field.
- The chest cue correctly disappeared on back and side, but that also removed most of the recipe's identity outside the front.
- Actionable V2 fix: preserve deliberate simplicity, use a minimal neckline region, and reject extra segmentation that turns a tee into another archetype.

### SWEATER — Hearth Ribbed Sweater

- V1's sweater-specific function repainted existing lower cells with different *main-fabric shade roles*. It did not reserve a ribbing region.
- The selected `lower_trim` added one protected row, but the garment kept the same torso outline, shoulder cap, and upper mass as the tee.
- “Heavy cloth” was therefore encoded mostly as hue/value, which is fragile after dyeing.
- Back and side repeated the lower line correctly, but did not add a heavier neckline or a two-row knit termination.
- Actionable V2 fix: reserve a connected `RIBBING` band with meaningful area in all directions and give the neckline more mass than a tee.

### BUTTON_SHIRT — Cedar Button Shirt

- The folded collar was a real protected region, but the placket itself was mostly a pair of ordinary main-shade columns.
- The three button cells were micro detail. Because the palette was low contrast, they did not create a tailored construction line in motion.
- The back retained only a small collar patch. The side reduced the closure to a narrow forward-edge shade change.
- It therefore read as “collared shirt with dots,” not as a torso organized around a placket.
- Actionable V2 fix: make `PLACKET` a continuous major mask independent of button pixels; buttons are applied only afterward.

### JACKET — Mistral Layer Jacket

- V1 never created persistent left and right outer-panel masks. It shaded columns near the opening but still treated them as the same main fabric field used by other shirts.
- The visible inner layer was a two-column protected center strip. This was the strongest surviving jacket cue, but two columns still resembled a shirt stripe when the surrounding panels lacked semantic ownership.
- The back removed the inner layer and fell back to the generic body plus collar and lower trim. The side kept only a narrow forward inner edge.
- Mistral performed better than the other V1 garments because the bright center layer and lower band occupied connected regions. It still lacked a broad “outer garment wrapping another garment” composition.
- Actionable V2 fix: `OUTER_PANEL_LEFT`, `OUTER_PANEL_RIGHT`, and `INNER_LAYER` must exist before shading. The inner opening should be broader than a placket, persist at the forward side edge, and be replaced on the back by outerwear yoke/hem structure.

### SAILOR_TOP — Garnet Pin-Collar Top

- The sailor collar was the one V1 treatment already close to a substantial region: a broad front wedge, a large back yoke, and a side band.
- The front center stripe and two-cell pin were decorative, but the garment remained recognizable when mentally removed because the collar/yoke occupied many connected cells.
- Garnet's strong upper/lower value break survived normal scale better than small closure marks.
- The main remaining weakness was the shared torso beneath the yoke and a side view whose lower half reverted to the generic shirt.
- Actionable V2 fix: keep the large `YOKE`/`COLLAR` system, increase its side depth, and make upper/lower region separation—not an emblem—the identity.

## What Mistral and Garnet proved

The two most successful V1 designs both spent pixels on connected areas:

- Mistral: center inner layer plus lower band;
- Garnet: broad collar/back yoke plus upper/lower contrast.

Their tiny accents were not the reason they survived. This validates V2's construction-first hypothesis: a few large, directionally coherent regions carry more identity than several independent decorative cells.

## V2 requirements derived from this audit

1. Preserve named major-region ownership through the whole render pipeline.
2. Allocate archetype masks before palette, shading, or micro detail.
3. Treat plackets, yokes, ribbing, outer panels, and inner layers as connected areas rather than line decoration.
4. Use a two-color unshaded comparison as a hard gate; a design that needs shading or a pin to identify itself has failed structurally.
5. Compare front, back, and side region arrangements automatically so a distinctive front cannot hide a generic back/side collapse.
6. Apply micro details last and forbid them from satisfying Rare identity.
7. Keep the common native occupancy contract for alignment, but stop confusing shared outer occupancy with shared garment construction.

## Audit boundary

This report diagnoses the exact V1 logical output and renderer rules. It does not claim that any similarity metric proves attractiveness. V2 still needs visual inspection on the two-color masks and later in-game testing.
