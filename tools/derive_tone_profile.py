"""Derive a reusable TONE PROFILE from one reference hat.

A palette carries colour identity: hue, saturation, the story.  A tone profile
carries value rhythm: where each semantic step sits on the luminance scale, how
far the highlight jumps, how tightly the shadows compress, and how much of the
sprite may sit at the top step.

They are separate on purpose.  Our curated ramps are laddered evenly across a
165-luminance span, and evenly is not how the references are built: vanilla 033
keeps its whole knit inside L 24-102 with a small jump at the top, and applying
an even ladder to that construction produced a pale cream cap from a dark green
one.  The construction was faithful; the tonal rhythm was not.

Applying a profile keeps the palette's hues and moves only values, so a recolour
still changes colour identity — it just stops changing the tonal rhythm too.

    python3 tools/derive_tone_profile.py 16 33 --out authored/tones.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from derive_base_from_reference import VIEWS, derive                    # noqa: E402
from v5.grammar import luminance                                        # noqa: E402

STEPS = 6


def profile(index: int, source: str = "vanilla") -> dict:
    out = derive(index, source)
    mapping, blk = out["mapping"], out["block"]

    counts = Counter()
    for view in VIEWS:
        counts.update(blk[view].values())
    total = sum(counts.values()) or 1

    # the luminance the reference actually uses at each step it uses
    known = {}
    for col, (role, step) in mapping.items():
        if role == "body":
            known.setdefault(step, []).append(luminance(col))
    known = {k: sum(v) / len(v) for k, v in known.items()}
    if not known:
        raise SystemExit(f"reference #{index} has no body colours")

    # fill the steps it does not use, so a profile is always six deep:
    # interpolate inside the range, extend the end gaps by the nearest spacing.
    lo_k, hi_k = min(known), max(known)
    levels = []
    for s in range(STEPS):
        if s in known:
            levels.append(known[s])
        elif lo_k < s < hi_k:
            below = max(k for k in known if k < s)
            above = min(k for k in known if k > s)
            t = (s - below) / (above - below)
            levels.append(known[below] + (known[above] - known[below]) * t)
        else:
            anchor = lo_k if s < lo_k else hi_k
            other = min(k for k in known if k != anchor) if len(known) > 1 else anchor
            per = abs(known[anchor] - known[other]) / max(1, abs(anchor - other))
            levels.append(known[anchor] + (s - anchor) * per)
    levels = [max(2.0, min(250.0, v)) for v in levels]
    levels = sorted(levels)

    top_step = max(known)
    top_area = sum(n for c, n in counts.items()
                   if mapping[c][0] == "body" and mapping[c][1] == top_step)
    span = levels[-1] - levels[0]
    return {
        "name": f"{source}_{index:03d}",
        "source": f"{source} hats.png #{index}",
        # absolute luminance per semantic step, deep -> highlight
        "levels": [round(v, 1) for v in levels],
        # the readable summary of the same thing
        "span": round(span, 1),
        "floor": round(levels[0], 1),
        "bias": round((sum(levels) / len(levels) - levels[0]) / max(1.0, span), 3),
        "highlight_jump": round(levels[5] - levels[4], 1),
        "shadow_compression": round((levels[2] - levels[0]) / max(1.0, span), 3),
        "max_highlight_share": round(top_area / total, 3),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("indices", nargs="+", type=int)
    ap.add_argument("--source", default="vanilla", choices=("vanilla", "mod"))
    ap.add_argument("--out", default="authored/tones.json")
    a = ap.parse_args()
    profiles = {}
    for i in a.indices:
        p = profile(i, a.source)
        profiles[p["name"]] = p
        print(f"{p['name']}: levels {p['levels']}  span {p['span']}  "
              f"floor {p['floor']}  bias {p['bias']}  jump {p['highlight_jump']}  "
              f"shadow_compression {p['shadow_compression']}  "
              f"max_highlight {p['max_highlight_share']}")
    existing = {}
    if os.path.exists(a.out):
        with open(a.out) as fh:
            existing = json.load(fh).get("profiles", {})
    existing.update(profiles)
    with open(a.out, "w") as fh:
        json.dump({"steps": STEPS, "profiles": existing}, fh, indent=2)
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
