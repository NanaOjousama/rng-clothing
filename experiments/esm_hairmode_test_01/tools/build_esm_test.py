"""ESM hair-mode test (user, 2026-10-13).  AI-ORIGINAL witch hats from lora_worn_test_01, worn through the
Enhanced Sewing Machine's real hat carrier ((H)RNGClothing.ESM.GeneratedHat), whose per-item hairDrawType comes
from the garment's HairMode (GarmentItemService.Write: Obscured -> 1 = vanilla covered hair).

Builds 4 TEMPORARY garments (no redesign: the exact round-2 sprites of lora_worn_test_01):
  exp.lw01.witch_s8.full / .covered, exp.lw01.witch_s9.full / .covered
Placement = the vanilla reference garment (qc/vanilla_trucker16: 20x20, RenderScale 1, anchor (10,16)),
i.e. vanilla hat placement, the same spot FS uses for a 20x20 hat at HeadPosition 0.

The repo's mods/EnhancedSewingMachine (source, garment index) is NOT touched.  --install stages a copy of the
packaged ESM build (bin/Release/net6.0/EnhancedSewingMachine 0.0.1.zip) into the game's Mods folder with an
index.json that registers ONLY these 4 test garments.  Undo: delete Mods/EnhancedSewingMachine.
usage: python3 -I build_esm_test.py [--install]"""
import json, shutil, sys, zipfile
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; ROOT = HERE.parents[1]
SRC = ROOT / 'experiments' / 'lora_worn_test_01' / 'out' / 'pack' / '[FS] LoRA Worn Test 01' / 'Hats'
ZIP = ROOT / 'mods' / 'EnhancedSewingMachine' / 'bin' / 'Release' / 'net6.0' / 'EnhancedSewingMachine 0.0.1.zip'
MODS = Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods')
HATS = {'witch_s8': 'LW01 01 Witch s8', 'witch_s9': 'LW01 02 Witch s9'}
MODES = {'full': 'Full', 'covered': 'Obscured'}
VIEW_Y = {'Front': 0, 'Right': 20, 'Left': 40, 'Back': 60}     # lora_worn_test_01 strip order: front|right|left|back


def garments():
    out = []
    for key, folder in HATS.items():
        for tag, mode in MODES.items():
            gid = f'exp.lw01.{key}.{tag}'
            out.append((gid, key, folder, {
                'Id': gid, 'Category': 'Hat', 'DefinitionVersion': 1,
                'WornTexture': f'assets/experiments/esm_hairmode_test_01/{key}.png',
                'FrameWidth': 20, 'FrameHeight': 20, 'RenderScale': 1.0,
                'VanillaReferenceAnchor': {'X': 10, 'Y': 16}, 'HairMode': mode,
                'Directions': {v: {'SourceX': 0, 'SourceY': y, 'AnchorX': 10, 'AnchorY': 16, 'OffsetX': 0, 'OffsetY': 0}
                               for v, y in VIEW_Y.items()},
                'Metadata': {'Family': 'witch_hat', 'Construction': f'lora_worn_test_01/{key}', 'Material': 'AI-ORIGINAL',
                             'Palette': '', 'Motif': '', 'GeneratorId': 'esm_hairmode_test_01', 'GeneratorVersion': 1,
                             'GeneratorSeed': 0, 'Style': f'hairmode-test,{tag}', 'QualityTier': 'QC', 'Decals': '',
                             'Classification': 'EXPERIMENT_ONLY'}}))
    return out


def main():
    out = HERE / 'out'; (out / 'garments').mkdir(parents=True, exist_ok=True); (out / 'textures').mkdir(exist_ok=True)
    gs = garments()
    for key, folder in HATS.items(): shutil.copyfile(SRC / folder / 'hat.png', out / 'textures' / f'{key}.png')
    for gid, key, folder, d in gs: json.dump(d, open(out / 'garments' / f'{gid}.json', 'w'), indent=2)
    print('built', [g[0] for g in gs])
    if '--install' not in sys.argv: return
    tgt = MODS / 'EnhancedSewingMachine'
    if tgt.exists() and not (tgt / '.esm_hairmode_test_01').exists():
        sys.exit(f'{tgt} exists and was not staged by this experiment; refusing to overwrite')
    if not tgt.exists():
        with zipfile.ZipFile(ZIP) as z: z.extractall(MODS)
        assert (tgt / 'manifest.json').exists(), 'zip layout changed'
        (tgt / '.esm_hairmode_test_01').write_text('staged by experiments/esm_hairmode_test_01; safe to delete\n')
    tex = tgt / 'assets' / 'experiments' / 'esm_hairmode_test_01'; tex.mkdir(parents=True, exist_ok=True)
    gdir = tgt / 'assets' / 'garments' / 'experiments'; gdir.mkdir(parents=True, exist_ok=True)
    for key in HATS: shutil.copyfile(out / 'textures' / f'{key}.png', tex / f'{key}.png')
    for gid, *_ in gs: shutil.copyfile(out / 'garments' / f'{gid}.json', gdir / f'{gid}.json')
    json.dump({'Garments': [f'experiments/{gid}.json' for gid, *_ in gs]}, open(tgt / 'assets' / 'garments' / 'index.json', 'w'), indent=2)
    print('installed ->', tgt)


if __name__ == '__main__':
    main()
