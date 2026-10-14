"""Variants next to the vanilla Witch Hat CONTROL (analysis, .venv PIL).  Each row: 4 views x6,
then 4 views at game scale x4 on grass, then x1 true size.  usage: control_sheet.py strips.json out.png [prev.json]"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '/run/media/deck/USD00/RNG_clothing/pack_study/tools'); import vanilla as V
rows = [('CONTROL vanilla Witch Hat', Image.fromarray(V.load_vanilla()[70]['arr'].astype(np.uint8), 'RGBA'))]
for f in sys.argv[3:]:
    for d in json.load(open(f)):
        a = np.array(d['strip'], np.uint8); rows.append((d['label'] if 'label' in d else 'PREV', Image.fromarray(a, 'RGBA')))
for d in json.load(open(sys.argv[1])):
    rows.append((d['design']['name'], Image.fromarray(np.array(d['strip'], np.uint8), 'RGBA')))
S, G = 6, 4; rh = 20 * S + 10; W = 250 + 4 * (20 * S + 6) + 14 + 4 * (20 * G + 4) + 14 + 4 * 22
img = Image.new('RGB', (W, rh * len(rows) + 6), (165, 165, 165)); d = ImageDraw.Draw(img)
for r, (name, im) in enumerate(rows):
    y0 = 4 + r * rh; d.text((4, y0 + 52), name[:40], fill=(0, 0, 0))
    for v in range(4):
        c = im.crop((v * 20, 0, v * 20 + 20, 20))
        big = c.resize((20 * S, 20 * S), Image.NEAREST); img.paste(big, (250 + v * (20 * S + 6), y0), big)
        x = 250 + 4 * (20 * S + 6) + 14 + v * (20 * G + 4)
        img.paste((96, 128, 72), (x, y0, x + 20 * G, y0 + 20 * G)); sm = c.resize((20 * G, 20 * G), Image.NEAREST); img.paste(sm, (x, y0), sm)
        x1 = 250 + 4 * (20 * S + 6) + 14 + 4 * (20 * G + 4) + 14 + v * 22
        img.paste((96, 128, 72), (x1, y0 + 30, x1 + 20, y0 + 50)); img.paste(c, (x1, y0 + 30), c)
img.save(sys.argv[2]); print(sys.argv[2], img.size)
