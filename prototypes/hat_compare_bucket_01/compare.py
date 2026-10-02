#!/usr/bin/env python3
"""Head-to-head: recipe (A) vs AI-native PixelLab (B) on the bucket hat.

    python3 prototypes/hat_compare_bucket_01/compare.py

A  = prototypes/hat_recipe_engine_01 bucket template, rendered with its preview palette.
B* = PixelLab outputs in ai_raw/, used AS GENERATED.  The only operation applied is
     seating: each frame is translated (never scaled, never repainted) so its lowest
     row lands on vanilla's brim row and it is centred, exactly how a hat is placed
     on the 20x20 vanilla hat grid.  Frames whose content cannot fit 20x20 are
     cropped and the crop is reported.
REF = vanilla Bucket Hat (102).

Writes out/COMPARISON_SHEET.png, out/WORN_1X_2X_4X.png, out/metrics.json and the
seated 20x80 strips (front/right/left/back, vanilla order) for each contender.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "prototypes/hat_recipe_engine_01"))

from build import load_variants  # noqa: E402
from engine import build_template  # noqa: E402
from preview import draw_text, render_strip, vanilla_strip, worn_row  # noqa: E402
from v5.pngio import blank_image, blit, nearest_scale, read_rgba_png, write_rgba_png  # noqa: E402

RAW, OUT = HERE / "ai_raw", HERE / "out"
SEAT_BOTTOM = 12          # vanilla Bucket Hat 102: lowest hat row (brim) in the front frame
BG, LABEL = (58, 58, 68, 255), (230, 230, 230, 255)

# contender -> {view: raw file}; PixelLab south = front, east = facing right.
# B1 (80x20 four-view sheet) and B3 (32x32 Pro, 26-28 px wide hats) are recorded in
# README as failures and shown only on the scale panel; they are not seated here.
AI = {
    "B2 PixelLab Pro Flash 8-dir (text+style)": {"front": "B2_south.png", "right": "B2_east.png",
                                                  "left": "B2_west.png", "back": "B2_north.png"},
    "B4 PixelLab Pro 20px (64 cands) + rotate": {"front": "B4_south.png", "right": "B4_east.png",
                                                 "left": "B4_west.png", "back": "B4_north.png"},
}
VIEWS = ("front", "right", "left", "back")


def seat(img):
    """Translate content onto a 20x20 frame: bottom row -> SEAT_BOTTOM, bbox centred."""
    pts = [(x, y) for y, r in enumerate(img) for x, p in enumerate(r) if p[3]]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    dx = 10 - (x0 + x1 + 1) // 2
    dy = SEAT_BOTTOM - y1
    out = blank_image(20, 20)
    cropped = 0
    for (x, y) in pts:
        nx, ny = x + dx, y + dy
        if 0 <= nx < 20 and 0 <= ny < 20:
            out[ny][nx] = img[y][x]
        else:
            cropped += 1
    return out, {"content_w": x1 - x0 + 1, "content_h": y1 - y0 + 1, "cropped_px": cropped}


def stats(strip):
    px = [p for r in strip for p in r if p[3]]
    return {"colours": len({p[:3] for p in px}), "partial_alpha_px": sum(1 for p in px if p[3] < 255)}


def mirror_diff(strip):
    r, l = strip[20:40], strip[40:60]
    return sum(1 for y in range(20) for x in range(20) if (r[y][x][3] > 0) != (l[y][19 - x][3] > 0))


def main():
    OUT.mkdir(exist_ok=True)
    _, variants = load_variants()
    p, meta = variants["bucket"]
    contenders = {"A Recipe (deterministic)": render_strip(build_template(p), meta["preview_palette"])}
    metrics = {}
    for name, files in AI.items():
        if not all((RAW / f).exists() for f in files.values()):
            print("skip (missing raw):", name)
            continue
        strip, seat_info = [], {}
        for v in VIEWS:
            fr, info = seat(read_rgba_png(RAW / files[v]))
            strip += fr
            seat_info[v] = info
        contenders[name] = strip
        metrics[name] = {"seating": seat_info}
    contenders["REF vanilla Bucket Hat (102)"] = vanilla_strip(102)

    for name, st in contenders.items():
        m = metrics.setdefault(name, {})
        m.update(stats(st))
        m["left_vs_mirrored_right_px"] = mirror_diff(st)
        m["front_size"] = seat(st[0:20])[1] if any(p[3] for r in st[0:20] for p in r) else None
        tag = name.split()[0]
        write_rgba_png(OUT / f"{tag}_bucket_20x80.png", st)

    # comparison sheet: 6x strips (front right back left) + worn head crops
    names = list(contenders)
    s = 6
    cell_h = 24 * s + 40
    sheet = blank_image(96 * s + 96 * s + 60, cell_h * len(names) + 20, BG)
    for i, n in enumerate(names):
        st = contenders[n]
        y = 20 + i * cell_h
        draw_text(sheet, n.upper(), 20, y, scale=2, color=LABEL)
        row = blank_image(96, 24, (150, 150, 160, 255))
        for k, vi in enumerate((0, 1, 3, 2)):
            blit(row, st[vi * 20:vi * 20 + 20], k * 24 + 2, 2)
        blit(sheet, nearest_scale(row, s), 20, y + 30)
        blit(sheet, nearest_scale([r[:96] for r in worn_row(st)[0:24]], s), 40 + 96 * s, y + 30)
    write_rgba_png(OUT / "COMPARISON_SHEET.png", sheet)

    # worn: 1x / 2x / 4x
    game = blank_image(96, 40 * len(names), (126, 150, 110, 255))
    for i, n in enumerate(names):
        blit(game, worn_row(contenders[n]), 0, i * 40)
    x2, x4 = nearest_scale(game, 2), nearest_scale(game, 4)
    w = 20 + 96 + 30 + len(x2[0]) + 30 + len(x4[0]) + 20
    worn = blank_image(w, len(x4) + 70, BG)
    xs = [20, 146, 176 + len(x2[0])]
    for x, img, lab in zip(xs, (game, x2, x4), ("1X NATIVE", "2X", "4X NORMAL ZOOM")):
        draw_text(worn, lab, x, 12, scale=2, color=LABEL)
        blit(worn, img, x, 50)
    for i, n in enumerate(names):
        draw_text(worn, n.upper()[:34], xs[2] + 6, 50 + i * 160 + 4, scale=2, color=(20, 30, 20, 255))
    write_rgba_png(OUT / "WORN_1X_2X_4X.png", worn)
    # failed routes, shown as generated at native size (no seating, no shrinking)
    fails = [("B1 PRO 80X20 FOUR-VIEW SHEET: LAYOUT IGNORED", RAW / "B1_cand02.png"),
             ("B3 PRO 32X32 BEST FRONT: 26-28 PX WIDE = 2X STARDEW SCALE", RAW / "B3_cands/c08.png"),
             ("VANILLA BUCKET HAT 102 FOR SCALE", None)]
    fs = blank_image(100, 3 * 36, (150, 150, 160, 255))
    for i, (_, path) in enumerate(fails):
        img = read_rgba_png(path) if path else vanilla_strip(102)[0:20]
        blit(fs, img, 2, i * 36 + 2)
    big = nearest_scale(fs, 6)
    panel = blank_image(max(len(big[0]) + 40, 760), len(big) + 20, BG)
    blit(panel, big, 20, 10)
    for i, (lab, _) in enumerate(fails):
        draw_text(panel, lab, 20 + 6, 10 + i * 216 + 200, scale=2, color=(20, 20, 30, 255))
    write_rgba_png(OUT / "FAILED_ROUTES_NATIVE_6X.png", panel)
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=1) + "\n")
    for n, m in metrics.items():
        print(f"{n:45s} colours={m['colours']:3d} partialA={m['partial_alpha_px']} "
              f"L!=mirror(R)={m['left_vs_mirrored_right_px']} front={m['front_size']}")


if __name__ == "__main__":
    main()
