"""Hybrid Garment Compiler V3 upstream architecture package.

Phase 1 intentionally contains no renderer imports.
"""

from .builder import CanonicalGarmentBuilder
from .config import HYBRID_GARMENT_COMPILER_V3_ENABLED, is_enabled
from .projector import DirectionalProjector
from .validator import PhysicalValidator

__all__ = [
    "CanonicalGarmentBuilder",
    "DirectionalProjector",
    "HYBRID_GARMENT_COMPILER_V3_ENABLED",
    "PhysicalValidator",
    "is_enabled",
]
