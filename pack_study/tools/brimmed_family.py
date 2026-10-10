"""List brimmed hats for the crown x brim study, by NAME evidence (author or vanilla
name says straw / sun hat / boater / cowboy / fedora / bowler / top hat / sombrero /
fishing / bucket / panama / witch hat -- gen/band.py BRIM_NAMES).  A width jump alone
does not prove a brim (CLAUDE.md s3).  One hat per library construction: recolours
share a shape and would only repeat combinations.  4 views required.
Writes data/brimmed_family_all.txt.  Pure Python.
"""
import json, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'gen'))
from band import BRIM_NAMES


def main():
    recs = {r['id']: r for r in json.load(open(os.path.join(HERE, 'data', 'hats.json')))}
    lib = json.load(open(os.path.join(HERE, 'data', 'library.json')))
    out = []
    for c in lib['constructions']:
        if c['missing']: continue
        src = c['colourways'][0]['source']
        names = c['names'] + [recs[w['source']].get('vanillaName') for w in c['colourways']]
        if any(BRIM_NAMES.search(n or '') for n in names):
            out.append(src)
    open(os.path.join(HERE, 'data', 'brimmed_family_all.txt'), 'w').write('\n'.join(out) + '\n')
    print(len(out), 'brimmed constructions by name')


if __name__ == '__main__':
    main()
