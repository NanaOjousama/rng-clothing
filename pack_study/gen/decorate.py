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
import json, os
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

RULE_WINS = ('right', 'left')   # A/B by eye 2026-10-09: rule better on sides; back keeps surface

def place(dec, target_masks, info=None, prefer_rule=RULE_WINS):
    """target_masks: {view: rows of 0/1}.  Returns {view: pixels} or None if any view fails.
    info (dict, optional) receives 'reseated' (views placed by the rule) and 'reseatFlags'.
    prefer_rule: views that take the rule's move (if valid) when they disagree with it.
    Sides: the rule keeps a perched part on top in profile, as in the front view.
    Back: the surface wins -- a perched part seen from behind pokes above the crown."""
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
    if info is not None:
        info['reseated'], info['reseatFlags'] = reseated, flags
    return res
