"""Derive the per-view reseating rule from measured evidence (data/vhe/moves.json).

Evidence = a head piece's art moved along the head by its author (Tea-Loving Lad's
VHE Alts: masks raised onto the crown, goggles lowered onto the eyes), aligned per
view by vhe_study.py.  For a move of dy in the FRONT view (dx = 0) we measure, per
other view, the ratios
    side dy / front dy        (right and left)
    side dx / |front dy|      toward the back of the head (right: -x, left: +x)
    back dy / front dy
Removals (an aligned remainder, not a move) are excluded.  A direction with fewer
than MIN_N moves is marked unusable.  Only clean vertical moves count (|front dy| >= 2, front dx = 0, right/left mirror).
Recoloured duplicates (Radioactive Goggles = Goggles) count once.  Up and down
moves are kept apart: they need not be symmetric (n for down is small).
Writes data/reseat_rule.json.  Pure Python.
"""
import json, os, statistics as st
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(HERE, 'data', *p)
MIN_N = 3


def main():
    moves = json.load(open(D('vhe', 'moves.json')))
    seen, samples = set(), []
    for m in moves:
        (fx, fy), (rx, ry), (lx, ly), (bx, by) = m['moved']
        if m['cls'] == 'REMOVAL': continue                 # aligned remainder of a cut, not a move
        if fx != 0 or abs(fy) < 2 or rx != -lx or ry != ly: continue
        key = tuple(map(tuple, m['moved']))
        if key in seen: continue                       # recoloured twin, same move
        seen.add(key)
        samples.append({'item': m['item'], 'dir': 'up' if fy < 0 else 'down', 'front': [fx, fy],
                        'sideDy': ry / fy, 'sideDxTowardBack': (-rx) / abs(fy), 'backDy': by / fy,
                        'moved': m['moved']})
    rule = {'_source': 'pack_study/data/vhe/moves.json (Vanilla Hats Extended Alts, Tea-Loving Lad)',
            '_meaning': 'for a front move dy: side dy = sideDy*dy; right dx = -sideDxTowardBack*|dy| (left mirrored); back dy = backDy*dy',
            'samples': samples}
    for d in ('up', 'down'):
        s = [x for x in samples if x['dir'] == d]
        if not s: continue
        rule[d] = {k: round(st.median(x[k] for x in s), 3) for k in ('sideDy', 'sideDxTowardBack', 'backDy')}
        rule[d]['n'] = len(s)
        rule[d]['usable'] = len(s) >= MIN_N                   # too few moves -> no prediction
        rule[d]['range'] = {k: [round(min(x[k] for x in s), 3), round(max(x[k] for x in s), 3)]
                            for k in ('sideDy', 'sideDxTowardBack', 'backDy')}
    json.dump(rule, open(D('reseat_rule.json'), 'w'), indent=1)
    for d in ('up', 'down'):
        if d in rule: print(d, rule[d])
    for x in samples: print(f"  {x['item']:22s} {x['moved']}")


if __name__ == '__main__':
    main()
