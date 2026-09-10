"""QC for the authored bases, measured against the corpus families they came from.

The procedural side's corpus tooling is the measuring instrument here: each
authored base is rendered through several curated palettes, measured exactly
the way the 194 reference hats were, and compared with the family it claims to
belong to.  A base that drifts out of its family's range is a drawing problem,
and this says which number moved.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze_hat_construction_corpus import family, measure
from v5 import authored

# soft_cap claims CLOSE_FIT, not SOFT_CAP, and that is a correction rather than
# a relabelling.  Looking at the 11 hats my geometric classifier put in
# SOFT_CAP, they are goggles, sunglasses, a chef's toque, a propeller cap and a
# laurel wreath — things grouped by "short and wide", not a construction
# tradition.  Every real cap in both corpora (vanilla 016, 102, 113, mod 044)
# sits in CLOSE_FIT with a 10-wide crown held for five rows.  A family is only
# worth deriving from if its members are actually built the same way.
CLAIMS = {"felt_hat": "BRIMMED_FELT", "wide_brim_hat": "WIDE_BRIM",
          "soft_cap": "CLOSE_FIT", "knit_cap": "CLOSE_FIT"}
KEYS = ["bbox_w", "bbox_h", "top", "brim_line", "crown_w", "crown_h", "cells",
        "colors", "span", "highlight_share", "outline", "contact",
        "side_vs_front", "back_vs_front"]


def corpus_medians(path):
    with open(path) as fh:
        data = json.load(fh)
    rows = [m for ms in data.values() for m in ms]
    out = {}
    for fam in set(CLAIMS.values()):
        e = [m for m in rows if m["family"] == fam]
        out[fam] = {k: st.median([m[k] for m in e if m.get(k) is not None])
                    for k in KEYS}
    return out


def as_block(g):
    """A composed garment in the shape the corpus measurer expects."""
    return {d: {(x, y): tuple(px)
                for y, row in enumerate(g.directions[d])
                for x, px in enumerate(row) if px[3] > 0}
            for d in ("front", "right", "left", "back")}


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ref = corpus_medians(os.path.join(root, "output", "hat_corpus_construction.json"))
    lib = authored.load()
    print(f"{'base':16s} {'claims':13s} {'family read':13s}  " +
          "  ".join(f"{k[:9]:>9s}" for k in KEYS))
    report = {}
    for base in lib.bases:
        if base.slot != "HEAD":
            continue
        gs, seed = [], 0
        while len(gs) < 8 and seed < 400:
            g = authored.compose(seed, "HEAD", lib)
            if g.base.name == base.name:
                gs.append(g)
            seed += 1
        ms = [measure(as_block(g)) for g in gs]
        read = st.mode([family(m) for m in ms])
        claim = CLAIMS.get(base.name, "?")
        vals = {k: st.median([m[k] for m in ms if m.get(k) is not None]) for k in KEYS}
        mark = "OK " if read == claim else "!! "
        print(f"{mark}{base.name:14s} {claim:13s} {read:13s}  " +
              "  ".join(f"{vals[k]:9.1f}" for k in KEYS))
        print(f"{'':16s} {'corpus':13s} {'':13s}  " +
              "  ".join(f"{ref[claim][k]:9.1f}" for k in KEYS))
        report[base.name] = {"claims": claim, "reads": read,
                             "authored": vals, "corpus": ref[claim]}
    out = os.path.join(root, "output", "v5_authored", "base_qc.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(report, fh, indent=2)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
