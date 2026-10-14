"""Comparison sheet: reference hats | the earlier candidates | the new hand-placed samples, at x10 (pixel grid),
x4 (= Stardew zoom 100%) and x1.  References are read-only (REFERENCE packs + vanilla hats.png).
Analysis only (.venv PIL).  usage: python sheet.py"""
import json, os
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); EXP = os.path.dirname(HERE)
VAN = '/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/hats.png'
BG, GRID, DARK = (122, 150, 100, 255), (108, 134, 88, 255), (30, 32, 40, 255)
R = json.load(open(os.path.join(EXP, 'witch_silhouette_matrix_01', 'out', 'refs.json')))


def ref(pack, name):
    r = next(r for r in R if r['pack'] == pack and r['name'] == name); x, y, w, h, _ = r['views']['F']
    return Image.open(os.path.join(EXP, r['dir'], 'hat.png')).convert('RGBA').crop((x, y, x + w, y + h))


def own(folder, key): return Image.open(os.path.join(EXP, folder, 'out', 'fronts', f'{key}.png')).convert('RGBA')


GROUPS = [('REFERENCE (read-only)', [('vanilla', Image.open(VAN).convert('RGBA').crop((200, 400, 220, 420))),
                                     ('Kailey', ref('Kailey', 'Witch Hat (Blue)')), ('Naver_1', ref('Naver', 'Witch Hat_1'))]),
          ('BEFORE (candidates_01)', [('T1', own('witch_front_candidates_01', 'T1')), ('P2', own('witch_front_candidates_01', 'P2'))]),
          ('A: hand-placed', [('T1d', own('witch_front_design_01', 'T1d')), ('P2d', own('witch_front_design_01', 'P2d'))]),
          ('B: reference-based', [('T1r', own('witch_front_design_01', 'T1r')), ('P2r', own('witch_front_design_01', 'P2r'))])]


def tile(sp, S, grid):
    t = Image.new('RGBA', (24, 20), BG)
    if grid:
        t = t.resize((24 * S, 20 * S), Image.NEAREST); d = ImageDraw.Draw(t)
        for i in range(25): d.line([(i * S, 0), (i * S, 20 * S)], fill=GRID)
        for i in range(21): d.line([(0, i * S), (24 * S, i * S)], fill=GRID)
        sp2 = Image.new('RGBA', (24, 20), (0, 0, 0, 0)); sp2.alpha_composite(sp, ((24 - sp.size[0]) // 2, 0))
        t.alpha_composite(sp2.resize((24 * S, 20 * S), Image.NEAREST)); return t
    t.alpha_composite(sp, ((24 - sp.size[0]) // 2, 0)); return t.resize((24 * S, 20 * S), Image.NEAREST)


def sheet(S, grid, out):
    gap, lab = 8, 16; tw, th = 24 * S, 20 * S
    W = 10 + sum(len(g) * (tw + gap) + 20 for _, g in GROUPS); H = 10 + 2 * lab + th + 10
    sh = Image.new('RGBA', (W, H), DARK); d = ImageDraw.Draw(sh); x = 10
    for title, items in GROUPS:
        d.text((x, 6), title, fill=(255, 220, 140))
        for k, sp in items:
            d.text((x, 6 + lab), k, fill=(230, 230, 230)); sh.paste(tile(sp, S, grid), (x, 6 + 2 * lab)); x += tw + gap
        x += 20
    sh.save(os.path.join(HERE, 'out', out)); print(out, sh.size)


sheet(10, True, 'compare_x10.png'); sheet(4, False, 'compare_x4_real.png'); sheet(1, False, 'compare_x1.png')
