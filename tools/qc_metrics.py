"""PART 5 + PART 7 — worn-fit metrics from REAL in-game captures.

Everything here reads the isolated capture pair the bridge writes:

    <dir>_worn.png    the farmer WITH the hat, drawn by the real
                      Fashion-Sense-patched FarmerRenderer
    <dir>_nohat.png   the same farmer with the hat cleared
    <dir>_hatonly.png their difference — the hat's actual drawn footprint

The difference image is what makes seating measurable.  An isolated 20x20 sprite
cannot tell you where a hat sits on a head; a pair of real renders can, because
the head is in both and the hat is in only one.

Nothing in this file reconstructs the farmer or the hat.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing")
from v5.pngio import read_rgba_png                                # noqa: E402

DIRECTIONS = ("front", "right", "back", "left")


def opaque(rows, threshold=8):
    return {(x, y) for y in range(len(rows)) for x in range(len(rows[0]))
            if rows[y][x][3] > threshold}


def bounds(cells):
    if not cells:
        return None
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    return dict(x0=min(xs), x1=max(xs), y0=min(ys), y1=max(ys),
                w=max(xs) - min(xs) + 1, h=max(ys) - min(ys) + 1, n=len(cells))


def head_region(bare):
    """The head, from the REAL bare-farmer render.

    Taken as the top 40% of the standing sprite's own bounding box rather than a
    hardcoded rectangle, so it follows whatever the renderer actually drew —
    custom body, height offset, animation frame and all.
    """
    b = bounds(bare)
    if not b:
        return None, None
    head_bottom = b["y0"] + int((b["y1"] - b["y0"] + 1) * 0.40)
    head = {(x, y) for (x, y) in bare if y <= head_bottom}
    return head, bounds(head)


def face_region(bare, head_box):
    """A conservative face box: the lower two-thirds of the head, inset from the
    sides.  Vanilla hats DO legitimately overlap the very top of this, so the
    metric reports intrusion rather than forbidding it."""
    if not head_box:
        return set()
    y0 = head_box["y0"] + int(head_box["h"] * 0.35)
    inset = max(1, head_box["w"] // 6)
    return {(x, y) for x in range(head_box["x0"] + inset, head_box["x1"] - inset + 1)
            for y in range(y0, head_box["y1"] + 1)}


def measure_direction(folder, direction):
    worn_p = os.path.join(folder, f"{direction}_worn.png")
    bare_p = os.path.join(folder, f"{direction}_nohat.png")
    only_p = os.path.join(folder, f"{direction}_hatonly.png")
    if not (os.path.exists(worn_p) and os.path.exists(bare_p)):
        return None

    worn = opaque(read_rgba_png(worn_p))
    bare = opaque(read_rgba_png(bare_p))
    hat = opaque(read_rgba_png(only_p)) if os.path.exists(only_p) else (worn - bare)

    head, head_box = head_region(bare)
    hat_box = bounds(hat)
    if not (head_box and hat_box):
        return dict(direction=direction, error="nothing rendered")

    face = face_region(bare, head_box)
    head_cx = (head_box["x0"] + head_box["x1"]) / 2
    hat_cx = (hat_box["x0"] + hat_box["x1"]) / 2

    # --- A. seating -----------------------------------------------------
    # rows where the hat and the head share columns: the actual contact band
    hat_cols = {x for x, _ in hat}
    contact = [y for (x, y) in bare if x in hat_cols and (x, y - 1) in hat]
    covered_cols = len({x for x, _ in head} & hat_cols)

    # --- B. face intrusion ----------------------------------------------
    intruding = hat & face
    max_intrusion = (max(y for _, y in intruding) - min(y for _, y in face)) if intruding else 0

    # --- C/D. contact vs floating ---------------------------------------
    # vertical gap between the hat's lowest pixel in each shared column and the
    # head's highest pixel in that column
    gaps = []
    for x in sorted(hat_cols):
        hs = [y for (xx, y) in hat if xx == x]
        bs = [y for (xx, y) in bare if xx == x]
        if hs and bs:
            gaps.append(min(bs) - max(hs) - 1)
    floating = [g for g in gaps if g > 0]

    # crown centre: the upper half of the hat only.  A declared directional
    # piece (a visor, a hanging tail) legitimately widens the footprint in
    # profile, and measuring the whole bbox reported that as a placement
    # instability — which is exactly the bug this metric exists to catch, so it
    # must not fire on the feature that is working as designed.
    crown_cut = hat_box["y0"] + max(1, hat_box["h"] // 2)
    crown = {(x, y) for (x, y) in hat if y <= crown_cut}
    crown_box = bounds(crown) or hat_box
    crown_cx = (crown_box["x0"] + crown_box["x1"]) / 2

    return dict(
        direction=direction,
        crown_offset=round(crown_cx - head_cx, 2),
        crown_bounds=crown_box,
        hat_bounds=hat_box, head_bounds=head_box,
        # A
        centre_offset=round(hat_cx - head_cx, 2),
        hat_top=hat_box["y0"] - head_box["y0"],
        hat_bottom=hat_box["y1"] - head_box["y0"],
        contact_band_y=(min(contact) - head_box["y0"]) if contact else None,
        head_columns_covered=covered_cols,
        head_column_coverage=round(covered_cols / max(1, head_box["w"]), 2),
        overhang_left=max(0, head_box["x0"] - hat_box["x0"]),
        overhang_right=max(0, hat_box["x1"] - head_box["x1"]),
        top_clearance=head_box["y0"] - hat_box["y0"],
        # B
        face_pixels=len(intruding),
        face_intrusion_depth=max_intrusion,
        # C/D
        seated_columns=sum(1 for g in gaps if g <= 0),
        floating_columns=len(floating),
        max_floating_gap=max(floating) if floating else 0,
        # scale
        hat_pixels=len(hat),
    )


def measure_capture(folder):
    out = {"folder": folder, "directions": {}}
    for d in DIRECTIONS:
        m = measure_direction(folder, d)
        if m:
            out["directions"][d] = m

    # --- E. direction stability -----------------------------------------
    got = [m for m in out["directions"].values() if "error" not in m]
    if len(got) >= 2:
        def spread(key):
            vals = [m[key] for m in got if m.get(key) is not None]
            return round(max(vals) - min(vals), 2) if vals else None
        out["stability"] = dict(
            # the one that matters: does the HAT ITSELF move as the farmer turns
            crown_offset_spread=spread("crown_offset"),
            centre_offset_spread=spread("centre_offset"),
            hat_top_spread=spread("hat_top"),
            hat_bottom_spread=spread("hat_bottom"),
            contact_band_spread=spread("contact_band_y"),
            overhang_left_spread=spread("overhang_left"),
            overhang_right_spread=spread("overhang_right"),
            width_spread=spread_box(got, "w"),
            height_spread=spread_box(got, "h"),
        )
    return out


def spread_box(rows, key):
    vals = [m["hat_bounds"][key] for m in rows if m.get("hat_bounds")]
    return (max(vals) - min(vals)) if vals else None


def main(argv):
    root = argv[0] if argv else None
    if not root:
        print(__doc__)
        return 2
    results = []
    for name in sorted(os.listdir(root)):
        folder = os.path.join(root, name)
        if os.path.isdir(folder):
            results.append(measure_capture(folder))
    out = os.path.join(root, "fit_metrics.json")
    with open(out, "w") as fh:
        json.dump(results, fh, indent=1)
    print(f"wrote {out}  ({len(results)} hats)")
    for r in results:
        f = r["directions"].get("front")
        if not f or "error" in f:
            continue
        s = r.get("stability", {})
        print(f"  {os.path.basename(r['folder']):<28} "
              f"centre {f['centre_offset']:+5.1f}  top {f['hat_top']:+3}  "
              f"contact {f['contact_band_y']}  face {f['face_pixels']:>3}px  "
              f"floating {f['floating_columns']:>2}col  "
              f"crown-drift {s.get('crown_offset_spread')}  "
              f"bbox-drift {s.get('centre_offset_spread')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
