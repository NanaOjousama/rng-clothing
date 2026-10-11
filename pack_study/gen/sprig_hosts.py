"""Leaf sprig host classes under the final sprig policy (user, 2026-10-10).  Pure Python.

  normal    family prefer/allow (straw, cottage, western) AND decorate.place seats it,
            which for the sprig includes decorate.brim_shelf in every view
  rejected  family     dome / beanie / cap / ... named families (profile reject list)
            no-shelf   the family is fine but the brim does not reach under the stem
                       (bonnet, beret, headscarf, dome-crowned cottage hats)
            no-seat    no crown-wall seat with enough contact at all
            off-family named hosts outside prefer/allow (no sprig novelty rolls)
usage: sprig_hosts.py  -> data/sprig_hosts.json"""
import json, os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
import semantics as S
from decorate import load_approved, place, place_side, VIEWS
from demo_band import views_of
from generate import names_of
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = 'seyph__hats_90'


def main():
    dec = [d for d in load_approved() if S.key_of(d) == KEY][0]
    prof = S.profiles()[KEY]
    lib = json.load(open(os.path.join(HERE, 'data', 'library.json')))
    out, n = {'normal': [], 'rejected': {}}, Counter()
    for c in lib['constructions']:
        if c['missing'] or c['frame'][0] != dec['frame'][0]: continue
        fams = S.host_families(names_of(c), c['id'])
        v, w = S.verdict(prof, fams)
        _, masks = views_of(c)
        if w > 0:
            if place(dec, masks, host=fams) is not None: why = None
            elif all(place_side(dec['views'][x]['pixels'], dec['views'][x]['baseMask'], masks[x]) for x in VIEWS):
                why = 'no-shelf'
            else: why = 'no-seat'
        else:
            why = 'family' if v == 'reject' else ('off-family' if v == 'novelty' else 'unknown-host')
        row = f"{c['id']}  {c['author']}: {(c['names'] or ['?'])[0]}  {sorted(fams)}"
        if why is None: out['normal'].append(row)
        else: out['rejected'].setdefault(why, []).append(row)
        n[why or 'normal'] += 1
    out['counts'] = dict(n)
    out['policy'] = prof['hostClass']
    json.dump(out, open(os.path.join(HERE, 'data', 'sprig_hosts.json'), 'w'), indent=1, ensure_ascii=False)
    print(dict(n))
    for r in out['normal']: print('  normal', r)
    for r in out['rejected'].get('no-shelf', [])[:40]: print('  no-shelf', r)


if __name__ == '__main__':
    main()
