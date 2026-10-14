"""REFERENCE-BASED fronts (method B, user request 2026-10-14): the same two designs (T1 tall floppy / P2 classic
pointed) built from REAL reference pixels instead of hand-drawn ones.  AI-ORIGINAL experiment (CLAUDE.md s2b),
personal use; reference packs are read-only and only read here.

  T1r  crown = Kailey '[FS] Witch Hats' Witch Hat (Blue) front rows 1-7, MIRRORED (its tip hooks right -> flops left)
       band + brim = Naver 492815 'Witch Hat_10' front rows 7-14 (gull-wing brim, band ends dropping)
  P2r  crown = vanilla Witch Hat (hats.png slot 70, ConcernedApe) front rows 0-5 (straight cone, crooked tip)
       band + brim = the same Naver rows 6-14
Every source colour is mapped to ONE target ramp by its role in its own pack (outline / shade / base / light /
band shade / band light), so the result has a single consistent palette.  Edits after composition are listed
explicitly in EDITS (none hidden).  Row 0 = top; the brim wings end on row 14 (Naver's seating).
Analysis-side tool (.venv PIL for reading the sources); the PNGs are written dependency-free.
usage: python refbased.py -> out/fronts/{T1r,P2r}.png + out/refbased.json"""
import json, os, sys
from pathlib import Path
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); EXP = os.path.dirname(HERE); ROOT = os.path.dirname(EXP)
sys.path.insert(0, ROOT)
from generator import png_utils as P
VAN = '/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/hats.png'
R = json.load(open(os.path.join(EXP, 'witch_silhouette_matrix_01', 'out', 'refs.json')))
TARGET = {'o': (40, 26, 60), 's': (64, 44, 96), 'b': (88, 64, 128), 'l': (118, 92, 162), 'g': (176, 126, 64), 'Y': (228, 188, 112)}
# role of every source colour (by eye on the pixel dumps, 2026-10-14)
ROLE = {
    'kailey': {(7, 7, 10): 'o', (23, 25, 29): 's', (30, 32, 35): 'b'},
    'naver': {(37, 87, 116): 'o', (44, 106, 141): 's', (79, 127, 154): 'b', (179, 137, 105): 'g', (200, 166, 140): 'Y'},
    'vanilla': {(16, 16, 16): 'o', (44, 38, 56): 's', (66, 57, 73): 'b', (97, 83, 99): 'l'},
}


def front(pack, name):
    r = next(r for r in R if r['pack'] == pack and r['name'] == name); x, y, w, h, _ = r['views']['F']
    return Image.open(os.path.join(EXP, r['dir'], 'hat.png')).convert('RGBA').crop((x, y, x + w, y + h)), r['dir']


def rows_of(img, role, mirror=False):
    out = []
    for y in range(img.size[1]):
        row = ''
        for x in range(img.size[0]):
            p = img.getpixel((img.size[0] - 1 - x if mirror else x, y))
            row += '.' if p[3] == 0 else role.get(p[:3], '?')          # '?' = colour outside the used rows
        out.append(row)
    return out


def build():
    kai, kdir = front('Kailey', 'Witch Hat (Blue)'); nav, ndir = front('Naver', 'Witch Hat_10')
    van = Image.open(VAN).convert('RGBA').crop((200, 400, 220, 420))
    K, N, V = rows_of(kai, ROLE['kailey'], mirror=True), rows_of(nav, ROLE['naver']), rows_of(van, ROLE['vanilla'])
    blank = '.' * 20
    T1 = K[1:8] + N[7:15] + [blank] * 5          # Kailey crown rows 1-7 -> 0-6; Naver band/brim rows 7-14
    P2 = V[0:6] + N[6:15] + [blank] * 5          # vanilla crown rows 0-5; Naver rows 6-14
    src = {'T1r': [f'rows 0-6: Kailey Witch Hat (Blue) front rows 1-7 mirrored ({kdir})', f'rows 7-14: Naver Witch Hat_10 front rows 7-14 ({ndir})'],
           'P2r': ['rows 0-5: vanilla Witch Hat front rows 0-5 (Content/Characters/Farmer/hats.png slot 70)', f'rows 6-14: Naver Witch Hat_10 front rows 6-14 ({ndir})']}
    return {'T1r': T1, 'P2r': P2}, src


# explicit post-composition edits: (key, x, y, role, why)
EDITS = []   # none: the composites are used as composed (a trial edit at T1r (4,6) left a detached pixel; removed)


def main():
    G, src = build(); meta = {}
    for k, x, y, role, why in EDITS:
        r = list(G[k][y]); r[x] = role; G[k][y] = ''.join(r)
    os.makedirs(os.path.join(HERE, 'out', 'fronts'), exist_ok=True)
    for k, rows in G.items():
        assert len(rows) == 20 and all(len(r) == 20 and '?' not in r for r in rows), (k, rows)
        P.write_rgba_png(Path(HERE) / 'out' / 'fronts' / f'{k}.png', [[(0, 0, 0, 0) if c == '.' else TARGET[c] + (255,) for c in r] for r in rows])
        meta[k] = {'grid': rows, 'sources': src[k], 'edits': [e[1:] for e in EDITS if e[0] == k], 'tag': 'AI-ORIGINAL (reference-based composite)',
                   'palette': TARGET}
        print(k); print('\n'.join(rows[:15]))
    json.dump(meta, open(os.path.join(HERE, 'out', 'refbased.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
