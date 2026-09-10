"""Bounded topology API for V4 directional component construction."""
from __future__ import annotations

TRANSPARENT = (0, 0, 0, 0)


class TopologyError(ValueError):
    pass


class TopologyEditorV4:
    def __init__(self, frames, defaults, *, safe_envelopes, ownership, opaque_value, default_value):
        self.frames = frames
        self.defaults = defaults
        self.safe_envelopes = safe_envelopes
        self.ownership = ownership
        self.opaque_value = opaque_value
        self.default_value = default_value
        self.operations = []

    def _allowed(self, direction, x, y):
        return (x, y) in self.safe_envelopes.get(direction, set())

    def _alpha_cells(self, direction):
        return {(x, y) for y, row in enumerate(self.frames[direction]) for x, pixel in enumerate(row) if pixel[3]}

    @staticmethod
    def _groups(cells):
        cells = set(cells); groups = []
        while cells:
            root = cells.pop(); group = {root}; todo = [root]
            while todo:
                x, y = todo.pop()
                for nxt in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if nxt in cells:
                        cells.remove(nxt); group.add(nxt); todo.append(nxt)
            groups.append(group)
        return groups

    def _record(self, *, op, direction, cell, owner, variant_id, before_alpha, after_alpha):
        self.operations.append({
            "op": op, "direction": direction, "cell": list(cell), "owner": owner,
            "variantId": variant_id, "beforeAlpha": before_alpha, "afterAlpha": after_alpha,
            "alphaDisplacement": int(before_alpha != after_alpha),
        })

    def add(self, direction, x, y, *, component_owner, variant_id, system="silhouette", semantic_region=None, shade="BASE"):
        if not (0 <= x < 16 and 0 <= y < 16):
            raise TopologyError(f"cell outside logical frame: {direction} {(x,y)}")
        if not self._allowed(direction, x, y):
            raise TopologyError(f"cell outside V4 safe envelope: {direction} {(x,y)}")
        if self.frames[direction][y][x][3]:
            raise TopologyError(f"alpha addition targets opaque cell: {direction} {(x,y)}")
        existing = self._alpha_cells(direction)
        if not any((x+dx, y+dy) in existing for dx,dy in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1))):
            raise TopologyError(f"unsupported alpha addition: {direction} {(x,y)}")
        self.frames[direction][y][x] = self.opaque_value(shade)
        self.defaults[direction][y][x] = self.default_value(shade)
        self.ownership.claim(
            direction, (x, y), component_owner=component_owner, system=system,
            topology_role="ALPHA_ADDITION", protection_level="LOCKED",
            semantic_region=semantic_region or system,
            allowed_later_mutations=("MATERIAL_FORM", "PALETTE_RESOLVE"),
            originating_stage="V4_2_SHAPE_TOPOLOGY",
        )
        self._record(op="ADD", direction=direction, cell=(x,y), owner=component_owner, variant_id=variant_id, before_alpha=0, after_alpha=255)

    def remove(self, direction, x, y, *, component_owner, variant_id, system="silhouette", semantic_region=None):
        if not (0 <= x < 16 and 0 <= y < 16):
            raise TopologyError(f"cell outside logical frame: {direction} {(x,y)}")
        if not self._allowed(direction, x, y):
            raise TopologyError(f"cell outside V4 safe envelope: {direction} {(x,y)}")
        if not self.frames[direction][y][x][3]:
            raise TopologyError(f"alpha removal targets transparent cell: {direction} {(x,y)}")
        old = self.frames[direction][y][x]; old_default = self.defaults[direction][y][x]
        self.frames[direction][y][x] = TRANSPARENT
        self.defaults[direction][y][x] = TRANSPARENT
        if len(self._groups(self._alpha_cells(direction))) != 1:
            self.frames[direction][y][x] = old; self.defaults[direction][y][x] = old_default
            raise TopologyError(f"alpha removal disconnects root garment mass: {direction} {(x,y)}")
        self.ownership.claim(
            direction, (x, y), component_owner=component_owner, system=system,
            topology_role="ALPHA_REMOVAL", protection_level="LOCKED",
            semantic_region=semantic_region or system,
            allowed_later_mutations=(), originating_stage="V4_2_SHAPE_TOPOLOGY",
        )
        self._record(op="REMOVE", direction=direction, cell=(x,y), owner=component_owner, variant_id=variant_id, before_alpha=255, after_alpha=0)

    def validate_final_connectivity(self):
        invalid = {}
        for direction in self.frames:
            groups = self._groups(self._alpha_cells(direction))
            if len(groups) != 1:
                invalid[direction] = sorted((len(group) for group in groups), reverse=True)
        if invalid:
            raise TopologyError(f"unsupported topology islands: {invalid}")
        return True
