# V4.6B Direction Orientation Audit

## Result

- **Fashion Sense asset mapping: FIXED**
- **Preview/comparison renderer mapping: FIXED**

The named model-to-block assignments were correct, but `LeftPants` was missing
Fashion Sense's required horizontal `Flipped: true` behavior. The generated
`pants.json` files were corrected. No game texture, garment construction,
recipe, palette, or anchor changed; all six `pants.png` SHA-256 hashes are
identical before and after this audit.

## Runtime authority

Fashion Sense 7.5.0
`PantsContentPack.GetPantsFromFacingDirection(int)` explicitly maps Stardew's
Farmer direction values as follows:

| Farmer FacingDirection | Physical direction | Fashion Sense model |
|---:|---|---|
| 0 | Up / Back | `BackPants` |
| 1 | Right | `RightPants` |
| 2 | Down / Front | `FrontPants` |
| 3 | Left | `LeftPants` |

The installed official `SimplePantsTemplate` supplies the representative idle
Farmer-frame contract:

| View | Current Farmer frame | Appearance source frame |
|---|---:|---:|
| Front / Down | 0 | 0 |
| Right | 6 | 6 |
| Back / Up | 12 | 12 |
| Left | 6 | 6 |

Left and right select different Fashion Sense models and different atlas
blocks. They both use Farmer frame 6 because Stardew's horizontal Farmer pose
topology reuses that frame number. The official model sets `LeftPants.Flipped`
to `true`; Fashion Sense `DrawManager` applies that flip to the base appearance
texture and its color mask.

## Generated Fashion Sense asset audit

All six appearances share the validated direction-frame contract below. Each
row was checked against its generated `pants.json`, its renderer model, and its
`UniformAnimation` condition.

| Garment | Front / Down | Right | Back / Up | Left |
|---|---|---|---|---|
| Harborline Fitted Trousers | `FrontPants`, frame 0, Y0, no flip | `RightPants`, frame 6, Y2752, no flip | `BackPants`, frame 12, Y1376, no flip | `LeftPants`, frame 6, Y4128, flipped |
| Ridgeline Panel Trousers | `FrontPants`, frame 0, Y0, no flip | `RightPants`, frame 6, Y2752, no flip | `BackPants`, frame 12, Y1376, no flip | `LeftPants`, frame 6, Y4128, flipped |
| Cedar Day Shorts | `FrontPants`, frame 0, Y0, no flip | `RightPants`, frame 6, Y2752, no flip | `BackPants`, frame 12, Y1376, no flip | `LeftPants`, frame 6, Y4128, flipped |
| Bramble Cuff Shorts | `FrontPants`, frame 0, Y0, no flip | `RightPants`, frame 6, Y2752, no flip | `BackPants`, frame 12, Y1376, no flip | `LeftPants`, frame 6, Y4128, flipped |
| Willow A-Line Skirt | `FrontPants`, frame 0, Y0, no flip | `RightPants`, frame 6, Y2752, no flip | `BackPants`, frame 12, Y1376, no flip | `LeftPants`, frame 6, Y4128, flipped |
| Heather Pleat Skirt | `FrontPants`, frame 0, Y0, no flip | `RightPants`, frame 6, Y2752, no flip | `BackPants`, frame 12, Y1376, no flip | `LeftPants`, frame 6, Y4128, flipped |

The physical order of the four blocks inside the combined texture is not a
direction contract by itself. What matters is that each named FS model's
`StartingPosition` points to the matching generated block. Those assignments
were correct:

- front block Y0;
- back block Y1376;
- right block Y2752;
- left block Y4128.

Before correction, the left block and `LeftPants` selection were already
correct, but the omitted `Flipped` property made the frame-6 source face the
same screen direction as Right. This was an actual content-model orientation
bug, not an art-block swap.

## Preview mismatch and correction

The preview generator previously used:

`front=0, back=8, right=4, left=12`

Those numbers were inherited as generic representative Farmer frames and were
not verified against the installed Fashion Sense Pants idle contract. The
result was:

- Front happened to be correct;
- Right sampled frame 4 instead of horizontal idle frame 6;
- Back sampled frame 8 instead of up/back idle frame 12;
- Left sampled frame 12—an up/back Farmer pose—instead of horizontal idle
  frame 6.

The preview generator, article comparison, and static representative-frame gate
now use:

`front=0, right=6, back=12, left=6`

The direction sheets are ordered and labeled `FRONT | RIGHT | BACK | LEFT`.
The preview compositor also mirrors the Farmer base and left garment exactly as
Fashion Sense does for `LeftPants.Flipped`.
Static article validation still passes all six with the corrected poses.

## Diagnostic output

`output/comparisons/V46B_DIRECTION_ORIENTATION_AUDIT.png` uses Ridgeline Panel
Trousers and displays conspicuous temporary labels for:

- physical direction;
- Fashion Sense model field;
- Farmer FacingDirection;
- current/source frame;
- atlas block Y.

The markers are drawn on the audit sheet only. They were never written into any
game `pants.png` or test-pack asset.
