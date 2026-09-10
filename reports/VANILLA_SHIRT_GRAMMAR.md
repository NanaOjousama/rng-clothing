# Vanilla shirt grammar learned for Generator V1

Research target: installed Stardew Valley `1.6.15.24356`.

This report describes reusable construction rules. It does not treat any vanilla shirt as an output template, and the generator never copies a source tile. The evidence comes from the installed `Characters/Farmer/shirts` sheet, `Data/Shirts`, and the installed `FarmerRenderer` behavior documented in `specs/CAPABILITIES.md`.

## Evidence set

The research tool `tools/analyze_vanilla_shirts.py` measured 34 representative shirts (136 direction frames) across five study groups:

| Study group | Installed sprite indices |
|---|---|
| T-shirt / simple top | 1, 6, 128, 194, 200, 209 |
| Sweater / pullover | 176, 177, 178, 198, 235, 301 |
| Button shirt | 29, 123, 140, 154, 248, 251 |
| Compact jacket | 18, 30, 137, 138, 155, 163, 211, 218, 231, 270, 271, 285 |
| Sailor / broad-collar top | 19, 239, 259, 261 |

The groups are analytical labels, not claims about the game's taxonomy. Several vanilla items could reasonably fit more than one group.

Observed across the sample:

- occupied cells per 8×8 direction: 53 minimum, 59 median, 64 maximum;
- meaningful rendered colors per direction: 3 minimum, 6 median, 11 maximum;
- rendered luminance range: 31.47 minimum, 154.26 median, 226.91 maximum;
- disconnected opaque single pixels: zero in every sampled direction;
- front occupancy: normally 60–64 cells;
- side occupancy: normally 53–58 cells;
- back occupancy: normally 62–64 cells.

These are observations, not universal engine requirements. V1 uses conservative limits inside these ranges.

## Confirmed renderer contract

- A custom shirt texture is exactly 256 pixels wide. A one-item V1 sheet is 256×32.
- One shirt consumes an 8×32 block in the left 128-pixel half and an aligned 8×32 dye block at `x + 128`.
- Direction order in that block is front `y+0`, right `y+8`, left `y+16`, back `y+24`.
- `SpriteIndex` addressing is `x = (index × 8) % 128`, `y = floor(index × 8 / 128) × 32`.
- The game draws the authored base tile and then draws the grayscale mask tile tinted by the equipped shirt color.
- With sleeves enabled, the installed renderer samples the front tile's first column at mask/base rows 4, 3, and 2 for dark, middle, and light sleeve tones respectively.
- Shirt animation is native Farmer movement plus integer feature offsets. The shirt supplies no independent animation frames.

## Recurring pixel grammar

### 1. Shoulder placement

Most sampled fronts begin with six occupied shoulder cells around a two-cell centered neck gap: `###..###`. The upper shoulder cap is usually darker than the row below it. The side view compresses that cap to roughly five occupied cells rather than inventing a new silhouette.

V1 rule: preserve the centered neck gap, use one short dark shoulder cap, and place light only in an attached upper-shoulder cluster.

### 2. Torso width

The fixed native torso anchor leaves little safe width variation. Sampled fronts commonly fill all eight columns from row 1 downward; backs commonly fill all eight columns through row 6 and narrow the final row to `.######.`. Fit is therefore communicated more by lower-row contour and value mass than by adding width.

V1 rule: use one connected 53–64-cell garment field. `fitted` may taper the last row; `regular` and `relaxed` retain vanilla coverage, with relaxed fit using broader lower shading.

### 3. Neckline pixels

Necklines spend the first two or three rows on one centered landmark. Round and crew necks use a short U/band boundary; shallow V necks use a two-step center descent. They do not compete with a second unrelated neck treatment.

V1 rule: choose exactly one neckline and reserve the top-center cells for it before surface details are applied.

### 4. Collar pixels

Folded collars are small paired clusters attached to the center opening. Broad/sailor collars use a wider contrast wedge in front and a substantially clearer yoke on the back. A readable collar typically needs a light/base region plus a shadow immediately underneath.

V1 rule: collar geometry is archetype-owned. A collar must have a legal neckline and a directional plan; arbitrary collar pixels cannot be added by a recipe.

### 5. Center openings

Button shirts and jackets use one continuous central construction line. Buttons, ties, or closure highlights are sparse cells attached to that line. Random center dots without a seam are not part of the learned grammar.

V1 rule: `buttons` and `center_open` are closures, not decorative motifs. `button_line` and `inner_layer` may refine the closure only when compatibility rules allow them.

### 6. Side-facing compression

Typical sampled side widths by row were approximately 5, 7, 7, 8, 8, 7, 7, 6–7 cells. Collars and front openings move toward the physical forward edge. Front-only chest marks often disappear.

V1 rule: construct one canonical side view from the same recipe and mirror its structure for the other side. Keep palette, collar, wrapping stripe, and hem height consistent; remove details that would be physically hidden.

### 7. Back-facing simplification

Back views usually have fewer meaningful colors than corresponding jacket/button fronts. They remove button lines, inner shirts, chest emblems, and ties, while retaining a collar back, yoke, broad material field, hem, or center seam.

V1 rule: simplify ornament, not construction. A collared recipe must still show a back collar/yoke; a wrapping band must still wrap.

### 8. Shadow placement

In most groups, edge luminance was lower than interior luminance. Deep values collect on top shoulder caps, lower outer edges, under collars, panel boundaries, and the hem. Some authored jackets intentionally invert a small edge highlight, so this is a strong tendency rather than an absolute law.

V1 rule: outer lower edges and under-collar cells prefer `main_shadow` or `main_deep`. Large shadow fields cannot replace the dominant base field.

### 9. Highlight placement

Highlights appear as attached two-to-several-pixel clusters on upper shoulders, upper panels, collar edges, or a fold. They are not distributed evenly and are rarely isolated.

V1 rule: highlights remain subordinate, contiguous, and upper-facing. Common designs may omit the brightest ramp step.

### 10. Outline / deep-shadow use

Vanilla does not require a continuous black outline around every shirt. It uses locally darkest pixels where separation matters: shoulder cap, lower edge, opening, collar underside, and side contour.

V1 rule: use a material-colored deepest shade in the dye mask instead of a universal black border. Protected dark pixels are reserved for secondary construction, not a second full outline.

### 11. Dye-mask use

The installed sample contains three valid strategies: no effective mask for fixed-color shirts, a full grayscale material field for simple dyeable pullovers, and partial/overlapping masks for designs with protected colors. The renderer permits base and mask overlap because the tinted mask is drawn second.

V1 chooses a simpler deterministic contract:

- main fabric is written only to the grayscale mask;
- secondary fabric and accent are written only to the base half;
- base and mask cells do not overlap;
- all five generated shirts are dyeable through the single vanilla channel;
- front mask cells `(0,2)`, `(0,3)`, `(0,4)` always contain ordered light/base/shadow values for native sleeve recoloring.

This no-overlap policy is stricter than vanilla, but it is fully compatible with the confirmed draw order and easier to validate.

### 12. Contrast levels

The sample's median overall luminance range is high because collars, inner shirts, and outlines are localized rather than blended. Even low-key garments retain separation between outer edge, body, and a construction landmark.

V1 rule: validate both shadow-to-base separation and overall default-color range. Reject a palette/recipe whose important regions merge at default dye color.

### 13. Meaningful color count

The sample median is six colors per direction; complex jackets reach eleven. V1 deliberately stays tighter:

- Common: at most six rendered colors;
- Uncommon: at most eight;
- Rare: at most nine.

Those include main ramp values, protected secondary values, and the optional accent. Extra near-duplicate colors are not allowed merely to raise detail.

### 14. Accent pixels

Vanilla uses small buttons, pins, ties, or symbols as attached landmarks. The sample contains no disconnected opaque speckles even when a color itself appears in one small location.

V1 rule: one declared motif maximum. Accent caps are 2, 3, and 4 cells for Common, Uncommon, and Rare. A chest accent is front-only and attached to the garment field.

### 15. Communicating identity in 8×8

Vanilla generally spends its pixel budget in this order:

1. recurring Farmer-aligned silhouette;
2. neckline/collar or opening;
3. one large color relationship;
4. hem/panel/stripe structure;
5. a sparse accent;
6. small shading refinements.

A sweater reads through broad mass, neckline, and hem weight. A button shirt reads through collar plus center line. A jacket reads through outer panels around an opening. A sailor top reads through the contrast collar and back yoke. Surface noise cannot substitute for those structures.

## V1 translation policy

The generator uses the vanilla evidence in three layers:

```text
semantic recipe
    -> archetype structure and compatibility tags
    -> shared silhouette/shading grammar
    -> direction-aware component placement
```

Recipes contain no coordinates. Coordinates live only in the renderer's project-owned logical templates and component rules. Left/right are not separately randomized, and all output is rasterized directly into the final logical PNG.

## Limits of the learned grammar

- The five analytical groups are intentionally narrow and do not cover every vanilla shirt.
- Metrics can reject obvious failures but cannot prove attractiveness.
- Fixed 8×8 torso coverage cannot express true oversized sleeves, long coats, or independent fabric motion.
- In-game animation, body-type interaction, and player-chosen dye extremes still require visual testing even when the static contract passes.
- V1 does not infer geometry from photographs or reference pixels; Lifestyle references affect only semantic probabilities, palette families, and restraint.
