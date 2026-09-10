"""Reusable Rare+ structured-field-jacket grammar over the proven V5B backend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from generator.png_utils import RGBA
from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.renderers.fashionsense.upper_v5b import FSV5BUpperRender, _coverage_missing, _stack, render_fs_v5b
from generator.renderers.fashionsense.upper_v5c2 import _bounds, _fixed, _put_fixed, _put_mask, _reset_v3_surface
from generator.v5e.engine import validate_v5e_recipe


SYSTEMS = ("silhouette", "collar", "opening", "layering", "pockets", "panels", "trim", "accent", "hem")


@dataclass(frozen=True)
class FSV5EOuterwearRender:
    recipe: dict[str, Any]
    base: FSV5BUpperRender
    frames: dict[str, list[list[RGBA]]]
    default_frames: dict[str, list[list[RGBA]]]
    texture: list[list[RGBA]]
    signal_cells: dict[str, dict[str, frozenset[tuple[int, int]]]]
    coverage_missing: dict[str, tuple[tuple[int, int], ...]]
    sleeve_colors: tuple[tuple[int, int, int], ...]
    companion_required: bool
    sleeves_texture: list[list[RGBA]] | None
    sleeves_json: dict[str, Any] | None
    sleeve_idle_frames: dict[str, list[list[RGBA]]] | None
    sleeve_metrics: dict[str, Any]


def _signals():
    return {system: {direction: set() for direction in DIRECTION_ORDER} for system in SYSTEMS}


def _replace_inherited_inner(base, frames, defaults) -> None:
    """Return V3's broad inner strip to shell cloth before authoring a bounded layer."""
    regions = base.base.design.base.regions
    for direction in DIRECTION_ORDER:
        for y in range(16):
            inner = [x for x in range(16) if regions[direction][y][x] == "INNER_LAYER" and frames[direction][y][x][3]]
            outer = [x for x in range(16) if regions[direction][y][x] in {"LEFT_OUTER_PANEL", "RIGHT_OUTER_PANEL", "BODY"} and frames[direction][y][x][3]]
            if not inner or not outer:
                continue
            for x in inner:
                source = min(outer, key=lambda candidate: abs(candidate - x))
                frames[direction][y][x] = frames[direction][y][source]
                defaults[direction][y][x] = defaults[direction][y][source]


def _front(base, frames, defaults, signals) -> None:
    # Folded collar shoulders descend into two lapels. The center remains a
    # deliberately bounded inner shirt, never a full-height decorative stripe.
    # The lapels are shell fabric, not bright undershirt. Keeping their broad
    # planes in the main dye ramp makes the garment read as outerwear instead
    # of a waistcoat with a white neck decoration.
    for x, y in ((4, 1), (5, 1), (5, 2), (6, 2), (6, 3)):
        _put_mask(base, frames, defaults, signals, "collar", "front", x, y, "LIGHT")
    for x, y in ((10, 1), (11, 1), (10, 2), (9, 2), (9, 3)):
        _put_mask(base, frames, defaults, signals, "collar", "front", x, y, "BASE")
    for x, y in ((5, 1), (10, 1), (6, 2), (9, 2), (7, 3), (8, 3), (6, 4), (9, 4), (7, 5), (8, 5)):
        _put_mask(base, frames, defaults, signals, "opening", "front", x, y, "DEEP_CREASE")
    inner = {
        1: range(7, 9), 2: range(7, 9), 3: range(7, 9),
        4: range(7, 9), 5: range(7, 9), 6: range(7, 9), 7: range(7, 9),
    }
    for y, xs in inner.items():
        for x in xs: _put_fixed(base, frames, defaults, signals, "layering", "front", x, y, "secondary")
    # Narrow lower opening shows panel overlap without turning into another shirt stripe.
    for y in range(8, 13):
        _put_mask(base, frames, defaults, signals, "opening", "front", 7, y, "STRUCTURAL_EDGE")
    # Broken shoulder panel: shaped ends flow toward the collar while leaving
    # the native animated sleeve boundary visually open instead of boxed off.
    for x, y in ((3, 3), (4, 3), (5, 3), (5, 4), (10, 4), (10, 3), (11, 3), (12, 3)):
        _put_mask(base, frames, defaults, signals, "panels", "front", x, y, "STRUCTURAL_EDGE")
    # Connected flap + pocket body clusters remain jacket fabric. Earlier
    # bright blocks competed with the inner shirt and weakened jacket identity.
    for start in (2, 10):
        for x in range(start, start + 4):
            _put_mask(base, frames, defaults, signals, "pockets", "front", x, 8, "STRUCTURAL_EDGE")
        for x in range(start + 1, start + 3):
            _put_mask(base, frames, defaults, signals, "pockets", "front", x, 9, "LIGHT" if start == 2 else "BASE")
        _put_mask(base, frames, defaults, signals, "pockets", "front", start + 2, 10, "SHADOW")
    # One small original field tab; it is a supporting cue, not a logo.
    for x, y in ((11, 5), (12, 5), (11, 6)):
        _put_fixed(base, frames, defaults, signals, "accent", "front", x, y, "accent")


def _back(base, frames, defaults, signals) -> None:
    # Back chooses one dominant yoke and a short subordinate center seam.
    for x in range(3, 13):
        y = 3 if 5 <= x <= 10 else 2
        _put_mask(base, frames, defaults, signals, "panels", "back", x, y, "STRUCTURAL_EDGE")
    # A low shell-fabric collar surrounds a tiny integrated undershirt glimpse.
    # This replaces the isolated bright pointed V seen in live gameplay.
    for x, y in ((5, 1), (6, 1), (9, 1), (10, 1), (5, 2), (10, 2)):
        _put_mask(base, frames, defaults, signals, "collar", "back", x, y, "BASE")
    for x, y in ((6, 2), (9, 2), (6, 3), (9, 3)):
        _put_mask(base, frames, defaults, signals, "collar", "back", x, y, "SHADOW")
    for x in (7, 8):
        _put_fixed(base, frames, defaults, signals, "layering", "back", x, 1, "secondary")
        _put_mask(base, frames, defaults, signals, "collar", "back", x, 2, "DEEP_CREASE")
    for y in range(4, 9):
        _put_mask(base, frames, defaults, signals, "panels", "back", 7, y, "SHADOW")
    for x, y in ((4, 7), (5, 7), (10, 7), (11, 7)):
        _put_mask(base, frames, defaults, signals, "panels", "back", x, y, "STRUCTURAL_EDGE")


def _side(base, frames, defaults, signals, direction: str) -> None:
    mirror = (lambda x: x) if direction == "right" else (lambda x: 15 - x)
    # A side is reconstructed as collar-led shell geometry, not compressed front art.
    for x, y in ((6, 1), (7, 1), (7, 2), (8, 2)):
        _put_mask(base, frames, defaults, signals, "collar", direction, mirror(x), y, "LIGHT" if direction == "right" else "BASE")
    for x, y in ((7, 2), (8, 3), (9, 4), (9, 5)):
        _put_mask(base, frames, defaults, signals, "opening", direction, mirror(x), y, "DEEP_CREASE")
    for x, y in ((8, 3), (8, 4), (9, 5)):
        _put_fixed(base, frames, defaults, signals, "layering", direction, mirror(x), y, "secondary")
    # A descending shoulder-to-shell break and a compact pocket body keep the
    # profile recognizably constructed when the front pockets are not visible.
    for x, y in ((5, 3), (6, 3), (6, 4), (7, 5)):
        _put_mask(base, frames, defaults, signals, "panels", direction, mirror(x), y, "STRUCTURAL_EDGE")
    for x in range(7, 10):
        _put_mask(base, frames, defaults, signals, "pockets", direction, mirror(x), 8, "STRUCTURAL_EDGE")
    for x in (8, 9):
        _put_mask(base, frames, defaults, signals, "pockets", direction, mirror(x), 9, "BASE")
    for y in range(7, 12):
        _put_mask(base, frames, defaults, signals, "panels", direction, mirror(11), y, "SHADOW")


def _terminations(base, frames, defaults, signals) -> None:
    for direction in DIRECTION_ORDER:
        occupied = [y for y in range(16) if any(pixel[3] for pixel in frames[direction][y])]
        bottom = max(occupied)
        bounds = _bounds(frames[direction], bottom)
        if not bounds: continue
        # Base cloth reaches the hem; only construction points receive weight.
        for x in (bounds[0], min(bounds[0] + 1, bounds[1]), max(bounds[1] - 1, bounds[0]), bounds[1]):
            _put_mask(base, frames, defaults, signals, "hem", direction, x, bottom, "DEEP_CREASE")
        if direction in {"front", "back"}:
            for x in (7, 8): _put_mask(base, frames, defaults, signals, "hem", direction, x, bottom, "SHADOW")


def render_fs_v5e(recipe: dict[str, Any]) -> FSV5EOuterwearRender:
    validation = validate_v5e_recipe(recipe)
    if not validation.valid: raise ValueError("invalid V5E recipe: " + "; ".join(validation.errors))
    base = render_fs_v5b(recipe["baseUpperRecipe"])
    frames = {direction: [list(row) for row in base.frames[direction]] for direction in DIRECTION_ORDER}
    defaults = {direction: [list(row) for row in base.default_frames[direction]] for direction in DIRECTION_ORDER}
    _reset_v3_surface(base, frames, defaults)
    _replace_inherited_inner(base, frames, defaults)
    signals = _signals()
    _front(base, frames, defaults, signals)
    _back(base, frames, defaults, signals)
    _side(base, frames, defaults, signals, "right")
    _side(base, frames, defaults, signals, "left")
    _terminations(base, frames, defaults, signals)
    coverage = _coverage_missing(base, frames, allow_sleeve_exposure=False)
    if any(coverage.values()): raise ValueError(f"V5E body coverage failed: {coverage}")
    # Runtime authority: the final hoodie correction proved that this custom
    # 32x64 Scale-2 Sleeves atlas detaches below the Farmer. V5E therefore
    # retains its sleeve palette/cuff value hierarchy through Shirt
    # SleeveColors and delegates pose/attachment to Stardew's native arms.
    # Never export the V5B experimental companion from this backend.
    native_metrics = {
        "mechanism": "NATIVE_ANIMATED_SLEEVES_V1",
        "source": "shirt.SleeveColors",
        "customSleevesAppearance": False,
        "attachment": "Stardew/Fashion Sense native Farmer arm path",
    }
    return FSV5EOuterwearRender(
        recipe, base, frames, defaults, _stack(frames),
        {name: {direction: frozenset(cells) for direction, cells in views.items()} for name, views in signals.items()},
        coverage, base.sleeve_colors, False, None,
        None, None, native_metrics,
    )
