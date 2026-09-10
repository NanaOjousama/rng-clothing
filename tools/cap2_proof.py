"""Small controlled proof for the cap2 source-derived base.

Only combinations the compatibility grammar marks ALLOW are generated, and the
only remix axes it permits are palette and the presence of front_emblem at its
authored cells.  No silhouette is invented, nothing is repositioned, and no
asset from the rejected soft_cap is touched.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored, pngio
from v5.source import dissect, semantic

BASE = "authored/source_bases/cap2"
OUT = "output/cap2_proof"
BG = (26, 28, 32, 255); INK = (233, 233, 228, 255); DIM = (122, 126, 132, 255)
OK = (110, 200, 135, 255); CH1 = (48, 52, 58, 255); CH2 = (38, 41, 46, 255)
DIRS = ["Front", "Right", "Left", "Back"]


def multiply(colour, grey):
    return tuple(min(255, round(c * grey / 255)) for c in colour[:3])


def recolour(frames, steps_by_dir, vocab, tint):
    """Tint the authored value ladder — the operation Fashion Sense itself
    performs on greyscale art, so the material reads as the author drew it."""
    levels = [sum(c) / 3 for c in vocab]
    ramp = [multiply(tint, lv) for lv in levels]
    out = {}
    for d, f in frames.items():
        rows = [[(0, 0, 0, 0)] * len(f[0]) for _ in f]
        for (x, y), s in steps_by_dir[d].items():
            rows[y][x] = (*ramp[min(s, len(ramp) - 1)], 255)
        out[d] = rows
    return out


def main():
    man = json.load(open(f"{BASE}/manifest.json"))
    compat = json.load(open(f"{BASE}/compatibility.json"))
    assert compat["matrix"]["cap2 x front_emblem"]["verdict"] == "ALLOW"

    cat = json.load(open("source_catalog/catalog.json"))
    app = next(a for a in cat["appearances"]
               if a["name"] == "Cap 2" and a["pack"].startswith("More Acc"))
    frames = dissect.frames_of(app)
    vocab = [tuple(c) for c in man["base"]["vocabulary"]]

    # base with the emblem removed, and the emblem itself
    emblem = {tuple(int(v) for v in k.split(",")): tuple(v)
              for k, v in man["components"]["front_emblem"]["cells"].items()}
    fill = tuple(man["components"]["front_emblem"]["fill_value"])
    base = {d: [list(r) for r in f] for d, f in frames.items()}
    for (x, y) in emblem:
        base["Front"][y][x] = fill

    steps_base = {d: dissect.step_map(f, vocab) for d, f in base.items()}
    steps_full = {d: dissect.step_map(f, vocab) for d, f in frames.items()}

    lib = authored.load()
    VARIANTS = [
        ("V1 source greyscale, emblem ON", None, True),
        ("V2 stone blue, emblem ON", "EVERYDAY_STONE_BLUE", True),
        ("V3 stone blue, emblem OFF", "EVERYDAY_STONE_BLUE", False),
        ("V4 autumn ochre, emblem ON", "AUTUMN_OCHRE_PLUM", True),
        ("V5 coastal seafoam, emblem ON", "COASTAL_SEAFOAM_CORAL", True),
    ]

    def checker(w, h, s=2):
        return [[(CH1 if ((x // s + y // s) % 2) else CH2) for x in range(w)]
                for y in range(h)]

    def tile(f, sc, l, sub="", c=INK):
        h, w = len(f), len(f[0]); bg = checker(w, h)
        comp = [[f[y][x] if f[y][x][3] else bg[y][x] for x in range(w)]
                for y in range(h)]
        art = pngio.nearest_scale(comp, sc)
        img = pngio.blank_image(max(len(art[0]), 100), len(art) + 22, BG)
        pngio.blit(img, art, 0, 0)
        pngio.draw_text(img, l, 1, len(art) + 3, color=c)
        if sub: pngio.draw_text(img, sub, 1, len(art) + 13, color=DIM)
        return img

    def title(t, w=960, c=INK):
        im = pngio.blank_image(w, 12, BG); pngio.draw_text(im, t, 0, 1, color=c)
        return im

    def rowof(ts, gap=8):
        h = max(len(t) for t in ts); w = sum(len(t[0]) for t in ts) + gap * (len(ts) - 1)
        r = pngio.blank_image(w, h, BG); x = 0
        for t in ts: pngio.blit(r, t, x, 0); x += len(t[0]) + gap
        return r

    rows = [title("CAP 2  source-derived base   'Cap 2' — More Accessories and "
                  "Stuff, by plurffle   [source pixels used directly]")]

    rows.append(title("1  ORIGINAL SOURCE (untouched, the reconstruction target)", c=DIM))
    rows.append(rowof([tile(frames[d], 8, d) for d in DIRS]))

    rows.append(title("2  EXTRACTED PIECES", c=DIM))
    hole = [list(r) for r in base["Front"]]
    em = [[(0, 0, 0, 0)] * 20 for _ in range(20)]
    for (x, y), px in emblem.items(): em[y][x] = px
    hl = [[(0, 0, 0, 0)] * 20 for _ in range(20)]
    for y in range(6, 8):
        for x in range(9, 12):
            if dissect.step_map(frames["Front"], vocab).get((x, y)) == 5:
                hl[y][x] = tuple(frames["Front"][y][x])
    rows.append(rowof([
        tile(hole, 8, "base (emblem removed)", "hole filled with the authored value"),
        tile(em, 8, "front_emblem", "4 cells  FAMILY-SPECIFIC"),
        tile(hl, 8, "crown_highlight", "BASE-SPECIFIC, left embedded"),
    ]))

    rows.append(title("3  RECONSTRUCTION  base + front_emblem  vs  source", c=DIM))
    rebuilt = {d: [list(r) for r in f] for d, f in base.items()}
    for (x, y), px in emblem.items(): rebuilt["Front"][y][x] = px
    ts = []
    for d in DIRS:
        a, b = frames[d], rebuilt[d]
        n = 0; dd = []
        for y in range(len(a)):
            r = []
            for x in range(len(a[0])):
                if tuple(a[y][x]) != tuple(b[y][x]): r.append((228, 74, 66, 255)); n += 1
                elif a[y][x][3]: r.append((70, 74, 80, 255))
                else: r.append((40, 43, 48, 255))
            dd.append(r)
        ts.append(tile(dd, 8, d, f"{n} px differ", OK if n == 0 else (228, 74, 66, 255)))
    rows.append(rowof(ts))

    rows.append(title("4  CONTROLLED VARIANTS  (only ALLOW combinations; "
                      "palette and emblem presence are the only permitted axes)", c=DIM))
    for label, pal_id, with_emblem in VARIANTS:
        src_steps = steps_full if with_emblem else steps_base
        src_frames = frames if with_emblem else base
        if pal_id is None:
            f = {d: [list(r) for r in src_frames[d]] for d in DIRS}
        else:
            pal = next(p for p in lib.palettes if p.id == pal_id)
            f = recolour(src_frames, src_steps, vocab, pal.ramps["body"][3])
        rows.append(title("   " + label, c=DIM))
        rows.append(rowof([tile(f[d], 6, d) for d in DIRS]))

    pad = 12; gap = 10
    W = max(len(r[0]) for r in rows) + pad * 2
    H = sum(len(r) for r in rows) + gap * (len(rows) - 1) + pad * 2
    sh = pngio.blank_image(W, H, BG); y = pad
    for r in rows: pngio.blit(sh, r, pad, y); y += len(r) + gap
    os.makedirs(OUT, exist_ok=True)
    pngio.write_rgba_png(f"{OUT}/proof.png", sh)
    print(f"wrote {OUT}/proof.png   variants={len(VARIANTS)}")


if __name__ == "__main__":
    main()
