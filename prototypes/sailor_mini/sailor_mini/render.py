"""Stage 7: direction rendering. RenderPlan -> role/slot/system grids -> RGBA.

Ops are applied in order; last writer wins; every opaque cell records the system
that last wrote it. Ops never paint outside the body silhouette.
`left` is mirror(side); the prototype authors no explicit left data.
"""

from __future__ import annotations

from dataclasses import dataclass

from .architecture import build_architecture
from .artgrammar import build_render_plan
from .body import W, silhouette
from .pngio import RGBA, blank_image

DIRECTIONS = ("front", "right", "back", "left")
VIEW_OF = {"front": "front", "right": "side", "back": "back", "left": "side"}


@dataclass
class Frame:
    role: list[list[str | None]]
    slot: list[list[str | None]]
    system: list[list[str | None]]

    def mirrored(self) -> "Frame":
        return Frame(*[[list(reversed(r)) for r in g] for g in (self.role, self.slot, self.system)])

    def alpha(self) -> set[tuple[int, int]]:
        return {(x, y) for y in range(W) for x in range(W) if self.role[y][x]}


@dataclass
class Garment:
    spec: object
    plans: dict
    render_plan: dict
    frames: dict[str, Frame]
    images: dict[str, list[list[RGBA]]]

    def system_at(self, direction: str, x: int, y: int) -> str:
        return self.frames[direction].system[y][x] or "NONE"


def _render_view(spec, view, ops) -> Frame:
    grid = silhouette(view, spec.derived["fit_taper"])
    slot = [["body" if grid[y][x] else None for x in range(W)] for y in range(W)]
    system = [["silhouette" if grid[y][x] else None for x in range(W)] for y in range(W)]
    for op in ops:
        if not (0 <= op.x < W and 0 <= op.y < W):
            continue
        if grid[op.y][op.x] is None:
            continue  # never paint outside the body silhouette
        grid[op.y][op.x] = op.role
        slot[op.y][op.x] = op.slot
        system[op.y][op.x] = op.system
    return Frame(grid, slot, system)


def colorize(frame: Frame, palette) -> list[list[RGBA]]:
    img = blank_image(W, W)
    for y in range(W):
        for x in range(W):
            role = frame.role[y][x]
            if role:
                img[y][x] = palette[frame.slot[y][x]][role]
    return img


def build_garment(spec) -> Garment:
    plans = build_architecture(spec)
    render_plan = build_render_plan(spec, plans)
    frames: dict[str, Frame] = {}
    for direction in ("front", "right", "back"):
        view = VIEW_OF[direction]
        frames[direction] = _render_view(spec, view, render_plan[view])
    frames["left"] = frames["right"].mirrored()
    images = {d: colorize(frames[d], spec.palette) for d in DIRECTIONS}
    return Garment(spec, plans, render_plan, frames, images)


def atlas(images: dict[str, list[list[RGBA]]]) -> list[list[RGBA]]:
    """Fashion Sense 16x64 stack, front / right / left / back."""
    tex = blank_image(W, W * 4)
    for i, d in enumerate(("front", "right", "left", "back")):
        for y, row in enumerate(images[d]):
            tex[i * W + y] = list(row)
    return tex
