"""Group reference witch hats by FRONT alpha silhouette (exact mask) -> out/silhouettes.json, out/unique_fronts_x8.png.
Decoration/colour-only variants collapse into one silhouette group.  Analysis only."""
import json, os
from PIL import Image, ImageDraw
EXP = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
refs = json.load(open('out/refs.json')); groups = {}
for i, h in enumerate(refs):
    img = Image.open(os.path.join(EXP, h['dir'], 'hat.png')).convert('RGBA'); x, y, w, l, _ = h['views']['F']
    m = tuple(tuple(img.getpixel((x + a, y + b))[3] > 0 for a in range(w)) for b in range(l))
    groups.setdefault(m, []).append(i)
G = [{'members': v, 'names': [f"{refs[i]['pack']}:{refs[i]['name']}" for i in v]} for v in groups.values()]
json.dump(G, open('out/silhouettes.json', 'w'), indent=1, ensure_ascii=False)
S, T, cols = 8, 34, 4
sheet = Image.new('RGBA', (cols * (T * S + 8), (len(G) + cols - 1) // cols * (T * S + 30)), (30, 32, 40, 255)); d = ImageDraw.Draw(sheet)
for k, g in enumerate(G):
    h = refs[g['members'][0]]; img = Image.open(os.path.join(EXP, h['dir'], 'hat.png')).convert('RGBA'); x, y, w, l, hp = h['views']['F']
    tile = Image.new('RGBA', (T, T), (122, 150, 100, 255)); tile.alpha_composite(img.crop((x, y, x + w, y + l)), ((T - w) // 2, T - l - 2))
    X = (k % cols) * (T * S + 8); Y = (k // cols) * (T * S + 30)
    sheet.paste(tile.resize((T * S, T * S), Image.NEAREST), (X, Y + 26))
    d.text((X + 2, Y + 2), f"G{k:02d} {h['pack']}:{h['name'][:24]} x{len(g['members'])}  {w}x{l}", fill=(230, 230, 230))
sheet.save('out/unique_fronts_x8.png'); print(len(G), 'front silhouettes'); [print(f'G{k:02d}', g['names']) for k, g in enumerate(G)]
