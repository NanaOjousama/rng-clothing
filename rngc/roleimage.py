"""RoleImage: the only intermediate representation in the V5 pipeline.

Per 16x16 view three integer grids:
  role  : 0 none/transparent, 1 base, 2 light, 3 shadow, 4 deep
  slot  : index into SLOTS (-1 when transparent)
  src   : provenance, -1 = blank, >=0 = index of the applied piece, -2 = none
  src_x / src_y : the local coordinate inside the authoring view of the source

No RGB is stored here. No parallel "default" frames exist.
"""

from __future__ import annotations

from dataclasses import dataclass

SIZE = 16
ROLES = ("none", "base", "light", "shadow", "deep")
ROLE_CHARS = {"b": 1, "l": 2, "s": 3, "d": 4}
SLOTS = ("primary", "secondary", "trim", "accent")
VIEWS = ("front", "side", "back")           # authored views
DIRECTIONS = ("front", "right", "back", "left")  # runtime directions
SRC_BLANK = -1
SRC_NONE = -2


def _grid(value: int) -> list[list[int]]:
    return [[value] * SIZE for _ in range(SIZE)]


@dataclass
class RoleImage:
    role: list[list[int]]
    slot: list[list[int]]
    src: list[list[int]]
    src_x: list[list[int]]
    src_y: list[list[int]]

    @classmethod
    def empty(cls) -> "RoleImage":
        return cls(_grid(0), _grid(-1), _grid(SRC_NONE), _grid(-1), _grid(-1))

    def copy(self) -> "RoleImage":
        return RoleImage(*[[list(r) for r in g] for g in (self.role, self.slot, self.src, self.src_x, self.src_y)])

    def opaque(self, x: int, y: int) -> bool:
        return self.role[y][x] != 0

    def alpha(self) -> set[tuple[int, int]]:
        return {(x, y) for y in range(SIZE) for x in range(SIZE) if self.role[y][x]}

    def mirrored(self) -> "RoleImage":
        """Horizontal flip. Local source coordinates are kept as authored."""
        return RoleImage(*[[list(reversed(r)) for r in g] for g in (self.role, self.slot, self.src, self.src_x, self.src_y)])

    def provenance(self, x: int, y: int, piece_ids: list[str]) -> str:
        s = self.src[y][x]
        if s == SRC_NONE:
            return "NONE"
        name = "blank" if s == SRC_BLANK else piece_ids[s]
        return f"{name}/local({self.src_x[y][x]},{self.src_y[y][x]})"

    def to_json(self, piece_ids: list[str]) -> dict:
        return {
            "role": [[ROLES[v] if v else "." for v in row] for row in self.role],
            "slot": [[SLOTS[v] if v >= 0 else "." for v in row] for row in self.slot],
            "source": [[self.provenance(x, y, piece_ids) for x in range(SIZE)] for y in range(SIZE)],
        }
