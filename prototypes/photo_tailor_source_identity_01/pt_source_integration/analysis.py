"""Advisory palette/texture evidence without quantizing or repainting art.

Photo Tailor's palette and texture analysis is adapted into exact source-pixel
statistics. No k-means result, inferred region, or pattern label is allowed to
become a render operation.
"""

from collections import Counter, defaultdict

from source_identity import VIEWS

from .contracts import PaletteCandidate, RegionMask, SourceAuthority, TextureEvidence


def _reviewed_masks(masks):
    result = tuple(masks)
    for mask in result:
        if not mask.reviewed:
            raise ValueError("Region-scoped analysis requires reviewed masks")
    return result


def analyze_palette(authority: SourceAuthority, masks=(), *, limit=None):
    """Rank exact opaque source colors; never merge or synthesize a color."""
    masks = _reviewed_masks(masks)
    counts = Counter()
    views_by_color = defaultdict(set)
    regions_by_color = defaultdict(set)
    for view, rows in zip(VIEWS, authority.frames):
        memberships = defaultdict(set)
        for mask in masks:
            for coordinate in mask.cells(view):
                memberships[coordinate].add(mask.region_id)
        for y, row in enumerate(rows):
            for x, pixel in enumerate(row):
                if not pixel[3]:
                    continue
                rgb = pixel[:3]
                counts[rgb] += 1
                views_by_color[rgb].add(view)
                regions_by_color[rgb].update(memberships[(x, y)])
    ranked = sorted(counts, key=lambda rgb: (-counts[rgb], rgb))
    if limit is not None:
        if limit < 0:
            raise ValueError("limit must be nonnegative")
        ranked = ranked[:limit]
    return tuple(PaletteCandidate(
        rgb=rgb,
        pixel_count=counts[rgb],
        views=tuple(view for view in VIEWS if view in views_by_color[rgb]),
        regions=tuple(sorted(regions_by_color[rgb])),
    ) for rgb in ranked)


def _texture_for_cells(scope, rows, cells):
    cells = {(x, y) for x, y in cells if rows[y][x][3]}
    colors = {rows[y][x][:3] for x, y in cells}
    horizontal = sum(rows[y][x][:3] != rows[y][x + 1][:3]
                     for x, y in cells if (x + 1, y) in cells)
    vertical = sum(rows[y][x][:3] != rows[y + 1][x][:3]
                   for x, y in cells if (x, y + 1) in cells)
    return TextureEvidence(scope, len(cells), len(colors), horizontal, vertical)


def analyze_texture(authority: SourceAuthority, masks=()):
    """Describe exact local color variation; do not label or generate patterns."""
    masks = _reviewed_masks(masks)
    evidence = []
    for view, rows in zip(VIEWS, authority.frames):
        whole = ((x, y) for y, row in enumerate(rows)
                 for x, pixel in enumerate(row) if pixel[3])
        evidence.append(_texture_for_cells(f"view:{view}", rows, whole))
        for mask in masks:
            cells = mask.cells(view)
            if cells:
                evidence.append(_texture_for_cells(
                    f"region:{mask.region_id}:{view}", rows, cells))
    return tuple(evidence)
