"""Take authored source garments apart, and prove the pieces put them back.

THE MODEL.  A family is a set of sibling appearances that share a construction
-- "Beret", "Beret (Ribbon)", "Beret (Dotted)".  One of them is the PLAIN
variant; it becomes the BASE, kept pixel-exact, because the authored silhouette
is the construction authority and nothing here is entitled to redraw it.

Every other sibling is expressed as a DELTA against that base: a sparse map of
cell -> pixel covering exactly the cells where the two differ, per direction.
Reconstruction is then base + delta, and it is exact by construction rather
than by approximation -- which is the property the mandatory reconstruction
test exists to verify rather than assume.

WHY DELTAS AND NOT SEGMENTATION.  Segmenting a single sprite into "hat" and
"bow" means guessing where the author's shading of one ends and the other
begins.  Differencing two siblings asks the author instead: the pixels that
changed between Beret and Beret (Ribbon) ARE the ribbon, with no judgement
call from us.

WHAT THE DELTA'S SHAPE MEANS.  Three kinds of cell, and their mix decides how
far a component can travel:

    added     drawn in the variant, transparent in the base.  Real new
              geometry -- a ribbon loop, a leaf.  This is the part that could
              be meaningful on another base.
    changed   drawn in both, different value.  The author re-shading the base
              itself, e.g. the dots of "Beret (Dotted)" are not added pixels
              at all, they are existing crown cells moved to a lighter value.
              That is inseparable from this silhouette's own shading.
    removed   drawn in the base, transparent in the variant.  The variant is
              not this base plus something; it is a different construction.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import sys
sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing")
from v5.source import audit, pngread, semantic

REUSABLE = "REUSABLE"
BASE_SPECIFIC = "BASE-SPECIFIC"
REFERENCE_ONLY = "REFERENCE-ONLY"

# A delta that removes base geometry is not a decoration on this base.
# A delta that mostly re-shades the base cannot be lifted off it.
MAX_CHANGED_SHARE = 0.10


def frames_of(app: dict) -> dict:
    """{direction: [[rgba]]} cut from the source PNG by its own declarations."""
    px = pngread.read(app["png_path"])
    return {d: audit.cut(px, tuple(box))
            for d, box in app["analysis"]["boxes"].items()}


@dataclass
class Delta:
    """One variant expressed against its base, per direction."""
    name: str
    qualifier: str
    source: dict                       # provenance of the VARIANT
    app: dict = field(default_factory=dict, repr=False)   # the variant itself
    cells: dict = field(default_factory=dict)   # {dir: {(x,y): rgba|None}}
    added: dict = field(default_factory=dict)
    changed: dict = field(default_factory=dict)
    removed: dict = field(default_factory=dict)
    classification: str = REUSABLE
    reason: str = ""

    @property
    def totals(self):
        f = lambda d: sum(len(v) for v in d.values())
        return f(self.added), f(self.changed), f(self.removed)


def delta_of(base_frames: dict, var_frames: dict, app: dict,
             base_cells: int, vocab: list | None = None) -> Delta:
    """Difference a variant against its base.

    Two spaces at once, deliberately.  `cells` holds the EXACT rgba difference
    and is what reconstruction replays, so rebuilding is byte-perfect.  The
    added/changed/removed tallies that drive classification are computed in the
    family's authored value vocabulary when one is supplied, so that a pack
    author writing 164 in one file and 165 in the next does not read as a
    wholesale re-shade.
    """
    d = Delta(app["name"], app.get("qualifier", ""),
              {"pack": app["pack"], "author": app["pack_author"],
               "pack_id": app["pack_id"], "asset": app["name"],
               "json": app["json_path"], "png": app["png_path"]},
              app=app)
    for direction in sorted(set(base_frames) & set(var_frames)):
        A, B = base_frames[direction], var_frames[direction]
        if len(A) != len(B) or len(A[0]) != len(B[0]):
            d.classification = REFERENCE_ONLY
            d.reason = f"{direction}: frame size differs from the base"
            return d
        cells, added, changed, removed = {}, [], [], []
        for y in range(len(A)):
            for x in range(len(A[0])):
                pa, pb = tuple(A[y][x]), tuple(B[y][x])
                if pa == pb:
                    continue
                cells[(x, y)] = pb if pb[3] else None
                if not pa[3]:
                    added.append((x, y))
                elif not pb[3]:
                    removed.append((x, y))
                elif vocab is None:
                    changed.append((x, y))
                elif (semantic.step_of(pa, vocab)
                      != semantic.step_of(pb, vocab)):
                    changed.append((x, y))      # a real move between values
        d.cells[direction] = cells
        d.added[direction] = added
        d.changed[direction] = changed
        d.removed[direction] = removed

    a, c, r = d.totals
    if r:
        d.classification = REFERENCE_ONLY
        d.reason = (f"removes {r} cells of the base silhouette: this is a "
                    f"different construction, not a decoration on it")
    elif a == 0:
        d.classification = BASE_SPECIFIC
        d.reason = (f"adds no geometry; it re-shades {c} of the base's own "
                    f"cells, which cannot be lifted off this silhouette")
    elif c > max(1, base_cells * MAX_CHANGED_SHARE):
        d.classification = BASE_SPECIFIC
        d.reason = (f"adds {a} cells but also re-shades {c} of the base's "
                    f"{base_cells}, above the {MAX_CHANGED_SHARE:.0%} bound")
    else:
        d.classification = REUSABLE
        d.reason = f"adds {a} cells and disturbs only {c} of the base"
    return d


def apply_delta(base_frames: dict, delta: Delta) -> dict:
    """base + delta, as new frames.  The inverse of delta_of, exactly."""
    out = {}
    for direction, frame in base_frames.items():
        rows = [list(row) for row in frame]
        for (x, y), px in delta.cells.get(direction, {}).items():
            rows[y][x] = tuple(px) if px else (0, 0, 0, 0)
        out[direction] = rows
    return out


def identical(a: dict, b: dict) -> tuple:
    """(ok, per-direction mismatch counts) — byte-exact comparison."""
    bad = {}
    for direction in sorted(set(a) | set(b)):
        if direction not in a or direction not in b:
            bad[direction] = "missing"
            continue
        A, B = a[direction], b[direction]
        if len(A) != len(B) or len(A[0]) != len(B[0]):
            bad[direction] = "size"
            continue
        n = sum(1 for y in range(len(A)) for x in range(len(A[0]))
                if tuple(A[y][x]) != tuple(B[y][x]))
        if n:
            bad[direction] = n
    return (not bad), bad


@dataclass
class Family:
    """One authored construction plus every sibling expressed against it."""
    pack: str
    author: str
    category: str
    stem: str
    base_app: dict
    base_frames: dict
    deltas: list = field(default_factory=list)
    vocab: list = field(default_factory=list)
    roles: dict = field(default_factory=dict)
    tone: dict = field(default_factory=dict)

    @property
    def base_cells(self):
        return sum(1 for f in self.base_frames.values()
                   for row in f for p in row if p[3])


def build_family(apps: list) -> Family | None:
    """Pick the PLAIN sibling as base and express the rest against it."""
    apps = [a for a in apps if not a["analysis"].get("error")
            and a["analysis"].get("boxes")]
    if len(apps) < 2:
        return None
    plain = [a for a in apps if not a.get("qualifier")]
    # no explicitly plain sibling: the one with the fewest drawn cells is the
    # least decorated, which is the closest thing to an undecorated base
    base_app = (plain[0] if plain
                else min(apps, key=lambda a: a["analysis"]["total_cells"]))
    fam = Family(base_app["pack"], base_app["pack_author"],
                 base_app["category"], base_app["stem"],
                 base_app, frames_of(base_app))
    variants = {a["name"]: frames_of(a) for a in apps if a is not base_app}
    fam.vocab = semantic.build_vocabulary(
        [fam.base_frames] + list(variants.values()),
        base_app["analysis"].get("declared_masks"))
    fam.roles = semantic.roles_for(fam.vocab)
    fam.tone = semantic.tone_profile(fam.vocab)
    for a in apps:
        if a is base_app:
            continue
        fam.deltas.append(delta_of(fam.base_frames, variants[a["name"]], a,
                                   fam.base_cells, fam.vocab))
    return fam


def reconstruct_report(fam: Family) -> dict:
    """THE MANDATORY TEST: every sibling we MODEL is rebuilt exactly.

    The test applies to variants this decomposition claims to express as
    base + delta -- REUSABLE and BASE-SPECIFIC.  A REFERENCE-ONLY variant is
    the decomposition declining to model it: it has a different frame size, a
    missing direction, or it deletes base geometry, which means it is a
    different authored construction rather than a decoration on this one.
    Those are promoted to bases of their own and kept pixel-exact, so nothing
    is lost -- but scoring them as reconstruction failures would be measuring
    the model against something it explicitly does not claim.
    """
    rows, promote = [], []
    for d in fam.deltas:
        modelled = d.classification in (REUSABLE, BASE_SPECIFIC)
        if modelled:
            ok, bad = identical(apply_delta(fam.base_frames, d),
                                frames_of(d.app))
        else:
            ok, bad = None, {}
            promote.append({"name": d.name, "png": d.source["png"],
                            "json": d.source["json"], "why": d.reason})
        a, c, r = d.totals
        rows.append({"variant": d.name, "class": d.classification,
                     "added": a, "changed": c, "removed": r,
                     "modelled": modelled, "exact": ok, "mismatch": bad,
                     "reason": d.reason})
    modelled = [r for r in rows if r["modelled"]]
    return {"family": fam.stem, "pack": fam.pack, "author": fam.author,
            "category": fam.category, "base": fam.base_app["name"],
            "base_cells": fam.base_cells, "variants": rows,
            "modelled_count": len(modelled),
            "all_exact": all(r["exact"] for r in modelled),
            "promote_to_own_base": promote}
