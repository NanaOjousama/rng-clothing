"""Semantic filter report: every approved part x every construction.
geometry first (decorate.place / band.place / pattern.eligible), then semantics.verdict.
Also checks each profile's placement anchor against where the part sits on its source.
usage: demo_semantics.py [per_part_examples]
  -> data/attachment_report.json, out/semantics_<n>.png (per part: kept | novelty | rejected-but-seated)"""
import json, os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
import png
import semantics as S
import band as B
import pattern as P
from decorate import load_approved, place, mask_info, VIEWS
from demo_band import views_of
from generate import names_of
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def anchor_of(d):
    """Measured source position of a perched part in the front view."""
    v = d['views']['front']; px = v['pixels']
    si = mask_info(v['baseMask'])
    if not px or not si: return None
    xs = [x for x, _, _ in px]; ys = [y for _, y, _ in px]
    rel = ((min(xs) + max(xs)) / 2 - (si[0] + si[1]) / 2) / (si[1] - si[0] + 1)
    top = min(si[2].values())
    return {'xRel': round(rel, 2), 'aboveTop': top - min(ys), 'bottomBelowTop': max(ys) - top}


def anchor_ok(anchor, m):
    if m is None: return None
    if anchor == 'top-centre': return abs(m['xRel']) <= 0.12 and m['aboveTop'] > 0
    if anchor == 'top-side': return abs(m['xRel']) > 0.12
    if anchor == 'side-wall': return abs(m['xRel']) > 0.12 and m['bottomBelowTop'] > 0
    if anchor == 'front-mount': return abs(m['xRel']) <= 0.12 and m['bottomBelowTop'] > 2 and m['aboveTop'] <= 0
    return None


def main():
    k_ex = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    lib = json.load(open(os.path.join(HERE, 'data', 'library.json')))
    cons = [c for c in lib['constructions'] if not c['missing']]
    fams = {c['id']: S.host_families(names_of(c), c['id']) for c in cons}
    views = {c['id']: views_of(c) for c in cons}
    profs = S.profiles()
    parts = [d for d in load_approved()]
    seen = set(); uniq = []
    for d in parts:                                  # one record per approval key (bands have per-base copies)
        k = S.key_of(d)
        if k in seen: continue
        seen.add(k); uniq.append(d)
    report, sheets = {}, []
    for d in uniq + [{'label': 'plaid', 'kind': 'pattern'}]:
        k = S.key_of(d); prof = profs[k]
        rec = {'label': prof['label'], 'class': prof['class'], 'transfer': prof['transfer'], 'anchor': prof['placement']['anchor']}
        if d['kind'] == 'perched':
            m = anchor_of(d); rec['measured'] = m; rec['anchorOk'] = anchor_ok(prof['placement']['anchor'], m)
        if prof['transfer'] == 'headpiece-only' or d['kind'] == 'headpiece':
            rec['seated'] = None; report[k] = rec; continue
        by = Counter(); ex = {'keep': [], 'novelty': [], 'reject': []}; fam_kept = Counter()
        for c in cons:
            px, masks = views[c['id']]
            if d['kind'] == 'pattern':
                ok = P.eligible(c)
                res = None
            else:
                if c['frame'][0] != d['frame'][0]: continue
                if d['kind'] == 'band':
                    res = B.place(d, masks) if B.eligible(names_of(c)) else None
                else:
                    res = place(d, masks)
                ok = res is not None
            if not ok: continue
            v, w = S.verdict(prof, fams[c['id']])
            by[v] += 1
            if v in ('prefer', 'allow', 'unknown') and w > 0:
                bucket = 'keep'
                for f in fams[c['id']]: fam_kept[f] += 1
            elif v == 'novelty' and (prof.get('novelty') is None or fams[c['id']] & set(prof['novelty'])): bucket = 'novelty'
            else: bucket = 'reject'
            if len(ex[bucket]) < k_ex: ex[bucket].append((c, res))
        rec['seated'] = sum(by.values()); rec['verdicts'] = dict(by); rec['keptFamilies'] = dict(fam_kept.most_common())
        rec['examples'] = {b: [f"{c['author'][:12]}:{c['names'][0][:22]} {sorted(fams[c['id']])}" for c, _ in e] for b, e in ex.items()}
        report[k] = rec
        sheets.append((d, prof, ex))
    json.dump(report, open(os.path.join(HERE, 'data', 'attachment_report.json'), 'w'), indent=1, ensure_ascii=False)

    # contact sheet: one row per part, three blocks of k_ex front views (keep | novelty | reject)
    S_, fw = 3, 34
    blk = k_ex * (fw * S_ + 4) + 16
    rowh = 30 * S_ + 8
    per = 9
    for si in range(0, len(sheets), per):
        chunk = sheets[si:si + per]
        W, H = 3 * blk, len(chunk) * rowh
        bgs = [(112, 140, 108, 255), (150, 140, 100, 255), (150, 108, 108, 255)]
        canvas = [[bgs[min(2, x // blk)] for x in range(W)] for _ in range(H)]
        for r, (d, prof, ex) in enumerate(chunk):
            for b, bucket in enumerate(['keep', 'novelty', 'reject']):
                for j, (c, res) in enumerate(ex[bucket]):
                    px, masks = views[c['id']]
                    if d['kind'] == 'pattern':
                        grid = P.apply(d_pat(lib), strip(c), c['frame'], P.material_mask(c))
                        pts = {(x, y): q for y, row in enumerate(grid) for x, q in enumerate(row) if x < c['frame'][0] and q[3]}
                        pad = 0
                    else:
                        pts = dict(px['front'])
                        for x, y, p in res['front']: pts[(x, y)] = p
                        pad = max([0] + [-y for _, y, _ in res['front']])
                    ox, oy = b * blk + 8 + j * (fw * S_ + 4), r * rowh + 4
                    for (x, y), p in pts.items():
                        if not p[3]: continue
                        for yy in range(S_):
                            Y = oy + (y + pad) * S_ + yy
                            if Y >= H: continue
                            for xx in range(S_):
                                X = ox + x * S_ + xx
                                if X < W: canvas[Y][X] = tuple(p[:3]) + (255,)
        png.write(os.path.join(HERE, 'out', f'semantics_{si // per}.png'), W, H, canvas)
    for k, r in report.items():
        print(f"{r['label'][:24]:24s} {r['class']:10s} {r['transfer']:14s} anchor={r['anchor']:19s} ok={r.get('anchorOk')}  seated={r.get('seated')} {r.get('verdicts', '')}")


_PAT = None
def d_pat(lib):
    global _PAT
    if _PAT is None: _PAT = P.load_approved(lib)[0]
    return _PAT


def strip(c):
    w, h = c['frame']; W = 4 * w; pal = c['colourways'][0]['palette']
    return [[tuple(pal[c['grid'][y * W + x]]) if c['grid'][y * W + x] >= 0 else (0, 0, 0, 0)
             for x in range(W)] for y in range(h)]


if __name__ == '__main__':
    main()
