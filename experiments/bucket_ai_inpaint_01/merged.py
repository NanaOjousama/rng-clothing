"""Merged core + allowance cut, applied to every tool's outputs at 1x.

core      = true vanilla Bucket Hat footprint (worn vs policy mannequin). Shape is
            fixed: every core pixel is hat; the AI only chooses its colour.
allowance = core +1 game px ring. Decoration only: a ring pixel is kept when the AI
            changed it, it is not backdrop, and its colour is not near a common core
            colour, a core-edge (outline) colour or any mannequin colour -- i.e. not
            a bigger brim/outline and not a redrawn face -- and it is 4-connected
            to the hat. Heuristic; judge the sheet, not the rule.
"""
import json
from collections import Counter
from PIL import Image, ImageDraw
from sf_hat import align
BG = (196, 214, 188)
core = Image.open('pixellab/mask_exact_1x.png').convert('L').load()
ring_m = Image.open('pixellab/mask_loose_1x.png').convert('L').load()
man = Image.open('spritefusion/mannequin_1x.png').convert('RGBA')
manf = Image.new('RGBA', (64, 64), BG + (255,)); manf.alpha_composite(man); mp = manf.load()
MAN_COLOURS = {mp[x, y][:3] for y in range(64) for x in range(64)} - {BG}
vanilla = Image.open('v3/vanilla_worn.png').convert('RGBA').resize((64, 64), Image.NEAREST)

def rd_to_1x(p):  # 4x RD output -> 1x by block majority
    im = Image.open(p).convert('RGB'); ip = im.load(); g = Image.new('RGB', (64, 64)); gp = g.load()
    for by in range(64):
        for bx in range(64):
            gp[bx, by] = Counter(ip[bx*4+i, by*4+j] for j in range(4) for i in range(4)).most_common(1)[0][0]
    return g

def sf_to_1x(p):  # trimmed SF output -> placed on the mannequin grid
    out = Image.open(p).convert('RGBA')
    _, s, dx, dy, *_ = align(out, man, Image.open('pixellab/mask_exact_1x.png').convert('L'))
    g = manf.copy(); g.alpha_composite(out, (max(dx, 0), max(dy, 0)), (max(-dx, 0), max(-dy, 0)))
    return g.convert('RGB'), (dx, dy)

def cut(full):
    fp = full.load(); hat = Image.new('RGBA', (64, 64)); hp = hat.load()
    cpx = [(x, y) for y in range(64) for x in range(64) if core[x, y]]
    holes = 0
    for p in cpx:
        c = fp[p]
        if max(abs(a - b) for a, b in zip(c, BG)) <= 12 or c == mp[p][:3]: holes += 1
        hp[p] = c + (255,)
    freq = Counter(fp[p] for p in cpx)
    common = {c for c, n in freq.items() if n >= 0.15 * len(cpx)}
    # core edge = outline colours; mannequin colours = skin/hair/eyes the AI redrew
    edge = {fp[x, y] for (x, y) in cpx if any(not (0 <= x+a < 64 and 0 <= y+b < 64) or not core[x+a, y+b]
                                              for a, b in ((1,0),(-1,0),(0,1),(0,-1)))}
    body_like = common | edge | MAN_COLOURS
    near = lambda c: any(max(abs(a - b) for a, b in zip(c, k)) < 28 for k in body_like)
    deco = 0; grew = True
    cand = {(x, y) for y in range(64) for x in range(64) if ring_m[x, y] and not core[x, y]
            and fp[x, y] != mp[x, y][:3] and max(abs(a - b) for a, b in zip(fp[x, y], BG)) > 12
            and not near(fp[x, y])}
    while grew:  # keep only ring pixels connected to the hat
        grew = False
        for (x, y) in list(cand):
            if any(0 <= x+a < 64 and 0 <= y+b < 64 and hp[x+a, y+b][3] for a, b in ((1,0),(-1,0),(0,1),(0,-1))):
                hp[x, y] = fp[x, y] + (255,); cand.discard((x, y)); deco += 1; grew = True
    return hat, {'core_px': len(cpx), 'core_holes': holes, 'deco_px_kept': deco}

rows, report = [], {}
tools = {
  'Retro Diffusion': [(n, lambda n=n: rd_to_1x(f'v3/out_loose_{n}.png')) for n in ('olive', 'pink', 'denim')],
  'PixelLab': [(n, lambda n=n: Image.open(f'pixellab/out_loose_{n}.png').convert('RGB')) for n in ('mustard', 'gingham', 'mushroom')],
  'SpriteFusion': [(n, lambda n=n, v=v: sf_to_1x(f'spritefusion/{v}_{n}/output_00.png')[0])
                   for n, v in (('mustard', 'exact'), ('gingham', 'loose'), ('mushroom', 'loose'))]}
for tool, items in tools.items():
    cells = [('VANILLA (game)', vanilla, None)]
    for n, fn in items:
        try:
            full = fn()
        except FileNotFoundError:  # dropped inputs (e.g. SF gingham) are not committed
            continue
        hat, rep = cut(full); report[f'{tool}/{n}'] = rep
        hat.save(f'merged_{tool.split()[0].lower()}_{n}_1x.png')
        worn = manf.copy(); worn.alpha_composite(hat)
        cells.append((f'{n}  deco+{rep["deco_px_kept"]} holes {rep["core_holes"]}', worn, full))
    rows.append((tool, cells))
json.dump(report, open('merged_report.json', 'w'), indent=1); print(json.dumps(report, indent=1))
box, k = (21, 12, 43, 34), 12; tw = (box[2]-box[0])*k; th = (box[3]-box[1])*k
sh = Image.new('RGBA', (10 + 4*(tw+10) + 10, len(rows)*(2*th+50) + 10), (40, 40, 48, 255)); d = ImageDraw.Draw(sh)
for r, (tool, cells) in enumerate(rows):
    y0 = 10 + r*(2*th+50); d.text((10, y0), tool + '   (top: merged cut on mannequin   bottom: raw AI output)', fill='white')
    for c, (label, worn, full) in enumerate(cells):
        x = 10 + c*(tw+10); d.text((x, y0+14), label, fill=(220, 220, 220))
        sh.paste(worn.crop(box).resize((tw, th), Image.NEAREST), (x, y0+28))
        if full is not None: sh.paste(full.crop(box).resize((tw, th), Image.NEAREST), (x, y0+32+th))
sh.save('MERGED_CORE_ALLOWANCE_3TOOLS.png')
