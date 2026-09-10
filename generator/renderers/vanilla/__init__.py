"""Compatibility facade for the existing vanilla V2 renderer.

The implementation remains in :mod:`generator.v2_renderer`; this facade makes
the optional-backend boundary explicit without moving or changing proven V2
code.
"""

from generator.v2_renderer import RenderedV2Shirt, render_v2_recipe

__all__ = ["RenderedV2Shirt", "render_v2_recipe"]

