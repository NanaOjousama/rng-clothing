"""Immutable contracts adapted from Photo Tailor's evidence/preview DTOs.

Photo Tailor's useful distinction between recognition evidence and prepared art
is retained. Source binding, provenance, and human-review state are added so a
detected hypothesis cannot silently become render authority.
"""

from dataclasses import dataclass, field
from typing import Any, Mapping

from source_identity import VIEWS, digest, freeze

RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]
Coord = tuple[int, int]
FrozenRows = tuple[tuple[RGBA, ...], ...]
FrozenFrames = tuple[FrozenRows, ...]


@dataclass(frozen=True)
class SourceAuthority:
    source_id: str
    pixels_sha256: str
    frames: FrozenFrames
    frame_sizes: tuple[tuple[str, int, int], ...]
    provenance: str

    @classmethod
    def bind(cls, source_id: str, frames: Mapping[str, Any], *, provenance: str):
        if not source_id.strip():
            raise ValueError("Explicit source_id is required")
        if not provenance.strip():
            raise ValueError("Source provenance is required")
        frozen = freeze(frames)
        sizes = tuple((view, len(rows[0]), len(rows))
                      for view, rows in zip(VIEWS, frozen))
        return cls(source_id, digest(frozen), frozen, sizes, provenance)

    def as_frames(self):
        return dict(zip(VIEWS, self.frames))


@dataclass(frozen=True)
class AttributeCandidate:
    group: str
    value: str
    category: str
    score: float
    rank: int
    provenance: str
    reviewed: bool = False


@dataclass(frozen=True)
class FeatureEvidence:
    feature_type: str
    view: str
    bounds: tuple[int, int, int, int] | None
    confidence: float
    provenance: str
    reviewed: bool = False


@dataclass(frozen=True)
class RegionEvidence:
    region_id: str
    view: str
    coordinates: tuple[Coord, ...]
    provenance: str
    reviewed: bool = False


@dataclass(frozen=True)
class RegionMask:
    """Explicit source-space coordinates; never inferred by this package."""

    region_id: str
    source_id: str
    source_sha256: str
    cells_by_view: tuple[tuple[str, tuple[Coord, ...]], ...]
    provenance: str
    reviewed: bool

    @classmethod
    def reviewed_mask(cls, region_id: str, authority: SourceAuthority,
                      cells_by_view: Mapping[str, Any],
                      *, provenance: str):
        return cls(region_id, authority.source_id, authority.pixels_sha256,
                   _freeze_cells(cells_by_view), provenance, True)

    @classmethod
    def proposal(cls, region_id: str, authority: SourceAuthority,
                 cells_by_view: Mapping[str, Any],
                 *, provenance: str):
        return cls(region_id, authority.source_id, authority.pixels_sha256,
                   _freeze_cells(cells_by_view), provenance, False)

    def cells(self, view: str):
        return frozenset(dict(self.cells_by_view).get(view, ()))


def _freeze_cells(cells_by_view):
    unknown = set(cells_by_view) - set(VIEWS)
    if unknown:
        raise ValueError(f"Unknown views in mask: {sorted(unknown)}")
    frozen = []
    for view in VIEWS:
        cells = tuple(sorted(set(tuple(cell) for cell in cells_by_view.get(view, ()))))
        if any(len(cell) != 2 or any(type(n) is not int for n in cell)
               for cell in cells):
            raise ValueError(f"{view}: mask coordinates must be integer x/y pairs")
        frozen.append((view, cells))
    return tuple(frozen)


@dataclass(frozen=True)
class RegionTransform:
    region_id: str
    mapping: tuple[tuple[RGB, RGB], ...]
    method: str = "source_relative_translation"

    @classmethod
    def source_relative(cls, region_id: str, mapping: Mapping[RGB, RGB]):
        return cls(region_id, tuple(sorted((tuple(a), tuple(b))
                                           for a, b in mapping.items())))


@dataclass(frozen=True)
class RenderRecipe:
    source_id: str
    source_sha256: str
    masks: tuple[RegionMask, ...] = ()
    transforms: tuple[RegionTransform, ...] = ()

    @classmethod
    def identity(cls, authority: SourceAuthority):
        return cls(authority.source_id, authority.pixels_sha256)


@dataclass(frozen=True)
class PaletteCandidate:
    rgb: RGB
    pixel_count: int
    views: tuple[str, ...]
    regions: tuple[str, ...]
    provenance: str = "exact_source_pixels"
    approved_for_render: bool = False


@dataclass(frozen=True)
class TextureEvidence:
    scope: str
    opaque_pixels: int
    unique_colors: int
    horizontal_transitions: int
    vertical_transitions: int
    classification: str = "UNDETERMINED_ADVISORY"
    approved_for_render: bool = False


@dataclass(frozen=True)
class RankedSemanticCandidate:
    item_id: str
    name: str
    sprite_index: int
    score: float


@dataclass(frozen=True)
class EvidenceBundle:
    source_id: str
    source_sha256: str
    prepared_pixels_sha256: str
    semantic_status: str
    semantic_candidates: tuple[RankedSemanticCandidate, ...] = ()
    palette_candidates: tuple[PaletteCandidate, ...] = ()
    texture_evidence: tuple[TextureEvidence, ...] = ()
    attributes: tuple[AttributeCandidate, ...] = ()
    features: tuple[FeatureEvidence, ...] = ()
    regions: tuple[RegionEvidence, ...] = ()
    automatic_pixel_operations: tuple = field(default_factory=tuple)

    def __post_init__(self):
        if self.automatic_pixel_operations:
            raise ValueError("Advisory evidence cannot authorize pixel operations")
