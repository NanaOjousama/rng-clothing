"""SOURCE-BACKED V2 — the source pixels ARE the artwork; semantics describe them.

The legacy authored path (`authored.py`) decodes a base into (role, step) cells
and PAINTS every pixel from a palette. That is right for art drawn onto the
index, and wrong for approved source sprites: ingest rewrote their greys onto a
fixed six-step ramp, and a subtle 45-grey beret came out as a high-contrast one.

A source-backed base keeps six things apart:

    source_pixels       the preserved source sheet, byte-identical, md5-pinned
    semantic_map        (role, step) per pixel, derived from the source and
                        stored separately -- it steers recolouring and
                        composition and never replaces a pixel
    placement_metadata  the source's own Fashion Sense HeadPosition per view,
                        unless an override backed by in-game QC is recorded
    view_metadata       which frames the source authors, which it draws Flipped
    render_metadata     the source hat.json model blocks verbatim: grayscale /
                        tint, ColorMasks, prismatic -- how FS colours the pixels
    material_masks      authored logical-pixel masks, per shape

Invariant: render(base) with no palette, no material and no decals is the source
sheet pixel for pixel, and its pack keeps the source's rendering semantics. The
only documented transforms are LAYOUT: frames restacked to front/right/left/back,
and a view the source draws `Flipped` materialised as an explicit mirrored frame.

Nothing here is imported by `authored.py`; legacy bases and their output are
untouched. Decals, zones, fits and extent checks are the legacy ones, applied to
the semantic map, so a V2 base composes with the same library.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from dataclasses import dataclass, field

from . import authored
from .authored import ATLAS_ORDER, Base, _attachment_ok, _mirror, _placement
from .integration import integrate
from .pngio import blank_image, blit, read_rgba_png

AUTHORED = authored.ROOT
PROJECT = os.path.dirname(AUTHORED)
SB_DIR = os.path.join(AUTHORED, "source_backed")
MANIFEST = "source_backed.json"
SCHEMA = "source_backed/v2"

MODEL_OF = {"front": "FrontHat", "right": "RightHat", "left": "LeftHat", "back": "BackHat"}
OPPOSITE = {"left": "right", "right": "left"}
# Fields of a Fashion Sense model that decide how its pixels are COLOURED in game
# (AppearanceModel.cs; DrawManager.DrawAppearance). Carried verbatim.
RENDER_FIELDS = ("DisableGrayscale", "IsPrismatic", "PrismaticAnimationSpeedMultiplier",
                 "ColorMasks", "ColorMaskLayers", "SkinToneMasks", "DisableSkinGrayscale")
# Fields keyed on exact source RGB. Baking new colour into the pixels would
# silently disconnect them, so a bake over any of these is refused.
RGB_KEYED = ("ColorMasks", "ColorMaskLayers", "SkinToneMasks")
# The palette colour a bake tints with: Fashion Sense's grayscale path draws the
# texture multiplied by one colour, and this is the palette's stand-in for the
# colour a player would pick. The lightest body step, so source white lands on it.
TINT_ROLE, TINT_STEP = "body", 5


class Incompatible(ValueError):
    """A requested treatment/decoration cannot be applied to this base as authored."""


def read_fs_json(path):
    """Fashion Sense packs allow // comments; strip them outside strings."""
    out, in_str, esc, i = [], False, False, 0
    with open(path, encoding="utf-8-sig") as fh:
        text = fh.read()
    while i < len(text):
        ch = text[i]
        if in_str:
            out.append(ch)
            esc = (ch == "\\") and not esc
            if ch == '"' and not esc:
                in_str = False
        elif ch == '"':
            in_str, esc = True, False
            out.append(ch)
        elif text.startswith("//", i):
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        else:
            out.append(ch)
        i += 1
    return json.loads("".join(out))


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def fs_views(models: dict, frame_h: int):
    """(authored {view: y}, mirrored {view: from_view}) read off the model blocks.

    A view is authored when its block owns a frame no other block draws
    un-flipped; it is mirrored when its block is `Flipped` onto a frame another
    view authors. Derived from the source JSON, not typed into a spec table."""
    authored_y, flipped = {}, {}
    for view, block in MODEL_OF.items():
        m = models.get(block)
        if not m:
            continue
        y = int(m.get("StartingPosition", {}).get("Y", 0))
        (flipped if m.get("Flipped") else authored_y)[view] = y
    mirrored = {}
    for view, y in flipped.items():
        src = next((v for v, yy in authored_y.items() if yy == y), None)
        if src is None:
            raise Incompatible(f"{view} is Flipped onto frame y={y}, which no view authors")
        mirrored[view] = src
    return authored_y, mirrored


@dataclass(frozen=True)
class MaterialMask:
    """An authored material: exact logical cells per view, and one conservative
    value operation. The cells are the pattern -- nothing re-derives, thins,
    breaks or re-spaces them."""
    treatment: str
    authored_for: str
    views: dict                 # view -> frozenset((x, y))
    factor: float               # RGB multiplier on mask cells; < 1 darkens
    provenance: str = ""


@dataclass(frozen=True)
class SourceBackedBase:
    name: str
    semantic: Base              # (role, step) map + zones/anchors; legacy-compatible
    source: dict                # authored view -> rows of RGBA, straight from the sheet
    source_png: str
    source_md5: str
    models: dict                # source hat.json model blocks, verbatim
    mirrored: dict              # view -> the authored view it is Flipped from
    placement_override: dict = field(default_factory=dict)   # view -> {"X","Y"} + evidence
    materials: dict = field(default_factory=dict)            # treatment -> MaterialMask
    provenance: str = ""
    classification: str = "REFERENCE"

    @property
    def views(self):
        return self.semantic.views

    @property
    def size(self):
        return self.semantic.size

    @property
    def family(self):
        return self.semantic.family

    @property
    def shape_variant(self):
        return self.semantic.shape_variant

    def model(self, view):
        return self.models[MODEL_OF[view]]

    def placement(self, view):
        o = self.placement_override.get(view)
        if o:
            return {"X": int(o["X"]), "Y": int(o["Y"])}
        return copy.deepcopy(self.model(view).get("HeadPosition", {"X": 0, "Y": 0}))

    def render_fields(self, view):
        return {k: copy.deepcopy(v) for k, v in self.model(view).items() if k in RENDER_FIELDS}

    def rgb_keyed_fields(self):
        return sorted({k for v in MODEL_OF for k in RGB_KEYED
                       if MODEL_OF[v] in self.models and k in self.models[MODEL_OF[v]]})


# --- loading --------------------------------------------------------------------

def load_one(name, root=SB_DIR) -> SourceBackedBase:
    d = os.path.join(root, name)
    with open(os.path.join(d, MANIFEST)) as fh:
        man = json.load(fh)
    if man.get("schema") != SCHEMA:
        raise ValueError(f"{name}: schema {man.get('schema')!r}, expected {SCHEMA!r}")
    src = man["source"]
    png = os.path.join(PROJECT, src["png"])
    got = md5(png)
    if got != src["md5"]:
        raise ValueError(f"{name}: source sheet changed (md5 {got} != {src['md5']}); "
                         "source pixels are canonical and must not drift")
    models = {k: v for k, v in read_fs_json(os.path.join(PROJECT, src["json"])).items()
              if k in MODEL_OF.values()}
    fw, fh_ = src["frame_size"]
    authored_y, mirrored = fs_views(models, fh_)
    sheet = read_rgba_png(png)
    source = {v: [r[:fw] for r in sheet[y:y + fh_]] for v, y in authored_y.items()}
    index, _ = authored._index()
    views = tuple(v for v in ATLAS_ORDER if v in authored_y)
    cells = {v: authored._decode(os.path.join(d, "semantic", f"{v}.png"), index) for v in views}
    for v in views:
        alpha = {(x, y) for y, r in enumerate(source[v]) for x, p in enumerate(r) if p[3]}
        if alpha != set(cells[v]):
            raise ValueError(f"{name}/{v}: semantic map does not cover exactly the source alpha")
    sem = Base(man["name"], man["slot"], (fw, fh_), tuple(man["style"]), man["anchors"],
               man.get("zones", {}), cells, None, man["family"], man["shape_variant"],
               views, man.get("provenance", ""), man.get("classification", "REFERENCE"))
    materials = {}
    mdir = os.path.join(d, "materials")
    if os.path.isdir(mdir):
        for f in sorted(os.listdir(mdir)):
            if f.endswith(".json"):
                m = load_material(os.path.join(mdir, f))
                if m.authored_for != name:
                    raise ValueError(f"{name}: material {f} was authored for {m.authored_for}")
                materials[m.treatment] = m
    return SourceBackedBase(man["name"], sem, source, src["png"], src["md5"], models, mirrored,
                            man.get("placement_override", {}), materials,
                            man.get("provenance", ""), man.get("classification", "REFERENCE"))


def load_material(path) -> MaterialMask:
    with open(path) as fh:
        m = json.load(fh)
    return MaterialMask(m["treatment"], m["authored_for"],
                        {v: frozenset(tuple(c) for c in cs) for v, cs in m["views"].items()},
                        float(m["factor"]), m.get("provenance", ""))


def load(root=SB_DIR) -> dict:
    if not os.path.isdir(root):
        return {}
    return {n: load_one(n, root) for n in sorted(os.listdir(root))
            if os.path.exists(os.path.join(root, n, MANIFEST))}


# --- rendering -----------------------------------------------------------------

def _scale(px, f):
    return (min(255, round(px[0] * f)), min(255, round(px[1] * f)), min(255, round(px[2] * f)), px[3])


def _tint(px, c):
    """Fashion Sense's grayscale draw: SpriteBatch colour = texture x tint."""
    return (round(px[0] * c[0] / 255), round(px[1] * c[1] / 255), round(px[2] * c[2] / 255), px[3])


def _lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


@dataclass
class SourceBackedRender:
    base: SourceBackedBase
    palette: object
    material: str
    decals: tuple
    dropped: tuple
    directions: dict
    baked: bool
    # view -> {"material": set, "decal": set, "occlusion": set}: every cell an
    # operation was AUTHORISED to change. Tests hold the pixels to exactly this.
    changes: dict


def render(sb: SourceBackedBase, palette=None, material: str | None = None, decals=(),
           lib=None, experimental_procedural: bool = False) -> SourceBackedRender:
    """Compose on the source pixels.

    palette   bake: every opaque source pixel x the palette's tint colour -- what
              Fashion Sense's own grayscale path draws, so source shading is kept
              as ratios instead of being re-laddered. Omit it and nothing is baked:
              the pack keeps the source's in-game tinting.
    material  an AUTHORED mask for this base wins. A procedural treatment is used
              only with experimental_procedural=True and never over an authored one.
    decals    legacy decals and the legacy placement/integration rules, run on the
              semantic map; only the cells they seat or shade are repainted.
    """
    decals = tuple(decals)
    if decals and palette is None:
        raise Incompatible("decals carry palette roles; composing them needs a palette (a bake)")
    baked = palette is not None
    if baked and sb.rgb_keyed_fields():
        raise Incompatible(f"{sb.name}: source uses {sb.rgb_keyed_fields()}, which are keyed on "
                           "exact source RGB; baking colour would disconnect them")
    mask = None
    if material:
        mask = sb.materials.get(material)
        if mask is None:
            if not experimental_procedural or lib is None:
                raise Incompatible(f"{sb.name} has no authored {material!r} mask "
                                   "(procedural treatments need experimental_procedural=True)")
            mask = _procedural_mask(sb, lib.treatment(material), palette)
    tint = palette.color(TINT_ROLE, TINT_STEP) if baked else None
    out, changes, dropped = {}, {}, []
    for v in sb.views:
        rows = [[p for p in r] for r in sb.source[v]]
        cells = dict(sb.semantic.view(v))
        ch = {"material": set(), "decal": set(), "occlusion": set()}
        if baked:
            rows = [[_tint(p, tint) if p[3] else p for p in r] for r in rows]
        if mask is not None:
            want = mask.views.get(v, frozenset())
            off = sorted(c for c in want if c not in cells)
            if off:
                raise Incompatible(f"{material} mask for {sb.name}/{v}: {len(off)} cells off the "
                                   f"silhouette, e.g. {off[:3]} -- author a mask for this shape")
            factors = mask.factor if isinstance(mask.factor, dict) else None
            for (x, y) in want:
                f = factors[v][(x, y)] if factors else mask.factor
                rows[y][x] = _scale(rows[y][x], f)
                ch["material"].add((x, y))
        surface = dict(cells)
        silhouette = set(cells)
        for d in sorted(decals, key=lambda d: (d.z, d.name)):
            if v not in d.views:
                continue
            origin = _placement(sb.semantic, d, v)
            if origin is None:
                dropped.append((d.name, v, "no zone or anchor in this view"))
                continue
            ax, ay = origin
            placed = {(ax + dx, ay + dy): val for (dx, dy), val in d.view_cells(v).items()}
            if d.kind == "attachment":
                why = _attachment_ok(placed, silhouette, d, sb.size)
                if why:
                    dropped.append((d.name, v, why))
                    continue
            else:
                off = [c for c in placed if c not in silhouette]
                if off:
                    dropped.append((d.name, v, f"{len(off)} cells off the base"))
                    continue
            seated, occl, note = integrate(placed, surface, d.kind, d.edge)
            if seated is None:
                dropped.append((d.name, v, note))
                continue
            w, h = sb.size
            for c, depth in (occl or {}).items():
                role, step = cells.get(c, surface.get(c, ("body", 3)))
                ramp = palette.ramps.get(role) or palette.ramps["body"]
                a, b = ramp[max(0, min(5, step))], ramp[max(0, min(5, step + depth))]
                x, y = c
                rows[y][x] = _scale(rows[y][x], _lum(b) / max(1.0, _lum(a)))
                cells[c] = (role, min(5, step + depth))
                ch["occlusion"].add(c)
            for (x, y), (role, step) in seated.items():
                if 0 <= x < w and 0 <= y < h:
                    rows[y][x] = palette.color(role, step)
                    ch["decal"].add((x, y))
            cells.update(seated)
        out[v], changes[v] = rows, ch
    for v, src in sb.mirrored.items():
        out[v] = _mirror(out[src])
        changes[v] = {k: {(sb.size[0] - 1 - x, y) for x, y in s} for k, s in changes[src].items()}
    return SourceBackedRender(sb, palette, material or "", decals, tuple(dropped), out, baked, changes)


def _procedural_mask(sb, treatment, palette):
    """EXPERIMENTAL: a procedural treatment expressed as a per-cell value ratio
    instead of an absolute ramp step, so it shifts local value rather than
    replacing a midtone with the highlight colour."""
    with open(os.path.join(AUTHORED, "index.json")) as fh:
        body = json.load(fh)["roles"]["body"]
    index = [tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) for h in body]
    ramp = (palette.ramps["body"] if palette is not None else index)
    views, factors = {}, {}
    for v in sb.views:
        cells = sb.semantic.view(v)
        moved = {c: new for c, new in treatment.apply(dict(cells)).items() if new != cells[c]}
        views[v] = frozenset(moved)
        factors[v] = {c: _lum(ramp[moved[c][1]]) / max(1.0, _lum(ramp[cells[c][1]])) for c in moved}
    return MaterialMask(treatment.name, sb.name, views, factors, "experimental procedural")


# --- Fashion Sense output -----------------------------------------------------

def sheet(r: SourceBackedRender):
    w, h = r.base.size
    img = blank_image(w, h * len(ATLAS_ORDER))
    for i, v in enumerate(ATLAS_ORDER):
        blit(img, r.directions[v], 0, i * h)
    return img


def hat_json(r: SourceBackedRender, name: str, tags=()) -> dict:
    """The source's own model blocks, with only the documented layout rewritten.

    Kept verbatim: HeadPosition (unless a QC-backed override is recorded),
    HatSize, animation, HideHair, and every field that decides colouring. Rewritten:
    StartingPosition (restacked) and Flipped (the mirror is now an explicit frame).
    A bake adds DisableGrayscale: true, because the colour is now in the pixels."""
    sb = r.base
    out = {"Name": name}
    if tags:
        out["Tags"] = list(tags)
    for i, v in enumerate(ATLAS_ORDER):
        src_view = v if v in sb.views else sb.mirrored[v]
        block = copy.deepcopy(sb.models.get(MODEL_OF[v]) or sb.models[MODEL_OF[src_view]])
        block["StartingPosition"] = {"X": 0, "Y": i * sb.size[1]}
        block.pop("Flipped", None)
        block["HeadPosition"] = sb.placement(v)
        if r.baked:
            block["DisableGrayscale"] = True
        out[MODEL_OF[v]] = block
    return out
