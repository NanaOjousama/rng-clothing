"""Compositor: blank -> pieces in (layer, plan order) -> RoleImage per direction.

Rules (and the whole conflict system):
  * pieces are applied in ascending (layer, plan index) order; last writer wins;
  * every write records provenance (piece index, local x, local y);
  * a write over a cell already owned by another piece is logged as a double write;
  * ``left`` is mirror(side) unless the blank or a piece supplies an explicit
    ``left`` view, in which case left is composed view-by-view with mirrored
    fallbacks for pieces that lack one.

NO-POLISH INVARIANT: this module never reads a neighbouring cell to decide a
role. It only copies authored characters onto the grid.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .data import Blank, Library, Piece, PieceView, Plan, resolve_row_expr
from .roleimage import ROLE_CHARS, SIZE, SLOTS, SRC_BLANK, DIRECTIONS, RoleImage


@dataclass
class AppliedPiece:
    index: int
    piece: Piece
    slot: str | None  # effective slot after plan override


@dataclass
class ComposeResult:
    plan: Plan
    blank: Blank
    applied: list[AppliedPiece]
    images: dict[str, RoleImage]  # keyed by DIRECTIONS
    explicit_left: bool
    double_writes: list[dict] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)
    alpha_ops: list[dict] = field(default_factory=list)

    @property
    def piece_ids(self) -> list[str]:
        return [a.piece.id for a in self.applied]


def blank_image(blank: Blank, view: str) -> RoleImage:
    img = RoleImage.empty()
    for y, row in enumerate(blank.views[view]):
        for x, ch in enumerate(row):
            if ch != ".":
                img.role[y][x] = ROLE_CHARS[ch]; img.slot[y][x] = 0
                img.src[y][x] = SRC_BLANK; img.src_x[y][x] = x; img.src_y[y][x] = y
    return img


def _mirror_view(view: PieceView) -> PieceView:
    ox = SIZE - (view.origin_x + view.width)
    return PieceView(ox, view.origin_y, tuple("".join(reversed(r)) for r in view.rows))


def apply_piece(img: RoleImage, ap: AppliedPiece, view: PieceView, blank: Blank, direction: str, result: ComposeResult, *, mirrored: bool = False) -> None:
    slot_idx = SLOTS.index(ap.slot) if ap.slot else None
    oy = resolve_row_expr(view.origin_y, blank)
    for ly, row in enumerate(view.rows):
        for lx, ch in enumerate(row):
            if ch == ".":
                continue
            x, y = view.origin_x + lx, oy + ly
            # local coordinate as authored (un-mirror x when applying a flipped view)
            ax = (view.width - 1 - lx) if mirrored else lx
            if not (0 <= x < SIZE and 0 <= y < SIZE):
                result.skipped.append({"piece": ap.piece.id, "direction": direction, "cell": [x, y], "reason": "outside frame"}); continue
            opaque = img.role[y][x] != 0
            if ch == "-":
                if not opaque:
                    result.skipped.append({"piece": ap.piece.id, "direction": direction, "cell": [x, y], "reason": "cut on transparent"}); continue
                img.role[y][x] = 0; img.slot[y][x] = -1
                img.src[y][x] = ap.index; img.src_x[y][x] = ax; img.src_y[y][x] = ly
                result.alpha_ops.append({"piece": ap.piece.id, "direction": direction, "op": "cut", "cell": [x, y]})
                continue
            if ch == "+":
                if opaque:
                    result.skipped.append({"piece": ap.piece.id, "direction": direction, "cell": [x, y], "reason": "add on opaque"}); continue
                img.role[y][x] = 1; img.slot[y][x] = slot_idx if slot_idx is not None else 0
                img.src[y][x] = ap.index; img.src_x[y][x] = ax; img.src_y[y][x] = ly
                result.alpha_ops.append({"piece": ap.piece.id, "direction": direction, "op": "add", "cell": [x, y]})
                continue
            if not opaque:
                result.skipped.append({"piece": ap.piece.id, "direction": direction, "cell": [x, y], "reason": "paint on transparent"}); continue
            prev = img.src[y][x]
            if prev >= 0 and prev != ap.index:
                result.double_writes.append({"direction": direction, "cell": [x, y], "previous": result.applied[prev].piece.id, "piece": ap.piece.id})
            if ch == "=":
                img.slot[y][x] = slot_idx
            else:
                img.role[y][x] = ROLE_CHARS[ch]
                if slot_idx is not None:
                    img.slot[y][x] = slot_idx
            img.src[y][x] = ap.index; img.src_x[y][x] = ax; img.src_y[y][x] = ly


def compose(plan: Plan, lib: Library) -> ComposeResult:
    blank = lib.blanks[plan.blank]
    applied = [AppliedPiece(i, lib.pieces[p.id], p.slot or lib.pieces[p.id].slot) for i, p in enumerate(plan.pieces)]
    order = sorted(applied, key=lambda a: (a.piece.layer, a.index))
    explicit_left = "left" in blank.views or any("left" in a.piece.views for a in applied)
    result = ComposeResult(plan, blank, applied, {}, explicit_left)

    for view, direction in (("front", "front"), ("side", "right"), ("back", "back")):
        img = blank_image(blank, view)
        for ap in order:
            if view in ap.piece.views:
                apply_piece(img, ap, ap.piece.views[view], blank, direction, result)
        result.images[direction] = img

    if not explicit_left:
        result.images["left"] = result.images["right"].mirrored()
    else:
        img = blank_image(blank, "left") if "left" in blank.views else blank_image(blank, "side").mirrored()
        for ap in order:
            if "left" in ap.piece.views:
                apply_piece(img, ap, ap.piece.views["left"], blank, "left", result)
            elif "side" in ap.piece.views:
                apply_piece(img, ap, _mirror_view(ap.piece.views["side"]), blank, "left", result, mirrored=True)
        result.images["left"] = img
    return result
