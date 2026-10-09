"""Normalise every source hat to a 4-view strip: front, right, left, back.

FS hats: per-direction StartingPosition/HatSize from hat.json (Flipped honoured,
Scale and colourable flag recorded).  CP/vanilla-format sheets: 20x80 cells,
rows down/right/left/up, empty cells skipped.  Analysis-only (PIL).
Writes data/hats/<id>.png (4 frames side by side, native pixels) + data/hats.json.
"""
import glob, hashlib, json, os, re, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from jsonl import load

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'data', 'hats')
AUTHOR_FIX = {"[FS] Kookoroo's 18 Hats": 'Kookoroo', '[FS] Cute beret hats': 'CuteBeret-35115'}
DIRS = [('front', 'FrontHat'), ('right', 'RightHat'), ('left', 'LeftHat'), ('back', 'BackHat')]

def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')[:60]

def crop(img, x, y, w, h):
    """Crop, zeroing RGB under alpha 0 so hidden colour never splits identical art."""
    f = img.crop((x, y, x + w, y + h))
    px = [(0, 0, 0, 0) if a == 0 else (r, g, b, a) for r, g, b, a in f.get_flattened_data()]
    f.putdata(px)
    return f

def qkey(frames):
    """Pixel key tolerant of +-1 export rounding (seen in semi-transparent edges)."""
    return bytes(((v + 2) // 4) for f in frames for v in f.tobytes())

def same(fa, fb, tol=3):
    """Same art: identical alpha mask, colour within tol per channel."""
    for a, b in zip(fa, fb):
        for pa, pb in zip(a.get_flattened_data(), b.get_flattened_data()):
            if (pa[3] == 0) != (pb[3] == 0) or max(abs(x - y) for x, y in zip(pa, pb)) > tol:
                return False
    return True

def empty(im):
    return im.getextrema()[3][1] == 0

def save(rec, frames, recs, seen):
    w = max(f.width for f in frames if f); h = max(f.height for f in frames if f)
    strip = Image.new('RGBA', (w * 4, h))
    for i, f in enumerate(frames):
        if f: strip.paste(f, (i * w, 0))
    digest = hashlib.sha1(qkey([strip])).hexdigest()[:12]
    mask = hashlib.sha1(bytes(a > 0 for a in strip.getchannel('A').tobytes())).hexdigest()
    if any(same([strip], [o]) for o in seen.get(mask, [])):
        return
    seen.setdefault(mask, []).append(strip)
    rec['id'] = f"{slug(rec['author'])}__{slug(rec['name'])}__{digest[:6]}"
    rec['frame'] = [w, h]
    rec['missing'] = [d for (d, _), f in zip(DIRS, frames) if not f or empty(f)]
    strip.save(os.path.join(OUT, rec['id'] + '.png'))
    recs.append(rec)

def fs_hats(inv, recs, seen):
    for it in inv['items']:
        if it['kind'] != 'hat': continue
        j = load(it['json'])
        png = os.path.join(it['dir'], 'hat.png')
        if not os.path.exists(png):
            pngs = [p for p in it['pngs'] if 'mask' not in p.lower()]
            if not pngs: continue
            png = os.path.join(it['dir'], pngs[0])
        img = Image.open(png).convert('RGBA')
        frames, scale, colourable, flags, head = [], set(), False, {}, {}
        for d, key in DIRS:
            m = j.get(key)
            if not m: frames.append(None); continue
            sp, sz = m.get('StartingPosition', {}), m.get('HatSize', {})
            f = crop(img, sp.get('X', 0), sp.get('Y', 0), sz.get('Width', 20), sz.get('Length', 20))
            if m.get('Flipped'): f = f.transpose(Image.FLIP_LEFT_RIGHT); flags[d] = 'flipped'
            frames.append(f)
            hp = m.get('HeadPosition', {}); head[d] = [hp.get('X', 0), hp.get('Y', 0)]
            scale.add(m.get('Scale', 4))
            colourable |= not m.get('DisableGrayscale', False)
            if m.get('HideHair'): flags['hideHair'] = True
            if d == 'front':
                layers = [{'name': 'mask', 'values': m['ColorMasks']}] if m.get('ColorMasks') else []
                layers += [{'name': l.get('Name', ''), 'values': l.get('Values', [])}
                           for l in m.get('ColorMaskLayers', []) if not l.get('IgnoreUserColorChoice')]
                flags['colorMaskLayers'] = layers
        if not any(frames): continue
        save({'author': AUTHOR_FIX.get(it['pack'], it['author']), 'pack': it['pack'], 'name': it['name'] or os.path.basename(it['dir']),
              'format': 'fs', 'scale': sorted(scale), 'colourable': colourable, 'flags': flags, 'head': head,
              'src': png}, frames, recs, seen)

def sheet_cells(path):
    img = Image.open(path).convert('RGBA')
    cols, rows = img.width // 20, img.height // 80
    for r in range(rows):
        for c in range(cols):
            frames = [crop(img, c * 20, r * 80 + i * 20, 20, 20) for i in range(4)]
            if not all(empty(f) for f in frames):
                yield r * cols + c, frames

def sheet_hats(specs, recs, seen):
    """A full vanilla-sheet replacement (240px wide) repaints only some hats and
    keeps ConcernedApe's art for the rest.  A cell that is pixel-identical at the
    same index in replacement sheets by two different authors is vanilla art."""
    cells = []
    for spec in specs:
        for p in sorted(glob.glob(spec['glob'])):
            full = Image.open(p).width == 240
            for idx, frames in sheet_cells(p):
                key = qkey(frames)
                cells.append((spec, p, idx, frames, key, full))
    def vanilla(c):
        spec, _, idx, frames, _, full = c
        return full and any(o[5] and o[2] == idx and o[0]['author'] != spec['author'] and same(frames, o[3])
                            for o in cells)
    for c in cells:
        spec, p, idx, frames, key, full = c
        author, pack = spec['author'], spec['pack']
        if vanilla(c):
            author, pack = 'ConcernedApe', 'vanilla (inferred: unchanged in 2+ replacement sheets)'
        name = f'{os.path.splitext(os.path.basename(p))[0]}_{idx}'
        save({'author': author, 'pack': pack, 'name': name, 'format': 'sheet', 'scale': [4],
              'colourable': False, 'flags': {}, 'src': p, 'cell': idx}, frames, recs, seen)

def main():
    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(os.path.join(OUT, '*.png')): os.remove(f)
    inv = json.load(open(os.path.join(HERE, 'data', 'inventory.json')))
    recs, seen = [], {}
    fs_hats(inv, recs, seen)
    sheet_hats(json.load(open(os.path.join(HERE, 'data', 'sheet_sources.json'))), recs, seen)
    json.dump(recs, open(os.path.join(HERE, 'data', 'hats.json'), 'w'), indent=1)
    from collections import Counter
    for (a, p), n in sorted(Counter((r['author'], r['pack']) for r in recs).items()): print(f'{n:4d} {a[:24]:24s} {p}')
    print('hats', len(recs), '| non-4x scale', sum(r['scale'] != [4] for r in recs),
          '| missing views', sum(bool(r['missing']) for r in recs), '| colourable', sum(r['colourable'] for r in recs))

if __name__ == '__main__':
    main()
