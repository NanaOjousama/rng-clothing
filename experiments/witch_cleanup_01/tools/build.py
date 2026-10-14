"""Build the cleanup-pass textures (AI-ORIGINAL) from tools/grids.py.  20x80, views F|R|L|B at y 0/20/40/60
(same layout as lora_worn_test_01), L = R mirrored.  Dependency-free (generator/png_utils), no resampling.
usage: python3 -I build.py   -> out/textures/witch_s{8,9}_clean.png (renamed _v1/_v2 per round)"""
import os, sys
from pathlib import Path
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, 'tools')); sys.path.insert(0, ROOT)
import grids as G
from generator import png_utils as P


def strip(hat):
    rows = []
    for v in ('F', 'R', 'L', 'B'):
        g = G.V[hat]['R' if v == 'L' else v].strip('\n').split('\n')
        assert len(g) == 20 and all(len(r) == 20 for r in g), (hat, v)
        rows += [r[::-1] if v == 'L' else r for r in g]
    pal = G.PAL[hat]
    return [[(0, 0, 0, 0) if c == '.' else pal[c] + (255,) for c in r] for r in rows]


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'out', 'textures'), exist_ok=True)
    for hat in G.V:
        p = os.path.join(HERE, 'out', 'textures', f'{hat}_clean.png'); P.write_rgba_png(Path(p), strip(hat)); print(p)
