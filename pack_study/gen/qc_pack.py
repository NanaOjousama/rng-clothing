"""Small in-game QC pack with self-describing names.  Pure Python.

Picks one generated hat per thing that still needs a worn check, from the roll logs
of generate.py runs, and copies it under a name that says what to look at:
    PSQC 03 bird above frame (cottage)
All names start with "PSQC" so they sort together in the Fashion Sense list.
usage: qc_pack.py <out_dir_with_roll_logs> <dest_parent_dir>
  -> <dest>/[FS] PackStudy QC/  + qc_index.json (what each hat tests)"""
import glob, json, os, shutil, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (tag, test) -> first log row that matches.  Order = numbering in game.
CASES = [
    ('baseline', 'common author recolour, no add-ons (reference)',
     lambda l, j: l['tier'] == 'common' and not l['decoration']),
    ('above-frame', 'decoration rises above the 20px frame: HatSize + HeadPosition.Y grown (FS source says OK, never worn)',
     lambda l, j: l['decoration'] and j['pad'] > 0),
    ('above-frame', 'second above-frame case, different part',
     lambda l, j: l['decoration'] and j['pad'] > 0),
    ('tassel tuft', 'tied tassel tuft on a tapered host',
     lambda l, j: l['decoration'] and 'tuft' in l['decoration']['label']),
    ('band', 'transferred hat band at the crown/brim junction',
     lambda l, j: l['decoration'] and 'band' in l['decoration']['label']),
    ('sprig', 'leaf sprig on an in-family host',
     lambda l, j: l['decoration'] and l['decoration']['label'] == 'leaf sprig'),
    ('ribbon', 'cockade ribbon on a dress/western hat',
     lambda l, j: l['decoration'] and l['decoration']['label'] == 'ribbon'),
    ('novelty', 'intentional off-family novelty decoration',
     lambda l, j: l['decoration'] and l['decoration']['novelty']),
    ('plaid', 'transferred CuteBeret plaid',
     lambda l, j: bool(l.get('pattern'))),
    ('combo', 'cross-author crown x brim',
     lambda l, j: l['tier'] == 'combined'),
    ('restyle', 'shape from one author, shading from another',
     lambda l, j: l['tier'] == 'restyled'),
]


def main():
    src, dest = sys.argv[1], sys.argv[2]
    rows = []
    for f in sorted(glob.glob(os.path.join(src, 'roll_log_s*.json'))):
        seed = f.rsplit('_s', 1)[1][:-5]
        pack = os.path.join(src, f'[FS] PackStudy Hats s{seed}')
        lib = {c['id']: c for c in json.load(open(os.path.join(HERE, 'data', 'library.json')))['constructions']}
        for l in json.load(open(f)):
            hd = os.path.join(pack, 'Hats', l['name'])
            j = json.load(open(os.path.join(hd, 'hat.json')))
            c = lib.get(l['construction'])
            pad = j['FrontHat']['HatSize']['Length'] - c['frame'][1] if c else 0
            rows.append((l, {'pad': pad}, hd))
    out = os.path.join(dest, '[FS] PackStudy QC')
    if os.path.exists(out): shutil.rmtree(out)
    os.makedirs(os.path.join(out, 'Hats'))
    json.dump({'Name': 'PackStudy QC', 'Author': 'pack_study generator', 'Version': '0.1.0',
               'Description': 'Worn-check hats from pack_study; names say what to look at',
               'UniqueID': 'PackStudy.QC', 'UpdateKeys': [],
               'ContentPackFor': {'UniqueID': 'PeacefulEnd.FashionSense'}},
              open(os.path.join(out, 'manifest.json'), 'w'), indent=2)
    used, index = set(), []
    for n, (tag, test, ok) in enumerate(CASES, 1):
        hit = next(((l, j, hd) for l, j, hd in rows if hd not in used and ok(l, j)
                    and not (tag == 'above-frame' and any(l['decoration'] and l['decoration']['label'] == i.get('decoration') for i in index if i['tag'] == 'above-frame'))), None)
        if hit is None:
            index.append({'n': n, 'tag': tag, 'missing': True}); continue
        l, j, hd = hit; used.add(hd)
        what = l['decoration']['label'] if l['decoration'] else (l.get('pattern') or l['tier'])
        host = ','.join(l['decoration']['host']) if l['decoration'] else l['author']
        what = {'common': 'baseline recolour', 'combined': 'crown x brim combo', 'restyled': 'restyle'}.get(what, what)
        if tag == 'above-frame': what += ' above frame'
        if l['decoration'] and l['decoration']['novelty']: what += ' NOVELTY'
        name = f"PSQC {n:02d} {what} ({host})"
        d = os.path.join(out, 'Hats', name.replace('/', '-'))
        shutil.copytree(hd, d)
        m = json.load(open(os.path.join(d, 'hat.json'))); m['Name'] = name
        json.dump(m, open(os.path.join(d, 'hat.json'), 'w'), indent=2)
        index.append({'n': n, 'tag': tag, 'name': name, 'test': test, 'source': l['name'], 'author': l['author'],
                      'construction': l['construction'], 'decoration': l['decoration'] and l['decoration']['label'],
                      'pattern': l.get('pattern'), 'padRows': j['pad']})
    json.dump(index, open(os.path.join(out, 'qc_index.json'), 'w'), indent=1)
    for i in index: print(i.get('name') or f"#{i['n']} {i['tag']}: NOT FOUND", '|', i.get('test', ''))


if __name__ == '__main__':
    main()
