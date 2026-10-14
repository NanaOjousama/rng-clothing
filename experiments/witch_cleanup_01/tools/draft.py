"""Scratch renderer: grid text -> x10 preview with pixel grid (analysis only)."""
import sys
from PIL import Image, ImageDraw
sys.path.insert(0, sys.argv[1]); import grids as G
S = 10; out = sys.argv[2]; keys = sys.argv[3:]
tiles = []
for k in keys:
    hat, view = k.split(':'); pal = G.PAL[hat]; rows = G.V[hat][view].strip('\n').split('\n')
    assert all(len(r) == 20 for r in rows), [(i, len(r)) for i, r in enumerate(rows) if len(r) != 20]
    t = Image.new('RGBA', (20 * S, 20 * S), (122, 150, 100, 255)); d = ImageDraw.Draw(t)
    for i in range(1, 20): d.line([(i*S, 0), (i*S, 20*S)], fill=(108, 134, 88)); d.line([(0, i*S), (20*S, i*S)], fill=(108, 134, 88))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != '.': d.rectangle([x*S, y*S, x*S+S-1, y*S+S-1], fill=pal[ch])
    tiles.append(t)
sh = Image.new('RGBA', (len(tiles) * (20*S+6), 20*S), (30, 32, 40, 255))
for i, t in enumerate(tiles): sh.paste(t, (i * (20*S+6), 0))
sh.save(out)
