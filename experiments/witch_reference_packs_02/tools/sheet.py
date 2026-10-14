"""Zoomed study sheet: rows = hats (20x80 strips, F|R|L|B), nearest-neighbour block scale with a faint pixel grid.
usage: python sheet.py <out.png> <scale> <label=png> ...   (analysis only)"""
import sys
from PIL import Image, ImageDraw
out, S = sys.argv[1], int(sys.argv[2]); items = [a.split('=', 1) for a in sys.argv[3:]]
BG, GRID, PAD, LW = (122, 150, 100, 255), (108, 134, 88, 255), 6, 150
W = LW + 4 * (20 * S + PAD); H = len(items) * (20 * S + PAD) + PAD
sheet = Image.new('RGBA', (W, H), (30, 32, 40, 255)); d = ImageDraw.Draw(sheet)
for r, (lab, p) in enumerate(items):
    im = Image.open(p).convert('RGBA'); y = PAD + r * (20 * S + PAD); d.text((4, y + 4), lab, fill=(230, 230, 230, 255))
    for v in range(4):
        x = LW + v * (20 * S + PAD); tile = Image.new('RGBA', (20 * S, 20 * S), BG); td = ImageDraw.Draw(tile)
        for k in range(1, 20): td.line([(k * S, 0), (k * S, 20 * S)], fill=GRID); td.line([(0, k * S), (20 * S, k * S)], fill=GRID)
        spr = im.crop((0, 20 * v, 20, 20 * v + 20)).resize((20 * S, 20 * S), Image.NEAREST)
        tile.alpha_composite(spr); sheet.paste(tile, (x, y))
sheet.save(out); print(out, sheet.size)
