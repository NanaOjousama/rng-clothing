#!/usr/bin/env python3
"""Local palette / colour analysis for pixel-art garments.

ADVISORY ONLY.  Colour theory is level 5 of the visual authority hierarchy: real
source artwork and the actual worn in-game result both outrank everything this
file computes (CLAUDE.md section 1).  A check here failing is a question to ask,
not a verdict; a check passing never makes a bad-looking garment good.

Offline and self-contained -- no Lospec call, no network.  Reads either a PNG
directly or the palettes already measured into source_catalog/catalog.json.

Colour maths:  sRGB -> linear -> CIE XYZ (D65) -> CIE Lab, then CIEDE2000 for
perceptual distance.  Lab is used rather than raw RGB because equal RGB steps
are not equal perceptual steps, which is exactly the mistake that makes a ramp
look uneven while measuring as regular.

    python3 tools/palette.py ramp <png>                      extract the ramp
    python3 tools/palette.py ramp --source "Beanie"          from the catalogue
    python3 tools/palette.py analyze <png>                   every check at once
    python3 tools/palette.py compare <png> --source "Beanie" against source art
    python3 tools/palette.py compare <png> --vanilla         against vanilla art
    python3 tools/palette.py recolor <png> --hue-shift 30    safe candidates

Needs the analysis venv:  source tools/env.sh
The GENERATOR must never import this -- it stays dependency-free.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "source_catalog" / "catalog.json"

# Thresholds are conventions, not laws.  Each is stated so a caller can argue
# with the number instead of guessing what the tool assumed.
# CALIBRATED against the 147 approved source appearances that have a measurable
# Front frame (see tools/palette_calibration.json).  Each sits at roughly the
# 5th percentile of what the source authors actually do, so a flag means "outside
# what approved source art does", not "outside a convention I picked".  The first
# draft used round numbers and flagged published source art immediately -- which
# is the authority hierarchy working as intended: the art corrected the theory.
MIN_VALUE_STEP = 2.0      # Lab L* between adjacent steps (source p10 = 1.6)
MIN_ROLE_DE = 7.0         # CIEDE2000 between colours doing DIFFERENT jobs
                          # (source outline-body p5 = 6.9)
COLLAPSE_DE = 4.0         # below this two entries are effectively one colour
                          # (source any-pair p5 = 4.3)
MAX_HUE_SPREAD = 80.0     # degrees across one material (source p90 = 76)
MIN_HUE_SHIFT = 12.0      # hue degrees that justify two steps at the same value
MIN_CHROMA_STEP = 6.0     # chroma difference that does the same


def _load_png(path: Path):
    try:
        from PIL import Image
    except ModuleNotFoundError:
        sys.exit("Pillow missing -- run `source tools/env.sh` first "
                 "(the generator itself needs no venv)")
    with Image.open(path) as im:
        im = im.convert("RGBA")
        return list(im.getdata()), im.size


# --- colour space ---------------------------------------------------------

def _lin(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def to_lab(rgb) -> tuple[float, float, float]:
    r, g, b = (_lin(v) for v in rgb[:3])
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 1.00000
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 216 / 24389 else (841 / 108) * t + 4 / 29
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def ciede2000(lab1, lab2) -> float:
    """Perceptual distance.  Full CIEDE2000, not a Euclidean Lab shortcut."""
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7))) if Cb else 0.5
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1 = math.degrees(math.atan2(b1, a1p)) % 360 if (a1p or b1) else 0.0
    h2 = math.degrees(math.atan2(b2, a2p)) % 360 if (a2p or b2) else 0.0
    dLp, dCp = L2 - L1, C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    elif abs(h2 - h1) <= 180:
        dhp = h2 - h1
    else:
        dhp = h2 - h1 - 360 if h2 > h1 else h2 - h1 + 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2)
    Lbp, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbp = h1 + h2
    elif abs(h1 - h2) <= 180:
        hbp = (h1 + h2) / 2
    elif h1 + h2 < 360:
        hbp = (h1 + h2 + 360) / 2
    else:
        hbp = (h1 + h2 - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30))
         + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6))
         - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    dTh = 30 * math.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7)) if Cbp else 0.0
    Sl = 1 + (0.015 * (Lbp - 50) ** 2) / math.sqrt(20 + (Lbp - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    Rt = -math.sin(math.radians(2 * dTh)) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2
                     + Rt * (dCp / Sc) * (dHp / Sh))


def hue_deg(rgb) -> float:
    _, a, b = to_lab(rgb)
    return math.degrees(math.atan2(b, a)) % 360


def hue_distance(c1, c2) -> float:
    d = abs(hue_deg(c1) - hue_deg(c2)) % 360
    return min(d, 360 - d)


# --- ramp extraction ------------------------------------------------------

def ramp_from_png(path: Path) -> list[dict]:
    px, _ = _load_png(path)
    counts: dict[tuple, int] = {}
    for p in px:
        if p[3] == 0:                       # fully transparent is not a colour
            continue
        counts[p] = counts.get(p, 0) + 1
    return _ramp(counts)


def ramp_from_catalog(name: str, direction: str = "Front") -> tuple[list[dict], dict]:
    cat = json.loads(CATALOG.read_text())
    hits = [a for a in cat["appearances"] if name.lower() in a["name"].lower()]
    if not hits:
        sys.exit(f"no source appearance matching {name!r}")
    a = hits[0]
    frames = (a.get("analysis") or {}).get("frames") or {}
    if direction not in frames:
        sys.exit(f"{a['name']} has no {direction} frame (has {list(frames)})")
    counts = {tuple(e[:4]): e[4] for e in frames[direction].get("palette", [])}
    return _ramp(counts), {"name": a["name"], "pack": a["pack"],
                           "author": a.get("pack_author"), "direction": direction}


def _ramp(counts: dict) -> list[dict]:
    """Ordered dark -> light, which is the order every value check assumes.

    Deduped by RGB, summing counts across alpha values.  Source packs do contain
    the same colour at more than one alpha; counting those as separate ramp steps
    produced phantom zero-distance pairs and made every threshold look violated.
    Alpha variants are reported per entry rather than treated as colours.
    """
    merged: dict[tuple, dict] = {}
    for rgba, n in counts.items():
        rgb = tuple(rgba[:3])
        e = merged.setdefault(rgb, {"count": 0, "alphas": set()})
        e["count"] += n
        e["alphas"].add(rgba[3] if len(rgba) > 3 else 255)
    rows = []
    for rgb, e in merged.items():
        L, aa, bb = to_lab(rgb)
        rows.append({"rgba": list(rgb) + [max(e["alphas"])],
                     "hex": "#%02x%02x%02x" % rgb,
                     "count": e["count"], "alphas": sorted(e["alphas"]),
                     "L": round(L, 1), "a": round(aa, 1),
                     "b": round(bb, 1), "chroma": round(math.hypot(aa, bb), 1),
                     "hue": round(hue_deg(rgb), 1)})
    rows.sort(key=lambda r: r["L"])
    total = sum(r["count"] for r in rows) or 1
    for i, r in enumerate(rows):
        r["share"] = round(100 * r["count"] / total, 1)
        r["step"] = i
    return rows


def roles(ramp: list[dict]) -> dict[str, dict]:
    """Assign the three structural jobs by position, then report them.

    Deliberately positional and dumb: the darkest step is the outline because
    that is how the source authors draw, the lightest is the highlight, and the
    largest-share middle step is the body.  Any richer inference would be the
    tool asserting semantics, which is exactly what section 3 forbids.
    """
    if not ramp:
        return {}
    mid = [r for r in ramp[1:-1]] or ramp
    return {"outline": ramp[0], "highlight": ramp[-1],
            "body": max(mid, key=lambda r: r["count"])}


# --- checks ---------------------------------------------------------------

def check_value_order(ramp) -> list[str]:
    """Adjacent steps must separate in value -- unless they separate in hue.

    Two colours at the same L* are not a defect when they differ in hue or
    chroma: that is deliberate hue shifting, which the source corpus does use.
    Only a pair that is close in BOTH value and colour has actually collapsed.
    """
    bad = []
    for x, y in zip(ramp, ramp[1:]):
        d = y["L"] - x["L"]
        if d >= MIN_VALUE_STEP:
            continue
        if hue_distance(x["rgba"], y["rgba"]) >= MIN_HUE_SHIFT or \
           abs(x["chroma"] - y["chroma"]) >= MIN_CHROMA_STEP:
            continue                       # a hue shift at one value: intentional
        bad.append(f"{x['hex']} -> {y['hex']}: L* step {d:.1f} "
                   f"< {MIN_VALUE_STEP} with no hue separation "
                   f"(reads as one step at normal scale)")
    return bad


def check_role_contrast(ramp) -> list[str]:
    r, bad = roles(ramp), []
    if not r:
        return bad
    for x, y in (("outline", "body"), ("body", "highlight"), ("outline", "highlight")):
        de = ciede2000(to_lab(r[x]["rgba"]), to_lab(r[y]["rgba"]))
        if de < MIN_ROLE_DE:
            bad.append(f"{x} {r[x]['hex']} vs {y} {r[y]['hex']}: "
                       f"dE {de:.1f} < {MIN_ROLE_DE} -- these do different jobs "
                       f"and must not read alike")
    return bad


def check_role_collapse(ramp) -> list[str]:
    bad = []
    for i, x in enumerate(ramp):
        for y in ramp[i + 1:]:
            de = ciede2000(to_lab(x["rgba"]), to_lab(y["rgba"]))
            if de < COLLAPSE_DE:
                bad.append(f"{x['hex']} and {y['hex']} collapse: dE {de:.1f} "
                           f"< {COLLAPSE_DE} -- one of them is wasted")
    return bad


def check_hue_distance(ramp) -> list[str]:
    chromatic = [r for r in ramp if r["chroma"] > 4]
    if len(chromatic) < 2:
        return []
    hues = [r["hue"] for r in chromatic]
    spread = max(hues) - min(hues)
    spread = min(spread, 360 - spread)
    if spread > MAX_HUE_SPREAD:
        return [f"hue spread {spread:.0f}deg > {MAX_HUE_SPREAD} across "
                f"{len(chromatic)} chromatic steps -- may read as two materials, "
                f"not one shaded one"]
    return []


def analyze(ramp: list[dict]) -> dict:
    r = roles(ramp)
    return {
        "steps": len(ramp),
        "roles": {k: v["hex"] for k, v in r.items()},
        "value_order": check_value_order(ramp),
        "role_contrast": check_role_contrast(ramp),
        "role_collapse": check_role_collapse(ramp),
        "hue_distance": check_hue_distance(ramp),
        "grey": all(x["chroma"] <= 4 for x in ramp),
        "corpus_flag_rate_percent": _corpus_rates(),
    }


# --- commands ------------------------------------------------------------

def show_ramp(ramp, args, header: str = "") -> None:
    if args.json:
        print(json.dumps(ramp, indent=1))
        return
    if header:
        print(header)
    print(f"{'#':<3}{'hex':<9}{'L*':>7}{'chroma':>8}{'hue':>7}{'count':>7}{'share%':>8}")
    for r in ramp:
        print(f"{r['step']:<3}{r['hex']:<9}{r['L']:>7}{r['chroma']:>8}"
              f"{r['hue']:>7}{r['count']:>7}{r['share']:>8}")


def _corpus_rates() -> dict:
    """What share of APPROVED SOURCE ART each check flags -- the tool's error bar.

    Printed beside every flag so a flag is never mistaken for a verdict.  Built
    by tools/palette_calibrate.py; absent is fine, the checks still run.
    """
    p = ROOT / "tools" / "palette_calibration.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text()).get("corpus_flag_rate_percent", {})
    except (json.JSONDecodeError, OSError):
        return {}


def report(res: dict, args) -> int:
    if args.json:
        print(json.dumps(res, indent=1))
    else:
        print(f"\nsteps {res['steps']}   roles "
              + ", ".join(f"{k}={v}" for k, v in res["roles"].items())
              + ("   (greyscale)" if res["grey"] else ""))
        rates = _corpus_rates()
        clean = True
        for label, key in (("value order", "value_order"),
                           ("role contrast", "role_contrast"),
                           ("role collapse", "role_collapse"),
                           ("hue distance", "hue_distance")):
            rows = res[key]
            note = (f"  [approved source art trips this on {rates[key]}% of items]"
                    if key in rates else "")
            if rows:
                clean = False
                print(f"\n  {label}:{note}")
                for r in rows:
                    print(f"    - {r}")
            else:
                print(f"  {label}: ok")
        if clean:
            print("\nno advisory flags. This says the NUMBERS are consistent --")
            print("it does not say the garment looks right. Capture it in game.")
    return 0


def cmd_ramp(args) -> int:
    if args.source:
        ramp, meta = ramp_from_catalog(args.source, args.direction)
        show_ramp(ramp, args, f"{meta['name']} [{meta['direction']}] "
                              f"-- {meta['pack']} by {meta['author']} (SOURCE ART)")
    else:
        ramp = ramp_from_png(Path(args.png))
        show_ramp(ramp, args, f"{args.png}")
    return 0


def cmd_analyze(args) -> int:
    if args.source:
        ramp, meta = ramp_from_catalog(args.source, args.direction)
        head = f"{meta['name']} [{meta['direction']}] (SOURCE ART)"
    else:
        ramp = ramp_from_png(Path(args.png))
        head = str(args.png)
    if not args.json:
        show_ramp(ramp, args, head)
    return report(analyze(ramp), args)


def cmd_compare(args) -> int:
    mine = ramp_from_png(Path(args.png))
    if args.source:
        theirs, meta = ramp_from_catalog(args.source, args.direction)
        label = f"{meta['name']} (source art, authority level 2)"
    elif args.vanilla:
        theirs = ramp_from_png(ROOT / args.vanilla)
        label = f"{args.vanilla} (vanilla corpus, authority level 4)"
    else:
        sys.exit("compare needs --source <name> or --vanilla <png path>")
    rows = []
    for m in mine:
        near = min(theirs, key=lambda t: ciede2000(to_lab(m["rgba"]), to_lab(t["rgba"])))
        rows.append({"mine": m["hex"], "nearest": near["hex"],
                     "dE": round(ciede2000(to_lab(m["rgba"]), to_lab(near["rgba"])), 1),
                     "dL": round(m["L"] - near["L"], 1),
                     "dHue": round(hue_distance(m["rgba"], near["rgba"]), 1)})
    if args.json:
        print(json.dumps({"reference": label, "steps_mine": len(mine),
                          "steps_ref": len(theirs), "pairs": rows}, indent=1))
        return 0
    print(f"{args.png}  vs  {label}")
    print(f"steps: {len(mine)} vs {len(theirs)}\n")
    print(f"{'mine':<9}{'nearest':<9}{'dE':>7}{'dL*':>7}{'dHue':>7}")
    for r in rows:
        print(f"{r['mine']:<9}{r['nearest']:<9}{r['dE']:>7}{r['dL']:>7}{r['dHue']:>7}")
    worst = max(rows, key=lambda r: r["dE"]) if rows else None
    if worst:
        print(f"\nfurthest from the reference: {worst['mine']} (dE {worst['dE']})")
    print("The reference outranks the theory. If they disagree, follow the source.")
    return 0


def cmd_recolor(args) -> int:
    """Hue-shift candidates that preserve the ramp's value structure.

    Value structure is preserved because it is what reads at Stardew's scale:
    L* and the ordering are held, only hue moves.  Any candidate is still a
    proposal for a human to look at in game.
    """
    ramp = (ramp_from_catalog(args.source, args.direction)[0] if args.source
            else ramp_from_png(Path(args.png)))
    out = []
    for r in ramp:
        L, a, b = r["L"], r["a"], r["b"]
        C, h = math.hypot(a, b), math.degrees(math.atan2(b, a))
        h2 = math.radians(h + args.hue_shift)
        a2, b2 = C * math.cos(h2), C * math.sin(h2)
        rgb = _lab_to_srgb(L, a2, b2)
        out.append({"from": r["hex"], "to": "#%02x%02x%02x" % rgb,
                    "L_kept": round(L, 1), "hue_from": r["hue"],
                    "hue_to": round(hue_deg(rgb), 1), "share": r["share"]})
    shifted = _ramp({tuple(list(_srgb(c["to"])) + [255]): 1 for c in out})
    res = analyze(shifted)
    if args.json:
        print(json.dumps({"hue_shift": args.hue_shift, "candidates": out,
                          "checks": res}, indent=1))
        return 0
    print(f"hue shift {args.hue_shift:+g}deg, L* held\n")
    print(f"{'from':<9}{'to':<9}{'L*':>7}{'hue':>7} ->{'hue':>6}{'share%':>8}")
    for c in out:
        print(f"{c['from']:<9}{c['to']:<9}{c['L_kept']:>7}"
              f"{c['hue_from']:>7}   {c['hue_to']:>6}{c['share']:>8}")
    return report(res, args)


def _srgb(hexstr: str) -> tuple[int, int, int]:
    h = hexstr.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lab_to_srgb(L, a, b) -> tuple[int, int, int]:
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200
    g = lambda t: t ** 3 if t ** 3 > 216 / 24389 else (116 * t - 16) / (841 / 108)
    x, y, z = g(fx) * 0.95047, g(fy), g(fz) * 1.08883
    r = 3.2406 * x - 1.5372 * y - 0.4986 * z
    gg = -0.9689 * x + 1.8758 * y + 0.0415 * z
    bb = 0.0557 * x - 0.2040 * y + 1.0570 * z
    f = lambda c: 12.92 * c if c <= 0.0031308 else 1.055 * (max(c, 0) ** (1 / 2.4)) - 0.055
    return tuple(max(0, min(255, round(f(c) * 255))) for c in (r, gg, bb))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, png_required=True):
        p.add_argument("png", nargs="?" if not png_required else None)
        p.add_argument("--source", help="read the ramp from source_catalog instead")
        p.add_argument("--direction", default="Front",
                       choices=["Front", "Back", "Left", "Right"])

    common(sub.add_parser("ramp", help="extract an ordered dark->light ramp"), False)
    common(sub.add_parser("analyze", help="run every advisory check"), False)

    p = sub.add_parser("compare", help="compare a PNG against source or vanilla art")
    p.add_argument("png")
    p.add_argument("--source"); p.add_argument("--vanilla")
    p.add_argument("--direction", default="Front",
                   choices=["Front", "Back", "Left", "Right"])

    p = sub.add_parser("recolor", help="hue-shift candidates that keep the value ramp")
    p.add_argument("png", nargs="?")
    p.add_argument("--source"); p.add_argument("--hue-shift", type=float, required=True)
    p.add_argument("--direction", default="Front",
                   choices=["Front", "Back", "Left", "Right"])

    args = ap.parse_args(argv)
    if args.cmd in ("ramp", "analyze", "recolor") and not args.png and not args.source:
        sys.exit(f"{args.cmd} needs a PNG path or --source <name>")
    return {"ramp": cmd_ramp, "analyze": cmd_analyze,
            "compare": cmd_compare, "recolor": cmd_recolor}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
