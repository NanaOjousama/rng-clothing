"""Provenance proof sheets: SOURCE -> BASE -> EXTRACTED / RECOMBINED PARTS -> FINAL.
Analysis tool (PIL; needs `source tools/env.sh`).  Records come from gen/qc_replay.py or
gen/qc_v2.py (format: gen/provenance.py).
usage: provenance_sheet.py <records.json> <out_dir> [installed_pack_dir]
  -> <out_dir>/<hat name>.png, one per record, plus <out_dir>/index.png
  With installed_pack_dir, FINAL is also checked pixel-for-pixel against the hat.png in
  game (the proof is about the hat you actually wore) and the result printed on the sheet."""
import json, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 6                                    # pixel scale
BG, PANEL, INK, MARK = (58, 62, 70), (118, 128, 112), (235, 235, 225), (255, 0, 220)
TYPE_INK = {'recolor': (150, 210, 255), 'restyle': (255, 200, 120), 'attachment': (160, 240, 150),
            'structural combination': (255, 150, 150)}


def grid_img(rows, w, scale=S):
    """rows of RGBA tuples, 4 views side by side (each w wide) -> image with 4 px gaps."""
    h = len(rows); im = Image.new('RGBA', (4 * (w * scale + 4), h * scale), PANEL)
    for y in range(h):
        for x in range(4 * w):
            p = tuple(rows[y][x])
            if p[3]: im.paste(p, ((x // w) * 4 + x * scale, y * scale, (x // w) * 4 + (x + 1) * scale, (y + 1) * scale))
    return im


def hat_img(src_id):
    p = os.path.join(HERE, 'data', 'hats', f'{src_id}.png')
    if not src_id or not os.path.exists(p): return None
    s = Image.open(p).convert('RGBA'); w = s.width // 4
    rows = [[s.getpixel((x, y)) for x in range(s.width)] for y in range(s.height)]
    return grid_img(rows, w)


def extracted_img(part):
    """Source base silhouette (grey) + exactly the extracted part pixels, per view."""
    ex = part['extracted']; m0 = ex['front']['baseMask']; h, w = len(m0), len(m0[0])
    rows = [[(0, 0, 0, 0)] * (4 * w) for _ in range(h)]
    for vi, v in enumerate(['front', 'right', 'left', 'back']):
        m = ex[v]['baseMask']
        for y in range(h):
            for x in range(w):
                if m[y][x]: rows[y][vi * w + x] = (92, 92, 96, 255)
        for x, y, p in ex[v]['pixels']:
            if 0 <= y < h: rows[y][vi * w + x] = tuple(p)
    return grid_img(rows, w)


def changed_img(rec):
    """FINAL with every pixel that differs from BASE boxed in magenta."""
    b, f = rec['base'], rec['final']; w = rec['frame'][0]; pad = rec['padRows']
    im = grid_img(f, w); d = ImageDraw.Draw(im)
    for y in range(len(f)):
        for x in range(4 * w):
            q = tuple(b[y - pad][x]) if y >= pad else (0, 0, 0, 0)
            if tuple(f[y][x]) != q:
                X = (x // w) * 4 + x * S; d.rectangle([X, y * S, X + S - 1, y * S + S - 1], outline=MARK)
    return im


def check_installed(rec, pack):
    if not pack: return None
    p = os.path.join(pack, 'Hats', rec['name'], 'hat.png')
    if not os.path.exists(p): return 'not installed'
    im = Image.open(p).convert('RGBA'); w, h = rec['frame'][0], im.height // 4
    f = rec['final']; bad = 0
    for v in range(4):
        for y in range(h):
            for x in range(w):
                a, q = im.getpixel((x, v * h + y)), tuple(f[y][v * w + x])
                if (a[3] or q[3]) and a != q: bad += 1
    return 'installed hat.png == FINAL' if bad == 0 else f'MISMATCH vs installed: {bad} px'


def source_panels(rec, lib):
    """(caption, image) for the authored sources behind the hat."""
    out = []
    for p in rec['parts']:
        if p['role'] == 'host':
            c = lib[p['from']]
            src = (p.get('colour') or {}).get('from') or c['colourways'][0]['source']
            out.append((f"SOURCE host: {c['author']} / {', '.join(c['names'][:2])}  [{src}]", hat_img(src)))
        elif p['role'] in ('shape', 'shading ramp', 'crown', 'brim', 'style (outline/ramp)'):
            src = p['from']
            if p['role'] == 'shape' and src in lib: src = lib[src]['colourways'][0]['source']
            out.append((f"SOURCE {p['role']}: {src}", hat_img(src)))
        elif p['role'] == 'attachment':
            out.append((f"PART SOURCE hat: {p.get('fromName') or p['from']}  [{p['from']}]  (diffed against {p.get('sourceBase')})",
                        hat_img(p['from'])))
            out.append((f"EXTRACTED: '{p['label']}' ({p['kind']}) = grey source base + the part pixels exactly as placed", extracted_img(p)))
        else:
            out.append((f"{p['role'].upper()}: {p.get('label') or p.get('from')}", None))
    return out


def sheet(rec, lib, pack):
    t = rec['type']; w = rec['frame'][0]
    blocks = [(f"{rec['name']}", None, 'title'),
              (f"TYPE: {t}  --  {rec['subtype']}   |  author style: {rec['author']}   |  host construction: {rec['construction']}", None, 'type')]
    for cap, im in source_panels(rec, lib): blocks.append((cap, im, ''))
    if t in ('attachment',) or rec['diff']:
        blocks.append(("BASE: the host as rendered for this hat, before any part was added", grid_img(rec['base'], w), ''))
    blocks.append((f"FINAL (as written to hat.png): {rec['padRows']} row(s) grown above the frame", grid_img(rec['final'], w), ''))
    if rec['diff']:
        blocks.append((f"FINAL vs BASE: {rec['diff']} changed px boxed (must be the part, nothing else)", changed_img(rec), ''))
    if rec.get('v1'):
        blocks.append((f"v1 FINAL for comparison ({rec['v1']['name']}, the hat judged in game)", grid_img(rec['v1']['final'], w), ''))
    chk = check_installed(rec, pack)
    if chk: blocks.append((chk, None, 'check'))
    if rec.get('test'): blocks.append(("WORN TEST: " + rec['test'], None, 'check'))
    W = max([900] + [im.width + 20 for _, im, _ in blocks if im])
    H = 10 + sum(18 + (im.height + 8 if im else 0) for _, im, _ in blocks)
    out = Image.new('RGBA', (W, H), BG); d = ImageDraw.Draw(out); y = 8
    for cap, im, kind in blocks:
        ink = TYPE_INK.get(t, INK) if kind == 'type' else ((255, 120, 120) if 'MISMATCH' in cap else INK)
        d.text((10, y), cap, fill=ink); y += 18
        if im: out.paste(im, (10, y)); y += im.height + 8
    return out


def main():
    recs = json.load(open(sys.argv[1])); dest = sys.argv[2]; pack = sys.argv[3] if len(sys.argv) > 3 else None
    lib = {c['id']: c for c in json.load(open(os.path.join(HERE, 'data', 'library.json')))['constructions']}
    os.makedirs(dest, exist_ok=True)
    thumbs = []
    for r in recs:
        im = sheet(r, lib, pack)
        im.save(os.path.join(dest, r['name'].replace('/', '-') + '.png'))
        thumbs.append(im)
        print(r['name'], '|', r['type'], '|', check_installed(r, pack) or '')
    W = max(t.width for t in thumbs); H = sum(t.height + 6 for t in thumbs)
    idx = Image.new('RGBA', (W, H), (30, 30, 34)); y = 0
    for t in thumbs: idx.paste(t, (0, y)); y += t.height + 6
    idx.save(os.path.join(dest, 'index.png'))


if __name__ == '__main__':
    main()
