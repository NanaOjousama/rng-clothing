"""QC v2: the worn-QC failures of QC v1 rebuilt with the fixed primitives.  Pure Python.

Worn QC of v1 (user, 2026-10-10):
  PSQC 03 propeller above frame  PASS (golden reference)
  PSQC 02 / 06 leaf sprig        FAIL: hat seated, sprig floats      -> decorate.place_side
  PSQC 04 tied tassel tuft       FAIL: malformed on a flat beanie   -> fit='wrap'
  PSQC 05 band, 07 ribbon        acceptable
Leaf cases reuse the EXACT v1 host pixels (same hat, same colour, replayed from the v1
commit by qc_replay.py), so in game the only difference is the new seat.  The control
re-places the propeller on its v1 host with the current code and must be pixel-identical.
usage: qc_v2.py <v1_records.json> <dest_parent_dir> <records_out.json>
  -> <dest>/[FS] PackStudy QC v2/ (+ qc_index.json) and provenance records."""
import json, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(__file__))
import generate as G
import semantics as S
import provenance as PV
from decorate import load_approved, place, VIEWS
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (what, test, host, part key).  host = 'v1:<log name>' (v1 pixels) or a construction id.
CASES = [
    ('CONTROL propeller', 'golden v1 PSQC 03 re-placed by current code: must look identical', 'v1:PS1_58_rare', 'vhe__propeller_hat_alt__kept'),
    ('leaf sprig side seat', 'v1 PSQC 02 host (cat beanie): sprig tucked into the crown wall, touching it', 'v1:PS1_06_rare', 'seyph__hats_90'),
    ('leaf sprig side seat', 'v1 PSQC 06 host: sprig tucked into the crown wall, touching it', 'v1:PS1_04_rare', 'seyph__hats_90'),
    ('leaf sprig side seat NOVELTY', 'v1 PSQC 08 host (cap): sprig touching, a deliberate joke', 'v1:PS1_21_rare', 'seyph__hats_90'),
    ('leaf sprig side seat', 'preferred straw host, closest to the source Forager\'s Hat', 'family:straw', 'seyph__hats_90'),
    ('tied tassel tuft', 'tuft tied round a narrow party-hat tip (fit=wrap)', 'lovisity__c', 'vhe__green_party_hat_alt__removed'),
    ('tied tassel tuft', 'second narrow-tip host', 'concernedape__c', 'vhe__red_party_hat_alt__removed'),
]


def masks_of(px, w, h):
    return {v: [[1 if px[y][vi * w + x][3] else 0 for x in range(w)] for y in range(h)] for vi, v in enumerate(VIEWS)}


def put(px, res, w):
    pad = max([0] + [-y for v in VIEWS for _, y, _ in res[v]])
    out = [[(0, 0, 0, 0)] * (4 * w) for _ in range(pad)] + [list(r) for r in px]
    for vi, v in enumerate(VIEWS):
        for x, y, p in res[v]: out[y + pad][vi * w + x] = tuple(p)
    return out


def hosts_for(spec, dec, lib):
    """Fresh hosts: semantically kept constructions where the part seats."""
    cons = [c for c in lib['constructions'] if not c['missing'] and c['frame'][0] == dec['frame'][0]]
    cons.sort(key=lambda c: not G.eligible(c))       # generator-reachable hosts first
    for c in cons:
        fams = S.host_families(G.names_of(c), c['id'])
        if spec.startswith('family:') and spec[7:] not in fams: continue
        if not spec.startswith('family:') and not c['id'].startswith(spec): continue
        if S.weight(dec, fams) <= 0: continue
        yield c, fams


def main():
    v1 = {r['name']: r for r in json.load(open(sys.argv[1]))}
    dest, rec_out = sys.argv[2], sys.argv[3]
    lib = json.load(open(os.path.join(HERE, 'data', 'library.json')))
    cons = {c['id']: c for c in lib['constructions']}
    decs = {d['from'].rsplit('__', 1)[0]: d for d in load_approved()}
    out = os.path.join(dest, '[FS] PackStudy QC v2')
    if os.path.exists(out): shutil.rmtree(out)
    os.makedirs(os.path.join(out, 'Hats'))
    json.dump({'Name': 'PackStudy QC v2', 'Author': 'pack_study generator', 'Version': '0.2.0',
               'Description': 'Worn re-check of the QC v1 failures (leaf sprig, tassel tuft) + propeller control',
               'UniqueID': 'PackStudy.QC2', 'UpdateKeys': [],
               'ContentPackFor': {'UniqueID': 'PeacefulEnd.FashionSense'}},
              open(os.path.join(out, 'manifest.json'), 'w'), indent=2)
    index, records = [], []
    for n, (what, test, host, key) in enumerate(CASES, 1):
        dec = decs[key]
        if host.startswith('v1:'):
            r1 = v1[host[3:]]; c = cons[r1['construction']]
            w, h = c['frame']
            base = [list(map(tuple, row)) for row in r1['base']][len(r1['base']) - h:]   # v1 base never has pad rows
            fams = S.host_families(G.names_of(c), c['id'])
            colour, author = r1['row']['colour'], r1['author']
            res = place(dec, masks_of(base, w, h))
            novelty = S.weight(dec, fams) <= 0
        else:
            res = None
            for c, fams in hosts_for(host, dec, lib):
                w, h = c['frame']
                if G.eligible(c):
                    pal, colour = G.colourise(c, random.Random(n))
                else:                                # no proven recolour: the author's own colourway, untouched
                    pal = c['colourways'][0]['palette']
                    colour = {'mode': 'authored colourway (host not generator-eligible: primitive check only)',
                              'from': c['colourways'][0]['source']}
                base = G.render(c, pal, None, colour.get('tint') if c['colourable'] else None)
                res = place(dec, masks_of(base, w, h))
                if res: break
            author, novelty = c['author'], False
        if res is None:
            index.append({'n': n, 'what': what, 'test': test, 'missing': True, 'host': host}); continue
        final = put(base, res, w)
        hostname = ','.join(sorted(fams))
        if not G.eligible(c): what += ' PRIMITIVE ONLY'
        name = f"PSQC2 {n:02d} {what} ({hostname})"
        G.write_hat(os.path.join(out), name, c, final)
        row = {'name': name, 'tier': 'rare', 'author': author, 'construction': c['id'], 'colour': colour, 'addon': None,
               'pattern': None, 'decoration': {'label': dec['label'], 'novelty': novelty, 'host': sorted(fams), 'from': dec['from']}}
        rec = {'name': name, 'frame': [w, h], 'construction': c['id'], 'base': base, 'final': final}
        PV.finish(G, {name: rec}, row); rec['row'] = row; rec['test'] = test
        if host.startswith('v1:'): rec['v1'] = {'name': r1['name'], 'final': r1['final']}
        if what.startswith('CONTROL'):
            rec['controlIdentical'] = final == [list(map(tuple, r)) for r in r1['final']]
            print('control identical to v1:', rec['controlIdentical'])
            if not rec['controlIdentical']: sys.exit('CONTROL CHANGED: the propeller path was altered')
        records.append(rec)
        index.append({'n': n, 'name': name, 'test': test, 'type': rec['type'], 'subtype': rec['subtype'],
                      'host': c['id'], 'hostNames': c['names'][:2], 'author': author, 'part': dec['label'], 'partFrom': dec['from'],
                      'v1Host': host[3:] if host.startswith('v1:') else None, 'padRows': rec['padRows'], 'changedPx': rec['diff']})
    json.dump(index, open(os.path.join(out, 'qc_index.json'), 'w'), indent=1)
    json.dump(records, open(rec_out, 'w'))
    for i in index: print(i.get('name') or f"#{i['n']} {i['what']}: NO HOST SEATS", '|', i['test'])


if __name__ == '__main__':
    main()
