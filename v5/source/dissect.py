"""Controlled dissection of a single authored source construction.

Sibling-differencing (see `decompose.py`) is the reliable way to isolate a
component, because the author supplies both halves of the subtraction.  Cap 2
has no siblings, so anything separated here is separated STRUCTURALLY -- and
that is precisely the situation where forcing a split invents a component the
author never drew.

So the bar is deliberately high.  A region is only a candidate if it is
ENCLOSED: every drawn neighbour outside it belongs to a single surrounding
value.  That means the hole left behind can be filled with one value the author
already used there, and the result is still their art rather than our guess.
Everything else stays embedded in the base.

    REUSABLE        enclosed, and its meaning does not depend on this crown
    FAMILY-SPECIFIC enclosed, but only sensible on this construction family
    BASE-SPECIFIC   separable in pixels, meaningless off this exact base
    REFERENCE-ONLY  not cleanly separable at all; left embedded

The reconstruction test is the gate: base-with-holes plus components must equal
the source byte-for-byte, in every direction.
"""
from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field

import sys
sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing")
from v5.source import audit, pngread, semantic

REUSABLE = "REUSABLE"
FAMILY_SPECIFIC = "FAMILY-SPECIFIC"
BASE_SPECIFIC = "BASE-SPECIFIC"
REFERENCE_ONLY = "REFERENCE-ONLY"

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def frames_of(app):
    px = pngread.read(app["png_path"])
    return {d: audit.cut(px, tuple(b)) for d, b in app["analysis"]["boxes"].items()}


def step_map(frame, vocab):
    return {(x, y): semantic.step_of(p, vocab)
            for y, r in enumerate(frame) for x, p in enumerate(r) if p[3]}


def regions(steps: dict, want) -> list:
    """4-connected runs of cells whose step is in `want`."""
    todo = {c for c, s in steps.items() if s in want}
    out = []
    while todo:
        seed = todo.pop()
        blob, q = {seed}, deque([seed])
        while q:
            x, y = q.popleft()
            for dx, dy in N4:
                n = (x + dx, y + dy)
                if n in todo:
                    todo.discard(n)
                    blob.add(n)
                    q.append(n)
        out.append(blob)
    return out


def enclosure(blob: set, steps: dict):
    """(is_enclosed, fill_value, neighbour_histogram).

    Enclosed means every drawn neighbour outside the blob carries the SAME
    step.  Then removing the blob leaves a hole with one unambiguous filler.
    """
    hist = Counter()
    touches_edge = False
    for (x, y) in blob:
        for dx, dy in N4:
            n = (x + dx, y + dy)
            if n in blob:
                continue
            if n not in steps:
                touches_edge = True          # borders transparency
            else:
                hist[steps[n]] += 1
    if touches_edge or not hist:
        return False, None, hist
    return len(hist) == 1, next(iter(hist)), hist


@dataclass
class Component:
    name: str
    kind: str
    classification: str
    reason: str
    cells: dict = field(default_factory=dict)      # {dir: {(x,y): rgba}}
    fill: dict = field(default_factory=dict)       # {dir: {(x,y): rgba}}
    directions: list = field(default_factory=list)
    zone: str = ""
    notes: list = field(default_factory=list)


def islands_on_field(steps: dict, field_value: int) -> list:
    """Connected groups of NON-field cells lying inside a field of one value.

    The single-value scan misses any motif drawn in more than one tone -- an
    emblem shaded 4/6/6/4 on a flat dark panel splits into three fragments and
    each one looks un-enclosed.  Grouping every non-field cell instead finds
    the motif whole, which is how the author drew it.
    """
    todo = {c for c, s in steps.items() if s != field_value}
    out = []
    while todo:
        seed = todo.pop()
        blob, q = {seed}, deque([seed])
        while q:
            x, y = q.popleft()
            for dx, dy in N4:
                n = (x + dx, y + dy)
                if n in todo:
                    todo.discard(n)
                    blob.add(n)
                    q.append(n)
        out.append(blob)
    return out


def find_components(app, min_cells=2, max_share=0.20) -> tuple:
    """(components, base_frames_with_holes, vocab, diagnostics)."""
    frames = frames_of(app)
    vocab = semantic.build_vocabulary([frames],
                                      app["analysis"].get("declared_masks"))
    diags, comps = [], []
    holes = {d: [list(r) for r in f] for d, f in frames.items()}

    for d, frame in frames.items():
        steps = step_map(frame, vocab)
        total = len(steps)
        # every step value is tried as a candidate "foreground"; a component is
        # a value island sitting inside a single surrounding value
        for value in sorted(set(steps.values())):
            for blob in regions(steps, {value}):
                if len(blob) < min_cells or len(blob) > total * max_share:
                    continue
                ok, fill, hist = enclosure(blob, steps)
                diags.append({"direction": d, "value": value,
                              "cells": len(blob), "enclosed": ok,
                              "fill": fill, "neighbours": dict(hist)})
                if not ok:
                    continue
                comps.append((d, blob, value, fill, frame, "value-island"))

        # second pass: multi-tone motifs sitting on a single flat field
        for fieldv in sorted(set(steps.values())):
            for blob in islands_on_field(steps, fieldv):
                if len(blob) < min_cells or len(blob) > total * max_share:
                    continue
                ok, fill, hist = enclosure(blob, steps)
                if not ok or fill != fieldv:
                    continue
                if any((d, b, v, f, fr, k) for (d2, b, v, f, fr, k) in comps
                       if d2 == d and b == blob):
                    continue
                vals = sorted({steps[c] for c in blob})
                if len(vals) < 2:
                    continue                 # already caught by the first pass
                diags.append({"direction": d, "value": vals, "cells": len(blob),
                              "enclosed": True, "fill": fill,
                              "neighbours": dict(hist), "multitone": True})
                comps.append((d, blob, tuple(vals), fill, frame, "motif"))
    return comps, holes, vocab, diags, frames
