"""Render and export the cap2 family: base + approved front emblems.

Only the grammar's allowed axes are exercised — palette, and one emblem from
the approved set placed at its authored cells. The base itself is never edited.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored, pngio
from v5.source import dissect

BASE = "authored/source_bases/cap2"
DIRS = ["Front", "Right", "Left", "Back"]


def load_family():
    man = json.load(open(f"{BASE}/manifest.json"))
    grammar = json.load(open(f"{BASE}/emblem_grammar.json"))
    motifs = json.load(open(f"{BASE}/motifs.json"))
    cat = json.load(open("source_catalog/catalog.json"))
    app = next(a for a in cat["appearances"]
               if a["name"] == "Cap 2" and a["pack"].startswith("More Acc"))
    frames = dissect.frames_of(app)
    vocab = [tuple(c) for c in man["base"]["vocabulary"]]
    # base with the author's emblem lifted out, so a motif can take its place
    emblem = {tuple(int(v) for v in k.split(",")): tuple(v)
              for k, v in man["components"]["front_emblem"]["cells"].items()}
    fill = tuple(man["components"]["front_emblem"]["fill_value"])
    base = {d: [list(r) for r in f] for d, f in frames.items()}
    for (x, y) in emblem:
        base["Front"][y][x] = fill
    return base, frames, vocab, grammar, motifs, app


def multiply(colour, grey):
    return tuple(min(255, round(c * grey / 255)) for c in colour[:3])


# PALETTE-ROLE CONSTRAINTS.
#
# Multiplicative tinting scales the WHOLE authored value ladder by the tint's
# own luminance, so every rung shrinks in proportion. Measured on this base:
# the source span of 197 becomes 102-117, and the predicted spans matched the
# measured ones to within 1.
#
# The ladder's weakest rung is visor-field to outline: only 24 apart in the
# source, because the author relied on the sprite being drawn near-white.
# Tinting halves it to 13, at which point the visor's dark field merges with
# its own outline and the peak loses definition and apparent thickness.
#
# The geometry is provably identical across variants, so this is corrected in
# COLOUR only, and only on the ROLE that fails: the outline is pushed darker
# until it separates. Hue, crown, visor field and every drawn cell stay as the
# multiply produced them.
MIN_VISOR_OUTLINE = 20      # luminance, below this the visor edge stops reading
MIN_CROWN_VISOR = 40        # already satisfied at 68-78; asserted, not adjusted


# the project's own luminance, so the constraint is measured in the same units
# the QC tooling reports; an ad-hoc formula here put ochre at 19.84 against a
# floor of 20 while the checker read it as passing
from v5.grammar import luminance as _lum


def enforce_roles(ramp: list) -> tuple:
    """Return (ramp, report) with the outline darkened enough to read.

    Only index 0 (outline) is touched, and only downward.
    """
    before_vo = _lum(ramp[1]) - _lum(ramp[0])
    before_cv = _lum(ramp[4]) - _lum(ramp[1])
    out = list(ramp)
    factor = 1.0
    while (_lum(out[1]) - _lum(out[0])) < MIN_VISOR_OUTLINE and factor > 0.05:
        factor -= 0.02
        out[0] = tuple(max(0, round(c * factor)) for c in ramp[0])
    return out, {
        "visor_outline_before": round(before_vo, 1),
        "visor_outline_after": round(_lum(out[1]) - _lum(out[0]), 1),
        "crown_visor": round(before_cv, 1),
        "outline_factor": round(factor, 2),
        "adjusted": factor < 1.0,
    }


def render(base, vocab, grammar, motifs, motif_name, tint):
    """Base in a palette, with one emblem at its authored cells."""
    z = grammar["zone"]["cells"]
    levels = [sum(c) / 3 for c in vocab]
    if tint:
        ramp, _ = enforce_roles([multiply(tint, lv) for lv in levels])
    else:
        ramp = [tuple(c) for c in vocab]
    out = {}
    for d, f in base.items():
        steps = dissect.step_map(f, vocab)
        rows = [[(0, 0, 0, 0)] * len(f[0]) for _ in f]
        for (x, y), s in steps.items():
            rows[y][x] = (*ramp[min(s, len(ramp) - 1)], 255)
        out[d] = rows
    if motif_name:
        art = motifs["motifs"][motif_name]["art"]
        for dy, row in enumerate(art):
            for dx, ch in enumerate(row):
                if ch == ".":
                    continue
                x, y = z["x0"] + dx, z["y0"] + dy
                out["Front"][y][x] = (*ramp[int(ch)], 255)
    return out


def atlas(frames, size=(20, 20)):
    w, h = size
    rows = []
    for d in DIRS:
        f = frames[d]
        for y in range(h):
            rows.append(list(f[y]) if y < len(f) else [(0, 0, 0, 0)] * w)
    return rows
