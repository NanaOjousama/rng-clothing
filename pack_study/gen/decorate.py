"""Place a source decoration onto a different hat, per view.  Pure Python.

PERCHED decorations (sunflower, bird, leaf, ears):
  * horizontal anchor: decoration centre relative to its source base, as a
    fraction of the base's width in that view -> same fraction on the target.
  * vertical: the source tells how deep the decoration sits into the base
    surface (decoration bottom minus base top surface under its columns); the
    decoration is lowered onto the target's top surface by the same depth.
  * reject the view (and so the pairing) if the decoration would leave the
    frame, float (no pixel touching the target), or be wider than 90% of the target.
Decoration pixels keep their source colour (they are a separate material) and
are drawn in front, exactly as they were visible on the source hat.

RESEAT RULE (data/reseat_rule.json, measured from authored head-piece moves):
the front view is the anchor.  When a side/back view cannot seat on its own
surface (typical: nothing under the decoration in the back view), its vertical
move is predicted from the front move instead of rejecting the pairing; the
horizontal anchor is unchanged.  A view that seats but disagrees with the
prediction by more than RESEAT_TOL px is flagged (info['reseatFlags']); side views
then take the rule's move, the back view keeps its surface seat (A/B by eye).
"""
import json, os, math
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = ['front', 'right', 'left', 'back']

def load_approved():
    decs = json.load(open(os.path.join(HERE, 'data', 'decorations.json')))
    vhe = os.path.join(HERE, 'data', 'vhe', 'decorations.json')       # tools/vhe_parts.py
    if os.path.exists(vhe): decs += json.load(open(vhe))
    ap = json.load(open(os.path.join(HERE, 'data', 'decorations_approved.json')))['dec_ids_by_from']
    out = []
    for d in decs:
        key = d['from'].rsplit('__', 1)[0]
        if key in ap and (key != 'kailey__straw_hat_blue' or 'colourable' in d['base']):
            out.append(dict(d, **ap[key]))
    return out

def mask_info(mask):
    """mask: rows of 0/1. Returns (xmin, xmax, top surface per column)."""
    h, w = len(mask), len(mask[0])
    cols = [x for x in range(w) if any(mask[y][x] for y in range(h))]
    if not cols: return None
    top = {x: min(y for y in range(h) if mask[y][x]) for x in cols}
    return min(cols), max(cols), top

RESEAT_TOL = 2
_RULE = None

def reseat_rule():
    global _RULE
    if _RULE is None:
        p = os.path.join(HERE, 'data', 'reseat_rule.json')
        _RULE = json.load(open(p)) if os.path.exists(p) else {}
    return _RULE

def predict(view, front_dy):
    """(dx, dy) of `view` for a head-piece moved front_dy in the front view, or None
    if the measured rule has too few moves in that direction."""
    if front_dy == 0: return (0, 0)
    r = reseat_rule().get('up' if front_dy < 0 else 'down')
    if not r or not r.get('usable'): return None
    if view == 'front': return (0, front_dy)
    if view == 'back': return (0, round(r['backDy'] * front_dy))
    toward_back = round(r['sideDxTowardBack'] * abs(front_dy))
    return ((-toward_back if view == 'right' else toward_back), round(r['sideDy'] * front_dy))

def reseat(pixels_by_view, front_dy):
    """Move a head piece along the head: front by front_dy, other views by the rule.
    Returns {view: pixels} or None when the rule cannot predict that direction."""
    out = {}
    for v in VIEWS:
        d = predict(v, front_dy)
        if d is None: return None
        out[v] = [[x + d[0], y + d[1], p] for x, y, p in pixels_by_view[v]]
    return out

def _anchor_x(dec_px, si, ti):
    sx0, sx1, _ = si; tx0, tx1, _ = ti
    sw, tw = sx1 - sx0 + 1, tx1 - tx0 + 1
    xs = [x for x, _, _ in dec_px]
    if max(xs) - min(xs) + 1 > 0.9 * tw: return None
    dc = (min(xs) + max(xs)) / 2
    rel = (dc - (sx0 + sx1) / 2) / sw
    return round((tx0 + tx1) / 2 + rel * tw - dc)

# Rows a part may rise above the hat frame.  The writer then grows the canvas upward
# and adds the same amount to HeadPosition.Y: FS uses HeadPosition as the draw origin
# (src/DrawManager.cs GetPositionOffset -> SpriteBatch origin), so the original rows
# stay put on screen.  Confirmed in FS source; NOT yet confirmed by a worn capture.
HEADROOM = 6

def _valid(out, tgt_mask):
    h, w = len(tgt_mask), len(tgt_mask[0])
    if any(not (0 <= x < w and -HEADROOM <= y < h) for x, y, _ in out): return False
    occ = {(x, y) for y in range(h) for x in range(w) if tgt_mask[y][x]}
    return any((x + dx, y + dy) in occ for x, y, _ in out for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)))

def place_view(dec_px, src_mask, tgt_mask, shift_y=None):
    """Seat on the target surface; with shift_y given, use that vertical move instead.
    Returns (pixels, shift_y) or None."""
    if not dec_px: return [], 0
    si, ti = mask_info(src_mask), mask_info(tgt_mask)
    if not si or not ti: return None
    shift_x = _anchor_x(dec_px, si, ti)
    if shift_x is None: return None
    xs = [x for x, _, _ in dec_px]; ys = [y for _, y, _ in dec_px]
    if shift_y is None:
        stop, ttop = si[2], ti[2]
        # depth into the source surface, averaged over the decoration's columns that have base under them
        under = [stop[x] for x in set(xs) if x in stop]
        bottom = max(ys)
        depth = bottom - (sum(under) / len(under)) if under else 0
        under_t = [ttop[x + shift_x] for x in set(xs) if x + shift_x in ttop]
        if not under_t: return None
        shift_y = round(sum(under_t) / len(under_t) + depth - bottom)
    out = [[x + shift_x, y + shift_y, p] for x, y, p in dec_px]
    return (out, shift_y) if _valid(out, tgt_mask) else None

# --- contact / seat primitives (worn QC 2026-10-10: PSQC 02/06 sprig floated, PSQC 04 tuft split) ---

def _n4(x, y): return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))

def _occ(mask):
    return {(x, y) for y in range(len(mask)) for x in range(len(mask[0])) if mask[y][x]}

def contacts(px, occ):
    """Part pixels touching the host (4-neighbour, host pixel not covered by the part)."""
    P = {(x, y) for x, y, _ in px}
    return [(x, y) for x, y in P if any(q in occ and q not in P for q in _n4(x, y))]

def need_contact(px, src_mask):
    """A placed part must touch its new host at least half as much as on its source,
    so a part that sat on a 6-px stem cannot hang off one diagonal-ish pixel."""
    n = len(contacts(px, _occ(src_mask)))
    return max(1, math.ceil(n / 2)) if n else 0

def wrap_rows(px, src_mask):
    """Rows where the part wraps the host (part pixels left AND right of a host pixel):
    the tuft tied round a cone tip.  Such a part only fits a host as narrow there."""
    P = {(x, y) for x, y, _ in px}; out = []
    for y in {y for _, y in P}:
        xs = sorted(x for x, yy in P if yy == y)
        if any(src_mask[y][x] and (x, y) not in P for x in range(xs[0] + 1, xs[-1])) if 0 <= y < len(src_mask) else False:
            out.append(y)
    return out

def fits_wrap(placed, rows_dy, tgt_mask):
    """Every wrapped row: the host is present and lies strictly inside the part's span."""
    P = {(x, y) for x, y, _ in placed}
    for y in rows_dy:
        xs = sorted(x for x, yy in P if yy == y)
        if not xs or not (0 <= y < len(tgt_mask)): return False
        host = [x for x in range(len(tgt_mask[0])) if tgt_mask[y][x] and (x, y) not in P]
        if not host or min(host) <= xs[0] or max(host) >= xs[-1]: return False
    return True

def _run_at(mask, y, x):
    """(x0, x1) of the filled run on row y containing x, or the run nearest x."""
    if not (0 <= y < len(mask)): return None
    row = mask[y]; runs, x0 = [], None
    for i, v in enumerate(list(row) + [0]):
        if v and x0 is None: x0 = i
        if not v and x0 is not None: runs.append((x0, i - 1)); x0 = None
    if not runs: return None
    return min(runs, key=lambda r: 0 if r[0] <= x <= r[1] else min(abs(x - r[0]), abs(x - r[1])))

def brim_shelf(out, tgt_mask, rows=3, step=2):
    """The host's brim reaches out UNDER a side-seated part: within `rows` rows below the
    part's lowest row, a host run extends outward (away from the hat centre) to within
    1 px of the part's outer edge, and at least `step` px past the crown edge at the
    part's TOP row (not its lowest: seen from behind, the source sprig overlaps the crown
    face down there).  This is the crown-over-brim notch the source sprig sits in (Forager's
    Hat, straw sun hats); a dome, beanie or cap wall has nothing under the stem and the
    part juts out sideways (worn QC v2 2026-10-10, PSQC2 02/03)."""
    if not out: return True
    ti = mask_info(tgt_mask)
    if not ti: return False
    h = len(tgt_mask)
    xs = [x for x, _, _ in out]
    out_dir = 1 if (min(xs) + max(xs)) / 2 > (ti[0] + ti[1]) / 2 else -1
    outer = max(xs) if out_dir == 1 else min(xs)
    low, top = max(y for _, y, _ in out), max(0, min(y for _, y, _ in out))
    crown = _run_at(tgt_mask, top, (ti[0] + ti[1]) // 2)
    if crown is None: return False
    crown_edge = crown[1] if out_dir == 1 else crown[0]
    for y in range(low + 1, min(h, low + 1 + rows)):
        run = _run_at(tgt_mask, y, (ti[0] + ti[1]) // 2)
        if run is None: continue
        edge = run[1] if out_dir == 1 else run[0]
        reach, past = (edge - outer, edge - crown_edge) if out_dir == 1 else (outer - edge, crown_edge - edge)
        if reach >= -1 and past >= step: return True
    return False

def stem_on_brim(out, tgt_mask):
    """NARROW-brim (boater) measure: the brim lip is too short to reach under the leaves,
    so the STEM must rest on it instead.  Stem root = lowest part pixel with the hat beside
    it; the pixel right under the root is hat, and that row reaches >= 1 px further out
    than the crown edge on the root's row (a lip, not the crown wall carrying on down)."""
    if not out: return True
    ti = mask_info(tgt_mask)
    if not ti: return False
    occ = _occ(tgt_mask); P = {(x, y) for x, y, _ in out}
    con = [(x, y, d) for x, y in P for d in (1, -1) if (x + d, y) in occ and (x + d, y) not in P]
    if not con: return False
    rx, ry, d = max(con, key=lambda t: t[1])
    if (rx, ry + 1) not in occ: return False
    mid = (ti[0] + ti[1]) // 2
    crown, lip = _run_at(tgt_mask, ry, mid), _run_at(tgt_mask, ry + 1, mid)
    if crown is None or lip is None: return False
    return (crown[0] - lip[0] >= 1) if d == 1 else (lip[1] - crown[1] >= 1)

def place_side(dec_px, src_mask, tgt_mask, shelf=False):
    """SIDE seat: a part tucked against the CROWN WALL (leaf sprig in a Forager's Hat).
    The stem root is the lowest part pixel with the source hat beside it.  On the source,
    find the crown run on that row and the root's offset from the run's edge; on the
    target, take the row the same depth below the hat top, the run nearest the hat's
    centre (the crown, not a brim tip or an ear), and keep the same offset from its edge.
    Then +-1/+2 rows to reach need_contact() contacts without covering more host than on
    the source.  Worn QC 2026-10-10: anchoring by whole-hat width put the sprig on the
    brim tip / outer corner, where it read as floating (PSQC 02/06)."""
    if not dec_px: return [], 0
    socc, tocc = _occ(src_mask), _occ(tgt_mask)
    si, ti = mask_info(src_mask), mask_info(tgt_mask)
    if not si or not ti: return None
    P = {(x, y) for x, y, _ in dec_px}
    side_con = [(x, y, d) for x, y in P for d in (1, -1) if (x + d, y) in socc and (x + d, y) not in P]
    if not side_con: return None
    rx, ry, d = max(side_con, key=lambda t: t[1])                   # stem root, d = direction to the hat
    s_top, t_top = min(y for _, y in socc), min(y for _, y in tocc)
    run = _run_at(src_mask, ry, rx + d)
    edge_s = run[0] if d == 1 else run[1]
    off = rx - edge_s                                              # root column relative to the wall
    ty = t_top + (ry - s_top)
    trun = _run_at(tgt_mask, ty, (ti[0] + ti[1]) // 2)
    if trun is None: return None
    edge_t = trun[0] if d == 1 else trun[1]
    dx, dy0 = edge_t + off - rx, ty - ry
    over_s = sum(q in socc for q in P)
    need = need_contact(dec_px, src_mask)
    if shelf == 'narrow':                  # boater: slide down / in until the stem sits on the lip
        pcx = sum(x for x, _, _ in dec_px) / len(dec_px) + dx
        inward = 1 if (ti[0] + ti[1]) / 2 > pcx else -1   # toward the hat centre (d is ambiguous when the part overlaps the crown)
        cands = [(dy0 + j, dx + k * inward) for j in (0, 1, -1, 2, -2, 3, -3) for k in (0, 1, 2)]
        ok = stem_on_brim
    else:
        cands = [(dy, dx) for dy in (dy0, dy0 + 1, dy0 - 1, dy0 + 2)]
        ok = brim_shelf if shelf else (lambda o, m: True)
    for dy, ddx in cands:
        out = [[x + ddx, y + dy, p] for x, y, p in dec_px]
        if sum((x, y) in tocc for x, y, _ in out) > over_s + 1: continue
        if len(contacts(out, tocc)) >= need and _valid(out, tgt_mask) and ok(out, tgt_mask):
            return out, dy
    return None

def seat_of(dec):
    import semantics
    pl = (semantics.profiles().get(dec['from'].rsplit('__', 1)[0]) or {}).get('placement', {})
    return pl.get('seat', 'surface'), pl.get('fit'), pl.get('host')

def _contact_ok(px, src_mask, out, tgt_mask):
    return len(contacts(out, _occ(tgt_mask))) >= need_contact(px, src_mask)

RULE_WINS = ('right', 'left')   # A/B by eye 2026-10-09: rule better on sides; back keeps surface

def place(dec, target_masks, info=None, prefer_rule=RULE_WINS, host=()):
    """target_masks: {view: rows of 0/1}.  Returns {view: pixels} or None if any view fails.
    host: the host's families + verified traits (semantics.host_families); a 'brim-narrow'
    host takes the boater measure (stem_on_brim) instead of brim_shelf for a brim-shelf part.
    info (dict, optional) receives 'reseated' (views placed by the rule) and 'reseatFlags'.
    prefer_rule: views that take the rule's move (if valid) when they disagree with it.
    Sides: the rule keeps a perched part on top in profile, as in the front view.
    Back: the surface wins -- a perched part seen from behind pokes above the crown."""
    seat, fit, shelf_rule = seat_of(dec)
    host_traits, need_shelf = set(host), shelf_rule == 'brim-shelf'
    if seat == 'side':
        res = {}
        for v in VIEWS:
            r = place_side(dec['views'][v]['pixels'], dec['views'][v]['baseMask'], target_masks[v],
                           shelf=(('narrow' if 'brim-narrow' in host_traits else True) if need_shelf else False))
            if r is None: return None
            res[v] = r[0]
        if info is not None: info['reseated'], info['reseatFlags'] = [], []
        return res
    res, dy = {}, {}
    front = place_view(dec['views']['front']['pixels'], dec['views']['front']['baseMask'], target_masks['front'])
    if front is None: return None
    res['front'], dy['front'] = front
    reseated, flags = [], []
    for v in VIEWS[1:]:
        px, sm = dec['views'][v]['pixels'], dec['views'][v]['baseMask']
        pred = predict(v, dy['front'])
        r = place_view(px, sm, target_masks[v])
        if r is not None and px and pred is not None and abs(r[1] - pred[1]) > RESEAT_TOL:
            flags.append([v, r[1], pred[1]])
            if v in prefer_rule:
                alt = place_view(px, sm, target_masks[v], shift_y=pred[1])
                if alt is not None: r = alt; reseated.append(v)
        if r is None and pred is not None:
            r = place_view(px, sm, target_masks[v], shift_y=pred[1])
            if r is not None: reseated.append(v)
        if r is None: return None
        res[v], dy[v] = r
    for v in VIEWS:          # every view must touch its new host about as firmly as its source
        px, sm = dec['views'][v]['pixels'], dec['views'][v]['baseMask']
        if px and not _contact_ok(px, sm, res[v], target_masks[v]): return None
        if fit == 'wrap':
            rows = wrap_rows(px, sm)
            if rows and not fits_wrap(res[v], [y + dy[v] for y in rows], target_masks[v]): return None
    if info is not None:
        info['reseated'], info['reseatFlags'] = reseated, flags
    return res
