"""PARTS 6 + 7 — worn-fit ranges from real captures, and where V5 sits in them.

Groups are taken from the capture folder prefix:
    VAN*  vanilla calibration          REF*  the four chosen references
    V5*   our generated hats
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

sys.path.insert(0, "tools")
from qc_metrics import measure_capture                            # noqa: E402

KEYS = [
    ("hat_top", "hat top vs head top (px, 4x)"),
    ("hat_bottom", "hat bottom vs head top"),
    ("contact_band_y", "contact band y"),
    ("head_column_coverage", "head columns covered"),
    ("overhang_left", "overhang left"),
    ("overhang_right", "overhang right"),
    ("top_clearance", "top clearance above head"),
    ("face_pixels", "pixels in the face box"),
    ("face_intrusion_depth", "face intrusion depth"),
    ("seated_columns", "seated columns"),
    ("floating_columns", "floating columns"),
    ("max_floating_gap", "max floating gap"),
    ("hat_pixels", "hat pixels drawn"),
]
STAB = [("crown_offset_spread", "crown drift across directions"),
        ("hat_top_spread", "top drift"),
        ("hat_bottom_spread", "bottom drift")]


def group_of(name: str) -> str | None:
    if name.startswith("VAN"):
        return "vanilla"
    if name.startswith("REF"):
        return "reference"
    if name.startswith("V5Hat"):
        return "V5"
    return None


def band(vals):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    n = len(vals)
    return (vals[max(0, int(n * .1))], vals[n // 2], vals[min(n - 1, int(n * .9))], n)


def main(argv):
    roots = argv or ["qc_bridge/captures"]
    data = {"vanilla": [], "reference": [], "V5": []}
    for root in roots:
        for session in sorted(os.listdir(root)):
            sdir = os.path.join(root, session)
            if not os.path.isdir(sdir):
                continue
            for name in sorted(os.listdir(sdir)):
                g = group_of(name)
                folder = os.path.join(sdir, name)
                if not g or not os.path.isdir(folder):
                    continue
                m = measure_capture(folder)
                f = m["directions"].get("front")
                if f and "error" not in f:
                    f["_stability"] = m.get("stability", {})
                    f["_name"] = name
                    data[g].append(f)

    print(f"captures: vanilla {len(data['vanilla'])}  "
          f"reference {len(data['reference'])}  V5 {len(data['V5'])}")
    print("\nall figures are 4x screen pixels (divide by 4 for sprite pixels)\n")
    print(f"{'metric':<32}{'VANILLA p10/med/p90':>26}{'REFERENCE':>16}{'V5 median':>12}  verdict")
    for key, label in KEYS:
        v = band(r.get(key) for r in data["vanilla"])
        rf = band(r.get(key) for r in data["reference"])
        o = band(r.get(key) for r in data["V5"])
        if not (v and o):
            continue
        inrange = v[0] <= o[1] <= v[2]
        mark = "ok" if inrange else "OUT OF RANGE"
        rs = f"{rf[1]:.1f}" if rf else "-"
        print(f"  {label:<30}{v[0]:>7.1f}/{v[1]:>6.1f}/{v[2]:>6.1f}{rs:>16}{o[1]:>12.1f}  {mark}")

    print()
    for key, label in STAB:
        v = band(r["_stability"].get(key) for r in data["vanilla"])
        o = band(r["_stability"].get(key) for r in data["V5"])
        rf = band(r["_stability"].get(key) for r in data["reference"])
        if not (v and o):
            continue
        rs = f"{rf[1]:.1f}" if rf else "-"
        print(f"  {label:<30}{v[0]:>7.1f}/{v[1]:>6.1f}/{v[2]:>6.1f}{rs:>16}{o[1]:>12.1f}"
              f"  {'ok' if o[1] <= v[2] else 'OUT OF RANGE'}")

    worst = sorted(data["V5"], key=lambda r: -(r.get("face_pixels") or 0))[:6]
    print("\nV5 hats furthest into the face box:")
    for r in worst:
        print(f"  {r['_name']:<26} face {r['face_pixels']:>4}px  depth {r['face_intrusion_depth']:>3}  "
              f"top {r['hat_top']:>4}  floating {r['floating_columns']:>2}")

    json.dump({k: [{kk: vv for kk, vv in r.items() if not kk.startswith('_') or kk == '_name'}
                   for r in v] for k, v in data.items()},
              open("output/v5_hat_reconstruction/worn_fit.json", "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
