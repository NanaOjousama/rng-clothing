"""Comparison sheet: the 8 fronts at x10 (pixel grid) and at real in-game size (x4 = Stardew zoom 100%, and x1),
vanilla Witch Hat front (hats_70) for scale.  Every tile is a 24x20 window, sprite centred on column 12
(20-wide sprites sit at x 2..21).  Analysis only (.venv PIL).  usage: python sheet.py"""
import json, os
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAN = '/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/hats.png'
BG, GRID, DARK = (122, 150, 100, 255), (108, 134, 88, 255), (30, 32, 40, 255)
meta = json.load(open(os.path.join(HERE, 'out', 'fronts.json')))
items = [('vanilla', 'Vanilla witch (scale)', Image.open(VAN).convert('RGBA').crop((10 * 20, 5 * 80, 11 * 20, 5 * 80 + 13)))]
items += [(k, v['name'][len(k) + 1:] + ('' if v['fits_20x20'] else f"  [{v['size'][0]}x{v['size'][1]}]"),
           Image.open(os.path.join(HERE, 'out', 'fronts', f'{k}.png')).convert('RGBA')) for k, v in meta.items()]


def tile(sp, S, grid):
    t = Image.new('RGBA', (24, 20), BG); t.alpha_composite(sp, ((24 - sp.size[0]) // 2, 0)); t = t.resize((24 * S, 20 * S), Image.NEAREST)
    if grid:
        d = ImageDraw.Draw(t)
        for i in range(25): d.line([(i * S, 0), (i * S, 20 * S)], fill=GRID)
        for i in range(21): d.line([(0, i * S), (24 * S, i * S)], fill=GRID)
        t.alpha_composite(Image.new('RGBA', (24 * S, 20 * S), (0, 0, 0, 0)))
        sp2 = Image.new('RGBA', (24, 20), (0, 0, 0, 0)); sp2.alpha_composite(sp, ((24 - sp.size[0]) // 2, 0))
        t.alpha_composite(sp2.resize((24 * S, 20 * S), Image.NEAREST))
        for x in (2 * S, 22 * S): d.line([(x, 0), (x, 20 * S)], fill=(160, 60, 60))  # 20-px frame edges
    return t


for S, grid, cols, name in ((10, True, 3, 'fronts_x10.png'), (4, False, 9, 'fronts_x4_real.png')):
    W, H = 24 * S + 10, 20 * S + 34; rows = (len(items) + cols - 1) // cols
    sh = Image.new('RGBA', (cols * W + 10, rows * H + 10), DARK); d = ImageDraw.Draw(sh)
    for i, (k, lab, sp) in enumerate(items):
        x, y = 10 + (i % cols) * W, 10 + (i // cols) * H
        d.text((x, y), f'{k}' if S == 4 else f'{k}  {lab}', fill=(230, 230, 230)); sh.paste(tile(sp, S, grid), (x, y + 16))
    if S == 4:  # x1 strip under the real-size row
        y = 10 + rows * H; sh2 = Image.new('RGBA', (sh.size[0], sh.size[1] + 40), DARK); sh2.paste(sh, (0, 0)); d = ImageDraw.Draw(sh2)
        d.text((10, y), 'x1 (raw pixels)', fill=(230, 230, 230))
        for i, (k, lab, sp) in enumerate(items): sh2.paste(tile(sp, 1, False), (130 + i * 30, y))
        sh = sh2
    sh.save(os.path.join(HERE, 'out', name)); print(name, sh.size)
