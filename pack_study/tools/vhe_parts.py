"""Turn reviewed VHE splits into decoration records (data/vhe/decorations.json).

Same record format as data/decorations.json, so gen/decorate.py places them unchanged:
per view, the part's pixels in frame coords + the mask of what it sits on (baseMask).

    python3 pack_study/tools/vhe_parts.py "<unzipped Hat Version dir>"

Each split is built from vanilla (ConcernedApe) and the VHE Alt, aligned per view:
  removal  part = vanilla minus Alt   (vanilla pixels; it sat on the Alt remainder)
  invert   part = the Alt itself      (unchanged vanilla pixels; sat on vanilla minus Alt)
           -- Propeller Hat Alt keeps the propeller and drops the cap
  addon    part = Alt pixels outside vanilla or changed over it (Tea-Loving Lad; sat on vanilla)
Which splits exist, and what each is, was decided by eye on out/vhe_parts.png; the
approvals themselves live in data/decorations_approved.json (keys 'vhe__...').
"""
import json, os, re, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vanilla import load_vanilla
from vhe_study import load_fs, align, mask

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = ['front', 'right', 'left', 'back']

# folder in VHE -> (how, vanilla index); vanilla index from data/vhe/items.json
SPLITS = {
    "Knight's Helmet Alt": 'removal', "Squire's Helmet Alt": 'removal', 'Infinity Crown Alt': 'removal',
    'Red Party Hat Alt': 'removal', 'Blue Party Hat Alt': 'removal', 'Green Party Hat Alt': 'removal',
    'Propeller Hat Alt': 'invert', 'Hard Hat Alt': 'addon', 'Tricorn Hat Alt': 'addon',
    # headpieces: worn on the head, not perched on a hat (kind 'headpiece')
    'Cat Ears Alt 1': 'removal', 'Cat Ears Alt 2': 'removal', 'Totem Mask Alt': 'removal+invert',
}


def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')


def record(key, author, base_name, from_name, part_m, src, base_m):
    views = {}
    for k, v in enumerate(VIEWS):
        sl = slice(k * 20, (k + 1) * 20)
        ys, xs = np.nonzero(part_m[:, sl])
        views[v] = {'pixels': [[int(x), int(y), [int(c) for c in src[y, k * 20 + x]]] for y, x in zip(ys, xs)],
                    'baseMask': base_m[:, sl].astype(int).tolist()}
    return {'id': key, 'author': author, 'frame': [20, 20], 'base': base_name, 'from': key + '__vhe',
            'baseName': base_name, 'fromName': from_name, 'px': int(part_m.sum()), 'views': views}


def main():
    hats = load_fs(sys.argv[1], 'hat')
    van = load_vanilla()
    items = {i['folder']: i for i in json.load(open(os.path.join(HERE, 'data', 'vhe', 'items.json')))
             if i['version'] == 'hat'}
    out = []
    for folder, how in SPLITS.items():
        vi = items[folder]['vanilla']['index']
        alt = hats[folder]['arr']
        base, _ = align(van[vi]['arr'], alt)              # vanilla moved onto the Alt, per view
        ma, mv = mask(alt), mask(base)
        vname = van[vi]['name']
        if 'removal' in how:
            out.append(record(f'vhe__{slug(folder)}__removed', 'ConcernedApe', folder, vname,
                              mv & ~ma, base, ma))
        if 'invert' in how:
            out.append(record(f'vhe__{slug(folder)}__kept', 'ConcernedApe',     # kept Alt pixels are unchanged vanilla art
                              f'{vname} minus {folder}', folder, ma, alt, mv & ~ma))
        if how == 'addon':
            # painted over the base counts too (a lamp on the crown's front face lies inside the mask)
            over = ma & mv & (np.abs(alt - base).max(axis=2) > 3)
            out.append(record(f'vhe__{slug(folder)}__added', 'Tea-Loving Lad', vname, folder, (ma & ~mv) | over, alt, mv))
    json.dump(out, open(os.path.join(HERE, 'data', 'vhe', 'decorations.json'), 'w'))
    for r in out:
        print(f"{r['id']:45s} {r['author']:15s} px={r['px']:3d} views={sum(bool(v['pixels']) for v in r['views'].values())}")


if __name__ == '__main__':
    main()
