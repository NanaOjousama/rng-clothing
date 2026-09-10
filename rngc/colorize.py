"""Colorize: rgb = palette[slot][role]. Exactly once. No blending, no derivation."""

from __future__ import annotations

from .compose import ComposeResult
from .data import Palette
from .pngio import RGBA, TRANSPARENT, blank_image
from .roleimage import ROLES, SIZE, SLOTS, RoleImage

ROLE_NAMES = {1: "base", 2: "light", 3: "shadow", 4: "deep"}


def colorize_image(img: RoleImage, palette: Palette) -> list[list[RGBA]]:
    out = blank_image(SIZE, SIZE)
    for y in range(SIZE):
        for x in range(SIZE):
            r = img.role[y][x]
            if not r:
                continue
            slot = SLOTS[img.slot[y][x]]
            if slot not in palette.slots:
                raise ValueError(f"palette {palette.id} has no slot {slot!r} needed at ({x},{y})")
            out[y][x] = palette.slots[slot][ROLE_NAMES[r]]
    return out


def colorize(result: ComposeResult, palette: Palette) -> dict[str, list[list[RGBA]]]:
    return {d: colorize_image(img, palette) for d, img in result.images.items()}


def sleeve_colors(palette: Palette, slot: str, roles: list[str]) -> list[list[int]]:
    if slot not in palette.slots:
        raise ValueError(f"palette {palette.id} has no sleeve slot {slot!r}")
    return [list(palette.slots[slot][r][:3]) for r in roles]


def distinct_colors(frames: dict[str, list[list[RGBA]]]) -> set[RGBA]:
    return {p for f in frames.values() for row in f for p in row if p[3]}
