"""Coordinated Fashion Sense hoodie renderer.

One semantic hoodie recipe produces a torso Shirt with native animated sleeve
colors, a true head-relative Hood/Hat, and one preset. Drawstrings stay in the
body-anchored Shirt. The reference archive is never read here. Every visible
custom component is authored as direct integer logical pixels at target size.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from generator.hoodie_layers.engine import validate_hoodie_layer_recipe
from generator.png_utils import RGBA, TRANSPARENT, blank_image, blit
from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.renderers.fashionsense.upper_v5b import _default_value, _mask_value, _stack
from generator.renderers.fashionsense.upper_v5c2 import (
    FSV5C2UpperRender,
    _coverage_missing,
    _fixed,
    _put_fixed,
    _put_mask,
    render_fs_v5c2,
)
from generator.v2_recipe_engine import load_v2_data


@dataclass(frozen=True)
class FSHoodieLayerRender:
    recipe: dict[str, Any]
    upper: FSV5C2UpperRender
    shirt_frames: dict[str, list[list[RGBA]]]
    shirt_default_frames: dict[str, list[list[RGBA]]]
    shirt_texture: list[list[RGBA]]
    hood_frames: dict[str, list[list[RGBA]]]
    hood_default_frames: dict[str, list[list[RGBA]]]
    hood_texture: list[list[RGBA]]
    hood_json: dict[str, Any]
    coverage_missing: dict[str, tuple[tuple[int, int], ...]]
    metrics: dict[str, Any]


def _copy_frame(frame: list[list[RGBA]]) -> list[list[RGBA]]:
    return [list(row) for row in frame]


def _mirror(frame: list[list[RGBA]]) -> list[list[RGBA]]:
    return [list(reversed(row)) for row in frame]


def _mask(upper: FSV5C2UpperRender, role: str) -> RGBA:
    return _mask_value(upper.base, role)


def _default(upper: FSV5C2UpperRender, role: str) -> RGBA:
    return _default_value(upper.base, role)


def _solid(upper: FSV5C2UpperRender, role: str) -> RGBA:
    return _fixed(upper.base, role)


def _primary_mask_layer(upper: FSV5C2UpperRender) -> dict[str, Any]:
    permanent = upper.base.base.design.base
    palette = load_v2_data()["palettes"]["families"][permanent.recipe["paletteFamily"]]
    # Unlike the base Shirt, the larger hood uses STRUCTURAL_EDGE explicitly
    # for back seams and lowered folds. Declare every grayscale role emitted by
    # this renderer so no seam can fall through as raw gray in game.
    roles = (
        "EXTERIOR_CONTOUR",
        "DEEP_CREASE",
        "STRUCTURAL_EDGE",
        "SHADOW",
        "BASE",
        "LIGHT",
    )
    return {
        "Name": "Primary Hoodie Fabric",
        "DefaultColor": palette["defaultDye"],
        "Values": [
            [permanent.config["outerMaskRamp"][role]] * 3
            for role in roles
        ],
    }


def _restore_torso_neck_bridge(
    recipe: dict[str, Any], upper: FSV5C2UpperRender
) -> tuple[dict[str, list[list[RGBA]]], dict[str, list[list[RGBA]]]]:
    """Move hood mass out of the Shirt while preserving an anatomical bridge."""

    frames = {direction: _copy_frame(upper.frames[direction]) for direction in DIRECTION_ORDER}
    defaults = {
        direction: _copy_frame(upper.default_frames[direction]) for direction in DIRECTION_ORDER
    }
    # Restore every old torso-only hood cell from the proven V5B garment. This
    # prevents a doubled hood once the true Hat layer is assembled.
    for direction, cells in upper.signal_cells["hood"].items():
        for x, y in cells:
            frames[direction][y][x] = upper.base.frames[direction][y][x]
            defaults[direction][y][x] = upper.base.default_frames[direction][y][x]
    # Remove the old torso-only strings before the shared bridge is rebuilt;
    # recipes that request them add them back exactly once in the Shirt below.
    for x in (6, 9):
        for y in range(3, 7):
            frames["front"][y][x] = upper.base.frames["front"][y][x]
            defaults["front"][y][x] = upper.base.default_frames["front"][y][x]

    signals = {"bridge": {direction: set() for direction in DIRECTION_ORDER}}
    lining_role = "secondary" if recipe["hoodLayer"]["lining"] == "contrast" else "dark_accent"
    # Front U-shaped neck bridge: a central interruption prevents a flat collar
    # band, while the side anchors connect the torso shell to the Hat hood.
    for x, y in ((5, 0), (10, 0), (4, 1), (11, 1), (5, 2), (10, 2), (6, 3), (9, 3)):
        _put_mask(upper.base, frames, defaults, signals, "bridge", "front", x, y, "DEEP_CREASE")
    for x, y in ((6, 0), (9, 0), (5, 1), (10, 1), (6, 2), (9, 2)):
        _put_fixed(upper.base, frames, defaults, signals, "bridge", "front", x, y, lining_role)
    for x, y in ((7, 0), (8, 0), (7, 1), (8, 1)):
        _put_fixed(upper.base, frames, defaults, signals, "bridge", "front", x, y, "dark_accent")
    # Back and sides retain only a small cloth anchor. Actual hood bulk is now
    # owned by the direction-aware Hat layer.
    for x, y in ((5, 0), (6, 0), (9, 0), (10, 0), (6, 1), (7, 1), (8, 1), (9, 1)):
        _put_fixed(upper.base, frames, defaults, signals, "bridge", "back", x, y, lining_role)
    for direction in ("right", "left"):
        source = ((5, 0), (6, 0), (5, 1), (6, 1), (7, 2))
        for x, y in source:
            xx = x if direction == "right" else 15 - x
            _put_fixed(upper.base, frames, defaults, signals, "bridge", direction, xx, y, lining_role)
        edge_x = 4 if direction == "right" else 11
        _put_mask(upper.base, frames, defaults, signals, "bridge", direction, edge_x, 1, "DEEP_CREASE")
    # Strings are a tiny body-relative feature. Keeping them in the Shirt is
    # safer than adding a head-relative Accessory origin to the live preset.
    if recipe["hoodLayer"]["drawstrings"]:
        # Two connected inward-falling strings read as cord rather than the
        # previous pair of rigid vertical bars. Their origins remain attached
        # to the hood bridge and their tips stay a restrained two-cell cue.
        for x, y in ((6, 3), (6, 4), (7, 5), (9, 3), (9, 4), (8, 5)):
            _put_fixed(upper.base, frames, defaults, signals, "bridge", "front", x, y, "light_accent")
        for x in (7, 8):
            _put_fixed(upper.base, frames, defaults, signals, "bridge", "front", x, 6, "accent")
    return frames, defaults


def _shape_bounds(y: int, rows: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return rows[min(max(y, 0), len(rows) - 1)]


def _hood_up_front(upper: FSV5C2UpperRender, contrast: bool, volume: str) -> list[list[RGBA]]:
    frame = blank_image(32, 32)
    expansion = 1 if volume == "baggy" else 0
    # The calibrated 32x32 cell is deliberately not filled. A raised hood in
    # the strongest reference pack occupies roughly 12x13 cells of its 16x16
    # source frame. At twice the logical density, this original reconstruction
    # keeps a comparable 24x26 optical footprint and spends the added cells on
    # a cleaner stepped arch instead of an oversized halo.
    rows = (
        (14, 17), (12, 19), (10, 21), (8, 23), (7, 24), (6, 25),
        (5, 26), (5, 26), (4, 27), (4, 27), (4, 27), (4, 27),
        (4, 27), (4, 27), (4, 27), (4, 27), (4, 27), (4, 27),
        (4, 27), (4, 27), (5, 26), (5, 26), (6, 25), (7, 24),
        (7, 24), (8, 23),
    )
    opening = {
        # The opening begins two cells higher and remains open through the
        # lower rim. This keeps cloth at the temples/cheeks while removing the
        # closed lower band that swallowed the Farmer's mouth in runtime.
        y: (max(10, 15 - min(5, y - 8)), min(21, 16 + min(5, y - 8)))
        for y in range(9, 32)
    }
    lining = _solid(upper, "secondary" if contrast else "dark_accent")
    for row_index, (lo0, hi0) in enumerate(rows):
        y = row_index + 6
        lo, hi = lo0, hi0
        lo = max(0, lo - expansion)
        hi = min(31, hi + expansion)
        for x in range(lo, hi + 1):
            if y in opening and opening[y][0] <= x <= opening[y][1]:
                continue
            outer = x in {lo, hi} or y in {6, 31}
            near_open = y in opening and x in {opening[y][0] - 1, opening[y][1] + 1}
            if outer:
                color = _mask(upper, "EXTERIOR_CONTOUR")
            elif near_open:
                color = lining
            elif x <= 7 or y >= 27:
                color = _mask(upper, "SHADOW")
            elif x >= 22 and 11 <= y <= 23:
                color = _mask(upper, "LIGHT")
            else:
                color = _mask(upper, "BASE")
            frame[y][x] = color
    # The continuous one-cell near-opening rim above is sufficient at Scale 2.
    # Earlier spaced lining pixels outside it created a dotted/stitched read;
    # omitting them leaves one clean connected rim and quieter fabric planes.
    return frame


def _hood_up_back(upper: FSV5C2UpperRender, contrast: bool, volume: str) -> list[list[RGBA]]:
    frame = blank_image(32, 32)
    expansion = 1 if volume == "baggy" else 0
    rows = (
        (14, 17), (12, 19), (10, 21), (8, 23), (7, 24), (6, 25),
        (5, 26), (5, 26), (4, 27), (4, 27), (4, 27), (4, 27),
        (4, 27), (4, 27), (4, 27), (4, 27), (4, 27), (4, 27),
        (4, 27), (4, 27), (5, 26), (5, 26), (6, 25), (7, 24),
    )
    seam = _solid(upper, "secondary" if contrast else "dark_accent")
    for row_index, (lo0, hi0) in enumerate(rows):
        y = row_index + 8
        lo, hi = max(0, lo0 - expansion), min(31, hi0 + expansion)
        for x in range(lo, hi + 1):
            if x in {lo, hi} or y in {8, 31}:
                color = _mask(upper, "EXTERIOR_CONTOUR")
            elif x == 15 and 13 <= y <= 27:
                color = _mask(upper, "DEEP_CREASE")
            elif x == 16 and 13 <= y <= 27:
                color = seam if y in {14, 15, 25, 26} else _mask(upper, "STRUCTURAL_EDGE")
            elif x <= 8 or y >= 28:
                color = _mask(upper, "SHADOW")
            elif x >= 23 and 13 <= y <= 25:
                color = _mask(upper, "LIGHT")
            else:
                color = _mask(upper, "BASE")
            frame[y][x] = color
    return frame


def _hood_up_side(upper: FSV5C2UpperRender, contrast: bool, volume: str) -> list[list[RGBA]]:
    frame = blank_image(32, 32)
    expansion = 1 if volume == "baggy" else 0
    rows = (
        (13, 16), (10, 19), (8, 21), (7, 22), (6, 23), (5, 24),
        (5, 25), (4, 25), (4, 25), (4, 25), (4, 25), (4, 25),
        (4, 25), (4, 25), (4, 25), (4, 25), (4, 25), (4, 25),
        (4, 25), (5, 24), (6, 23), (5, 22), (6, 21), (7, 20),
        (8, 19), (9, 18),
    )
    lining = _solid(upper, "secondary" if contrast else "dark_accent")
    for row_index, (lo0, hi0) in enumerate(rows):
        y = row_index + 6
        lo, hi = max(0, lo0 - expansion), min(31, hi0 + expansion)
        open_lo = 14 - min(4, max(0, y - 11))
        # Keep upper/front hair visible, then close the rear/lower opening in
        # a diagonal stair-step. Because Hat draws above Hair, this connected
        # cloth plane visually masks long lower side hair without cropping the
        # hairstyle or adding bulk around the face.
        if y >= 22:
            open_lo += min(4, y - 21)
        open_hi = 22 + min(2, max(0, y - 13))
        for x in range(lo, hi + 1):
            if 12 <= y <= 26 and open_lo <= x <= open_hi:
                continue
            outer = x in {lo, hi}
            near_open = 12 <= y <= 26 and x in {open_lo - 1, open_hi + 1}
            if outer:
                color = _mask(upper, "EXTERIOR_CONTOUR")
            elif near_open:
                color = lining
            elif x <= 8 or y >= 27:
                color = _mask(upper, "SHADOW")
            elif x >= 20 and y <= 23:
                color = _mask(upper, "LIGHT")
            else:
                color = _mask(upper, "BASE")
            frame[y][x] = color
    return frame


def _render_hood_up(upper: FSV5C2UpperRender, recipe: dict[str, Any]):
    contrast = recipe["hoodLayer"]["lining"] == "contrast"
    volume = recipe["hoodLayer"]["volume"]
    frames = {
        "front": _hood_up_front(upper, contrast, volume),
        "back": _hood_up_back(upper, contrast, volume),
        "right": _hood_up_side(upper, contrast, volume),
    }
    frames["left"] = _mirror(frames["right"])
    texture = blank_image(96, 32)
    blit(texture, frames["front"], 0, 0)
    blit(texture, frames["back"], 32, 0)
    blit(texture, frames["right"], 64, 0)
    return frames, texture


def _hood_down_side(upper: FSV5C2UpperRender, contrast: bool, volume: str) -> list[list[RGBA]]:
    frame = blank_image(16, 32)
    rows = ((3, 7), (1, 9), (0, 11), (0, 13), (1, 14), (2, 14), (3, 13), (4, 12), (5, 11), (6, 10))
    extra = 1 if volume == "baggy" else 0
    lining = _solid(upper, "secondary" if contrast else "dark_accent")
    for y, (lo0, hi0) in enumerate(rows):
        lo, hi = max(0, lo0 - extra), min(15, hi0 + extra)
        for x in range(lo, hi + 1):
            if x in {lo, hi} or y == 0:
                color = _mask(upper, "EXTERIOR_CONTOUR")
            elif x <= lo + 2 or y >= 7:
                color = _mask(upper, "SHADOW")
            elif x >= hi - 2:
                color = _mask(upper, "LIGHT")
            elif y in {2, 3} and x in range(lo + 4, hi - 2):
                color = lining
            else:
                color = _mask(upper, "BASE")
            frame[y][x] = color
    return frame


def _hood_down_front(
    upper: FSV5C2UpperRender, contrast: bool, volume: str
) -> list[list[RGBA]]:
    """A connected collapsed hood mass intended to draw behind the Farmer.

    The Farmer body masks the center at runtime; the asset therefore keeps a
    complete low folded silhouette instead of encoding a hairstyle-shaped
    hole. Short hair reveals more fabric and long hair naturally hides it.
    """

    # Front is intentionally wider than side/back. At Scale 2 this 24-cell
    # source permits a shallow 22-cell folded mass around the 16-cell Shirt
    # without turning the hood into a head-sized ring.
    frame = blank_image(24, 32)
    expansion = 1 if volume == "baggy" else 0
    lining_role = "secondary" if contrast else "dark_accent"
    contour = _mask(upper, "EXTERIOR_CONTOUR")
    crease = _mask(upper, "DEEP_CREASE")
    shadow = _mask(upper, "SHADOW")
    base = _mask(upper, "BASE")
    light = _mask(upper, "LIGHT")
    lining = _solid(upper, lining_role)

    rows = (
        (8, 15),
        (5, 18),
        (3, 20),
        (1, 22),
        (1, 22),
        (2, 21),
        (2, 21),
        (4, 19),
    )
    for y, (lo0, hi0) in enumerate(rows):
        lo = max(0, lo0 - (expansion if y in {2, 3, 4, 5} else 0))
        hi = min(23, hi0 + (expansion if y in {2, 3, 4, 5} else 0))
        for x in range(lo, hi + 1):
            if x in {lo, hi} or y == 0:
                color = contour
            elif y >= 6 or x <= lo + 2:
                color = shadow
            elif x == 11 and 2 <= y <= 6:
                color = crease
            elif x == 12 and 2 <= y <= 6:
                color = lining if y in {2, 3, 4} else shadow
            elif x >= hi - 2 and y <= 3:
                color = light
            else:
                color = base
            frame[y][x] = color
    # Two attached fold masses clarify collapsed cloth without adding a dotted
    # seam or changing the proven outer bounds/anchor.
    for x, y, color in (
        (7, 3, crease), (8, 4, crease), (9, 5, shadow),
        (16, 3, light), (15, 4, light), (14, 5, base),
    ):
        if frame[y][x][3]: frame[y][x] = color
    return frame


def _hood_down_back(upper: FSV5C2UpperRender, contrast: bool, volume: str) -> list[list[RGBA]]:
    frame = blank_image(16, 32)
    rows = ((5, 10), (3, 12), (1, 14), (0, 15), (0, 15), (1, 14), (2, 13), (3, 12), (4, 11), (5, 10))
    extra = 1 if volume == "baggy" else 0
    lining = _solid(upper, "secondary" if contrast else "dark_accent")
    for y, (lo0, hi0) in enumerate(rows):
        lo, hi = max(0, lo0 - extra), min(15, hi0 + extra)
        for x in range(lo, hi + 1):
            if x in {lo, hi} or y == 0:
                color = _mask(upper, "EXTERIOR_CONTOUR")
            elif x == 7 and 3 <= y <= 8:
                color = _mask(upper, "DEEP_CREASE")
            elif x == 8 and 3 <= y <= 8:
                color = lining if y <= 5 else _mask(upper, "STRUCTURAL_EDGE")
            elif x <= 3 or y >= 7:
                color = _mask(upper, "SHADOW")
            elif x >= 12:
                color = _mask(upper, "LIGHT")
            else:
                color = _mask(upper, "BASE")
            frame[y][x] = color
    return frame


def _render_hood_down(upper: FSV5C2UpperRender, recipe: dict[str, Any]):
    contrast = recipe["hoodLayer"]["lining"] == "contrast"
    volume = recipe["hoodLayer"]["volume"]
    front = _hood_down_front(upper, contrast, volume)
    right = _hood_down_side(upper, contrast, volume)
    back = _hood_down_back(upper, contrast, volume)
    frames = {"front": front, "right": right, "back": back, "left": _mirror(right)}
    # Direction models may select different widths from the same texture.
    # Only front uses the 24-cell shoulder-spread frame; side/back retain their
    # already runtime-acceptable 16-cell contracts byte-for-byte.
    texture = blank_image(24, 96)
    blit(texture, front, 0, 0)
    blit(texture, right, 0, 32)
    blit(texture, back, 0, 64)
    return frames, texture


def _hat_json(
    upper: FSV5C2UpperRender, recipe: dict[str, Any]
) -> dict[str, Any]:
    name = recipe["itemName"] + " Hood"
    mask_layer = _primary_mask_layer(upper)
    common = {
        "Scale": 2.0,
        "HideWhileSwimming": True,
        "HideWhileWearingBathingSuit": True,
        "ColorMaskLayers": [mask_layer],
    }

    def scale4_head_origin_to_scale2(x: int, y: int) -> dict[str, int]:
        """Preserve a reference Hat's screen position at twice its density.

        Fashion Sense passes the Farmer draw origin into SpriteBatch and then
        adds HeadPosition to that origin. For the normal 16x32 Farmer frame,
        the live draw origin is (0, 32). Keeping the same screen footprint
        while changing Scale 4 -> 2 therefore requires:

            high_density_origin = farmer_origin + 2 * reference_origin

        The previous renderer only doubled the reference origin. Omitting the
        retained Farmer-origin Y term put every Hat 64 display pixels low.
        """

        return {"X": 2 * x, "Y": 32 + 2 * y}

    if recipe["hoodLayer"]["state"] == "up":
        def model(
            x: int,
            reference_head_x: int,
            reference_head_y: int,
            *,
            flipped: bool = False,
        ):
            value = {
                **common,
                "StartingPosition": {"X": x, "Y": 0},
                "HeadPosition": scale4_head_origin_to_scale2(
                    reference_head_x, reference_head_y
                ),
                "HatSize": {"Width": 32, "Length": 32},
                "HideHair": True,
                "UniformAnimation": [{"Frame": 0}],
            }
            if flipped:
                value["Flipped"] = True
            return value
        return {
            "Name": name,
            "Format": "7.5.0",
            "Tags": ["RNG Clothing", "Hoodie", "Hood Up", recipe["rarity"], "Test"],
            # Runtime review found the raised front two logical cells too low.
            # Raising HeadPosition.Y from 28 to 30 moves the Scale-2 art four
            # display pixels upward without changing any other direction.
            "FrontHat": model(0, -2, -1),
            "BackHat": model(32, -2, -3),
            "RightHat": model(64, -2, -3),
            "LeftHat": model(64, -2, -3, flipped=True),
        }

    def down_model(
        starting_y: int,
        reference_head_x: int,
        reference_head_y: int,
        *,
        flipped: bool = False,
        before: str | None = None,
        after: str | None = None,
        width: int = 16,
    ):
        value = {
            **common,
            "StartingPosition": {"X": 0, "Y": starting_y},
            "HeadPosition": scale4_head_origin_to_scale2(
                reference_head_x, reference_head_y
            ),
            "HatSize": {"Width": width, "Length": 32},
            "HideHair": False,
            "UniformAnimation": [{"Frame": 0}],
        }
        if flipped:
            value["Flipped"] = True
        if before:
            value["DrawOrderOverride"] = {"Preposition": "Before", "AppearanceType": before}
        if after:
            value["DrawOrderOverride"] = {"Preposition": "After", "AppearanceType": after}
        return value
    return {
            "Name": name,
            "Format": "7.5.0",
            "Tags": ["RNG Clothing", "Hoodie", "Hood Down", recipe["rarity"], "Test"],
            # The supplied reference has no visible lowered-front pixels, so
            # its nominal (0,0) Scale-4 front origin cannot calibrate visible
            # art. Use the already proven torso-level lowered side Y contract
            # instead. HeadPosition is a SpriteBatch *origin*, so positive X
            # moves art left. X=-8 centers the 24-cell Scale-2 fold over the
            # 16-cell Scale-2 torso; the previous X=4 displaced it 24 display
            # pixels left.
            "FrontHat": down_model(0, -4, -16, before="Player", width=24),
            "RightHat": down_model(32, -3, -16, before="Player"),
            "LeftHat": down_model(32, -9, -16, flipped=True, before="Player"),
            "BackHat": down_model(64, -6, -17, after="Shirt"),
        }


def _opaque_count(frame: list[list[RGBA]]) -> int:
    return sum(pixel[3] != 0 for row in frame for pixel in row)


def _default_colored_hood(
    upper: FSV5C2UpperRender, frames: dict[str, list[list[RGBA]]]
) -> dict[str, list[list[RGBA]]]:
    """Preview the Hat's ColorMaskLayers default without changing game art."""

    roles = (
        "EXTERIOR_CONTOUR",
        "DEEP_CREASE",
        "STRUCTURAL_EDGE",
        "SHADOW",
        "BASE",
        "LIGHT",
        "OPTIONAL_HIGHLIGHT",
    )
    replacements = {_mask(upper, role): _default(upper, role) for role in roles}
    return {
        direction: [
            [replacements.get(pixel, pixel) for pixel in row]
            for row in frame
        ]
        for direction, frame in frames.items()
    }


def render_fs_hoodie_layers(recipe: dict[str, Any]) -> FSHoodieLayerRender:
    validation = validate_hoodie_layer_recipe(recipe)
    if not validation.valid:
        raise ValueError("invalid coordinated hoodie recipe: " + "; ".join(validation.errors))
    upper = render_fs_v5c2(recipe["baseUpperRecipe"])
    shirt_frames, shirt_defaults = _restore_torso_neck_bridge(recipe, upper)
    coverage = _coverage_missing(upper.base, shirt_frames, allow_sleeve_exposure=False)
    if any(coverage.values()):
        raise ValueError(f"coordinated hoodie Shirt coverage failed: {coverage}")
    if recipe["hoodLayer"]["state"] == "up":
        hood_frames, hood_texture = _render_hood_up(upper, recipe)
    else:
        hood_frames, hood_texture = _render_hood_down(upper, recipe)
    hood_defaults = _default_colored_hood(upper, hood_frames)
    return FSHoodieLayerRender(
        recipe=recipe,
        upper=upper,
        shirt_frames=shirt_frames,
        shirt_default_frames=shirt_defaults,
        shirt_texture=_stack(shirt_frames),
        hood_frames=hood_frames,
        hood_default_frames=hood_defaults,
        hood_texture=hood_texture,
        hood_json=_hat_json(upper, recipe),
        coverage_missing=coverage,
        metrics={
            "hoodState": recipe["hoodLayer"]["state"],
            "hoodFrameSize": [len(hood_frames["front"][0]), len(hood_frames["front"])],
            "hoodOpaqueByDirection": {direction: _opaque_count(frame) for direction, frame in hood_frames.items()},
            "shirtOpaqueByDirection": {direction: _opaque_count(frame) for direction, frame in shirt_frames.items()},
            "hasPullstringAccessory": False,
            "drawstringsIntegratedIntoShirt": recipe["hoodLayer"]["drawstrings"],
            "sleeveMode": "native_animated_from_shirt_sleeve_colors",
            "hairPolicy": "hide" if recipe["hoodLayer"]["state"] == "up" else "preserve",
            "hoodAnchorContract": "scale2_head_origin_includes_farmer_origin_y32",
            "promotion": "EXPERIMENTAL",
            "runtime": "NOT_TESTED",
        },
    )
