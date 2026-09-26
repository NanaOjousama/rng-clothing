"""Photo Tailor-informed infrastructure around source-authoritative pixels.

This package intentionally contains no Photo Tailor renderer, canonical canvas,
UV projection, shade reconstruction, harmonization, or procedural decoration.
"""

from .contracts import (
    AttributeCandidate,
    EvidenceBundle,
    FeatureEvidence,
    PaletteCandidate,
    RegionEvidence,
    RegionMask,
    RegionTransform,
    RenderRecipe,
    SourceAuthority,
    TextureEvidence,
)
from .pipeline import IntegrationResult, prepare_integration

__all__ = [
    "AttributeCandidate",
    "EvidenceBundle",
    "FeatureEvidence",
    "IntegrationResult",
    "PaletteCandidate",
    "RegionEvidence",
    "RegionMask",
    "RegionTransform",
    "RenderRecipe",
    "SourceAuthority",
    "TextureEvidence",
    "prepare_integration",
]
