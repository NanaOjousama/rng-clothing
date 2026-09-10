#!/usr/bin/env python3
"""Calibrate tools/palette.py against the approved source corpus.

Writes tools/palette_calibration.json: the distribution of every measured
quantity across the approved source packs, plus -- the number that actually
matters -- what share of APPROVED SOURCE ART each check flags.

That share is the tool's own error bar.  Measured here: roughly a fifth of
approved source appearances contain near-duplicate colours, at any threshold
low enough to be meaningful.  So a "role collapse" flag is NOT evidence of a
defect in source-derived work; it is only informative for a GENERATED palette,
where a collapsed step means the generator wasted a slot it was given.  This is
why palette.py prints the corpus rate beside every flag.

Re-run if the source corpus changes:  python3 tools/palette_calibrate.py
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import palette as P                                              # noqa: E402

CHECKS = {"value_order": P.check_value_order,
          "role_contrast": P.check_role_contrast,
          "role_collapse": P.check_role_collapse,
          "hue_distance": P.check_hue_distance}


def ramps() -> list[tuple[str, str, list[dict]]]:
    cat = json.loads((ROOT / "source_catalog" / "catalog.json").read_text())
    out = []
    for a in cat["appearances"]:
        f = ((a.get("analysis") or {}).get("frames") or {}).get("Front")
        if not f or f.get("empty"):
            continue
        r = P._ramp({tuple(e[:4]): e[4] for e in f.get("palette", [])})
        if len(r) >= 3:                     # a 2-colour sprite has no ramp to judge
            out.append((a["name"], a["pack"], r))
    return out


def pct(xs, p):
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(len(xs) * p / 100))], 2)


def main() -> int:
    rows = ramps()
    if not rows:
        sys.exit("no measurable source frames -- is source_catalog built?")
    steps, vals, coll, hues = [], [], [], []
    roles = {k: [] for k in ("outline-body", "body-highlight", "outline-highlight")}
    for _, _, r in rows:
        steps.append(len(r))
        vals += [round(y["L"] - x["L"], 2) for x, y in zip(r, r[1:])]
        rl = P.roles(r)
        for x, y in (("outline", "body"), ("body", "highlight"), ("outline", "highlight")):
            roles[f"{x}-{y}"].append(
                P.ciede2000(P.to_lab(rl[x]["rgba"]), P.to_lab(rl[y]["rgba"])))
        for i, x in enumerate(r):
            coll += [P.ciede2000(P.to_lab(x["rgba"]), P.to_lab(y["rgba"])) for y in r[i + 1:]]
        ch = [q["hue"] for q in r if q["chroma"] > 4]
        if len(ch) >= 2:
            s = max(ch) - min(ch)
            hues.append(min(s, 360 - s))

    per_check, examples = {}, {}
    for name, fn in CHECKS.items():
        hit = [(n, p) for n, p, r in rows if fn(r)]
        per_check[name] = round(100.0 * len(hit) / len(rows), 1)
        examples[name] = [f"{n} ({p})" for n, p in hit[:5]]
    any_hit = sum(1 for _, _, r in rows if any(fn(r) for fn in CHECKS.values()))

    out = {
        "calibrated_against": "approved source packs in source_catalog "
                              "(Front frames with >=3 colours)",
        "appearances": len(rows),
        "median_ramp_steps": st.median(steps),
        "thresholds": {"MIN_VALUE_STEP": P.MIN_VALUE_STEP, "MIN_ROLE_DE": P.MIN_ROLE_DE,
                       "COLLAPSE_DE": P.COLLAPSE_DE, "MAX_HUE_SPREAD": P.MAX_HUE_SPREAD,
                       "MIN_HUE_SHIFT": P.MIN_HUE_SHIFT,
                       "MIN_CHROMA_STEP": P.MIN_CHROMA_STEP},
        "corpus_flag_rate_percent": per_check,
        "corpus_flag_rate_any_check_percent": round(100.0 * any_hit / len(rows), 1),
        "interpretation": (
            "These rates are the tool's error bar. Approved source art trips these "
            "checks at the rates above, so a flag is a question, never a verdict, "
            "and never overrides how the garment reads in game. Near-duplicate "
            "colours in particular are common in approved source art at any useful "
            "threshold: treat role_collapse as informative for GENERATED palettes "
            "(a wasted slot) and not as a defect in source-derived work."),
        "distributions": {
            "L_step_between_adjacent": {f"p{p}": pct(vals, p) for p in (1, 5, 10, 25, 50)},
            "dE_roles": {k: {f"p{p}": pct(v, p) for p in (1, 5, 10, 50)}
                         for k, v in roles.items()},
            "dE_any_pair": {f"p{p}": pct(coll, p) for p in (1, 5, 10, 50)},
            "hue_spread": {f"p{p}": pct(hues, p) for p in (50, 75, 90, 95, 99)},
        },
        "examples_still_flagged": examples,
    }
    (ROOT / "tools" / "palette_calibration.json").write_text(json.dumps(out, indent=1))
    print(f"{len(rows)} source appearances measured")
    for k, v in per_check.items():
        print(f"  {k:<16} flags {v:>5}% of approved source art")
    print(f"  {'any check':<16} flags {out['corpus_flag_rate_any_check_percent']:>5}%")
    print("-> tools/palette_calibration.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
