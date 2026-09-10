# Fashion Sense HD jacket body-coverage correction

## Result

The Mistral HD jacket now covers every required upper-torso/shoulder cell while retaining a stepped shoulder slope and the four-cell front neck opening. The correction changes the Fashion Sense jacket masks only. `Scale: 2`, `BodyPosition: (0,32)`, the semantic V2 recipe, palette, lapels, inner layer, back yoke, native `SleeveColors`, vanilla renderer, and all vanilla assets are unchanged.

Review images:

- `output/comparisons/FS_JACKET_SHOULDER_COVERAGE_BEFORE_AFTER.png`
- `output/fashionsense/poc_hd_jacket/mistral_lapel_layer_jacket_hd-coverage-debug.png`

## Installed-game mapping

Installed Stardew Valley 1.6.15 is authoritative for the mapping:

- `FarmerSprite.UpdateSourceRect` selects 16×32 body frames from a 96-pixel logical row.
- Standard standing frames are front `0`, side `6`, and back `12`.
- The vanilla shirt box overlays Farmer-frame coordinates X `4..11`, Y `14..21`.
- A corrected 16×16 Scale-2 Fashion Sense frame occupies exactly that same 32×32 display box, so each Farmer source pixel maps to a 2×2 HD-cell block.
- The installed `farmer_base.png` and the working vanilla Mistral jacket establish the minimum opaque upper-torso region. The envelope excludes the intentional front neck opening and leaves cells outside the required shoulder/sleeve junction available to the artistic silhouette.

This separates two tests: the body-coverage envelope answers whether skin can leak through; normal structure/readability checks answer whether the jacket still looks good.

## Exact logical-cell changes

Coordinates are zero-based `(X,Y)` within each 16×16 directional frame. All changes add opaque structural cells; no existing opaque cell was removed.

| Direction | Added cells and regions |
|---|---|
| Front | `SHOULDER_CAP`: `(2,0)`, `(3,0)`, `(12,0)`, `(13,0)`, `(0,1)`, `(1,1)`, `(14,1)`, `(15,1)`, `(0,2)`, `(15,2)` |
| Back | `SHOULDER_CAP`: `(2,0)`, `(3,0)`, `(4,0)`, `(11,0)`, `(12,0)`, `(13,0)`, `(0,1)`, `(1,1)`, `(14,1)`, `(15,1)`, `(0,2)`, `(15,2)` |
| Right | `SHOULDER_CAP`: `(2,0)`, `(3,0)`, `(10,0)`, `(11,0)`, `(0,1)`, `(1,1)`, `(0,2)` |
| Left | Mirrored `SHOULDER_CAP`: `(4,0)`, `(5,0)`, `(12,0)`, `(13,0)`, `(14,1)`, `(15,1)`, `(15,2)` |

Total additions: front 10, back 12, right 7, left 7. The front top row grows from four to eight occupied cells but retains transparent outer corners and the central X `6..9` neck opening. The back top row grows from six centered collar cells to a twelve-cell stepped shoulder/collar span, still leaving two transparent cells on each side. Neither top row is full-width.

The additions use a dedicated `SHOULDER_CAP` region. This prevents expanding panel/sleeve bounds from reclassifying existing shading: all 36 additions are new opaque cells, there are zero removals, and every previously opaque RGBA pixel remains byte-identical to the pre-correction texture.

## Permanent validation rule

`bodyCoverageEnvelope` is renderer data in `generator/data/fashionsense/hd_jacket_poc.json`. It uses `#` for mandatory opaque cells and `.` for silhouette freedom. The Fashion Sense renderer:

1. validates envelope dimensions and symbols;
2. mirrors the right-side envelope for the left view;
3. compares required cells against named structural regions before shading;
4. rejects rendering if any required cell is transparent.

The pre-correction fixture fails with exactly 10/12/7/7 missing cells for front/back/right/left. The corrected mask has zero missing cells in all directions. This rule is independent of Mistral's colors and can be reused by future 16×16 Scale-2 jackets using the same body alignment.

## Validation status

- Static Fashion Sense 7.5.0 source contract: PASS.
- Body-coverage envelope: PASS, zero missing cells.
- Front top width 8 versus mid-body width 16: shoulder remains tapered.
- Central neck opening: preserved.
- Corrected texture and test-pack texture: byte-identical.
- Vanilla Mistral PNG and Generator V2 regression: unchanged.
- Final confirmation of the skin seam still requires an in-game `fs_reload` check because static mask validation cannot replace the actual Farmer composite.
