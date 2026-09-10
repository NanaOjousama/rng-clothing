"""One player roll, end to end."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import ARCHITECTURE_LIBRARY, SLOT_LIBRARY
from .grammar import Envelope
from . import aa, ag, projection, quality
from .resolver import generate_spec


@dataclass
class Garment:
    spec: object
    construction: object
    art: object
    raster: object
    projection: object
    verdict: object = None
    signature: object = None
    problems: tuple = ()


def generate(seed: int, *, slot: str = "TOP",
             envelope: Envelope | None = None) -> Garment:
    # The Slot owns its authoring envelope and render class (Pass 2 decides
    # representation capability before anything else is rolled).
    slot_contract = SLOT_LIBRARY[slot]
    envelope = envelope or slot_contract.envelope
    spec = generate_spec(seed, slot=slot, envelope=envelope)         # Passes 1-9
    arch = ARCHITECTURE_LIBRARY[spec.architecture]
    construction = arch.realize(spec, envelope)                      # Pass 10
    construction.validate()
    art = aa.plan(spec, construction, arch)                                # Pass 11
    raster = ag.rasterize(spec, construction, art,
                          slot_contract.render_class)                # Pass 12
    proj = projection.project(spec, construction, art, raster)       # Pass 13
    problems = tuple(projection.check_continuity(spec, construction, art)
                     + projection.check_coverage(spec, proj))
    return Garment(spec, construction, art, raster, proj, problems=problems)


def generate_batch(seeds, *, slot: str = "TOP") -> list:
    """Pass 14 runs across the batch: diversity is a batch property."""
    out, accepted = [], []
    for seed in seeds:
        g = generate(seed, slot=slot)
        g.verdict, g.signature = quality.evaluate(
            g.spec, g.construction, g.art, g.raster, accepted,
            ARCHITECTURE_LIBRARY[g.spec.architecture])
        if g.verdict.classification == quality.ACCEPT:
            accepted.append((seed, g.signature))
        out.append(g)
    return out
