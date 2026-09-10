"""PART 9 — numerically test the visual claims about the four chosen hats.

Five claims were made from looking at them.  Each is turned into a number here
and either survives or does not.  The accent question is the one that decides a
Color Architecture change, so it is broken down into hue / value / saturation
separately rather than asserted as "a different colour".
"""
from __future__ import annotations

import colorsys
import statistics as st
import sys
from collections import Counter

sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing")
from v5.pngio import read_rgba_png                                # noqa: E402

GOOD = "/run/media/deck/USD00/RNG_clothing/good hats/"
REFS = [(GOOD + "0_BoysCap.png", "BoysCap"),
        (GOOD + "1_SweetGent.png", "SweetGent"),
        (GOOD + "hats_11/hat.png", "hyoung_11"),
        (GOOD + "hats_8/hat.png", "Kookoroo_8")]
VANILLA = ("/run/media/deck/USD00/steamapps/common/Stardew Valley/"
           "Content (unpacked)/Characters/Farmer/hats.png")


def lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def hls(c):
    return colorsys.rgb_to_hls(c[0] / 255, c[1] / 255, c[2] / 255)


def hue_gap(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def frame(rows, ox=0, oy=0, w=20, h=20):
    return {(x, y): rows[oy + y][ox + x]
            for y in range(h) for x in range(w) if rows[oy + y][ox + x][3] > 0}


def blocks(px):
    """Contiguous same-colour regions, largest first — a hat's real construction
    areas, as opposed to steps in a gradient."""
    seen, out = set(), []
    for k in px:
        if k in seen:
            continue
        col, stack, cells = px[k], [k], []
        while stack:
            q = stack.pop()
            if q in seen or px.get(q) != col:
                continue
            seen.add(q)
            cells.append(q)
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                stack.append((q[0] + d[0], q[1] + d[1]))
        out.append((len(cells), col, cells))
    out.sort(reverse=True, key=lambda r: r[0])
    return out


def analyse(px, name):
    """Body = the largest block's colour family. Accent = the biggest region
    whose hue is far from it."""
    n = len(px)
    bl = blocks(px)
    body_col = bl[0][1]
    bh, bl_, bs = hls(body_col)
    body_hue = bh * 360

    # --- 1. contour: perimeter vs interior, and how dark the darkest is ------
    per = [c for (x, y), c in px.items()
           if any((x + a, y + b) not in px for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    inner = [c for (x, y), c in px.items()
             if all((x + a, y + b) in px for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    darkest = min(px.values(), key=lum)
    contour = (st.median([lum(c) for c in per]) - st.median([lum(c) for c in inner])) if inner else 0
    # is the darkest colour mostly ON the perimeter?
    dark_cells = [k for k, c in px.items() if lum(c) <= lum(darkest) + 12]
    dark_on_edge = sum(1 for (x, y) in dark_cells
                       if any((x + a, y + b) not in px
                              for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))))
    edge_share = dark_on_edge / max(1, len(dark_cells))

    # --- 2/3. accent: hue vs value vs saturation, and how big ---------------
    accent = None
    for size, col, cells in bl[1:]:
        h, l, s = hls(col)
        if hue_gap(h * 360, body_hue) > 30 and size >= 3:
            accent = (size, col, cells)
            break
    accent_info = None
    if accent:
        size, col, cells = accent
        h, l, s = hls(col)
        accent_info = dict(
            area=size / n,
            hue_distance=round(hue_gap(h * 360, body_hue)),
            value_distance=round(abs(lum(col) - lum(body_col))),
            saturation_ratio=round(s / max(0.01, bs), 2),
            body_rgb=tuple(body_col[:3]), accent_rgb=tuple(col[:3]))

    # total share of pixels whose hue is far from the body hue
    far = sum(1 for c in px.values()
              if hls(c)[2] > 0.12 and hue_gap(hls(c)[0] * 360, body_hue) > 40)

    # --- 4. highlight: where is the brightest region, and is it concentrated -
    top = max(px.values(), key=lum)
    hi_cells = [k for k, c in px.items() if lum(c) >= lum(top) - 10]
    ys = [y for _, y in px]
    xs = [x for x, _ in px]
    lo_y, hi_y = min(ys), max(ys)
    lo_x, hi_x = min(xs), max(xs)
    hi_depth = st.mean((y - lo_y) / max(1, hi_y - lo_y) for _, y in hi_cells)
    hi_span = len(hi_cells) / n

    # --- 5. contact shadow: are the bottom rows darker than the body --------
    body_l = st.median([lum(c) for c in px.values()])
    row_l = {}
    for (x, y), c in px.items():
        row_l.setdefault(y, []).append(lum(c))
    bottom = st.median(row_l[hi_y]) - body_l
    second = (st.median(row_l[hi_y - 1]) - body_l) if (hi_y - 1) in row_l else None

    return dict(name=name, cells=n, colors=len(set(px.values())),
                span=round(max(lum(c) for c in px.values()) - lum(darkest)),
                contour=round(contour), darkest_lum=round(lum(darkest)),
                dark_edge_share=round(edge_share, 2),
                accent=accent_info, far_hue_share=round(far / n, 3),
                hi_depth=round(hi_depth, 2), hi_span=round(hi_span, 3),
                bottom=round(bottom), second=None if second is None else round(second),
                wh=round((hi_x - lo_x + 1) / (hi_y - lo_y + 1), 2),
                blocks_over_3=sum(1 for s, _, _ in bl if s >= 3))


def main():
    print("=== GROUP B — the four hats chosen as good " + "=" * 30)
    refs = []
    for path, name in REFS:
        r = analyse(frame(read_rgba_png(path)), name)
        refs.append(r)
        print(f"\n{name}")
        print(f"  cells {r['cells']:>3}  colours {r['colors']:>2}  span {r['span']:>3}  "
              f"w/h {r['wh']}  blocks>=3px {r['blocks_over_3']}")
        print(f"  contour: perimeter-interior {r['contour']:+4}   darkest luminance "
              f"{r['darkest_lum']:>3}   darkest sits on the edge {r['dark_edge_share']:.0%}")
        print(f"  highlight: depth {r['hi_depth']} from top, {r['hi_span']:.1%} of the sprite")
        print(f"  contact: bottom row {r['bottom']:+}, second row "
              f"{'n/a' if r['second'] is None else format(r['second'], '+')}")
        if r["accent"]:
            a = r["accent"]
            print(f"  ACCENT {a['accent_rgb']} vs body {a['body_rgb']}: "
                  f"hue {a['hue_distance']}deg  value {a['value_distance']}  "
                  f"sat x{a['saturation_ratio']}  area {a['area']:.1%}")
        else:
            print("  ACCENT: none found (no contiguous region >30deg from the body hue)")
        print(f"  pixels far from the body hue: {r['far_hue_share']:.1%}")

    print("\n=== GROUP A — vanilla, for range " + "=" * 40)
    im = read_rgba_png(VANILLA)
    W = len(im[0])
    van = []
    for i in range((len(im) // 80) * (W // 20)):
        px = frame(im, (i * 20) % W, (i * 20 // W) * 80)
        if len(px) >= 24:
            van.append(analyse(px, str(i)))
    def med(key, sub=None):
        vals = [(r[key][sub] if sub else r[key]) for r in van
                if r[key] is not None and (sub is None or r[key].get(sub) is not None)]
        return st.median(vals) if vals else None
    print(f"  n={len(van)}   colours {med('colors')}  span {med('span')}  "
          f"contour {med('contour')}  hi_depth {med('hi_depth')}")
    print(f"  bottom row {med('bottom')}  second row {med('second')}  "
          f"darkest-on-edge {med('dark_edge_share'):.0%}")
    with_accent = [r for r in van if r["accent"]]
    print(f"  hats with a hue accent: {len(with_accent)}/{len(van)} "
          f"({len(with_accent)/len(van):.0%})")
    if with_accent:
        print(f"    of those: hue distance {st.median(r['accent']['hue_distance'] for r in with_accent):.0f}deg  "
              f"value {st.median(r['accent']['value_distance'] for r in with_accent):.0f}  "
              f"area {st.median(r['accent']['area'] for r in with_accent):.1%}")

    print("\n=== OURS " + "=" * 55)
    from v5.library import brimmed_hat, brimless_hat            # noqa: F401
    from v5.pipeline import generate_batch
    ours = [analyse(g.raster["front"], str(g.spec.seed))
            for g in generate_batch(range(120), slot="HEAD") if len(g.raster["front"]) >= 24]
    def omed(key, sub=None):
        vals = [(r[key][sub] if sub else r[key]) for r in ours
                if r[key] is not None and (sub is None or r[key].get(sub) is not None)]
        return st.median(vals) if vals else None
    print(f"  n={len(ours)}   colours {omed('colors')}  span {omed('span')}  "
          f"contour {omed('contour')}  hi_depth {omed('hi_depth')}")
    print(f"  bottom row {omed('bottom')}  second row {omed('second')}  "
          f"darkest-on-edge {omed('dark_edge_share'):.0%}")
    oa = [r for r in ours if r["accent"]]
    print(f"  hats with a hue accent: {len(oa)}/{len(ours)} ({len(oa)/len(ours):.0%})")


if __name__ == "__main__":
    main()
