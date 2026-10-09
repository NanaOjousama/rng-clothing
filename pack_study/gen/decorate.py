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
"""
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = ['front', 'right', 'left', 'back']

def load_approved():
    decs = json.load(open(os.path.join(HERE, 'data', 'decorations.json')))
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

def place_view(dec_px, src_mask, tgt_mask):
    if not dec_px: return []
    si, ti = mask_info(src_mask), mask_info(tgt_mask)
    if not si or not ti: return None
    sx0, sx1, stop = si; tx0, tx1, ttop = ti
    sw, tw = sx1 - sx0 + 1, tx1 - tx0 + 1
    xs = [x for x, _, _ in dec_px]; ys = [y for _, y, _ in dec_px]
    dw = max(xs) - min(xs) + 1
    if dw > 0.9 * tw: return None
    dc = (min(xs) + max(xs)) / 2
    rel = (dc - (sx0 + sx1) / 2) / sw
    shift_x = round((tx0 + tx1) / 2 + rel * tw - dc)
    # depth into the source surface, averaged over the decoration's columns that have base under them
    under = [stop[x] for x in set(xs) if x in stop]
    bottom = max(ys)
    depth = bottom - (sum(under) / len(under)) if under else 0
    cols_t = [x + shift_x for x in set(xs)]
    under_t = [ttop[x] for x in cols_t if x in ttop]
    if not under_t: return None
    shift_y = round(sum(under_t) / len(under_t) + depth - bottom)
    h, w = len(tgt_mask), len(tgt_mask[0])
    out = [[x + shift_x, y + shift_y, p] for x, y, p in dec_px]
    if any(not (0 <= x < w and 0 <= y < h) for x, y, _ in out): return None
    occ = {(x, y) for y in range(h) for x in range(w) if tgt_mask[y][x]}
    if not any((x + dx, y + dy) in occ for x, y, _ in out for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))):
        return None
    return out

def place(dec, target_masks):
    """target_masks: {view: rows of 0/1}.  Returns {view: pixels} or None if any view fails."""
    res = {}
    for v in VIEWS:
        r = place_view(dec['views'][v]['pixels'], dec['views'][v]['baseMask'], target_masks[v])
        if r is None: return None
        res[v] = r
    return res
