# Slouch Beanie Generator Spec

Status: roll matrix ready; construction art pending final fit/style pass.

## Frozen construction reference

PixelLab 24px multi-direction object is frozen as **construction reference only**:
`experiments/slouch_beanie_compare/pixellab/pl_24_sheet.png`

Cardinal source frames: Front 0, Right 2, Back 4, Left 6.
Use it for slouch angle, backward drape, band placement, silhouette family, and view coherence. Do not inherit its final outline, shading, polish, or current live-QC size.

Final art must use the accepted generator beanie outline/shading language and a slightly smaller wearable construction.

## Generator matrix

Canonical machine-readable matrix:
`generator/data/headwear/slouch_beanie_roll_matrix.json`

Axes cover presentation lean (soft preference only), slouch depth, cuff/band, drape, crown, opening fit, knit structure, pattern, motif, decoration style, motif placement, and palette ordering.

Presentation lean is never a hard gender lock. Neutral, masculine-leaning, and feminine-leaning settings only modify roll preference.

## Exclusion policy

Invalid combinations are rejected by compatibility rules, including cuff placements on cuffless hats, unstable motifs on extra slouch folds, cable/chunky conflicts with dense surface patterns, placement restrictions for patches/labels, and geometry conflicts between extreme slouch/crown/opening choices.

Validation: `python3 tools/validate_slouch_beanie_roll_matrix.py`
