"""LoRA worn test 01 (AI-ORIGINAL lane, CLAUDE.md s2b).  Deck, pure Python.

Input: input/worn_picks_atlas.png (7 rows x front|right|left|back, 20x20 each, alpha = hat mask) exported
on the laptop from the phase-2 clean-front LoRA renders (checkpoint e06; provenance in input/worn_picks.json).
The front of each hat is the given front (exact); right/left/back are generated.

Colour correction (user, 2026-10-12: "use the front-view palette, preserve shading and details"):
  every right/left/back cell is mapped to a FRONT colour.  Distance in OKLab with chroma (a,b) weighted x2,
  so a cell keeps its hue family (ramp) and its lightness picks the ramp step -> shading survives as the
  front's own ramp steps.  The front is never changed.  Per view we report: cells changed, mean/max move,
  lightness levels before/after (shading kept?), and 'far' cells (move > FAR: a colour the front does not
  have, e.g. an invented detail; snapped anyway, listed so they can be judged by eye).
Seating: HeadPosition per view from a library host (pack_study/data/library.json): the source construction
  when the front came from one (flowers, bear), else the 20x20 host with the best unshifted front-silhouette
  IoU (phase-2 frames keep the authored placement, so no shift).
Outputs: out/<hat>_compare_x8.png (raw | corrected), out/contact_x4.png, out/report.json, and the pack
  '[FS] LoRA Worn Test 01' (UniqueID LoraWorn.T01) in out/pack/ and, with --install, in the game Mods folder.
usage: python3 -I build_worn_pack.py [--install]"""
import json, math, os, shutil, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'generator')); sys.path.insert(0, str(ROOT / 'pack_study' / 'gen'))
import png_utils as P
from colour import to_lch

VIEWS = ['front', 'right', 'left', 'back']
MODS = Path('/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods')
PACK = '[FS] LoRA Worn Test 01'; UID = 'LoraWorn.T01'
FAR = 0.12
SOURCE_HOST = {'flower_pink': 'plurffle__c80', 'flower_purple': 'kailey__c226', 'bear': 'seyph__c287'}
LABEL = {'witch_s8': 'Witch s8', 'witch_s9': 'Witch s9', 'frog': 'Frog', 'bee': 'Bee',
         'flower_pink': 'Pink flower crown', 'flower_purple': 'Purple flower crown', 'bear': 'Bear'}


def lab(rgb):
    L, C, H = to_lch(rgb); h = math.radians(H)
    return L, C * math.cos(h), C * math.sin(h)


def dist(p, q, w=2.0):
    return math.sqrt((p[0] - q[0]) ** 2 + w * ((p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2))


def de(p, q): return dist(p, q, 1.0)


def load():
    meta = json.load(open(HERE / 'input' / 'worn_picks.json'))
    px = P.read_rgba_png(HERE / 'input' / 'worn_picks_atlas.png')['pixels']
    hats = {}
    for i, k in enumerate(meta['order']):
        hats[k] = {v: {(x, y): px[i * 20 + y][vi * 20 + x][:3] for y in range(20) for x in range(20)
                       if px[i * 20 + y][vi * 20 + x][3]} for vi, v in enumerate(VIEWS)}
    return meta, hats


def snap(views):
    pal = sorted(set(views['front'].values())); plab = {c: lab(c) for c in pal}
    out = {'front': dict(views['front'])}; rep = {}
    for v in VIEWS[1:]:
        cells = {}; moves = []; far = []
        for p, c in views[v].items():
            cl = lab(c); best = min(pal, key=lambda f: dist(cl, plab[f]))
            m = de(cl, plab[best]); moves.append(m); cells[p] = best
            if m > FAR: far.append({'xy': p, 'from': c, 'to': best, 'move': round(m, 3)})
        Lb = sorted({round(lab(c)[0], 2) for c in views[v].values()}); La = sorted({round(plab[c][0], 2) for c in cells.values()})
        rep[v] = {'cells': len(cells), 'changed': sum(1 for p in cells if cells[p] != views[v][p]),
                  'mean_move': round(sum(moves) / max(1, len(moves)), 3), 'max_move': round(max(moves, default=0), 3),
                  'colours_before': len(set(views[v].values())), 'colours_after': len(set(cells.values())),
                  'front_colours': len(pal), 'L_levels_before': len(Lb), 'L_levels_after': len(La),
                  'far_cells': len(far), 'far': far[:12]}
        out[v] = cells
    return out, rep


# ---- round 2 fixes (user worn review 2026-10-12, out/round2_review.png) ------------------------------
CAPTURE = HERE / 'out' / 'worn_round1'     # copy of round-1 worn captures (qc_bridge/captures/20261012-222738)
MIRROR_SIDE = {'witch_s9': 'left'}
# gap fill only on SOLID hats (felt witch hats): there see-through is never intended.  Crowns/animal hats have
# open-work and face openings that are part of the design (a first unrestricted pass filled the frog's face
# opening and the gaps between flowers - wrong).  User flagged head showing through witch s8.
GAP_FILL = {'witch_s8', 'witch_s9'}
NO_ACCENT_SYNC = {'flower_pink', 'flower_purple'}   # flowers are arranged asymmetrically on purpose     # user: witch s9 side 'a little deformed' -> right := mirror(clean left)
SCALE = 4                              # worn renders: 4 image px per sprite cell (hat_only_bounds / bbox)


def mirror(cells): return {(19 - x, y): c for (x, y), c in cells.items()}


def nohat_mask(hat_dir, view):
    """opaque farmer pixels (head/hair/body) of the no-hat worn render, as a set of (x, y) image pixels"""
    px = P.read_rgba_png(hat_dir / f'{view}_nohat.png')['pixels']
    return {(x, y) for y, r in enumerate(px) for x, p in enumerate(r) if p[3]}


def fill_head_gaps(key, views, label):
    """Empty cells INSIDE a row's hat span that lie over the farmer (from the round-1 no-hat capture): the head
    shows through there.  Fill with the most common non-outline neighbour colour.  Gaps over empty background
    (e.g. the curl of a witch tip) are left open."""
    d = CAPTURE / label; st = json.load(open(d / 'render_state.json'))['directions']; filled = {}
    for v in VIEWS:
        cells = views[v]; xs = [x for x, _ in cells]; ys = [y for _, y in cells]
        b = st[v]['hat_only_bounds']; ox, oy = b['x'] - min(xs) * SCALE, b['y'] - min(ys) * SCALE
        farmer = nohat_mask(d, v); darkest = min(set(cells.values()), key=lambda c: lab(c)[0]); new = []
        for y in range(20):
            row = [x for x in range(20) if (x, y) in cells]
            if not row: continue
            for x in range(min(row) + 1, max(row)):
                if (x, y) in cells: continue
                if not any((x, y + k) in cells for k in (1, 2, 3)): continue   # notch: hat right below it
                over = sum((ox + x * SCALE + i, oy + y * SCALE + j) in farmer for i in range(SCALE) for j in range(SCALE))
                if over < SCALE * SCALE // 2: continue
                nb = [cells[q] for q in ((x + i, y + j) for i in (-1, 0, 1) for j in (-1, 0, 1)) if q in cells]
                body = [c for c in nb if c != darkest] or nb
                if not body: continue                    # no hat neighbour: leave it
                new.append(((x, y), max(set(body), key=body.count)))
        for p, c in new: cells[p] = c
        if new: filled[v] = [p for p, _ in new]
    return filled


def sync_side_accents(views):
    """An accent colour (front colour on < 8% of front cells, not the outline) present on one side view but
    absent from the other is copied to the mirrored cells of the other side, where those are hat cells."""
    F = views['front']; cnt = {}
    for c in F.values(): cnt[c] = cnt.get(c, 0) + 1
    darkest = min(cnt, key=lambda c: lab(c)[0])
    acc = {c for c, n in cnt.items() if n / len(F) < 0.08 and c != darkest}
    moved = {}
    for a, b in (('right', 'left'), ('left', 'right')):
        for c in acc:
            if any(v == c for v in views[a].values()) and not any(v == c for v in views[b].values()):
                for (x, y), v in list(views[a].items()):
                    q = (19 - x, y)
                    if v == c and q in views[b]: views[b][q] = c; moved.setdefault(b, []).append(q)
    return moved


def library_hosts():
    L = json.load(open(ROOT / 'pack_study' / 'data' / 'library.json'))
    for c in L['constructions']:
        if c['missing'] or c['frame'] != [20, 20]: continue
        g = c['grid'] if isinstance(c['grid'], list) else json.loads(c['grid'])
        front = {(k % 80, k // 80) for k, x in enumerate(g) if x >= 0 and (k % 80) < 20}
        if front: yield c, front


def pick_host(key, front):
    best = None
    for c, f in library_hosts():
        if key in SOURCE_HOST:
            if c['id'] == SOURCE_HOST[key]: return c, 1.0, 'source construction'
            continue
        s = len(f & set(front)) / len(f | set(front))
        if best is None or s > best[1]: best = (c, s, 'best unshifted front IoU')
    return best


def strip(views):
    return [[(*views[v][(x, y)], 255) if (x, y) in views[v] else (0, 0, 0, 0) for v in VIEWS for x in range(20)] for y in range(20)]


def scaled(rows, s, bgc=(118, 146, 96, 255)):
    out = []
    for r in rows:
        line = []
        for c in r: line += [c if c[3] else bgc] * s
        out += [list(line) for _ in range(s)]
    return out


def stack(blocks, gap=4, bgc=(34, 36, 44, 255)):
    w = max(len(b[0]) for b in blocks); out = []
    for b in blocks:
        out += [r + [bgc] * (w - len(r)) for r in b] + [[bgc] * w for _ in range(gap)]
    return out


def main():
    meta, hats = load(); report = {'lane': 'AI-ORIGINAL', 'pack': PACK, 'unique_id': UID, 'far_threshold': FAR,
                                   'snap': 'nearest front colour, OKLab, chroma weight 2', 'hats': {}}
    out = HERE / 'out'; out.mkdir(exist_ok=True); contact = []
    dest = out / 'pack' / PACK
    if dest.exists(): shutil.rmtree(dest)
    (dest / 'Hats').mkdir(parents=True)
    json.dump({'Name': 'LoRA Worn Test 01', 'Author': 'lora_worn_test_01 experiment (AI-ORIGINAL)', 'Version': '0.1.0',
               'Description': 'AI-ORIGINAL: phase-2 clean-front LoRA views (e06), side colours snapped to the front palette',
               'UniqueID': UID, 'UpdateKeys': [], 'ContentPackFor': {'UniqueID': 'PeacefulEnd.FashionSense'}},
              open(dest / 'manifest.json', 'w'), indent=2)
    for n, k in enumerate(meta['order'], 1):
        fixed, rep = snap(hats[k]); host, score, why = pick_host(k, hats[k]['front'])
        name = f'LW01 {n:02d} {LABEL[k]}'
        r2 = {}
        if k in MIRROR_SIDE:
            src = MIRROR_SIDE[k]; dst = 'right' if src == 'left' else 'left'
            fixed[dst] = mirror(fixed[src]); r2['mirrored'] = f'{dst} := mirror({src})'
        r2['accents_synced'] = sync_side_accents(fixed) if k not in NO_ACCENT_SYNC else 'skipped (asymmetric design)'
        r2['head_gaps_filled'] = fill_head_gaps(k, fixed, name) if k in GAP_FILL else 'skipped (open design)'
        rep['round2'] = r2
        hd = dest / 'Hats' / name; hd.mkdir()
        P.write_rgba_png(hd / 'hat.png', [r[v * 20:(v + 1) * 20] for v in range(4) for r in strip(fixed)])
        model = {'Name': name}
        for vi, v in enumerate(VIEWS):
            hx, hy = host['head'].get(v, [0, 0])
            model[v.capitalize() + 'Hat'] = {'DisableGrayscale': True, 'StartingPosition': {'X': 0, 'Y': vi * 20},
                                             'HeadPosition': {'X': int(hx), 'Y': int(hy)}, 'HatSize': {'Width': 20, 'Length': 20}}
        json.dump(model, open(hd / 'hat.json', 'w'), indent=2)
        P.write_rgba_png(out / f'{k}_compare_x8.png', stack([scaled(strip(hats[k]), 8), scaled(strip(fixed), 8)]))
        contact += [scaled(strip(hats[k]), 4), scaled(strip(fixed), 4)]
        report['hats'][k] = {'name': name, 'provenance': meta['hats'][k], 'host': {'id': host['id'], 'names': host['names'][:2],
                             'head': host['head'], 'why': why, 'front_iou': round(score, 3)}, 'views': rep}
        print(name, '| host', host['id'], why, round(score, 3), '|', {v: (r['changed'], r['mean_move'], r['far_cells'],
              f"L {r['L_levels_before']}->{r['L_levels_after']}") for v, r in rep.items() if v != 'round2'}, '| round2', rep['round2'])
    P.write_rgba_png(out / 'contact_x4.png', stack(contact, gap=2))
    json.dump(report, open(out / 'report.json', 'w'), indent=1, default=str)
    if '--install' in sys.argv:
        # update IN PLACE: recreating the folder changes its mtime and qc.py (rightly, by its rule) then demands a
        # game restart.  Same hat names -> same entries -> the pack folder's own mtime is untouched.
        tgt = MODS / PACK
        for src in dest.rglob('*'):
            t = tgt / src.relative_to(dest)
            if src.is_dir(): t.mkdir(parents=True, exist_ok=True)
            else: shutil.copyfile(src, t)
        print('installed (in place) ->', tgt)


if __name__ == '__main__':
    main()
