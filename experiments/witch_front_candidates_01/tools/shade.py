"""Mask -> shaded RGBA sprite with one neutral palette (shape study).  Outline = body pixel with an empty
4-neighbour; interior shaded by horizontal position in its row run (light upper-left).  Bottom of every
silhouette is placed on row 13 of the frame (vanilla witch brim ends at row 12, ref 492815 at 14).
Dependency-free (generator/png_utils).  usage: python3 -I shade.py -> out/fronts/*.png + out/fronts.json"""
import json, os, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE / 'tools')); sys.path.insert(0, str(ROOT))
import masks
from generator import png_utils as P
PAL = {'0': (24, 18, 36), '1': (46, 34, 72), '2': (70, 54, 104), '3': (98, 80, 140), '5': (214, 168, 70), '6': (150, 108, 44)}
BOTTOM = 13


def grid(txt):
    rows = txt.strip('\n').split('\n'); W = len(rows[0]); assert all(len(r) == W for r in rows), txt
    H = 20
    return [r for r in ['.' * W] * (BOTTOM + 1 - len(rows)) + rows] + ['.' * W] * (H - BOTTOM - 1), W, H


def shade(rows, W, H):
    on = lambda x, y: 0 <= x < W and 0 <= y < H and rows[y][x] != '.'
    out = [['.'] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if not on(x, y): continue
            if not all(on(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))): out[y][x] = '0'; continue
            l = x
            while on(l - 1, y): l -= 1
            r = x
            while on(r + 1, y): r += 1
            t = (x - l) / max(1, r - l)
            if rows[y][x] == 'c': out[y][x] = '1'; continue
            if rows[y][x] == 'b': out[y][x] = '6' if t > 0.75 else '5'
            else: out[y][x] = '3' if t < 0.3 else ('1' if t > 0.72 else '2')
    return [''.join(r) for r in out]


if __name__ == '__main__':
    (HERE / 'out' / 'fronts').mkdir(parents=True, exist_ok=True); meta = {}
    for name, txt in masks.C.items():
        rows, W, H = grid(txt); s = shade(rows, W, H); key = name.split()[0]
        P.write_rgba_png(HERE / 'out' / 'fronts' / f'{key}.png', [[(0, 0, 0, 0) if c == '.' else PAL[c] + (255,) for c in r] for r in s])
        meta[key] = {'name': name, 'size': [W, H], 'fits_20x20': W <= 20 and H <= 20, 'grid': s}
    json.dump(meta, open(HERE / 'out' / 'fronts.json', 'w'), indent=1); print({k: v['size'] for k, v in meta.items()})
