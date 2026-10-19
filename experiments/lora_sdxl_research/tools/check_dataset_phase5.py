"""Validate dataset/phase5_v1 (build_dataset_phase5.py).  Pure Python (zlib/struct), bare python3.
  1  files: every manifest item has .png + .txt, nothing extra; 768x768 RGB8, unfiltered rows (as written)
  2  exact grid: every cell x cell block is one colour (32 px front, 16 px four-view) -- no resampling anywhere
  3  background removal: keying the exact background colour recovers the item's exact cell set (manifest cells_sha),
     and no hat colour lies within KEY_TOL OKLab of the background, so a tolerant key on generated images is safe
  4  captions: ASCII; trigger + the item's own layout phrase first; the other layout's phrase absent; its family token
     present and no other family token; frame word; no vanilla slot names (hats_N); colours last
  5  split: train / holdout disjoint by construction, colourway, structure group and silhouette body; holdout never
     mirrored; every family with >= 3 bodies has a holdout; both layouts present for every colourway
  6  balance + provenance: train family share <= MAX_SHARE; no generated-experiment source
usage: python3 -I check_dataset_phase5.py"""
import collections, json, os, re, struct, sys, zlib
sys.argv, _ARGS = [sys.argv[0], '512'], sys.argv[1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_dataset as B
import build_dataset_phase4 as P4
import build_dataset_phase5 as P5
KEY_TOL, MAX_SHARE = 0.06, 0.13


def read_rows(path):
    d = open(path, 'rb').read(); assert d[:8] == b'\x89PNG\r\n\x1a\n', 'not a PNG'
    i, idat, hdr = 8, b'', None
    while i < len(d):
        n = struct.unpack('>I', d[i:i + 4])[0]; t = d[i + 4:i + 8]; c = d[i + 8:i + 8 + n]; i += 12 + n
        if t == b'IHDR': hdr = struct.unpack('>IIBBBBB', c)
        elif t == b'IDAT': idat += c
    w, h, bd, ct = hdr[:4]; raw = zlib.decompress(idat); st = 1 + w * 3
    rows = [raw[y * st:(y + 1) * st] for y in range(h)]
    return w, h, bd, ct, rows


def main():
    man = json.load(open(os.path.join(P5.OUT, 'manifest.json'))); E = []; bg = tuple(man['background']); bgb = bytes(bg)
    dirs = {'train': os.path.join(P5.OUT, 'train', f'1_{B.TRIGGER}'), 'holdout': os.path.join(P5.OUT, 'holdout')}
    fams = {i['family'] for i in man['items']}
    expect = {s: set() for s in dirs}
    for it in man['items']: expect[it['split']] |= {it['file'] + '.png', it['file'] + '.txt'}
    for s, d in dirs.items():
        have = set(os.listdir(d))
        for f in sorted(expect[s] - have): E.append((f, 'missing'))
        for f in sorted(have - expect[s]): E.append((f, 'not in manifest'))
    colours = set()
    for it in man['items']:
        L = man['layouts'][it['layout']]; cell, grid = L['cell'], L['grid']; p = os.path.join(dirs[it['split']], it['file'])
        w, h, bd, ct, rows = read_rows(p + '.png')
        if (w, h, bd, ct) != (768, 768, 8, 2): E.append((it['file'], f'png {w}x{h} depth {bd} type {ct}')); continue
        if any(r[0] != 0 for r in rows): E.append((it['file'], 'filtered rows (not written by the builder)')); continue
        cells, bad = set(), 0
        for by in range(grid):
            r0 = rows[by * cell]
            if any(rows[by * cell + k] != r0 for k in range(1, cell)): bad += 1
            for bx in range(grid):
                seg = r0[1 + bx * cell * 3: 1 + (bx + 1) * cell * 3]
                if seg != seg[:3] * cell: bad += 1
                if seg[:3] != bgb: cells.add((bx, by)); colours.add(tuple(seg[:3]))
        if bad: E.append((it['file'], f'{bad} non-uniform blocks (grid not exact)'))
        if len(cells) != it['n_cells'] or P5.cell_hash(cells) != it['cells_sha']:
            E.append((it['file'], f'background key recovers {len(cells)} cells, manifest {it["n_cells"]} (mask mismatch)'))
        if it['augmented']:
            pass
        cap = open(p + '.txt', encoding='ascii', errors='replace').read(); toks = cap.split(', ')
        other = 'fourview' if it['layout'] == 'front' else 'front'
        if cap != it['caption']: E.append((it['file'], 'caption differs from manifest'))
        if not cap.isascii(): E.append((it['file'], 'non-ASCII caption'))
        if not cap.startswith(f"{B.TRIGGER}, {L['phrase']}, "): E.append((it['file'], 'trigger/layout phrase not first'))
        if man['layouts'][other]['phrase'].split(',')[0] in cap: E.append((it['file'], f'{other} layout phrase in caption'))
        if it['family'] not in toks: E.append((it['file'], f"family token '{it['family']}' missing"))
        wrong = [t for t in toks if t in fams and t != it['family']]
        if wrong: E.append((it['file'], f'other family tokens {wrong}'))
        if not cap.endswith(f"pixel art, {L['frame']}, dark outline"): E.append((it['file'], 'frame / style tail'))
        if re.search(r'\bhats_\d+\b', cap): E.append((it['file'], 'vanilla slot name in caption'))
        if it['source_kind'] != 'library' and any(seg.startswith(P4.FORBIDDEN_SOURCES) for seg in it['source'].split('/')):
            E.append((it['file'], f"forbidden source {it['source']}"))       # library sources are pack_study ids, not paths
    # 3: tolerant-key safety on the hat colours actually present
    near = min(colours, key=lambda c: sum((a - b) ** 2 for a, b in zip(B.oklab(c), B.oklab(bg))))
    dmin = sum((a - b) ** 2 for a, b in zip(B.oklab(near), B.oklab(bg))) ** 0.5
    if dmin < KEY_TOL: E.append(('background', f'hat colour {near} only {dmin:.3f} OKLab from background'))
    # 5: split
    tr = [i for i in man['items'] if i['split'] == 'train']; ho = [i for i in man['items'] if i['split'] == 'holdout']
    for key in ('construction', 'colourway', 'body'):
        both = {i[key] for i in tr} & {i[key] for i in ho}
        if both: E.append(('split', f'{key} in train and holdout: {sorted(both)[:5]}'))
    sg = {g for i in tr for g in i['struct_group']} & {i['colourway'] for i in ho}
    if sg: E.append(('split', f'holdout colourway shares a structure group with train: {sorted(sg)[:5]}'))
    if any(i['augmented'] for i in ho): E.append(('split', 'mirrored image in holdout'))
    bodies = collections.defaultdict(set)
    for i in man['items']: bodies[i['family']].add(i['body'])
    for f, bs in bodies.items():
        if len(bs) >= 3 and not any(i['family'] == f for i in ho): E.append(('split', f'family {f} has {len(bs)} bodies but no holdout'))
    lay = collections.defaultdict(set)
    for i in man['items']: lay[(i['colourway'], i['augmented'])].add(i['layout'])
    for k, v in lay.items():
        if v != {'front', 'fourview'}: E.append(('layouts', f'{k} has only {sorted(v)}'))
    # 4b: a descriptive word in most captions carries no information (the 2026-10-18 'decorated' bug)
    fixed = {B.TRIGGER, 'pixel art', 'dark outline'} | {w for L in man['layouts'].values() for w in L['phrase'].split(', ') + [L['frame']]}
    tok = collections.Counter(t for i in man['items'] for t in set(i['caption'].split(', ')) if t not in fixed and t not in fams)
    for t, c in tok.most_common(3):
        if c / len(man['items']) > 0.40: E.append(('captions', f"'{t}' in {c / len(man['items']):.0%} of captions"))
    # 6: balance
    share = collections.Counter(i['family'] for i in tr); n = sum(share.values())
    for f, c in share.items():
        if c / n > MAX_SHARE: E.append(('balance', f'{f} is {c / n:.1%} of train > {MAX_SHARE:.0%}'))
    print(f"items {len(man['items'])} (train {len(tr)}, holdout {len(ho)}) | families {len(fams)} | hat colours {len(colours)}"
          f" | background {bg}, nearest hat colour {near} at {dmin:.3f} OKLab (tolerant-key limit {KEY_TOL})")
    print('largest train shares', [(f, round(c / n, 3)) for f, c in share.most_common(4)])
    for f, why in E[:60]: print('  ERROR', f, '|', why)
    print('errors', len(E)); sys.exit(1 if E else 0)


if __name__ == '__main__':
    main()
