"""In-game acceptance: untouched source-pack hat vs its Source-Backed V2 neutral twin.

Diagnose only. Both captures must come from ONE game session (same farmer, same
hairstyle, same hat tint colour), which `qc.py worn` guarantees by stamping every
capture folder with the running session.

Per pair and per direction (front/right/back/left) it answers:

    appearance   worn.png source vs V2: identical pixels?
    scene        nohat.png source vs V2: identical? (if not, the scene moved and
                 nothing else in the row can be trusted)
    placement    hat-only bounds: same screen position and size?
    flipped      the LEFT row is the test of Fashion Sense `Flipped` (source)
                 vs an explicit mirrored frame (V2)

    python3 tools/compare_source_v2_worn.py [session-dir]
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from v5.pngio import blank_image, blit, nearest_scale, read_rgba_png, write_rgba_png  # noqa: E402

CAPTURES = os.path.join(ROOT, "qc_bridge", "captures")
PAIRS = [("beret_02", "Beret", "SB2Beret02Neutral"),
         ("beret_01", "hyoung_hats_24", "SB2Beret01Neutral")]
DIRS = ("front", "right", "back", "left")


def diff(a, b):
    return [(x, y) for y in range(len(a)) for x in range(len(a[0])) if a[y][x] != b[y][x]]


def diff_img(a, b):
    img = blank_image(len(a[0]), len(a), (255, 255, 255, 255))
    for y in range(len(a)):
        for x in range(len(a[0])):
            pa, pb = a[y][x], b[y][x]
            if pa != pb:
                img[y][x] = (230, 30, 30, 255)
            elif pa[3]:
                img[y][x] = (205, 205, 205, 255)
    return img


def crop(img, box):
    x0, y0, x1, y1 = box
    return [r[x0:x1] for r in img[y0:y1]]


def main():
    session = sys.argv[1] if len(sys.argv) > 1 else os.path.join(CAPTURES, sorted(os.listdir(CAPTURES))[-1])
    out_dir = os.path.join(ROOT, "experiments", "source_fidelity", "v2_worn", os.path.basename(session))
    os.makedirs(out_dir, exist_ok=True)
    report = {"session": session, "pairs": {}}
    for base, src_label, v2_label in PAIRS:
        sd, vd = os.path.join(session, src_label), os.path.join(session, v2_label)
        if not (os.path.isdir(sd) and os.path.isdir(vd)):
            report["pairs"][base] = {"missing": [p for p in (sd, vd) if not os.path.isdir(p)]}
            print(f"{base}: MISSING capture folder(s) {report['pairs'][base]['missing']}")
            continue
        ss = json.load(open(os.path.join(sd, "render_state.json")))
        vs = json.load(open(os.path.join(vd, "render_state.json")))
        rows, pair = [], {}
        for d in DIRS:
            worn_s, worn_v = (read_rgba_png(os.path.join(p, f"{d}_worn.png")) for p in (sd, vd))
            nohat_s, nohat_v = (read_rgba_png(os.path.join(p, f"{d}_nohat.png")) for p in (sd, vd))
            only_s, only_v = (read_rgba_png(os.path.join(p, f"{d}_hatonly.png")) for p in (sd, vd))
            bs, bv = ss["directions"][d]["hat_only_bounds"], vs["directions"][d]["hat_only_bounds"]
            r = {"worn_px_diff": len(diff(worn_s, worn_v)),
                 "nohat_px_diff": len(diff(nohat_s, nohat_v)),
                 "hatonly_px_diff": len(diff(only_s, only_v)),
                 "hat_bounds_source": bs, "hat_bounds_v2": bv,
                 "placement_offset_screen_px": [bv["x"] - bs["x"], bv["y"] - bs["y"]],
                 "placement_offset_logical_px": [(bv["x"] - bs["x"]) / 4, (bv["y"] - bs["y"]) / 4]}
            r["identical"] = r["worn_px_diff"] == 0 and r["hatonly_px_diff"] == 0
            pair[d] = r
            # side by side: source worn | V2 worn | diff, cropped round the head, x3
            box = (60, 20, 196, 190)
            row = [crop(worn_s, box), crop(worn_v, box), crop(diff_img(worn_s, worn_v), box)]
            w, h = box[2] - box[0], box[3] - box[1]
            strip = blank_image(w * 3 + 8, h, (255, 255, 255, 255))
            for i, im in enumerate(row):
                blit(strip, [[p if p[3] else (238, 238, 238, 255) for p in rr] for rr in im], i * (w + 4), 0)
            rows.append(strip)
            print(f"{base:9} {d:5}  worn diff {r['worn_px_diff']:5}  hat-only diff {r['hatonly_px_diff']:5}  "
                  f"scene diff {r['nohat_px_diff']:4}  placement offset {r['placement_offset_logical_px']} logical px"
                  + ("   IDENTICAL" if r["identical"] else ""))
        sheet = blank_image(len(rows[0][0]), sum(len(r) for r in rows) + 4 * len(rows), (255, 255, 255, 255))
        y = 0
        for r in rows:
            blit(sheet, r, 0, y)
            y += len(r) + 4
        write_rgba_png(os.path.join(out_dir, f"{base}_source_vs_v2_x3.png"), nearest_scale(sheet, 3))
        report["pairs"][base] = pair
    with open(os.path.join(out_dir, "report.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    print(f"wrote {out_dir}")


if __name__ == "__main__":
    main()
