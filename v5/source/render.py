"""Recolour an authored source garment without redrawing it.

The authored value hierarchy is the thing that makes a source asset read as
the material its author drew, and it is exactly what a naive recolour destroys.
So a palette here supplies HUE ONLY: each step keeps the source's own absolute
luminance and takes the palette's colour at that step, which is the same
separation `v5.authored.ToneProfile` already applies to our own art.

Geometry is never touched.  A rendered garment is the author's cells, in new
colours, plus components replayed at the exact positions the author drew them.
"""
from __future__ import annotations

import sys
sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing")
from v5.authored import _at_luminance


def ramp_for(palette, role_hint: str, steps: int, levels: list) -> list:
    """The palette's colours for this material, re-levelled to the source.

    `levels` is the source family's own tone profile, so the returned ramp has
    the author's contrast and the palette's hue.  A source with six authored
    values gets six colours; we never pad or truncate to a house ramp size,
    because the number of values IS part of the authored construction.
    """
    base = palette.ramps.get(role_hint) or palette.ramps["body"]
    out = []
    for i in range(steps):
        src = base[min(int(round(i * (len(base) - 1) / max(1, steps - 1))),
                       len(base) - 1)]
        out.append(_at_luminance(src, levels[i]))
    return out


# How a source's authored greys become colour.
#
#   "multiply"  what Fashion Sense itself does in grayscale mode: the authored
#               value scales the chosen colour.  These assets were drawn AS
#               tint masks for exactly this, so it is the author's intent, and
#               it preserves the RELATIVE value rhythm (the ratios between
#               steps) which is what makes the material read.
#   "levels"    replace hue while pinning each step to its authored ABSOLUTE
#               luminance.  Right for our own art, where the ramp was authored
#               as final colour -- but applied to a tint mask it washes the
#               garment out, because a mask's light end is near white by
#               design and stays there.
TINT_MULTIPLY = "multiply"
TINT_LEVELS = "levels"


def _multiply(colour, grey):
    return tuple(min(255, round(c * grey / 255)) for c in colour[:3])


def render(base, palette, components=(), role_hint="body",
           mode: str = TINT_MULTIPLY) -> dict:
    """{direction: [[rgba]]} — the authored silhouette in a new palette."""
    levels = base.tone["levels"]
    if mode == TINT_MULTIPLY:
        # the palette's own mid colour is the garment colour; the authored
        # value does the shading, exactly as the source was drawn to be used
        tint = palette.ramps.get(role_hint, palette.ramps["body"])[3]
        ramp = [_multiply(tint, lv) for lv in levels]
    else:
        ramp = ramp_for(palette, role_hint, len(base.vocab), levels)
    out = {}
    for direction, frame in base.frames.items():
        h, w = len(frame), len(frame[0])
        rows = [[(0, 0, 0, 0)] * w for _ in range(h)]
        for (x, y), step in base.steps[direction].items():
            rows[y][x] = (*ramp[min(step, len(ramp) - 1)], 255)
        out[direction] = rows
    for comp in components:
        # A component that ADDS geometry is a separate object -- a leaf, a
        # bell, a bow -- and painting it with the garment's own ramp makes it
        # vanish into the cloth.  It takes the palette's accent material
        # instead, at its own authored values, so it stays a distinct thing
        # made of a distinct material.  A component that only re-shades the
        # base (BASE-SPECIFIC, no added cells) IS the cloth, and keeps the
        # body ramp -- dots on a beret are the beret, not something on it.
        added = {d: set(v) for d, v in getattr(comp, "added", {}).items()}
        crole = "accent" if getattr(comp, "adds_geometry", False) else role_hint
        if crole == role_hint:
            cramp = ramp
        elif mode == TINT_MULTIPLY:
            ctint = palette.ramps.get(crole, palette.ramps["body"])[3]
            cramp = [_multiply(ctint, lv) for lv in levels]
        else:
            cramp = ramp_for(palette, crole, len(base.vocab), levels)
        for direction, cells in comp.steps.items():
            if direction not in out:
                continue
            for (x, y), step in cells.items():
                if step is None:
                    out[direction][y][x] = (0, 0, 0, 0)
                    continue
                # only the cells that are genuinely NEW take the accent
                # material; cells the component re-shades are still cloth
                use = (cramp if (x, y) in added.get(direction, ()) else ramp)
                out[direction][y][x] = (*use[min(step, len(use) - 1)], 255)
    return out


def atlas(frames: dict, order: list, size: tuple) -> list:
    """Stack the directions into one Fashion Sense sheet, in FS frame order."""
    w, h = size
    rows = []
    for d in order:
        f = frames.get(d)
        for y in range(h):
            rows.append(list(f[y]) if f and y < len(f) else [(0, 0, 0, 0)] * w)
    return rows


def credits_for(base, components=()) -> dict:
    """Combined attribution for a generated item, source-accurate."""
    parts = [base.credit] + [c.credit for c in components]
    seen, packs, authors, assets = set(), [], [], []
    for c in parts:
        if (c.pack, c.author) not in seen:
            seen.add((c.pack, c.author))
            packs.append(c.pack)
            authors.append(c.author)
        assets.append(c.line())
    return {
        "authors": authors,
        "packs": packs,
        "assets": assets,
        "text": "Source art: " + "; ".join(assets),
        "short": "Art by " + ", ".join(sorted(set(authors))),
    }
