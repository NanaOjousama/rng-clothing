# V4.6B Lower-Body Readability Findings

## Why the previous pants failed

The V4.6 prototype followed valid Fashion Sense frame bounds, but it occupied
only a narrow vanilla-like band around the lower torso. It emphasized color,
seams, and trim before establishing a long two-leg silhouette. At gameplay size
the result could be parsed as shorts, a skirt, or an arbitrary lower-body block.
Static validity never proved article identity.

V4.6B corrects the translation layer rather than repainting that prototype. A
shared pose contract maps every Farmer frame into a direct 32×64 Scale-2 logical
canvas, then three independent article grammars construct the garment.

## What now creates a pants read

- waist-to-hip continuity;
- paired left/right leg channels extending visibly below the hips;
- front/back center construction that becomes an inseam;
- independent ankle/cuff terminations with a small central break;
- knee/outer panels only after the long-leg structure exists;
- a dedicated side seam and side cuff.

The two pants prototypes differ in fit, length, waistband, panels, knees, and
cuffs. They do not share one final mask.

## What separates shorts from skirts

Shorts retain connected hips but split into two high leg openings. Their two
hems are separate and native lower legs remain visible below them. Skirts use a
single connected mass whose hem crosses the center. Pleats are internal value
lines, never transparent leg splits.

## What separates skirts from pants

Pants preserve two channels down to independent terminations. Skirts suppress
the inseam entirely and use waistband-to-hem volume: straight, A-line, pleated,
or soft flare. Their identity comes from one unified silhouette and intentional
hem rather than paired legs.

## Directional construction

- Front: pants/shorts show paired channels and center construction; skirts show
  unified volume and optional folds.
- Back: the same article logic is rebuilt around the wider stride topology;
  this is the highest static/runtime risk.
- Left/right: pants use a long trouser side with seam/cuff; shorts use a high
  side hem; skirts use a narrower unified side volume.
- Designs are generated from semantic regions (`waistband`, leg channels,
  inseam, knees, cuffs, skirt mass, folds, and hem), not arbitrary recipe
  coordinates.

## High-detail usage

The 32×64 Scale-2 contract is not a 16×32 image enlarged. Extra logical cells
resolve stepped silhouettes, waist-to-hip transitions, long vs short
termination, paired cuffs/hems, knee and utility panels, pleat lines, flare,
controlled light planes, and one-cell seams that remain small on screen.

## Static result and limitations

All six front/side/back representative poses pass article-identity guardrails.
At gameplay footprint the two pants read as long paired garments, the two
shorts terminate clearly higher, and the two skirts remain unified masses.

This is not runtime evidence. Back stride, sitting, riding, and tool poses may
still expose leg swaps, gaps, or detachment. All six remain `EXPERIMENTAL`.
The four direction blocks also produce a large 192×5504 atlas per appearance;
that is acceptable for this diagnostic milestone, not yet a production memory
decision.

