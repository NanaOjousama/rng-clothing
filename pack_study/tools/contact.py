"""Contact sheets of normalised hats, grouped by a key (author by default).
usage: contact.py <out_dir> [group_key] [scale]  -> one PNG per group, 4 views per hat."""
import json, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def sheet(recs, scale=3, cols=6, bg=(118, 128, 112, 255)):
    cw, ch = 4 * 20 * scale + 8, 20 * scale + 14
    rows = (len(recs) + cols - 1) // cols
    im = Image.new('RGBA', (cols * cw, rows * ch), bg); d = ImageDraw.Draw(im)
    for i, r in enumerate(recs):
        s = Image.open(os.path.join(HERE, 'data', 'hats', r['id'] + '.png'))
        s = s.resize((s.width * scale, s.height * scale), Image.NEAREST)
        x, y = (i % cols) * cw, (i // cols) * ch
        im.alpha_composite(s, (x + 2, y + 12))
        d.text((x + 2, y), f"{i}:{r['name'][:22]}", fill=(255, 255, 255, 255))
    return im

if __name__ == '__main__':
    out, key = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else 'author')
    scale = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    os.makedirs(out, exist_ok=True)
    recs = json.load(open(os.path.join(HERE, 'data', 'hats.json')))
    groups = {}
    for r in recs: groups.setdefault(str(r.get(key)), []).append(r)
    for g, rs in groups.items():
        sheet(rs, scale).save(os.path.join(out, ''.join(c if c.isalnum() else '_' for c in g)[:40] + '.png'))
        print(len(rs), g)
