"""Immutable preview/export and exact source/output diff support."""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from source_identity import VIEWS
from v5.pngio import encode_rgba_png, read_rgba_png

from .contracts import SourceAuthority
from .render import PreparedPixels


@dataclass(frozen=True)
class ViewDiff:
    view: str
    changed_pixels: int
    changed_coordinates: tuple[tuple[int, int], ...]
    outside_authority: tuple[tuple[int, int], ...]
    alpha_changes: int
    occupancy_changes: int


@dataclass(frozen=True)
class DiffAudit:
    source_sha256: str
    output_sha256: str
    identity_exact: bool
    views: tuple[ViewDiff, ...]
    color_changes: tuple[tuple[tuple[int, int, int], tuple[int, int, int], int], ...]
    passed: bool


def audit_diff(authority: SourceAuthority, prepared: PreparedPixels):
    if prepared.source_id != authority.source_id:
        raise ValueError("Prepared pixels belong to another source")
    if prepared.source_sha256 != authority.pixels_sha256:
        raise ValueError("Prepared source hash drift")
    allowed = {view: set(cells) for view, cells in prepared.authorized_cells}
    per_view = []
    changes = Counter()
    for view, before_rows, after_rows in zip(VIEWS, authority.frames, prepared.frames):
        changed, outside = [], []
        alpha_changes = occupancy_changes = 0
        for y, (before_row, after_row) in enumerate(zip(before_rows, after_rows)):
            for x, (before, after) in enumerate(zip(before_row, after_row)):
                if before != after:
                    changed.append((x, y))
                    changes[(before[:3], after[:3])] += 1
                    if (x, y) not in allowed.get(view, set()):
                        outside.append((x, y))
                alpha_changes += before[3] != after[3]
                occupancy_changes += bool(before[3]) != bool(after[3])
        per_view.append(ViewDiff(view, len(changed), tuple(changed), tuple(outside),
                                 alpha_changes, occupancy_changes))
    identity = authority.frames == prepared.frames
    passed = all(not view.outside_authority and not view.alpha_changes
                 and not view.occupancy_changes for view in per_view)
    return DiffAudit(authority.pixels_sha256, prepared.pixels_sha256, identity,
                     tuple(per_view),
                     tuple((a, b, count) for (a, b), count in sorted(changes.items())),
                     passed)


def preview_frames(prepared: PreparedPixels):
    """Preview receives the exact immutable tuples later sent to export."""
    return prepared.as_frames()


def export_prepared(prepared: PreparedPixels, directory, *, overwrite=False):
    """Export exactly the prepared pixels; never rerender at save time."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    exported = []
    for view, rows in zip(VIEWS, prepared.frames):
        path = directory / f"{view}.png"
        payload = encode_rgba_png(rows)
        if path.exists() and not overwrite and path.read_bytes() != payload:
            raise FileExistsError(f"Refusing to replace different export: {path}")
        path.write_bytes(payload)
        if tuple(tuple(tuple(pixel) for pixel in row) for row in read_rgba_png(path)) != rows:
            raise AssertionError(f"Exported pixels drifted: {view}")
        exported.append(path)
    return tuple(exported)
