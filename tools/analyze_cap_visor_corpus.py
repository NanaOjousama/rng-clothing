"""What the corpus actually does with a cap peak.

A cap is identified structurally, not by name: in PROFILE its widest row is
off-centre relative to the crown (the peak projects forward), which is the one
thing no brimmed hat does.  For each one, measure how the visor is built.
"""
import os, sys, statistics as st
sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing")
sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing/tools")
from analyze_hat_construction_corpus import frames, VANILLA, MOD
from v5.grammar import luminance, row_widths, brim_line, crown_metrics

def runs(px):
    rows = {}
    for (x, y) in px:
        rows.setdefault(y, []).append(x)
    return {y: (min(v), max(v)) for y, v in rows.items()}

def lum_rows(px):
    rows = {}
    for (x, y), c in px.items():
        rows.setdefault(y, []).append(luminance(c[:3]))
    return {y: sum(v) / len(v) for y, v in rows.items()}

def is_cap(blk):
    """Profile widest row projects forward of the crown's own centre."""
    for v in ("left", "right"):
        px = blk[v]
        if not px: return False
    px = blk["left"]
    r = runs(px)
    ys = sorted(r)
    w = {y: r[y][1] - r[y][0] + 1 for y in ys}
    widest = max(ys, key=lambda y: (w[y], y))
    above = [y for y in ys if y < widest]
    if not above: return False
    cw = st.median([w[y] for y in above])
    if not (1.05 <= w[widest] / cw <= 1.6): return False
    # peak is off-centre: the widest row's midpoint shifts from the crown's
    cmid = st.median([(r[y][0] + r[y][1]) / 2 for y in above])
    pmid = (r[widest][0] + r[widest][1]) / 2
    if abs(pmid - cmid) < 0.8: return False
    # and the crown must be shallow — a cap, not a brimmed hat
    return (widest - min(ys)) <= 8

def report(path, label):
    out = []
    for i, blk in enumerate(frames(path)):
        if not is_cap(blk): continue
        f, p = blk["front"], blk["left"]
        for view, px in (("front", f), ("profile", p)):
            r, L = runs(px), lum_rows(px)
            ys = sorted(r)
            w = {y: r[y][1] - r[y][0] + 1 for y in ys}
            widest = max(ys, key=lambda y: (w[y], y))
            below = [y for y in ys if y >= widest]
            crown_rows = [y for y in ys if y < widest]
            cw = st.median([w[y] for y in crown_rows]) if crown_rows else w[widest]
            seam = L[crown_rows[-1]] if crown_rows else 0
            out.append({
                "sheet": label, "hat": i, "view": view,
                "visor_rows": len(below),
                "visor_w": w[widest], "crown_w": cw,
                "ratio": round(w[widest] / cw, 2),
                "taper": [w[y] for y in below],
                "crown_bottom_L": round(seam),
                "visor_L": [round(L[y]) for y in below],
                "break": round(L[widest] - seam),
                "crown_span": (round(min(L.values())), round(max(L[y] for y in crown_rows)) if crown_rows else 0),
            })
    return out

rows = report(VANILLA, "vanilla") + report(MOD, "mod")
print(f"{len(rows)//2} cap-like hats found\n")
hdr = f"{'sheet':8s}{'hat':>4s} {'view':8s} {'rows':>4s} {'vw':>3s} {'cw':>3s} {'ratio':>5s} {'taper':>12s} {'seamL':>6s} {'visorL':>14s} {'break':>6s}"
print(hdr); print("-"*len(hdr))
for r in rows:
    print(f"{r['sheet']:8s}{r['hat']:>4d} {r['view']:8s} {r['visor_rows']:>4d} "
          f"{r['visor_w']:>3d} {int(r['crown_w']):>3d} {r['ratio']:>5.2f} "
          f"{str(r['taper']):>12s} {r['crown_bottom_L']:>6d} {str(r['visor_L']):>14s} "
          f"{r['break']:>+6d}")

for view in ("front", "profile"):
    sub = [r for r in rows if r["view"] == view]
    if not sub: continue
    print(f"\n{view}: n={len(sub)}  visor rows median {st.median([r['visor_rows'] for r in sub])}"
          f"  ratio median {st.median([r['ratio'] for r in sub]):.2f}"
          f"  break median {st.median([r['break'] for r in sub]):+.0f}"
          f"  (range {min(r['break'] for r in sub):+d} to {max(r['break'] for r in sub):+d})")
    ups = sum(1 for r in sub if r["break"] > 8)
    downs = sum(1 for r in sub if r["break"] < -8)
    print(f"  visor LIGHTER than crown bottom: {ups}/{len(sub)}   DARKER: {downs}/{len(sub)}"
          f"   flat: {len(sub)-ups-downs}/{len(sub)}")
