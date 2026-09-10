"""MATERIAL LIBRARY — rendering behaviour, separate from colour (section 20).

Every material must earn its entropy: each entry below moves at least one
lever that is visible at native 8x8 (ramp amplitude, highlight extent, or
pattern eligibility).  Materials that only differ semantically are not listed.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Material:
    name: str
    ramp_amplitude: float      # how far the ramp spreads around the base value
    ramp_depth: int            # 4-6 steps (corpus)
    highlight_extent: float    # fraction of lit cells that reach the light step
    saturation_scale: float
    edge_treatment: str        # "crisp" | "soft"
    patterns: tuple            # eligible Surface families
    contrast_bias: float       # nudges the resolved contrast tier
    formality_weight: dict = field(default_factory=dict)


MATERIALS = {
    m.name: m for m in (
        Material("cotton_drill", 1.00, 5, 0.50, 1.00, "crisp",
                 ("solid", "horizontal_stripe", "vertical_stripe", "panel"), 0.0,
                 {"work": 1.2, "casual": 1.3, "smart": 0.9, "formal": 0.5}),
        Material("wool_melton", 0.68, 4, 0.22, 0.86, "soft",
                 ("solid", "panel"), -0.15,
                 {"work": 0.9, "casual": 0.9, "smart": 1.3, "formal": 1.4}),
        Material("linen", 1.18, 5, 0.68, 0.88, "crisp",
                 ("solid", "horizontal_stripe", "vertical_stripe"), 0.05,
                 {"work": 0.8, "casual": 1.3, "smart": 1.1, "formal": 0.7}),
        Material("heavy_canvas", 0.84, 4, 0.28, 0.76, "crisp",
                 ("solid", "vertical_stripe", "panel"), -0.05,
                 {"work": 1.6, "casual": 1.0, "smart": 0.5, "formal": 0.2}),
        Material("silk_satin", 1.52, 6, 0.90, 1.12, "crisp",
                 ("solid", "panel"), 0.20,
                 {"work": 0.1, "casual": 0.5, "smart": 1.2, "formal": 1.6}),
    )
}
