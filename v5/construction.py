"""NEW CONSTRUCTION SYSTEM (Pass 10) — authored-piece first, bounded parametric.

A Construction is a set of authored Pieces resolved against one Envelope.  Each
Piece owns its own per-view cells, its edge semantics, its wrap behaviour, its
semantic-zone footprint and its declared occlusion stamps.  Nothing here carves
silhouettes procedurally (INV-10) and nothing here invents colour.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .grammar import ATTACHED, FREE, GIRTH, PLANE, VIEWS, Envelope, compose_occlusion

Cell = tuple[int, int]


def parse_art(rows: list[str]) -> set[Cell]:
    """Authored string art -> cell set.  '#' is opaque, anything else is empty."""
    return {(x, y) for y, row in enumerate(rows) for x, ch in enumerate(row) if ch == "#"}


# Authored shading micro-pattern alphabet, darkest to lightest.  Used where the
# procedural form model does not give enough control at 8x8 — a three-row yoke
# has too few cells for a distance transform to say anything useful, but a
# hand-written stencil says it exactly.
SHADE_CHARS = {"D": 2, "S": 1, "M": 0, "L": -1, "H": -2}


def parse_shading(rows: list[str], origin: Cell = (0, 0)) -> dict:
    """Authored string art -> {cell: ramp-step offset}.  '.' means 'no opinion'."""
    ox, oy = origin
    return {(ox + x, oy + y): SHADE_CHARS[ch]
            for y, row in enumerate(rows) for x, ch in enumerate(row)
            if ch in SHADE_CHARS}


@dataclass
class Piece:
    """One authored structural piece."""
    name: str
    role: str                                  # fabric role, never a colour
    z: int
    wrap: str = PLANE
    cells: dict = field(default_factory=dict)          # view -> set[Cell]
    free_edges: dict = field(default_factory=dict)     # view -> set[Cell] with a free boundary
    occlusion: dict = field(default_factory=dict)      # view -> {Cell: ramp-step depth}
    surface_domain: str | None = None
    zones: tuple = ()
    accent_cells: dict = field(default_factory=dict)   # view -> set[Cell] (1-2px accents)
    identity: bool = False                     # is this piece load-bearing for family identity?
    # Fraction of this piece that must still be painted in its own role after
    # composition.  None inherits the Architecture's figure.  Authored per piece
    # because some pieces are MEANT to be painted over — piping belongs on the
    # dickey — while a collar that loses a third of itself stops being a collar.
    min_retention: float | None = None
    # For a GIRTH piece: which edge actually runs round the body.  A collar is
    # anchored at its top; a blouse showing under a yoke is anchored at its hem,
    # because how much of it is covered differs per view.
    girth_anchor: str = "top"
    # How this piece reads as a form under the render class's shading model.
    #   "mass"  a panel: top and lateral edges darker, interior lighter
    #   "knot"  a tied/folded object: top and outer edges lighter, centre darker
    # Traced from the references, where the yoke lightens downward but the bow
    # lightens upward — shading direction is a property of the thing, not a law.
    form: str = "mass"
    # Authored per-cell ramp offsets that override the shading model.
    shading: dict = field(default_factory=dict)     # view -> {Cell: offset}

    def view_cells(self, view: str) -> set:
        return self.cells.get(view, set())

    def edge_kind(self, view: str, cell: Cell) -> str:
        return FREE if cell in self.free_edges.get(view, set()) else ATTACHED

    def area(self) -> int:
        return sum(len(c) for c in self.cells.values())


@dataclass
class Construction:
    env: Envelope
    silhouette: dict                # view -> set[Cell]
    pieces: list                    # z-ordered
    surface_domains: dict = field(default_factory=dict)   # domain -> [piece names]

    def ordered(self) -> list:
        return sorted(self.pieces, key=lambda p: (p.z, p.name))

    def by_name(self, name: str) -> Piece | None:
        for p in self.pieces:
            if p.name == name:
                return p
        return None

    def region_map(self, view: str) -> dict:
        """Cell -> owning piece name, after z-order compositing."""
        out: dict[Cell, str] = {}
        for piece in self.ordered():
            for cell in piece.view_cells(view):
                if cell in self.silhouette[view]:
                    out[cell] = piece.name
        return out

    def occlusion_field(self, view: str) -> dict:
        """Declared shadow stamps composed by MAX, never addition (INV-09)."""
        return compose_occlusion([p.occlusion.get(view, {}) for p in self.pieces])

    def free_edge_cells(self, view: str) -> dict:
        out: dict[Cell, str] = {}
        for piece in self.ordered():
            for cell in piece.free_edges.get(view, set()):
                out[cell] = piece.name
        return out

    def drop(self, name: str) -> None:
        self.pieces = [p for p in self.pieces if p.name != name]

    def validate(self) -> None:
        for view in VIEWS:
            sil = self.silhouette[view]
            for piece in self.pieces:
                stray = piece.view_cells(view) - sil
                if stray:
                    raise ValueError(
                        f"piece {piece.name!r} paints outside the {view} silhouette: "
                        f"{sorted(stray)}"
                    )
            covered = self.region_map(view)
            missing = sil - set(covered)
            if missing:
                raise ValueError(f"{view}: silhouette cells with no piece: {sorted(missing)}")
        for piece in self.pieces:
            if piece.wrap not in (GIRTH, PLANE):
                raise ValueError(f"piece {piece.name!r}: bad wrap mode")


def girth_rows(construction: Construction, view: str, piece_name: str) -> set:
    """Rows a girth feature occupies — must agree across views (section 38)."""
    piece = construction.by_name(piece_name)
    if piece is None:
        return set()
    return {y for (_, y) in piece.view_cells(view)}
