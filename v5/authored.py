"""PRE-AUTHORED PATH — bases + decals + curated palettes + style tags.

A second way to make a garment, alongside the procedural V5 one.  Nothing is
carved here: a base sprite is DRAWN (see `tools/author_base_assets.py`), decals
are DRAWN, palettes are hand-picked, and the combinator only chooses which
authored things go together and which curated harmony recolours them.

    base      the garment's silhouette and its whole interior, indexed as
              (role, ramp step) — one drawing, three views
    decal     a small drawn piece with an anchor: collar, buttons, band, patch
    palette   a curated harmony, three 6-step ramps, carrying style tags
    style     the tag every component must share for a combination to be legal

Views: FRONT, BACK and LEFT are authored; RIGHT is the mirror of LEFT.  Fashion
Sense wants four frames and a hand-drawn right view is one more thing that can
disagree with its own left.

Ownership, the same rule the procedural templates keep:

    base     owns the silhouette.  A decal cell that falls outside the base is
             DROPPED — a decal can never change what the garment is.
    decal    owns its own pixels, inside that silhouette.
    palette  owns colour.  No component names a hue; they carry roles.
    style    owns what may meet what.  One tag is chosen per garment and every
             component must carry it.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from .integration import integrate
from .pngio import read_rgba_png, write_rgba_png, blank_image, blit, nearest_scale
from .rng import StreamBank

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "authored")

VIEWS = ("front", "back", "left")
ATLAS_ORDER = ("front", "right", "left", "back")     # Fashion Sense stacking
TRANSPARENT = (0, 0, 0, 0)


# --- the index: every authored pixel decodes to (role, step) -----------------

def _read_json(path):
    with open(path) as fh:
        return json.load(fh)


def _index(root=ROOT):
    idx = _read_json(os.path.join(root, "index.json"))
    out = {}
    for role, ramp in idx["roles"].items():
        for step, hx in enumerate(ramp):
            c = hx.lstrip("#")
            out[tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))] = (role, step)
    return out, idx["steps"]


@dataclass(frozen=True)
class Base:
    name: str
    slot: str
    size: tuple
    style: tuple
    anchors: dict
    # Named legal decoration regions per view: zone -> view -> (x0,y0,x1,y1).
    # An anchor says "start drawing here"; a zone says "this whole area is the
    # band, and a piece must fit inside it".  Placement stays authored either
    # way — a decal is centred in its zone, never scattered.
    zones: dict
    cells: dict            # view -> {(x, y): (role, step)}
    # The tone profile this base was drawn against, by name.  A base with none
    # keeps the palette's own even ladder, which is what the two control bases
    # do — so adding tone to one base cannot restyle another.
    tone_profile: str | None = None

    def view(self, v):
        return self.cells[v]


@dataclass(frozen=True)
class Decal:
    name: str
    slot: str
    attach: str
    z: int
    style: tuple
    views: tuple
    size: tuple
    cells: dict            # (x, y) -> (role, step), or view -> that, per_view
    # The legal zone this motif belongs in.  A decal with a zone is centred
    # inside it; one with only an `attach` anchor keeps the older behaviour.
    zone: str | None = None
    # "surface" stays inside the base's silhouette; "attachment" may extend
    # beyond it by at most `max_extent` cells.  Attachments exist for
    # decorations whose identity IS the protrusion — a feather, a pom — which
    # read as blotches when confined to the crown.  Everything else stays a
    # surface motif: the base still owns the core silhouette.
    kind: str = "surface"
    # What KIND OF THING this is — band, patch, star, pom, feather.  Policy is
    # written against classes, not names, so a base can ban "every band" without
    # listing them and a new band inherits the ban automatically.
    motif_class: str = "unclassified"
    # An edge treatment — a brim trim, a hem stitch — belongs ON the hat's
    # outline rather than inset from it.  Declared, so the integration pass
    # knows which of the two correct behaviours this piece wants.
    edge: bool = False
    # A motif under review: loadable, renderable, but never chosen by the
    # combinator until it has passed the integration pass.
    pending: bool = False
    max_extent: int = 0
    per_view: bool = False
    # For an attachment: the cell of its own art that must sit ON the base, and
    # which corner of the zone that cell aligns to.  Centring an attachment in
    # its zone buried it inside the crown — the whole point is that the rest of
    # it hangs outside.
    anchor_cell: tuple = (0, 0)
    anchor_point: str = "top_centre"
    # Bases this piece was DRAWN for.  Empty means any base with the anchor.
    # A 16-wide brim trim and a 14-wide one both attach at `brim_edge`, and
    # without this the wide one wanders onto the felt hat and spills off it.
    fits: tuple = ()

    def fits_base(self, base) -> bool:
        return not self.fits or base.name in self.fits

    def view_cells(self, view: str) -> dict:
        return self.cells.get(view, {}) if self.per_view else self.cells

    def view_size(self, view: str) -> tuple:
        cells = self.view_cells(view)
        if not cells:
            return (0, 0)
        return (max(x for x, _ in cells) + 1, max(y for _, y in cells) + 1)


def _lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _at_luminance(c, target):
    """Move a colour to a target luminance, keeping its hue and saturation.

    Scaling toward black or toward white — what a pixel artist does to extend a
    ramp.  The colour keeps its identity; only its value moves.
    """
    have = _lum(c)
    if target <= have:
        t = 0.0 if have <= 0 else target / have
        return tuple(max(0, min(255, round(v * t))) for v in c[:3])
    t = (target - have) / max(1.0, 255 - have)
    return tuple(max(0, min(255, round(v + (255 - v) * t))) for v in c[:3])


@dataclass(frozen=True)
class ToneProfile:
    """Value rhythm, held separately from colour identity.

    A palette says what colour a garment is; a tone profile says how its values
    are spaced — where each step sits, how far the highlight jumps, how tightly
    the shadows compress.  Our curated ramps are laddered evenly, and evenly is
    not how the references are built: applying an even ladder to vanilla 033's
    construction turned a dark green knit into a pale cream one.  The
    construction was faithful, the tonal rhythm was not.
    """
    name: str
    source: str
    levels: tuple                    # absolute luminance per step, deep -> light
    max_highlight_share: float = 1.0

    # The profile was derived from the reference's BODY colours, and it governs
    # the body only.  Re-toning trim, accent and hardware to the same levels
    # flattened them onto the cloth: a band at trim step 1 and a crown at body
    # step 1 came out the same value, so decoration differed by hue alone and
    # vanished on a desaturated palette.  Decoration is a different material and
    # keeps the palette's own contrast.
    TONED_ROLES = ("body",)

    def apply(self, palette: "Palette") -> "Palette":
        ramps = {}
        for role, ramp in palette.ramps.items():
            if role in self.TONED_ROLES:
                ramps[role] = [_at_luminance(c, self.levels[min(i, len(self.levels) - 1)])
                               for i, c in enumerate(ramp)]
            else:
                ramps[role] = list(ramp)
        return Palette(palette.id, palette.identity, palette.style, ramps)


@dataclass(frozen=True)
class Palette:
    id: str
    identity: str
    style: tuple
    ramps: dict            # role -> [rgb] * steps

    def color(self, role, step):
        ramp = self.ramps.get(role) or self.ramps["body"]
        return (*ramp[max(0, min(len(ramp) - 1, step))], 255)


@dataclass(frozen=True)
class Library:
    bases: tuple
    decals: tuple
    palettes: tuple
    tones: dict = None

    def tone_for(self, base: Base):
        return (self.tones or {}).get(base.tone_profile)

    def styles(self):
        return sorted({s for b in self.bases for s in b.style})


def _decode(path, index):
    im = read_rgba_png(path)
    out = {}
    for y, row in enumerate(im):
        for x, px in enumerate(row):
            if px[3] == 0:
                continue
            key = tuple(px[:3])
            if key not in index:
                raise ValueError(f"{path}: colour {key} at {(x, y)} is not in the "
                                 f"authoring index; the art must stay indexed")
            out[(x, y)] = index[key]
    return out


def load(root=ROOT) -> Library:
    index, _ = _index(root)
    bases = []
    bdir = os.path.join(root, "bases")
    for name in sorted(os.listdir(bdir)):
        man = _read_json(os.path.join(bdir, name, "base.json"))
        cells = {v: _decode(os.path.join(bdir, name, f"{v}.png"), index)
                 for v in VIEWS}
        bases.append(Base(man["name"], man["slot"], tuple(man["size"]),
                          tuple(man["style"]), man["anchors"],
                          man.get("zones", {}), cells, man.get("tone_profile")))
    decals = []
    ddir = os.path.join(root, "decals")
    for f in sorted(x for x in os.listdir(ddir) if x.endswith(".json")):
        man = _read_json(os.path.join(ddir, f))
        if man.get("per_view"):
            cells = {v: _decode(os.path.join(ddir, f"{man['name']}_{v}.png"), index)
                     for v in man["views"]}
        else:
            cells = _decode(os.path.join(ddir, f[:-5] + ".png"), index)
        decals.append(Decal(man["name"], man["slot"], man.get("attach", ""),
                            man["z"], tuple(man["style"]), tuple(man["views"]),
                            tuple(man["size"]), cells, man.get("zone"),
                            man.get("kind", "surface"),
                            man.get("motif_class", "unclassified"),
                            bool(man.get("edge", False)),
                            bool(man.get("pending", False)),
                            int(man.get("max_extent", 0)),
                            bool(man.get("per_view", False)),
                            tuple(man.get("anchor_cell", (0, 0))),
                            man.get("anchor_point", "top_centre"),
                            tuple(man.get("fits", ()))))
    pals = _read_json(os.path.join(root, "palettes.json"))["palettes"]
    palettes = []
    for p in pals:
        ramps = {role: [tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
                        for h in ramp] for role, ramp in p["ramps"].items()}
        palettes.append(Palette(p["id"], p["identity"], tuple(p["style"]), ramps))
    tones = {}
    tpath = os.path.join(root, "tones.json")
    if os.path.exists(tpath):
        for name, t in _read_json(tpath)["profiles"].items():
            tones[name] = ToneProfile(name, t["source"], tuple(t["levels"]),
                                      t.get("max_highlight_share", 1.0))
    return Library(tuple(bases), tuple(decals), tuple(palettes), tones)


# --- the combinator ----------------------------------------------------------

@dataclass
class Garment:
    seed: int
    base: Base
    style: str
    palette: Palette
    decals: tuple
    dropped: tuple                # decal cells that fell off the base
    directions: dict              # direction -> rows of RGBA


MAX_DECALS = 3          # busyness ceiling; regions are exclusive besides

# Semantic occupancy.  Two motifs in one REGION compete for the same reading,
# which is how a buckle and a pin became speckle in the in-game pass: the eye
# resolves a region, not a zone.  Several zones share a region on purpose —
# crown_top, crown_face and side are all the upper crown.
ZONE_REGION = {
    "crown_top": "upper_crown",
    "crown_face": "upper_crown",
    "side": "upper_crown",
    "band": "band",
    "cuff": "band",
    "brim": "brim",
    "neck": "neck",
    "placket": "front_body",
    "chest_left": "front_body",
    "hem": "hem",
}


def region_of(d: "Decal") -> str:
    return ZONE_REGION.get(d.zone or d.attach, d.zone or d.attach or "unzoned")


def compose(seed: int, slot: str, lib: Library | None = None,
            style: str | None = None) -> Garment:
    """One roll: a base, a style, a curated palette, and legal decals."""
    lib = lib or load()
    rng = StreamBank(seed)

    bases = [b for b in lib.bases if b.slot == slot]
    # A requested style narrows the BASES too.  With one base per slot this did
    # not matter; with four it did — asking for a formal hat picked the knit cap
    # and then failed, because the base was chosen before the style was honoured.
    if style is not None:
        bases = [b for b in bases if style in b.style]
    if not bases:
        raise ValueError(f"no authored base for slot {slot}"
                         + (f" in style {style}" if style else ""))
    base = rng("base").choice(sorted(bases, key=lambda b: b.name))

    # The style tag is chosen FIRST and then constrains everything else.  This
    # is the whole point of the tags: coherence is a precondition, not a filter
    # applied afterwards to whatever was rolled.
    choices = [s for s in base.style if style is None or s == style]
    if not choices:
        raise ValueError(f"{base.name} cannot be {style}")
    story = rng("style").choice(sorted(choices))

    pals = [p for p in lib.palettes if story in p.style] or list(lib.palettes)
    palette = rng("palette").choice(sorted(pals, key=lambda p: p.id))

    legal = [d for d in lib.decals
             if d.slot == slot and not d.pending
             and story in d.style and d.fits_base(base)
             and any(_placement(base, d, v) for v in d.views)]
    chosen, used = [], set()
    for d in sorted(legal, key=lambda d: d.name):
        slot_key = region_of(d)
        if len(chosen) >= MAX_DECALS or slot_key in used:
            continue
        if rng(f"decal:{d.name}").chance(0.62):
            chosen.append(d)
            used.add(slot_key)

    directions, dropped = _render(base, chosen, palette, lib.tone_for(base))
    return Garment(seed, base, story, palette, tuple(chosen), dropped, directions)


def _paint(cells, palette, w, h):
    rows = [[TRANSPARENT for _ in range(w)] for _ in range(h)]
    for (x, y), (role, step) in cells.items():
        if 0 <= x < w and 0 <= y < h:
            rows[y][x] = palette.color(role, step)
    return rows


def _mirror(rows):
    return [list(reversed(r)) for r in rows]


def _placement(base: Base, d: Decal, view: str):
    """Where a decal's top-left goes: centred in its zone, or on its anchor.

    An ATTACHMENT is anchored by its zone but sized freely: it is allowed to
    hang off the base, so its own footprint is not required to fit the zone.
    It is aligned so its LAST row sits on the zone, which is what keeps a pom
    on top of a crown rather than floating above it.
    """
    if d.zone:
        box = (base.zones.get(view) or {}).get(d.zone)
        if not box:
            return None
        x0, y0, x1, y1 = box
        w, h = d.view_size(view)
        if d.kind == "attachment" and w <= (x1 - x0 + 1) and h <= (y1 - y0 + 1):
            # An attachment small enough to sit INSIDE its zone is not really
            # projecting off anything — a pin or badge on a panel — so it is
            # seated like any other motif: centred in the panel, biased up by
            # the integer division, which is the "middle or upper-middle" a
            # cap emblem wants.  Corner alignment is for the pieces that only
            # make sense hanging off an edge, and those are exactly the ones
            # too big for their zone.
            return (x0 + (x1 - x0 + 1 - w) // 2, y0 + (y1 - y0 + 1 - h) // 2)
        if d.kind == "attachment":
            # align the art's own anchor cell to a corner of the zone
            ax, ay = d.anchor_cell
            if d.anchor_point == "top_right":
                tx, ty = x1, y0
            elif d.anchor_point == "top_left":
                tx, ty = x0, y0
            else:                                   # top_centre
                tx, ty = (x0 + x1) // 2, y0
            return (tx - ax, ty - ay)
        if w > (x1 - x0 + 1) or h > (y1 - y0 + 1):
            return None                       # the piece is bigger than its zone
        return (x0 + (x1 - x0 + 1 - w) // 2, y0 + (y1 - y0 + 1 - h) // 2)
    anchor = base.anchors.get(d.attach, {}).get(view)
    return tuple(anchor) if anchor else None


def _attachment_ok(placed: dict, silhouette: set, d: Decal, size: tuple) -> str | None:
    """Why this attachment is illegal, or None if it is fine.

    Bounded, connected, on-frame — the three things that separate a declared
    attachment from procedural silhouette invention.
    """
    w, h = size
    if any(not (0 <= x < w and 0 <= y < h) for (x, y) in placed):
        return "leaves the frame"
    outside = [c for c in placed if c not in silhouette]
    if len(outside) > d.max_extent:
        return f"{len(outside)} cells outside, past its bound of {d.max_extent}"
    # Every cell must reach the base through its OWN cells: no floating pixels.
    # The chain may run diagonally — a quill is a diagonal line and reads as
    # connected — but it must TOUCH the base orthogonally, so an attachment
    # cannot hang off a corner.
    neigh8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    reachable, frontier = set(), [c for c in placed
                                  if any((c[0] + dx, c[1] + dy) in silhouette
                                         for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                                  or c in silhouette]
    if not frontier:
        return "does not touch the base"
    while frontier:
        c = frontier.pop()
        if c in reachable:
            continue
        reachable.add(c)
        x, y = c
        frontier += [(x + dx, y + dy) for dx, dy in neigh8
                     if (x + dx, y + dy) in placed
                     and (x + dx, y + dy) not in reachable]
    if len(reachable) != len(placed):
        return f"{len(placed) - len(reachable)} floating cells"
    return None


def _render(base: Base, decals, palette: Palette, tone: "ToneProfile | None" = None):
    # Colour identity comes from the palette; value rhythm from the tone
    # profile, if the base declares one.  Two axes, composed here and nowhere
    # else, so a palette file never has to know about a base.
    if tone is not None:
        palette = tone.apply(palette)
    w, h = base.size
    out, dropped = {}, []
    for view in VIEWS:
        cells = dict(base.view(view))
        silhouette = set(cells)
        for d in sorted(decals, key=lambda d: (d.z, d.name)):
            if view not in d.views:
                continue
            origin = _placement(base, d, view)
            if origin is None:
                dropped.append((d.name, view, "no zone or anchor in this view"))
                continue
            ax, ay = origin
            placed = {(ax + dx, ay + dy): v
                      for (dx, dy), v in d.view_cells(view).items()}
            if d.kind == "attachment":
                why = _attachment_ok(placed, silhouette, d, base.size)
                if why:
                    dropped.append((d.name, view, why))
                    continue
            else:
                off = [c for c in placed if c not in silhouette]
                if off:
                    # A motif is drawn or it is not: half of a buckle is worse
                    # than no buckle.  The base owns the silhouette, so a piece
                    # that will not fit is skipped whole and reported.
                    dropped.append((d.name, view, f"{len(off)} cells off the base"))
                    continue
            # NATURAL INTEGRATION: re-seat the motif into the surface it covers
            # rather than stamping it on.  Every decision comes from the base's
            # own pixels — see v5/integration.py.
            seated, occl, note = integrate(placed, base.view(view), d.kind, d.edge)
            if seated is None:
                dropped.append((d.name, view, note))
                continue
            for c, depth in (occl or {}).items():
                role, step = cells.get(c, base.view(view).get(c, ("body", 3)))
                cells[c] = (role, min(5, step + depth))
            cells.update(seated)
        out[view] = _paint(cells, palette, w, h)
    out["right"] = _mirror(out["left"])
    return out, tuple(dropped)


def build(base_name: str, palette_id: str, decal_names=(), lib: Library | None = None,
          style: str | None = None) -> Garment:
    """Compose a NAMED combination — no rolling.

    `compose` is the combinator; this is the same assembly driven by an explicit
    choice, for a test pack where the point is to inspect a known matrix of base
    x palette rather than a sample of the distribution.  It still refuses an
    illegal combination: a decal must fit the base and share a style with it, so
    a hand-built pack cannot quietly contain something the combinator would
    never produce.
    """
    lib = lib or load()
    base = next((b for b in lib.bases if b.name == base_name), None)
    if base is None:
        raise ValueError(f"no authored base {base_name!r}")
    palette = next((p for p in lib.palettes if p.id == palette_id), None)
    if palette is None:
        raise ValueError(f"no curated palette {palette_id!r}")
    shared = sorted(set(base.style) & set(palette.style))
    if not shared:
        raise ValueError(f"{base_name} and {palette_id} share no style tag")
    story = style if style in shared else shared[0]

    decals = []
    for name in decal_names:
        d = next((x for x in lib.decals if x.name == name), None)
        if d is None:
            raise ValueError(f"no decal {name!r}")
        if not d.fits_base(base):
            raise ValueError(f"{name} was not drawn for {base_name}")
        if not any(_placement(base, d, v) for v in d.views):
            raise ValueError(f"{name} has no legal placement on {base_name}")
        if story not in d.style:
            raise ValueError(f"{name} is not {story}")
        decals.append(d)

    directions, dropped = _render(base, decals, palette, lib.tone_for(base))
    return Garment(-1, base, story, palette, tuple(decals), dropped, directions)


def atlas(g: Garment, scale: int = 1):
    """Fashion Sense frame stack: front, right, left, back."""
    w, h = g.base.size
    img = blank_image(w * scale, h * len(ATLAS_ORDER) * scale, TRANSPARENT)
    for i, d in enumerate(ATLAS_ORDER):
        blit(img, nearest_scale(g.directions[d], scale), 0, i * h * scale)
    return img


def fs_metadata(g: Garment) -> dict:
    """The Fashion Sense model entry for one authored garment."""
    key = "Hats" if g.base.slot == "HEAD" else "Shirts"
    entry = {
        "Name": f"{g.base.name}_{g.style}_{g.seed}",
        "Texture": f"{g.base.name}_{g.seed}.png",
        "FrameSize": {"Width": g.base.size[0], "Height": g.base.size[1]},
        "Scale": 4,
        "Palette": g.palette.id,
        "Style": g.style,
        "Decals": [d.name for d in g.decals],
    }
    if key == "Hats":
        entry["HideHair"] = False
        entry["HeadPosition"] = {"X": 0, "Y": 0}
    return {key: [entry]}


def write(g: Garment, out_dir: str, scale: int = 1) -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{g.base.name}_{g.seed}.png")
    write_rgba_png(path, atlas(g, scale))
    with open(os.path.join(out_dir, f"{g.base.name}_{g.seed}.json"), "w") as fh:
        json.dump(fs_metadata(g), fh, indent=2)
    return path
