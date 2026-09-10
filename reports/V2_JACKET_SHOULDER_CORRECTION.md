# V2 jacket shoulder/collar correction

Scope: a logical-pixel micro-adjustment to the shared `JACKET` structure only. Recipes, palettes, other archetypes, dimensions, frame positions, dye layout, and Content Patcher registration are unchanged.

## Exact upper-region changes

- Front small collar: reduced from two repeated vertical rows to one shallow row; the second row is now visible `INNER_LAYER`.
- Front wide lapel: changed from a 4-cell horizontal collar block plus a deep 2-cell tail to two separated diagonal wings (4 cells, then 2 cells). The two center cells remain `INNER_LAYER` on both rows.
- Back yoke: narrowed from 6 cells over 4 cells to a tapered 4-cell over 2-cell shape.
- Back wide collar: reduced from two rows (6 then 4 cells) to one centered 4-cell row.
- Side collar/lapel: reduced from three rows to two and redirected diagonally toward the visible inner opening.

Split left/right outer panels, the four-cell front inner layer, jacket hem, dye-mask format/placement, and side-facing layer opening remain intact.

Pixel-diff review confirmed that every changed native base or dye-mask cell is confined to logical rows 0–3. Lower torso, panel, and hem pixels are unchanged.

Review sheet: `output/vanilla/v2/V2_JACKET_SHOULDER_BEFORE_AFTER.png`.

Validation: both jackets pass the revised collar-anatomy check and the full V2 technical/export/pack suite. All 24 non-jacket native/preview/contact PNGs are byte-identical to the pre-correction outputs.
