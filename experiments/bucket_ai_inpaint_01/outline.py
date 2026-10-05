"""Vanilla-structured, palette-derived outline repair on the merged core cuts.

Vanilla Bucket Hat front is used ONLY for structure: its outline pixels (the darkest
ramp step, 34 px: external contour, 1 px, continuous) say WHERE an outline goes and
the vanilla hats.png corpus says HOW dark and how much hue shift. The colour comes
from each hat's own nearby body colour. At most 2
outline colours per hat. AI pixels already at least that dark are kept. Nothing
outside the core and no interior boundary is touched. Writes outlined_*.png; the
merged_*.png inputs are never modified.

  python3 outline.py <merged_hat_1x.png> [...]
"""
import colorsys, sys
from collections import Counter
from PIL import Image
core = Image.open('pixellab/mask_exact_1x.png').convert('L').load()
van = Image.open('v3/vanilla_worn.png').convert('RGB').resize((64, 64), Image.NEAREST).load()
CORE = [(x, y) for y in range(64) for x in range(64) if core[x, y]]
lum = lambda c: 0.299*c[0] + 0.587*c[1] + 0.114*c[2]
GREY = lambda c: max(c) - min(c) < 12          # vanilla hat ramp is neutral grey
OUTLINE_C = min((van[p] for p in CORE if GREY(van[p])), key=lum)
OUTLINE = {p for p in CORE if van[p] == OUTLINE_C}
# vanilla contrast: outline luminance / mean luminance of its inward non-outline neighbours
_r = []
for (x, y) in OUTLINE:
    nb = [van[x+a, y+b] for a, b in ((1,0),(-1,0),(0,1),(0,-1)) if (x+a, y+b) in CORE and (x+a, y+b) not in OUTLINE and GREY(van[x+a, y+b])]
    if nb: _r.append(lum(OUTLINE_C) / (sum(map(lum, nb)) / len(nb)))
RATIO = sum(_r) / len(_r)

# Calibrated on the vanilla hats.png corpus (110 front frames, edge vs interior
# median luminance): dark bodies 0.38, mid 0.37, bright 0.35 (yellows ~0.30);
# bright coloured bodies hue-shift ~-23 deg toward red/purple, dark/mid ~0.
# The Bucket Hat's own 0.45 is a grey-on-grey value and too light for colour.
def darken(c):
    h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in c))
    L = lum(c)
    ratio = 0.38 if L < 90 else 0.37 if L < 140 else (0.30 if L > 170 else 0.35)
    shift = -23 * max(0.0, min(1.0, (L - 90) / 60)) if s > 0.25 else 0
    h = (h + shift / 360) % 1.0
    target = L * ratio / 255
    lo, hi = 0.0, l
    for _ in range(20):                         # find HLS lightness hitting target luminance
        mid = (lo + hi) / 2
        rgb = colorsys.hls_to_rgb(h, mid, s)
        if lum([v*255 for v in rgb]) > target*255: hi = mid
        else: lo = mid
    # vanilla outlines are deep and muted (corpus mustard outline: L~0.24, S~0.6):
    # a saturated red can hit the target luminance while staying vivid, so cap both
    return tuple(round(v*255) for v in colorsys.hls_to_rgb(h, min(lo, 0.30), min(s, 0.65)))

def repair(path):
    hat = Image.open(path).convert('RGBA'); hp = hat.load()
    inner = lambda p: hp[p][3] and p not in OUTLINE
    want = {}
    for (x, y) in OUTLINE:
        ring = [hp[x+a, y+b][:3] for b in range(-2, 3) for a in range(-2, 3)
                if (x+a, y+b) in CORE and inner((x+a, y+b))]
        if ring: want[(x, y)] = darken(Counter(ring).most_common(1)[0][0])
    # at most two outline colours per hat: snap to the two most common targets
    top = [c for c, _ in Counter(want.values()).most_common(2)]
    near = lambda c: min(top, key=lambda t: sum((a-b)**2 for a, b in zip(c, t)))
    changed = kept = 0
    for p, c in want.items():
        c = near(c)
        if hp[p][3] and lum(hp[p][:3]) <= lum(c) * 1.05: kept += 1; continue
        hp[p] = c + (255,); changed += 1
    out = path.replace('merged_', 'outlined_'); hat.save(out)
    return out, {'outline_px': len(OUTLINE), 'repainted': changed, 'ai_kept': kept, 'outline_colours': top}

if __name__ == '__main__':
    print('vanilla outline px', len(OUTLINE), 'colour', OUTLINE_C, 'ratio %.2f' % RATIO)
    for p in sys.argv[1:]: print(*repair(p))
