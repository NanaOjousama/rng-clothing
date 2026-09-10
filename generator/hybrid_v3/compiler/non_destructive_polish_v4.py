"""Ownership-aware wrapper for frozen legacy polish stages."""
from __future__ import annotations

from generator.renderers.fashionsense.art_polish_v5e import PolishedUpperFrames, polish_upper_frames
from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER


def _copy(frames):
    return {d: [list(row) for row in frames[d]] for d in DIRECTION_ORDER}


def merge_legacy_polish_non_destructive(base, source_frames, source_defaults, *, article_family: str, ownership):
    """Run frozen polish on a clone and merge only mutations ownership permits.

    Alpha changes are always rejected. Structural/component-owned cells may not
    be recolored unless their contract explicitly grants LEGACY_POLISH.
    """
    candidate = polish_upper_frames(base, source_frames, source_defaults, article_family=article_family)
    frames = _copy(source_frames)
    defaults = _copy(source_defaults)
    merged = {d: set() for d in DIRECTION_ORDER}
    rejected = {d: set() for d in DIRECTION_ORDER}

    for d in DIRECTION_ORDER:
        for y in range(16):
            for x in range(16):
                old = source_frames[d][y][x]
                new = candidate.frames[d][y][x]
                old_default = source_defaults[d][y][x]
                new_default = candidate.default_frames[d][y][x]
                if old == new and old_default == new_default:
                    continue
                if bool(old[3]) != bool(new[3]):
                    ownership.reject(d, (x, y), "LEGACY_POLISH", reason="alpha mutation forbidden")
                    rejected[d].add((x, y))
                    continue
                if not ownership.may_mutate(d, (x, y), "LEGACY_POLISH"):
                    ownership.reject(d, (x, y), "LEGACY_POLISH", reason="component-owned structural cell")
                    rejected[d].add((x, y))
                    continue
                frames[d][y][x] = new
                defaults[d][y][x] = new_default
                merged[d].add((x, y))

    return PolishedUpperFrames(frames, defaults, {
        **candidate.metrics,
        "ownershipAwareMerge": True,
        "mergedCells": {d: len(c) for d, c in merged.items()},
        "rejectedCells": {d: len(c) for d, c in rejected.items()},
        "rejectedCoordinates": {d: sorted(c) for d, c in rejected.items()},
    })
