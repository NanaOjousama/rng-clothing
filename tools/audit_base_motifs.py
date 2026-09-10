"""Per-base motif audit from real captures: measure, classify, and record.

Judges each motif ON ONE BASE across all four directions, because a motif that
reads head-on can vanish in profile, and a motif that works on a knitted crown
can fragment on a cap's flat band row.  The output is a compatibility record —
motif x base — meant to outlive the run that produced it.

    python3 tools/audit_base_motifs.py <session-dir> <pack-dir> [--write]
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored                                              # noqa: E402
from v5.grammar import luminance                                     # noqa: E402
from v5.pngio import read_rgba_png                                   # noqa: E402

DIRS = ("front", "right", "left", "back")


def downscale(im, f=4):
    return [[tuple(im[y][x]) for x in range(0, len(im[0]), f)]
            for y in range(0, len(im), f)]


def anchor(cells):
    bottom = max(y for _, y in cells)
    xs = [x for x, y in cells if y == bottom]
    return (min(xs) + max(xs)) // 2, bottom


def fragments(cells):
    seen, n = set(), 0
    for c in cells:
        if c in seen:
            continue
        n += 1
        stack = [c]
        while stack:
            x, y = stack.pop()
            if (x, y) in seen:
                continue
            seen.add((x, y))
            stack += [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                      if (x + dx, y + dy) in cells and (x + dx, y + dy) not in seen]
    return n


def compare(session, folder, plain, view):
    p = os.path.join(session, folder, f"{view}_hatonly.png")
    if not os.path.exists(p):
        return None
    game = {(x, y): c for y, r in enumerate(downscale(read_rgba_png(p)))
            for x, c in enumerate(r) if c[3] > 0}
    off = {(x, y): tuple(px) for y, r in enumerate(plain.directions[view])
           for x, px in enumerate(r) if px[3] > 0}
    if not game or not off:
        return None
    gx, gy = anchor(set(game))
    ox, oy = anchor(set(off))
    dx, dy = ox - gx, oy - gy
    aligned = {(x + dx, y + dy): c for (x, y), c in game.items()}
    changed = {c for c in set(aligned) | set(off)
               if c not in aligned or c not in off
               or abs(luminance(aligned[c]) - luminance(off[c])) > 10}
    if not changed:
        return (0, 0.0, 0)
    dl = [abs(luminance(aligned[c]) - luminance(off[c]))
          if c in aligned and c in off else 255.0 for c in changed]
    return (len(changed), sum(dl) / len(dl), fragments(changed))


# A deliberate POINT ACCENT is one cell by design.  crown_button read clearly
# in the decoration checkpoint on both caps, so a size floor alone would throw
# away a motif the game has already validated — the same exception the library
# review carries.
POINT_ACCENT_DL = 120.0


def classify(per_view, probe_delta):
    """KEEP / KEEP BUT BASE-SPECIFIC / REWORK / DROP FOR THIS BASE."""
    vis = [v for v in per_view.values() if v]
    if not vis:
        return "DROP FOR THIS BASE", "renders nothing on this base"
    worst_frag = max(v[2] for v in vis)
    changed = [v[0] for v in vis]
    dls = [v[1] for v in vis]
    blind = [d for d, v in per_view.items() if v and v[0] < 3]
    if worst_frag >= 3:
        return "REWORK", f"fragments into {worst_frag} pieces at gameplay scale"
    if max(changed) <= 2 and min(dls) >= POINT_ACCENT_DL and worst_frag == 1:
        return "KEEP", (f"point accent: {max(changed)} cell at dL {min(dls):.0f}, "
                        f"visible in every view")
    if max(changed) < 4:
        return "DROP FOR THIS BASE", f"only {max(changed)} cells change in any view"
    if blind:
        return ("KEEP BUT BASE-SPECIFIC",
                f"invisible in {'/'.join(blind)} on this base")
    if min(dls) < 25:
        return "REWORK", f"contrast falls to dL {min(dls):.0f} in some view"
    if probe_delta is not None and probe_delta > 45:
        return ("KEEP BUT BASE-SPECIFIC",
                f"reading swings dL {probe_delta:.0f} between palettes")
    return "KEEP", f"{min(changed)}-{max(changed)} cells, dL {min(dls):.0f}-{max(dls):.0f}, <=2 fragments"


def main():
    session, pack = sys.argv[1], sys.argv[2]
    lib = authored.load()
    trace = json.load(open(os.path.join(pack, "TRACEABILITY.json")))
    base = trace["base"]
    rows = {}
    probes = {}
    for e in trace["entries"]:
        plain = authored.build(base, e["palette"], [], lib, style=e["style"])
        per = {d: compare(session, e["folder"], plain, d) for d in DIRS}
        if e["kind"] == "probe":
            probes[e["motifs"][0]] = per
        rows[e["folder"]] = (e, per)

    print(f"AUDIT — base: {base} — {len(rows)} entries\n")
    print(f"{'entry':22s} {'kind':7s} {'motifs':34s} "
          + " ".join(f"{d[:2]:>10s}" for d in DIRS))
    for folder, (e, per) in rows.items():
        cells = " ".join(
            (f"{v[0]:3d}/{v[1]:3.0f}/{v[2]}" if v else "     -    ").rjust(10)
            for v in (per[d] for d in DIRS))
        print(f"{folder:22s} {e['kind']:7s} {', '.join(e['motifs'])[:34]:34s} {cells}")

    print("\n\nPER-MOTIF VERDICTS  (cells/dL/fragments per direction)\n")
    singles = {e["motifs"][0]: per for _, (e, per) in rows.items()
               if e["kind"] == "single"}
    out = {}
    for motif, per in sorted(singles.items()):
        pd = None
        if motif in probes:
            a = [v[1] for v in per.values() if v]
            b = [v[1] for v in probes[motif].values() if v]
            if a and b:
                pd = abs(st.mean(a) - st.mean(b))
        v, why = classify(per, pd)
        out[motif] = {"verdict": v, "why": why,
                      "per_view": {d: per[d] for d in DIRS},
                      "palette_swing": round(pd, 1) if pd is not None else None}
        print(f"{motif:16s} {v:24s} {why}"
              + (f"  [palette swing dL {pd:.0f}]" if pd else ""))

    if "--write" in sys.argv:
        path = "authored/compatibility.json"
        db = json.load(open(path)) if os.path.exists(path) else {"bases": {}}
        db["bases"][base] = {"session": os.path.basename(session), "motifs": out}
        json.dump(db, open(path, "w"), indent=2)
        print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
