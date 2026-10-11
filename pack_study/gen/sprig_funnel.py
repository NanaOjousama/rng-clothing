"""Why is the leaf sprig rare?  Host funnel + in-generator competition.  Pure Python.

Static funnel (every library host with the sprig's frame width):
  family     semantics verdict > 0 (prefer/allow + required traits)
  seat       decorate.place (side seat + brim shelf, every view)
  eligible   generate.eligible: a proven recolour exists (else the generator never renders it)
  rare-pool  generate.roll's rare pool for its author (own add-on bases, else >=160 grid cells)
             or the >=120-cell retry pool used when a rare hat seats nothing
Dynamic: generate.main run for N hats with decorate() hooked; per decorate() call on a
host where the sprig seats: which part won, and was the sprig even tried before it.
usage: sprig_funnel.py [hats] [seeds]  -> data/sprig_funnel.json"""
import json, os, random, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(__file__))
import generate as G
import semantics as S
import decorate as D
from demo_band import views_of
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = 'seyph__hats_90'


def static(lib, dec):
    addon_bases = {a['base'] for a in lib['addons']}
    rows, n = [], Counter()
    for c in lib['constructions']:
        if c['missing'] or c['frame'][0] != dec['frame'][0]: continue
        fams = S.host_families(G.names_of(c), c['id'])
        fam_ok = S.weight(dec, fams) > 0
        seat = D.place(dec, views_of(c)[1], host=fams) is not None
        elig = G.eligible(c)
        cells = sum(g >= 0 for g in c['grid'])
        mine = [k for k in lib['constructions'] if k['author'] == c['author'] and G.eligible(k)]
        rare_pool = [k for k in mine if k['id'] in addon_bases] or [k for k in mine if sum(g >= 0 for g in k['grid']) >= 160]
        in_rare = any(k['id'] == c['id'] for k in rare_pool) and c['id'] not in addon_bases
        in_retry = elig and cells >= 120
        rows.append({'id': c['id'], 'author': c['author'], 'name': (c['names'] or ['?'])[0], 'families': sorted(fams),
                     'family': fam_ok, 'seat': seat, 'eligible': elig, 'rarePool': in_rare, 'retryPool': in_retry, 'cells': cells})
        n['hosts'] += 1
        if seat: n['seat'] += 1
        if seat and fam_ok: n['seat+family'] += 1
        if seat and fam_ok and elig: n['seat+family+eligible'] += 1
        if seat and fam_ok and elig and (in_rare or in_retry): n['...+reachable as rare'] += 1
        if seat and not fam_ok: n['seat but family/trait rejects'] += 1
        if seat and fam_ok and not elig: n['compatible but no proven recolour'] += 1
    return rows, n


def dynamic(hats, seeds, compat):
    calls, wins, tried_before = Counter(), Counter(), Counter()
    orig = G.decorate
    log = []

    def hooked(px, frame, rng, names=(), cons_id=None):
        st = rng.getstate()
        r = orig(px, frame, rng, names, cons_id)
        if cons_id in compat:
            calls[cons_id] += 1
            wins[(r or {}).get('label', 'nothing seats')] += 1
            log.append((cons_id, (r or {}).get('label')))
        return r
    G.decorate = hooked
    total = 0
    for s in seeds:
        out = os.path.join(HERE, 'out', 'qc_work', 'funnel', str(s))
        sys.argv = ['generate.py', out, str(hats), str(s)]
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()): G.main()
        total += hats
    G.decorate = orig
    return {'hats': total, 'decorateCallsOnCompatibleHosts': dict(calls), 'winnerOnCompatibleHosts': dict(wins)}


def competition(lib, dec, compat, trials=4000):
    """Exact decorate() ordering on each compatible host, sampled: P(sprig wins | host decorated, no novelty)."""
    decs = [d for d in D.load_approved() if d['kind'] in ('perched', 'band')]
    out = {}
    for cid in compat:
        c = next(k for k in lib['constructions'] if k['id'] == cid)
        masks = views_of(c)[1]
        fams = S.host_families(G.names_of(c), cid)
        import band
        banded = band.eligible(G.names_of(c))
        seats = {}
        groups = {}
        for d in decs:
            if d['frame'][0] != c['frame'][0]: continue
            wt = S.weight(d, fams)
            if wt <= 0: continue
            if d['kind'] == 'band': ok = banded and band.place(d, masks) is not None
            else: ok = D.place(d, masks, host=fams) is not None
            if ok: groups.setdefault(S.concept_of(d), []).append(wt)
        rng = random.Random(1); w = Counter()
        for _ in range(trials):
            order = sorted(((rng.random() ** (1 / max(groups[k])), k) for k in groups), reverse=True)
            w[order[0][1].split('__')[1] if '__' in order[0][1] else order[0][1]] += 1
        out[cid] = {'seatingCompetitors': {k: max(v) for k, v in groups.items()},
                    'pWin': {k: round(v / trials, 3) for k, v in w.most_common()}}
    return out


def main():
    hats = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    seeds = [int(s) for s in (sys.argv[2] if len(sys.argv) > 2 else '1,2,3,4,5').split(',')]
    lib = json.load(open(os.path.join(HERE, 'data', 'library.json')))
    dec = [d for d in D.load_approved() if S.key_of(d) == KEY][0]
    rows, n = static(lib, dec)
    compat = [r['id'] for r in rows if r['seat'] and r['family']]
    comp = competition(lib, dec, compat)
    dyn = dynamic(hats, seeds, set(compat))
    res = {'funnel': dict(n), 'compatibleHosts': [r for r in rows if r['id'] in compat],
           'seatButRejected': [r for r in rows if r['seat'] and not r['family']],
           'competition': comp, 'generator': dyn}
    json.dump(res, open(os.path.join(HERE, 'data', 'sprig_funnel.json'), 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(res['funnel'], indent=1))
    for r in res['compatibleHosts']:
        print(f"  {r['id']:22s} {r['name'][:26]:26s} elig={r['eligible']!s:5} rare={r['rarePool']!s:5} retry={r['retryPool']!s:5} cells={r['cells']}  pWin={comp[r['id']]['pWin']}")
    print('seat but family/trait rejects:', len(res['seatButRejected']))
    print(json.dumps(dyn, indent=1))


if __name__ == '__main__':
    main()
