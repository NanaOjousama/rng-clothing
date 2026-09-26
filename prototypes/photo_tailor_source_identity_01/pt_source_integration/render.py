"""The only pixel-authoritative layer in the PT integration prototype."""

from dataclasses import dataclass

from source_identity import VIEWS, digest
from .contracts import FrozenFrames, RegionMask, RenderRecipe, SourceAuthority


@dataclass(frozen=True)
class PreparedPixels:
    source_id: str
    source_sha256: str
    pixels_sha256: str
    frames: FrozenFrames
    authorized_cells: tuple[tuple[str, tuple[tuple[int, int], ...]], ...]
    operations: tuple[str, ...]

    def as_frames(self):
        return dict(zip(VIEWS, self.frames))


def _validate_channel_tuple(rgb, label):
    if len(rgb) != 3 or any(type(c) is not int or not 0 <= c <= 255 for c in rgb):
        raise ValueError(f"{label}: expected in-gamut RGB8")


def _validate_mask(authority: SourceAuthority, mask: RegionMask):
    if not mask.reviewed:
        raise ValueError(f"{mask.region_id}: unreviewed mask cannot authorize pixels")
    if (mask.source_id != authority.source_id
            or mask.source_sha256 != authority.pixels_sha256):
        raise ValueError(f"{mask.region_id}: mask is bound to different source pixels")
    for view, rows in zip(VIEWS, authority.frames):
        height, width = len(rows), len(rows[0])
        for x, y in mask.cells(view):
            if not (0 <= x < width and 0 <= y < height):
                raise ValueError(f"{mask.region_id}/{view}: coordinate outside source")
            if rows[y][x][3] == 0:
                raise ValueError(f"{mask.region_id}/{view}: transparent coordinate")


def prepare_pixels(authority: SourceAuthority, recipe: RenderRecipe):
    if recipe.source_id != authority.source_id:
        raise ValueError("Recipe source_id does not match explicit source authority")
    if recipe.source_sha256 != authority.pixels_sha256:
        raise ValueError("Recipe source hash does not match explicit source pixels")
    masks = {mask.region_id: mask for mask in recipe.masks}
    if len(masks) != len(recipe.masks):
        raise ValueError("Duplicate region mask")
    for mask in recipe.masks:
        _validate_mask(authority, mask)
    if not recipe.transforms:
        return PreparedPixels(authority.source_id, authority.pixels_sha256,
                              authority.pixels_sha256, authority.frames, (), ())

    transformed_regions = set()
    operations = []
    change_plan = {}
    transformed_occupancy = {view: set() for view in VIEWS}
    for transform in recipe.transforms:
        if transform.region_id in transformed_regions:
            raise ValueError("Multiple transforms for one region are ambiguous")
        transformed_regions.add(transform.region_id)
        if transform.region_id not in masks:
            raise ValueError(f"{transform.region_id}: transform lacks reviewed mask")
        if transform.method != "source_relative_translation":
            raise ValueError("Only source-relative translation is implemented")
        mapping = dict(transform.mapping)
        if len(mapping) != len(transform.mapping):
            raise ValueError("Duplicate source color in transform")
        if not mapping:
            continue
        for source, target in mapping.items():
            _validate_channel_tuple(source, "source color")
            _validate_channel_tuple(target, "target color")
        if len(set(mapping.values())) != len(mapping):
            raise ValueError("Source shades would merge")
        deltas = {tuple(target[i] - source[i] for i in range(3))
                  for source, target in mapping.items()}
        if len(deltas) != 1:
            raise ValueError("Mapping is not one source-relative RGB translation")
        mask = masks[transform.region_id]
        for view in VIEWS:
            overlap = transformed_occupancy[view] & mask.cells(view)
            if overlap:
                raise ValueError(
                    f"Transformed region masks overlap in {view}: {sorted(overlap)}")
            transformed_occupancy[view].update(mask.cells(view))
        seen = set()
        for view_index, (view, rows) in enumerate(zip(VIEWS, authority.frames)):
            for x, y in mask.cells(view):
                source = rows[y][x][:3]
                if source in mapping:
                    key = (view_index, x, y)
                    if key in change_plan:
                        raise ValueError("Overlapping transforms target the same pixel")
                    change_plan[key] = mapping[source]
                    seen.add(source)
        absent = set(mapping) - seen
        if absent:
            raise ValueError(f"Mapped colors absent from reviewed region: {sorted(absent)}")
        operations.append(f"region:{transform.region_id}:source_relative_translation")

    out = []
    for view_index, rows in enumerate(authority.frames):
        rendered_rows = []
        for y, row in enumerate(rows):
            rendered_rows.append(tuple(
                (*change_plan[(view_index, x, y)], pixel[3])
                if (view_index, x, y) in change_plan else pixel
                for x, pixel in enumerate(row)
            ))
        out.append(tuple(rendered_rows))
    frozen_out = tuple(out)

    # Reject shade collisions with both changed and untouched source colors.
    origin_by_output = {}
    for before_rows, after_rows in zip(authority.frames, frozen_out):
        for before_row, after_row in zip(before_rows, after_rows):
            for before, after in zip(before_row, after_row):
                if before[3]:
                    origin_by_output.setdefault(after[:3], set()).add(before[:3])
    collisions = {target: origins for target, origins in origin_by_output.items()
                  if len(origins) > 1}
    if collisions:
        raise ValueError(f"Mapped shades collide with other source colors: {collisions}")
    for before_rows, after_rows in zip(authority.frames, frozen_out):
        for before_row, after_row in zip(before_rows, after_rows):
            for before, after in zip(before_row, after_row):
                if before[3] != after[3]:
                    raise AssertionError("Alpha changed in source-preserving render")
                if bool(before[3]) != bool(after[3]):
                    raise AssertionError("Occupancy changed in source-preserving render")

    authorized = []
    for view_index, view in enumerate(VIEWS):
        cells = tuple(sorted((x, y) for vi, x, y in change_plan if vi == view_index))
        authorized.append((view, cells))
    return PreparedPixels(authority.source_id, authority.pixels_sha256,
                          digest(frozen_out), frozen_out, tuple(authorized),
                          tuple(operations))
