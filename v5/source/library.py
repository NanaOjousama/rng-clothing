"""Runtime library over the dissected source: bases, components, provenance.

This is the authored-source counterpart to `v5.authored.Library`, and it keeps
the same shape deliberately so the existing Slot -> Family -> Architecture
machinery, the compatibility rules and the Fashion Sense exporter all continue
to apply.  What changes is where a silhouette comes from: not from procedural
construction, but from a real authored asset kept pixel-exact.

A SourceBase owns:
    frames      the author's own pixels, per direction, untouched
    steps       those pixels expressed in the family's value vocabulary, which
                is what a recolour rewrites -- the value RHYTHM is preserved
                and only the hue moves
    zones       semantic regions derived from the base's own drawn cells
    credit      pack, author, original asset; carried into every export

A SourceComponent is a delta that passed the reconstruction test and was
classified REUSABLE or BASE-SPECIFIC.  It is stored as authored pixels plus
their step values, so it can be recoloured with the garment rather than
appearing as a foreign sticker in the source's original greys.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import sys
sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing")
from v5.source import decompose, roundtrip, semantic

CATALOG = "source_catalog/catalog.json"
FAMILIES = "source_catalog/families.json"


@dataclass
class Credit:
    pack: str
    author: str
    pack_id: str
    asset: str

    def line(self):
        return f"{self.asset} — {self.pack} by {self.author}"


@dataclass
class SourceComponent:
    name: str
    qualifier: str
    family: str
    classification: str
    cells: dict                       # {dir: {(x,y): rgba|None}}
    steps: dict                       # {dir: {(x,y): step|None}}
    added: dict
    changed: dict
    credit: Credit
    reason: str = ""

    @property
    def adds_geometry(self) -> bool:
        """Whether this component draws where the base drew nothing.

        The distinction that decides how it is coloured: added cells are a
        separate object and take the accent material; a delta with no added
        cells is the author re-shading the garment itself.
        """
        return any(self.added.get(d) for d in self.added)

    def fits(self, base) -> bool:
        """A component only ever goes back on constructions it came from.

        REUSABLE means it adds geometry without disturbing its own base, which
        makes it a candidate elsewhere -- but "candidate" is not "compatible",
        and the only thing proven so far is the family it was cut from.
        Widening this is a decision for the compatibility pass, with evidence.
        """
        return base.family == self.family


@dataclass
class SourceBase:
    name: str
    family: str
    category: str
    frames: dict
    steps: dict
    vocab: list
    roles: dict
    tone: dict
    credit: Credit
    size: tuple
    directions: list
    declared_masks: list = field(default_factory=list)
    zones: dict = field(default_factory=dict)
    boxes: dict = field(default_factory=dict)
    # The author's own per-direction model properties, kept so that anything
    # generated from this art can wear the way they made it wear.  Dropping
    # these is what made source-derived hats sit wrongly on the head: 293 of
    # 462 direction blocks in the library declare a non-zero HeadPosition, and
    # the first exporter emitted {0, 0} for all of them.
    source_props: dict = field(default_factory=dict)

    def wear_props(self, direction: str) -> dict:
        """What the source author declared for this direction, minus the
        sheet coordinate (which belongs to whatever atlas we emit)."""
        blk = dict(self.source_props.get(direction.capitalize()) or {})
        blk.pop("StartingPosition", None)
        return blk

    @property
    def cells(self):
        return sum(len(s) for s in self.steps.values())


def _credit(d, asset):
    return Credit(d["pack"], d["author"], d.get("pack_id", ""), asset)


def load(catalog_path=CATALOG, families_path=FAMILIES):
    """Every authored base and every proven component, ready to render."""
    cat = json.load(open(catalog_path))
    fams = json.load(open(families_path))
    by_name = {(a["pack"], a["category"], a["name"]): a
               for a in cat["appearances"]}

    bases, components = [], []
    for f in fams["families"]:
        key = (f["pack"], f["category"], f["base"])
        app = by_name.get(key)
        if not app:
            continue
        frames = decompose.frames_of(app)
        vocab = [tuple(c) for c in f["vocabulary"]]
        steps = semantic.to_steps(frames, vocab)
        size = next(iter(app["analysis"]["boxes"].values()))[2:]
        credit = _credit(f["credit"], f["base"])
        base = SourceBase(f["base"], f["family"], f["category"], frames, steps,
                          vocab, {int(k): v for k, v in f["roles"].items()},
                          f["tone"], credit, tuple(size), f["directions"],
                          app["analysis"].get("declared_masks", []),
                          boxes=app["analysis"]["boxes"],
                          source_props=roundtrip.source_blocks(app))
        bases.append(base)

        # rebuild the deltas for this family so components carry real pixels
        group = [a for a in cat["appearances"]
                 if a["pack"] == f["pack"] and a["category"] == f["category"]
                 and a["stem"] == f["family"]]
        fam = decompose.build_family(group)
        if fam is None:
            continue
        for d in fam.deltas:
            if d.classification == decompose.REFERENCE_ONLY:
                # its own construction: a base, kept pixel-exact
                vframes = decompose.frames_of(d.app)
                vsteps = semantic.to_steps(vframes, vocab)
                vsize = next(iter(d.app["analysis"]["boxes"].values()))[2:]
                bases.append(SourceBase(
                    d.name, f["family"], f["category"], vframes, vsteps, vocab,
                    {int(k): v for k, v in f["roles"].items()}, f["tone"],
                    _credit(f["credit"], d.name), tuple(vsize),
                    sorted(vframes), d.app["analysis"].get("declared_masks", []),
                    boxes=d.app["analysis"]["boxes"],
                    source_props=roundtrip.source_blocks(d.app)))
                continue
            # TWO views of the same delta, and they must not be confused.
            #
            # `cells` is every differing pixel and exists so reconstruction is
            # byte-exact.  Most of those pixels are not the decoration at all:
            # for Beret (Leaf) only 34 of ~118 carry meaning, the rest being
            # the author writing 164 where the base wrote 165.  Painting the
            # whole set turned the entire beret the accent colour.
            #
            # `steps` is the PAINTABLE component: the cells that actually
            # changed in the family's value vocabulary -- new geometry, plus
            # genuine re-shading.  That is what a render draws.
            csteps = {}
            for direction, cells in d.cells.items():
                meaningful = set(d.added.get(direction, ()))
                meaningful |= set(d.changed.get(direction, ()))
                meaningful |= {xy for xy, px in cells.items() if px is None}
                csteps[direction] = {
                    xy: (semantic.step_of(cells[xy], vocab)
                         if cells[xy] else None)
                    for xy in meaningful if xy in cells}
            components.append(SourceComponent(
                d.name, d.qualifier, f["family"], d.classification,
                d.cells, csteps, d.added, d.changed,
                _credit(f["credit"], d.name), d.reason))
    return bases, components
