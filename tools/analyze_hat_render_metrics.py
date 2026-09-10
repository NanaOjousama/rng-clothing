"""Phase-4 rendering metrics: ours vs vanilla vs the four reference hats."""
import colorsys, json, os, statistics as st, sys
sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing")
from v5.pngio import read_rgba_png

VANILLA = ("/run/media/deck/USD00/steamapps/common/Stardew Valley/"
           "Content (unpacked)/Characters/Farmer/hats.png")

def lum(c):
    r, g, b = c[:3]
    return 0.299*r + 0.587*g + 0.114*b

def hsv(c):
    return colorsys.rgb_to_hsv(c[0]/255, c[1]/255, c[2]/255)

def metrics(px):
    """px: list of (r,g,b,a) opaque pixels of one 20x20 frame, with coords."""
    cells = [(xy, c) for xy, c in px if c[3] > 0]
    if len(cells) < 12:
        return None
    cols = [c for _, c in cells]
    L = [lum(c) for c in cols]
    mx, mn = max(L), min(L)
    hi = sum(1 for v in L if v >= mx - 12) / len(L)
    # dominant hue = hue of the most common colour with sat > .12
    from collections import Counter
    cnt = Counter(cols)
    body = None
    for c, _ in cnt.most_common():
        h, s, v = hsv(c)
        if s > 0.12:
            body = h
            break
    if body is None:
        far = 0.0
    else:
        far = 0
        for c in cols:
            h, s, v = hsv(c)
            if s <= 0.08:
                continue
            d = abs(h - body)
            d = min(d, 1 - d) * 360
            if d > 25:
                far += 1
        far /= len(L)
    # contact shadow: 2nd-from-bottom occupied row vs overall mean
    rows = {}
    for (x, y), c in cells:
        rows.setdefault(y, []).append(lum(c))
    ys = sorted(rows)
    second = rows[ys[-2]] if len(ys) >= 2 else rows[ys[-1]]
    contact = st.mean(second) - st.mean(L)
    return dict(colors=len(set(cols)), span=mx-mn, darkest=mn, brightest=mx,
                highlight=100*hi, far_hue=100*far, contact=contact,
                area=len(L))

def frames_from_sheet(path, fw=20, fh=20, per=4):
    im = read_rgba_png(path)
    w, h = len(im[0]), len(im)
    out, idx = [], 0
    while True:
        x0, y0 = (idx*fw) % w, (idx*fw//w)*(fh*per)
        if y0 + fh*per > h:
            break
        front = [((x, y), tuple(im[y0+y][x0+x])) for y in range(fh) for x in range(fw)]
        if sum(1 for _, c in front if c[3] > 0) >= 12:
            out.append(front)
        idx += 1
    return out

def summarize(name, ms):
    ms = [m for m in ms if m]
    keys = ["colors", "span", "darkest", "highlight", "far_hue", "contact"]
    print(f"\n{name}  (n={len(ms)})")
    for k in keys:
        vals = sorted(m[k] for m in ms)
        med = st.median(vals)
        print(f"  {k:10s} median {med:7.1f}   p10 {vals[int(.1*(len(vals)-1))]:7.1f}"
              f"   p90 {vals[int(.9*(len(vals)-1))]:7.1f}")
    return ms

if __name__ == "__main__":
    if os.path.exists(VANILLA):
        summarize("VANILLA", [metrics(f) for f in frames_from_sheet(VANILLA)])
    ref = []
    base = "/run/media/deck/USD00/RNG_clothing/good hats"
    for p in ("0_BoysCap.png", "1_SweetGent.png", "hats_8/hat.png", "hats_11/hat.png"):
        fp = os.path.join(base, p)
        if os.path.exists(fp):
            fr = frames_from_sheet(fp)
            if fr:
                ref.append(metrics(fr[0]))
    summarize("REFERENCE (user's good hats)", ref)
