"""ORNAMENT / DETAIL LIBRARY (sections 26-27).

Ornament resolves after Surface, out of whatever complexity remains, subject to
semantic occupancy, Architecture affinity, and readability.  Receiving no
budget at all is a valid outcome.

Detail Packages coordinate accents instead of scattering independent pixels.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .schema import CONDITIONAL_SHARE, EXCLUSIVE, OVERLAY


@dataclass(frozen=True)
class OrnamentType:
    name: str
    zone: str
    claim_mode: str
    cost: int
    role: str
    views: tuple                 # which authored views it may appear in
    max_cells: int               # accent economy: corpus says 1-2px accents
    formality_weight: dict = field(default_factory=dict)


ORNAMENTS = {
    o.name: o for o in (
        OrnamentType("chest_emblem", "chest:center", CONDITIONAL_SHARE, 2, "accent",
                     ("front",), 2, {"work": 0.6, "casual": 1.2, "smart": 1.0, "formal": 0.7}),
        OrnamentType("cuff_band", "hip:left", CONDITIONAL_SHARE, 1, "secondary_accent",
                     ("front", "side", "back"), 4,
                     {"work": 0.9, "casual": 1.1, "smart": 1.2, "formal": 1.1}),
        OrnamentType("hem_band", "hem:girth", EXCLUSIVE, 1, "secondary_accent",
                     ("front", "side", "back"), 6,
                     {"work": 0.8, "casual": 1.0, "smart": 1.2, "formal": 1.3}),
        # Back only: on the side view the flap is two cells wide, so a pair of
        # studs consumes the whole edge and reads as two floating dots.
        OrnamentType("flap_stud", "chest:right", EXCLUSIVE, 1, "hardware",
                     ("back",), 2,
                     {"work": 0.7, "casual": 0.9, "smart": 1.2, "formal": 1.2}),
    )
}


@dataclass(frozen=True)
class DetailPackage:
    """Coordinated accents rather than random independent accent pixels."""
    name: str
    hardware_finish: str
    affinity: dict               # ornament name -> weight multiplier
    formality_weight: dict


DETAIL_PACKAGES = {
    d.name: d for d in (
        DetailPackage("SUBTLE_GOLD", "gold",
                      {"flap_stud": 2.2, "cuff_band": 1.3, "hem_band": 1.0, "chest_emblem": 0.6},
                      {"work": 0.5, "casual": 0.9, "smart": 1.4, "formal": 1.5}),
        DetailPackage("NAVY_WHITE_CLASSIC", "pearl",
                      {"flap_stud": 0.7, "cuff_band": 1.6, "hem_band": 1.5, "chest_emblem": 1.1},
                      {"work": 1.1, "casual": 1.4, "smart": 1.1, "formal": 0.9}),
        DetailPackage("ROPE_RED", "brass",
                      {"flap_stud": 1.0, "cuff_band": 1.1, "hem_band": 0.8, "chest_emblem": 1.7},
                      {"work": 1.3, "casual": 1.2, "smart": 0.7, "formal": 0.4}),
    )
}
