"""Loaders and load-time validation for blanks, pieces, templates, palettes and plans."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .roleimage import ROLE_CHARS, SIZE, SLOTS, VIEWS

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
BLANK_CHARS = set(ROLE_CHARS) | {"."}
PIECE_CHARS = set(ROLE_CHARS) | {".", "=", "+", "-"}
LAYER_NAMES = {"UNDER": 0, "BODY_EDIT": 1, "OVER": 2, "DETAIL": 3}
RGBA = tuple[int, int, int, int]


def _json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _hex(value: str) -> RGBA:
    v = value.lstrip("#")
    return int(v[:2], 16), int(v[2:4], 16), int(v[4:6], 16), 255


@dataclass(frozen=True)
class Blank:
    id: str
    rows: dict[str, int]
    views: dict[str, list[str]]  # front/side/back (+ optional left), 16 rows of 16 chars

    def row(self, name: str) -> int:
        return self.rows[name]


@dataclass(frozen=True)
class PieceView:
    origin_x: int
    origin_y: int | str  # int or "hem_row-1" style expression
    rows: tuple[str, ...]

    @property
    def width(self) -> int:
        return len(self.rows[0])

    @property
    def height(self) -> int:
        return len(self.rows)


@dataclass(frozen=True)
class Piece:
    id: str
    kind: str
    layer: int
    slot: str | None
    identity: bool
    wrap: bool
    views: dict[str, PieceView]
    note: str = ""


@dataclass(frozen=True)
class Template:
    id: str
    blank: str
    identity: tuple[str, ...]
    allowed: tuple[str, ...]
    sleeve_slot: str
    hide_sleeves: bool
    max_colors: int | None
    components: dict[str, int]


@dataclass(frozen=True)
class Palette:
    id: str
    slots: dict[str, dict[str, RGBA]]  # slot -> role -> rgba


@dataclass(frozen=True)
class PlanPiece:
    id: str
    slot: str | None = None  # override


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    template: str | None
    blank: str
    pieces: tuple[PlanPiece, ...]
    palette: str
    sleeve_slot: str
    hide_sleeves: bool
    identity: tuple[str, ...]
    max_colors: int | None
    tags: tuple[str, ...]
    description: str


def resolve_row_expr(expr: int | str, blank: Blank) -> int:
    if isinstance(expr, int):
        return expr
    m = re.fullmatch(r"([a-z_]+)\s*([+-]\s*\d+)?", expr.strip())
    if not m:
        raise ValueError(f"bad row expression {expr!r}")
    base = blank.row(m.group(1))
    return base + (int(m.group(2).replace(" ", "")) if m.group(2) else 0)


def _check_rows(rows, width, chars, what):
    if not rows or any(len(r) != width for r in rows):
        raise ValueError(f"{what}: rows must all be {width} wide")
    bad = {c for r in rows for c in r} - chars
    if bad:
        raise ValueError(f"{what}: illegal chars {sorted(bad)}")


def load_blank(path: Path) -> Blank:
    d = _json(path)
    views = {}
    for name, rows in d["views"].items():
        if name not in VIEWS + ("left",):
            raise ValueError(f"{d['id']}: unknown view {name}")
        if len(rows) != SIZE:
            raise ValueError(f"{d['id']}/{name}: need {SIZE} rows")
        _check_rows(rows, SIZE, BLANK_CHARS, f"{d['id']}/{name}")
        views[name] = list(rows)
    for v in VIEWS:
        if v not in views:
            raise ValueError(f"{d['id']}: missing view {v}")
    return Blank(d["id"], dict(d.get("rows", {})), views)


def load_piece(path: Path) -> Piece:
    d = _json(path)
    layer = d["layer"]
    layer = LAYER_NAMES[layer] if isinstance(layer, str) else int(layer)
    if layer not in (0, 1, 2, 3):
        raise ValueError(f"{d['id']}: layer must be 0..3")
    slot = d.get("slot")
    if slot is not None and slot not in SLOTS:
        raise ValueError(f"{d['id']}: unknown slot {slot}")
    views = {}
    for name, v in d["views"].items():
        if name not in VIEWS + ("left",):
            raise ValueError(f"{d['id']}: unknown view {name}")
        rows = tuple(v["rows"])
        _check_rows(rows, len(rows[0]), PIECE_CHARS, f"{d['id']}/{name}")
        if slot is None and any("=" in r for r in rows):
            raise ValueError(f"{d['id']}/{name}: '=' requires a piece slot")
        ox, oy = v["origin"]
        views[name] = PieceView(int(ox), oy if isinstance(oy, str) else int(oy), rows)
    if not views:
        raise ValueError(f"{d['id']}: no views")
    return Piece(d["id"], d["kind"], layer, slot, bool(d.get("identity", False)), bool(d.get("wrap", False)), views, d.get("note", ""))


def load_template(path: Path) -> Template:
    d = _json(path)
    return Template(d["id"], d["blank"], tuple(d.get("identity", [])), tuple(d["allowed"]), d.get("sleeve_slot", "primary"),
                    bool(d.get("hide_sleeves", False)), d.get("max_colors"), dict(d.get("components", {})))


def load_palette(path: Path) -> Palette:
    d = _json(path)
    slots = {}
    for slot, roles in d["slots"].items():
        if slot not in SLOTS:
            raise ValueError(f"{d['id']}: unknown slot {slot}")
        if set(roles) != {"deep", "shadow", "base", "light"}:
            raise ValueError(f"{d['id']}/{slot}: need exactly deep/shadow/base/light")
        slots[slot] = {k: _hex(v) for k, v in roles.items()}
    return Palette(d["id"], slots)


def load_plan(path: Path) -> Plan:
    d = _json(path)
    pieces = tuple(PlanPiece(p["id"], p.get("slot")) if isinstance(p, dict) else PlanPiece(p) for p in d["pieces"])
    for p in pieces:
        if p.slot is not None and p.slot not in SLOTS:
            raise ValueError(f"{d['id']}: unknown slot override {p.slot}")
    return Plan(d["id"], d["name"], d.get("template"), d["blank"], pieces, d["palette"], d.get("sleeve_slot", "primary"),
                bool(d.get("hide_sleeves", False)), tuple(d.get("identity", [])), d.get("max_colors"),
                tuple(d.get("tags", [])), d.get("description", ""))


@dataclass
class Library:
    blanks: dict[str, Blank] = field(default_factory=dict)
    pieces: dict[str, Piece] = field(default_factory=dict)
    templates: dict[str, Template] = field(default_factory=dict)
    palettes: dict[str, Palette] = field(default_factory=dict)
    plans: dict[str, Plan] = field(default_factory=dict)
    contract: dict = field(default_factory=dict)

    @classmethod
    def load(cls, root: Path = DATA) -> "Library":
        lib = cls()
        for p in sorted((root / "blanks").glob("*.json")): b = load_blank(p); lib.blanks[b.id] = b
        for p in sorted((root / "pieces").glob("*.json")): x = load_piece(p); lib.pieces[x.id] = x
        for p in sorted((root / "templates").glob("*.json")): t = load_template(p); lib.templates[t.id] = t
        for p in sorted((root / "palettes").glob("*.json")): pal = load_palette(p); lib.palettes[pal.id] = pal
        for p in sorted((root / "plans").rglob("*.json")): pl = load_plan(p); lib.plans[pl.id] = pl
        lib.contract = _json(root / "runtime" / "fs_shirt_contract.json")
        lib.check_references()
        return lib

    def check_references(self) -> None:
        for t in self.templates.values():
            if t.blank not in self.blanks: raise ValueError(f"template {t.id}: unknown blank {t.blank}")
            for pid in t.identity + t.allowed:
                if pid not in self.pieces: raise ValueError(f"template {t.id}: unknown piece {pid}")
        for pl in self.plans.values():
            if pl.blank not in self.blanks: raise ValueError(f"plan {pl.id}: unknown blank {pl.blank}")
            if pl.palette not in self.palettes: raise ValueError(f"plan {pl.id}: unknown palette {pl.palette}")
            if pl.template is not None and pl.template not in self.templates: raise ValueError(f"plan {pl.id}: unknown template {pl.template}")
            for p in pl.pieces:
                if p.id not in self.pieces: raise ValueError(f"plan {pl.id}: unknown piece {p.id}")
            for pid in pl.identity:
                if pid not in self.pieces: raise ValueError(f"plan {pl.id}: unknown identity piece {pid}")

    def plan_identity(self, plan: Plan) -> tuple[str, ...]:
        ids = list(self.templates[plan.template].identity) if plan.template else []
        ids += [i for i in plan.identity if i not in ids]
        return tuple(ids)

    def plan_max_colors(self, plan: Plan) -> int:
        if plan.max_colors: return plan.max_colors
        if plan.template and self.templates[plan.template].max_colors: return self.templates[plan.template].max_colors
        return int(self.contract.get("max_colors_default", 8))
