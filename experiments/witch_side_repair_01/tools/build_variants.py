"""Witch side-view repair variants (user, 2026-10-13).  AI-ORIGINAL; experiment only.
Front and Back views are the exact round-2 sprites (lora_worn_test_01); only Right is redrawn (grids.py) and Left is
its mirror.  Every variant is an ESM test garment with HairMode Obscured (vanilla covered hair).  Round 2 is kept as
variant 'orig' for comparison.  --install adds the garments to the STAGED ESM copy from esm_hairmode_test_01 (refuses
if that marker is missing) and never touches the repo's mods/EnhancedSewingMachine.
usage: python -I build_variants.py [--install]   (needs PIL: source tools/env.sh)"""
import json, shutil, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from grids import PAL, R
HERE = Path(__file__).resolve().parents[1]; ROOT = HERE.parents[1]
SRC = ROOT / 'experiments' / 'esm_hairmode_test_01' / 'out' / 'textures'
MODS = Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods')
VIEW_Y = {'Front': 0, 'Right': 20, 'Left': 40, 'Back': 60}


def grid_img(key, txt):
    rows = [r for r in txt.strip('\n').split('\n')]
    assert all(len(r) == 20 for r in rows), (key, [len(r) for r in rows])
    im = Image.new('RGBA', (20, 20), (0, 0, 0, 0))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != '.': im.putpixel((x, y), PAL[key][ch] + (255,))
    return im


def variants():
    out = {}
    for key in R:
        base = Image.open(SRC / f'{key}.png').convert('RGBA')
        out[(key, 'orig')] = base
        for v, txt in R[key].items():
            right = grid_img(key, txt); im = base.copy()
            im.paste(right, (0, 20)); im.paste(right.transpose(Image.FLIP_LEFT_RIGHT), (0, 40))
            out[(key, v)] = im
    return out


def garment(key, v):
    gid = f'exp.wsr01.{key}.{v}'
    return gid, {
        'Id': gid, 'Category': 'Hat', 'DefinitionVersion': 1,
        'WornTexture': f'assets/experiments/witch_side_repair_01/{key}_{v}.png',
        'FrameWidth': 20, 'FrameHeight': 20, 'RenderScale': 1.0,
        'VanillaReferenceAnchor': {'X': 10, 'Y': 16}, 'HairMode': 'Obscured',
        'Directions': {d: {'SourceX': 0, 'SourceY': y, 'AnchorX': 10, 'AnchorY': 16, 'OffsetX': 0, 'OffsetY': 0}
                       for d, y in VIEW_Y.items()},
        'Metadata': {'Family': 'witch_hat', 'Construction': f'lora_worn_test_01/{key} side-repair {v}', 'Material': 'AI-ORIGINAL',
                     'Palette': '', 'Motif': '', 'GeneratorId': 'witch_side_repair_01', 'GeneratorVersion': 1,
                     'GeneratorSeed': 0, 'Style': f'side-repair,{v},covered', 'QualityTier': 'QC', 'Decals': '',
                     'Classification': 'EXPERIMENT_ONLY'}}


def preview(vs, path, scale=12):
    keys = sorted({k for k, _ in vs}); names = ['orig'] + sorted({v for _, v in vs if v != 'orig'})
    sheet = Image.new('RGBA', (4 * 22 * len(keys) + 10, 22 * len(names)), (118, 146, 96, 255))
    for i, n in enumerate(names):
        for j, k in enumerate(keys):
            if (k, n) not in vs: continue
            im = vs[(k, n)]
            for d in range(4):
                sheet.alpha_composite(im.crop((0, 20 * d, 20, 20 * d + 20)), (j * (88 + 10) + d * 22, i * 22))
    sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST).save(path)


def main():
    vs = variants(); tex = HERE / 'out' / 'textures'; gdir = HERE / 'out' / 'garments'
    tex.mkdir(parents=True, exist_ok=True); gdir.mkdir(exist_ok=True)
    gs = []
    for (k, v), im in sorted(vs.items()):
        im.save(tex / f'{k}_{v}.png'); gid, d = garment(k, v); gs.append(gid)
        json.dump(d, open(gdir / f'{gid}.json', 'w'), indent=2)
    preview(vs, HERE / 'out' / 'sprites_x12.png')
    print('built', gs)
    if '--install' not in sys.argv: return
    tgt = MODS / 'EnhancedSewingMachine'
    if not (tgt / '.esm_hairmode_test_01').exists(): sys.exit('staged ESM test copy not found; refusing')
    t = tgt / 'assets' / 'experiments' / 'witch_side_repair_01'; t.mkdir(parents=True, exist_ok=True)
    g = tgt / 'assets' / 'garments' / 'experiments'; g.mkdir(parents=True, exist_ok=True)
    for (k, v) in vs: shutil.copyfile(tex / f'{k}_{v}.png', t / f'{k}_{v}.png')
    for gid in gs: shutil.copyfile(gdir / f'{gid}.json', g / f'{gid}.json')
    idx = tgt / 'assets' / 'garments' / 'index.json'; I = json.load(open(idx))
    I['Garments'] = sorted(set(I['Garments']) | {f'experiments/{gid}.json' for gid in gs}); json.dump(I, open(idx, 'w'), indent=2)
    print('installed ->', t)


if __name__ == '__main__':
    main()
