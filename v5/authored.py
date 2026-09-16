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

# The view set a base declares when it says nothing.  Right is synthesised by
# mirroring Left for these, which is what every base authored before the
# four-view contract existed relies on.
VIEWS = ("front", "back", "left")
ALL_VIEWS = ("front", "right", "left", "back")
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
    # Which garment family this base belongs to.  A family groups SHAPES of the
    # same garment so the combinator can be asked for "a beret" and get one of
    # the beret shapes, never a knit cap.  A base that declares nothing forms a
    # family of its own under its own name, so the four bases authored before
    # families existed keep behaving exactly as they did.
    family: str = ""
    # This base's value on the shape axis, within its family.  Shape is a first
    # class axis: it varies independently of palette, decal and quality tier.
    shape_variant: str = ""
    # The views this base actually authors.  A base that authors `right` has it
    # rendered from its own pixels; one that does not keeps the historical
    # mirror-of-left fallback.  See `_render`.
    views: tuple = VIEWS
    # Where this base's art came from, and what was done to it on the way in.
    provenance: str = ""
    # PORT_CLASSIFICATION state. Only a PRODUCTION base is eligible for the
    # slot-wide roll; a REFERENCE base is reachable only by naming its family,
    # which is what "usable for architecture and testing, not shippable" has to
    # mean mechanically rather than as a comment. It also keeps ingesting a new
    # base from moving the existing slot-wide distribution.
    classification: str = "PRODUCTION"

    def view(self, v):
        return self.cells[v]

    def authors_right(self) -> bool:
        return "right" in self.views

    def mirrored_view(self) -> str | None:
        """The profile view this base does NOT author, and so gets by mirroring."""
        if "right" not in self.views:
            return "right"
        if "left" not in self.views:
            return "left"
        return None


@dataclass(frozen=True)
class Treatment:
    """A material: a deterministic re-stepping of a base's own body cells.

    It adds no geometry and invents no colour -- it only moves cells up or down
    the ramp they are already on -- so it composes with every palette and every
    shape for free. That is why material is its own axis rather than a kind of
    decal: a plaid covers the whole crown, and no zone-bounded piece can say
    that.
    """
    name: str
    label: str
    rule: str
    params: dict

    def _hash(self, x, y):
        h = (x * 73856093) ^ (y * 19349663) ^ 0x9E3779B9
        h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
        return ((h ^ (h >> 16)) & 0xFFFF) / 0xFFFF

    def apply(self, cells: dict) -> dict:
        if self.rule == "plain":
            return cells
        p = self.params
        lo = int(p.get("min_step", 0))
        d = int(p.get("delta", 1))
        out = dict(cells)
        for (x, y), (role, step) in cells.items():
            # Only the body carries material. The band and under-edge steps are
            # construction, and texturing them turns a readable rim into noise.
            if role != "body" or step < lo:
                continue
            if self.rule == "speckle":
                if self._hash(x, y) < float(p.get("density", 0.15)):
                    out[(x, y)] = (role, min(5, step + d))
            elif self.rule == "rib":
                if x % int(p.get("period", 2)) == 0:
                    out[(x, y)] = (role, max(lo, step - d))
            elif self.rule == "check":
                n = (1 if x % int(p.get("period", 4)) == 0 else 0) + \
                    (1 if y % int(p.get("row_period", 3)) == 0 else 0)
                if n:
                    out[(x, y)] = (role, min(5, step + d * n))
            elif self.rule == "panel":
                ys = [b for _, b in cells]
                xs = [a for a, _ in cells]
                seam_y = min(ys) + (max(ys) - min(ys)) // 3
                seam_x = (min(xs) + max(xs)) // 2
                if y == seam_y or x == seam_x:
                    out[(x, y)] = (role, max(lo, step - d))
        return out


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
    # Families this piece belongs to.  `fits` names individual bases; this names
    # whole families, so a piece drawn for the beret family covers beret_02 and
    # beret_03 the day they are ingested without anyone editing this file.
    # Empty means "not family-scoped" and `fits` alone decides.
    families: tuple = ()
    # Optional player-facing family variants this piece belongs to.  Empty means
    # it participates in the normal pools; non-empty pieces are variant-only and
    # are invisible to legacy/tier/profile rolls unless that variant is named.
    variants: tuple = ()

    def fits_base(self, base) -> bool:
        # Declaring a family CONSTRAINS: a piece scoped to the beret family and
        # named for no base at all must not fall through to "fits everything".
        # `fits` still grants membership on its own, so widening a shared piece
        # with a family never takes it away from the bases it was drawn for.
        if self.families:
            return base.family in self.families or base.name in self.fits
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
    # family id -> policy: which shapes, which palettes per material, and which
    # motif classes each quality tier may draw from.  Data, not code, so a new
    # family is a JSON file rather than an engine change.
    families: dict = None
    # The quality-tier ladder: order plus the per-tier decoration ceilings.
    # Generic — a family names motif CLASSES per tier, the ladder owns the
    # counts and the cell budget that keep a hat readable at Stardew scale.
    quality: dict = None
    # name -> Treatment.  The material axis: a surface treatment over a base's
    # own body cells, independent of shape, palette, decal and tier.
    treatments: dict = None

    def tone_for(self, base: Base):
        return (self.tones or {}).get(base.tone_profile)

    def styles(self):
        return sorted({s for b in self.bases for s in b.style})

    def family(self, fid: str) -> dict:
        fam = (self.families or {}).get(fid)
        if fam is None:
            raise ValueError(f"no authored family {fid!r}")
        return fam

    def family_bases(self, fid: str) -> list:
        return sorted((b for b in self.bases if b.family == fid),
                      key=lambda b: b.shape_variant)

    def tier(self, name: str) -> dict:
        t = (self.quality or {}).get("tiers", {}).get(name)
        if t is None:
            raise ValueError(f"no quality tier {name!r}")
        return t

    def tier_order(self) -> list:
        return list((self.quality or {}).get("order", []))

    def treatment(self, name: str) -> "Treatment | None":
        if not name or name == "felt":
            return (self.treatments or {}).get("felt")
        t = (self.treatments or {}).get(name)
        if t is None:
            raise ValueError(f"no authored treatment {name!r}")
        return t

    def profile(self, family: str, name: str) -> dict:
        p = (self.family(family).get("profiles") or {}).get(name)
        if p is None:
            raise ValueError(f"family {family!r} has no profile {name!r}")
        return p

    def variant(self, family: str, name: str) -> dict:
        v = (self.family(family).get("variants") or {}).get(name)
        if v is None:
            raise ValueError(f"family {family!r} has no variant {name!r}")
        return v


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
        # A base declares its own views.  Saying nothing means the historical
        # three, so nothing authored before this contract has to be edited.
        views = tuple(man.get("views", VIEWS))
        unknown = [v for v in views if v not in ALL_VIEWS]
        if unknown:
            raise ValueError(f"{name}: unknown view(s) {unknown}")
        if "front" not in views:
            raise ValueError(f"{name}: a base must author a front view")
        if "back" not in views:
            raise ValueError(f"{name}: a base must author a back view")
        if not ({"left", "right"} & set(views)):
            raise ValueError(f"{name}: a base must author at least one profile "
                             f"view; the other is mirrored from it")
        cells = {v: _decode(os.path.join(bdir, name, f"{v}.png"), index)
                 for v in views}
        bases.append(Base(man["name"], man["slot"], tuple(man["size"]),
                          tuple(man["style"]), man["anchors"],
                          man.get("zones", {}), cells, man.get("tone_profile"),
                          man.get("family", man["name"]),
                          man.get("shape_variant", man["name"]),
                          views, man.get("provenance", ""),
                          man.get("classification", "PRODUCTION")))
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
                            tuple(man.get("fits", ())),
                            tuple(man.get("families", ())),
                            tuple(man.get("variants", ()))))
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
    families = {}
    fpath = os.path.join(root, "families.json")
    if os.path.exists(fpath):
        families = _read_json(fpath)["families"]
    tiers = {}
    qpath = os.path.join(root, "quality_tiers.json")
    if os.path.exists(qpath):
        tiers = _read_json(qpath)
    treatments = {}
    tpath2 = os.path.join(root, "treatments.json")
    if os.path.exists(tpath2):
        for name, t in _read_json(tpath2)["treatments"].items():
            treatments[name] = Treatment(name, t["label"], t["rule"],
                                         t.get("params", {}))
    return Library(tuple(bases), tuple(decals), tuple(palettes), tones,
                   families, tiers, treatments)


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
    # The family axes, recorded so a roll can be inspected and reproduced.
    # None on a legacy roll that named no family.
    family: str = ""
    shape_variant: str = ""
    quality_tier: str = ""
    material: str = ""
    treatment: str = ""
    profile: str = ""
    variant: str = ""


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


def can_place(base: Base, d: Decal) -> bool:
    """Can this piece be drawn on this base in every view it claims?

    A piece must place in EVERY view it declares that the base also authors, not
    merely in one of them. `any` let a 6-wide band be chosen for a shape whose
    side band zone is 5 wide: it drew on the front and back and was dropped in
    profile, so the hat wore a band that vanished when the farmer turned.

    Zone fit is not legality either. An attachment may hang off the silhouette,
    so its bounds and connectivity are only checked at render; a surface motif
    must lie entirely ON the silhouette, and the `side` zone deliberately
    overhangs the crown edge because attachments live there. This applies
    exactly the renderer's own tests, so nothing is picked that is about to be
    thrown away -- and tools that report pool coverage ask the same question the
    combinator asks, rather than a weaker one that drifts from it.
    """
    want = [v for v in d.views if v in base.views]
    if not want:
        return False
    for v in want:
        origin = _placement(base, d, v)
        if origin is None:
            return False
        ax, ay = origin
        silhouette = set(base.view(v))
        placed = {(ax + dx, ay + dy): val
                  for (dx, dy), val in d.view_cells(v).items()}
        if d.kind == "attachment":
            if _attachment_ok(placed, silhouette, d, base.size):
                return False
        elif any(c not in silhouette for c in placed):
            return False
    return True


def _weighted_decals(rng, lib, fam, tier_name, base, story, palette_id, weights,
                     deny=()):
    """Tier selection biased by motif-class weight, for the profile path.

    Weights bias, they never restrict: every piece legal for the tier can still
    be drawn, which is what stops a weighted batch collapsing into copies of the
    one combination the weights like best. A class with no weight gets 1.
    """
    tier = lib.tier(tier_name)
    pools = fam.get("pools", {})
    allowed = {"attachment": set(pools.get("attachment", {}).get(tier_name, [])),
               "surface": set(pools.get("surface_motif", {}).get(tier_name, []))}
    caps = {"attachment": int(tier.get("max_attachments", 0)),
            "surface": int(tier.get("max_motifs", 0))}
    budget = int(tier.get("max_decor_cells", 0))
    floor = int(tier.get("min_decor_pieces", 0))
    chance = float(tier.get("pick_chance", 0.62))

    legal = [d for d in lib.decals
             if d.slot == base.slot and not d.pending and not d.variants
             and story in d.style and d.fits_base(base)
             and d.motif_class in allowed.get(d.kind, set())
             and d.motif_class not in deny
             and can_place(base, d)]

    chosen, used, spent = [], set(), 0

    def cost(d):
        return max(len(d.view_cells(v)) for v in d.views) if d.views else 0

    def admissible(d):
        return region_of(d) not in used and spent + cost(d) <= budget

    def take(d):
        nonlocal spent
        chosen.append(d)
        used.add(region_of(d))
        spent += cost(d)

    for kind in ("attachment", "surface"):
        if caps[kind] <= 0:
            continue
        cands = [d for d in legal if d.kind == kind and admissible(d)]
        if not cands:
            continue
        want = rng(f"want:{base.name}:{palette_id}:{kind}").chance(chance)
        if not (want or len(chosen) < floor):
            continue
        pick = rng(f"pick:{base.name}:{palette_id}:{kind}").weighted(
            {d.name: max(1, int(weights.get(d.motif_class, 1))) for d in cands})
        take(next(d for d in cands if d.name == pick))

    # the floor still applies, and still tops up deterministically
    if len(chosen) < floor:
        for d in sorted((d for d in legal if d not in chosen),
                        key=lambda d: (d.kind != "attachment", d.name)):
            if len(chosen) >= floor:
                break
            k = sum(1 for c in chosen if c.kind == d.kind)
            if k < caps[d.kind] and admissible(d):
                take(d)
    return chosen


def _tier_decals(rng, lib, fam, tier_name, base, story, palette_id=""):
    """Pick decals under a quality tier's allow-list and its cell budget.

    The tier owns the COUNTS and the pixel budget; the family owns which motif
    CLASSES are legal at each tier.  Gating on class rather than on decal name
    is what makes this generic: a new flower drawn next month is legal at the
    tiers that already allow `flower`, with nobody editing a list.
    """
    tier = lib.tier(tier_name)
    pools = fam.get("pools", {})
    allowed = {
        "attachment": set(pools.get("attachment", {}).get(tier_name, [])),
        "surface": set(pools.get("surface_motif", {}).get(tier_name, [])),
    }
    caps = {"attachment": int(tier.get("max_attachments", 0)),
            "surface": int(tier.get("max_motifs", 0))}
    budget = int(tier.get("max_decor_cells", 0))

    legal = [d for d in lib.decals
             if d.slot == base.slot and not d.pending and not d.variants
             and story in d.style and d.fits_base(base)
             and d.motif_class in allowed.get(d.kind, set())
             and can_place(base, d)]

    chosen, used, taken, spent = [], set(), {"attachment": 0, "surface": 0}, 0

    def admissible(d):
        cost = max(len(d.view_cells(v)) for v in d.views) if d.views else 0
        return (taken[d.kind] < caps[d.kind] and region_of(d) not in used
                and spent + cost <= budget)

    def take(d):
        nonlocal spent
        chosen.append(d)
        used.add(region_of(d))
        taken[d.kind] += 1
        spent += max(len(d.view_cells(v)) for v in d.views) if d.views else 0

    for d in sorted(legal, key=lambda d: d.name):
        if not admissible(d):
            continue
        # Key the stream on the base and palette as well as the piece. Keying it
        # on the piece alone made decoration a function of the seed only, so a
        # whole batch of different shapes in different palettes came out wearing
        # exactly the same decals — the shape axis existed but did nothing.
        if rng(f"decal:{base.name}:{palette_id}:{d.name}").chance(0.62):
            take(d)

    # A premium tier that rolls nothing is not premium. The chance loop gives
    # variety; the floor guarantees the ladder still means something, by topping
    # up deterministically from what is left rather than re-rolling until it
    # looks right. Attachments first: at the top tiers the accent is the point.
    floor = int(tier.get("min_decor_pieces", 0))
    if len(chosen) < floor:
        rest = sorted((d for d in legal if d not in chosen),
                      key=lambda d: (d.kind != "attachment", d.name))
        for d in rest:
            if len(chosen) >= floor:
                break
            if admissible(d):
                take(d)
    return chosen


def _apply_family_variant(rng, lib, variant_name, spec, base, story, palette_id, chosen, tier_name):
    """Apply a family-defined player-facing variant without changing base art.

    Variants are intentionally shallow: they may constrain shape selection and
    decoration, but they do not introduce a second renderer or duplicate bases.
    "plain" can suppress decoration; "one_of" picks exactly one legal motif
    from a small family-owned class list. With no variant, this function is not
    called, so historical rolls remain byte-identical.
    """
    mode = spec.get("decoration_mode", "inherit")
    if mode == "none":
        return []
    if mode != "one_of":
        return chosen

    allowed = set(spec.get("allowed_motif_classes", ()))
    minimum = int(spec.get("min_decor_pieces", 1))
    maximum = int(spec.get("max_decor_pieces", 1))
    kept = [d for d in chosen if d.motif_class in allowed][:maximum]
    if len(kept) >= minimum:
        return kept

    legal = [d for d in lib.decals
             if d.slot == base.slot and not d.pending
             and (not d.variants or variant_name in d.variants)
             and story in d.style and d.fits_base(base)
             and d.motif_class in allowed and can_place(base, d)]
    if tier_name:
        tier = lib.tier(tier_name)
        caps = {"attachment": int(tier.get("max_attachments", 0)),
                "surface": int(tier.get("max_motifs", 0))}
        budget = int(tier.get("max_decor_cells", 0))
        legal = [d for d in legal
                 if caps.get(d.kind, 0) > 0
                 and max(len(d.view_cells(v)) for v in d.views) <= budget]
    if not legal:
        raise ValueError("family variant cannot satisfy its decoration requirement "
                         f"for {base.name}/{story}/{tier_name or 'legacy'}")
    pick = rng(f"variant:{base.name}:{palette_id}:{spec.get('label','variant')}").choice(
        sorted(legal, key=lambda d: d.name))
    return [pick]


def compose(seed: int, slot: str | None = None, lib: Library | None = None,
            style: str | None = None, family: str | None = None,
            quality_tier: str | None = None,
            shape_variant: str | None = None,
            profile: str | None = None,
            treatment: str | None = None,
            variant: str | None = None) -> Garment:
    """One roll: a base, a style, a curated palette, and legal decals.

    Naming a `family` restricts the shape pool to that family's own bases, so
    asking for a beret cannot return a knit cap.  Naming a `quality_tier` on top
    of that gates palette and decoration richness.  With neither, this behaves
    exactly as it did before families existed.
    """
    lib = lib or load()
    rng = StreamBank(seed)

    if family is not None:
        fam = lib.family(family)
        slot = slot or fam.get("slot")
        bases = lib.family_bases(family)
        var = lib.variant(family, variant) if variant else None
        if var is not None:
            allowed = var.get("shape_variants", "any")
            if allowed not in (None, "any"):
                bases = [b for b in bases if b.shape_variant in allowed]
            if quality_tier is None:
                quality_tier = var.get("default_quality_tier")
        prof = lib.profile(family, profile) if profile else None
        if prof is not None:
            if var is not None:
                raise ValueError("profile= and variant= are separate selectors; choose one")
            return _compose_profile(rng, lib, family, fam, prof, profile,
                                    quality_tier, shape_variant, treatment, seed)
        if shape_variant is not None:
            bases = [b for b in bases if b.shape_variant == shape_variant]
        if not bases:
            raise ValueError(f"family {family!r} has no ingested base"
                             + (f" for shape {shape_variant!r}" if shape_variant else ""))
        if quality_tier is not None:
            allowed_shapes = lib.tier(quality_tier).get("shape_variants")
            fam_shapes = fam.get("quality_tiers", {}).get(quality_tier, {}).get("shape_variants")
            pick = fam_shapes if fam_shapes is not None else allowed_shapes
            if pick not in (None, "any"):
                bases = [b for b in bases if b.shape_variant in pick] or bases
        base = rng("base").choice(sorted(bases, key=lambda b: b.name))
        variant_styles = set(var.get("styles", ())) if var is not None else None
        choices = [s for s in base.style
                   if (style is None or s == style)
                   and (not variant_styles or s in variant_styles)]
        if not choices:
            raise ValueError(f"{base.name} cannot be {style}"
                             + (f" in variant {variant!r}" if variant else ""))
        story = rng("style").choice(sorted(choices))

        material = ""
        if quality_tier is not None:
            mats = fam.get("quality_tiers", {}).get(quality_tier, {}).get("materials", [])
            pool = []
            for m in sorted(mats):
                for pid in fam.get("materials", {}).get(m, []):
                    pool.append((m, pid))
            pool = [(m, pid) for m, pid in pool
                    if any(p.id == pid and story in p.style for p in lib.palettes)]
            if not pool:
                raise ValueError(f"{family}/{quality_tier}: no palette for style {story}")
            material, pid = rng("material").choice(sorted(pool))
            palette = next(p for p in lib.palettes if p.id == pid)
            chosen = _tier_decals(rng, lib, fam, quality_tier, base, story, pid)
        else:
            pals = [p for p in lib.palettes if story in p.style] or list(lib.palettes)
            palette = rng("palette").choice(sorted(pals, key=lambda p: p.id))
            chosen = _legacy_decals(rng, lib, base, story)

        if var is not None:
            chosen = _apply_family_variant(rng, lib, variant or "", var, base, story, palette.id,
                                           chosen, quality_tier)
        directions, dropped = _render(base, chosen, palette, lib.tone_for(base))
        return Garment(seed, base, story, palette, tuple(chosen), dropped, directions,
                       family, base.shape_variant, quality_tier or "", material,
                       variant=variant or "")

    bases = [b for b in lib.bases
             if b.slot == slot and b.classification == "PRODUCTION"]
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

    chosen = _legacy_decals(rng, lib, base, story)

    directions, dropped = _render(base, chosen, palette, lib.tone_for(base))
    return Garment(seed, base, story, palette, tuple(chosen), dropped, directions)


def _compose_profile(rng, lib, family, fam, prof, profile_name, quality_tier,
                     shape_variant, treatment, seed=0):
    """A roll inside a named style profile.

    The profile owns nothing the engine does not already understand: it is a set
    of WEIGHTS over the same shape, palette, treatment and motif-class axes.
    That is what keeps it a profile rather than a second generator -- a family
    without one behaves exactly as it did.
    """
    if quality_tier is None:
        quality_tier = lib.tier_order()[0]
    shapes = {k: v for k, v in prof["shape_variants"].items()
              if shape_variant is None or k == shape_variant}
    have = {b.shape_variant: b for b in lib.family_bases(family)}
    shapes = {k: v for k, v in shapes.items() if k in have}
    if not shapes:
        raise ValueError(f"profile {profile_name!r} has no ingested shape"
                         + (f" for {shape_variant!r}" if shape_variant else ""))
    base = have[rng("base").weighted(shapes)]

    stories = [t for t in prof["styles"] if t in base.style]
    if not stories:
        raise ValueError(f"{base.name} cannot wear profile {profile_name!r}")
    story = rng("style").choice(sorted(stories))

    pool = [p for p in lib.palettes
            if p.id in prof["palettes"] and story in p.style]
    if not pool:
        raise ValueError(f"profile {profile_name!r}: no palette for style {story}")
    pid = rng("palette").choice(sorted(x.id for x in pool))
    palette = next(p for p in pool if p.id == pid)

    tw = prof.get("treatment_by_tier", {}).get(quality_tier, {"felt": 1})
    tname = treatment or rng("treatment").weighted(tw)
    treat = lib.treatment(tname)

    chosen = _weighted_decals(rng, lib, fam, quality_tier, base, story,
                              palette.id, prof.get("class_weights", {}),
                              tuple(prof.get("class_deny", ())))
    directions, dropped = _render(base, chosen, palette, lib.tone_for(base), treat)
    mats = [m for m, ids in fam.get("materials", {}).items() if palette.id in ids]
    return Garment(seed, base, story, palette, tuple(chosen), dropped, directions,
                   family, base.shape_variant, quality_tier,
                   mats[0] if mats else "", tname, profile_name)


def build_profile(family: str, profile: str, shape_variant: str, palette_id: str,
                  quality_tier: str, treatment: str | None = None, seed: int = 0,
                  lib: Library | None = None) -> Garment:
    """The profile assembly with every axis named explicitly.

    Used by the validation batch, where the point is to walk a known matrix of
    shape x palette x treatment x tier rather than sample the distribution.
    """
    lib = lib or load()
    fam = lib.family(family)
    prof = lib.profile(family, profile)
    base = next((b for b in lib.family_bases(family)
                 if b.shape_variant == shape_variant), None)
    if base is None:
        raise ValueError(f"family {family!r} has no shape {shape_variant!r}")
    palette = next((p for p in lib.palettes if p.id == palette_id), None)
    if palette is None:
        raise ValueError(f"no curated palette {palette_id!r}")
    stories = [t for t in prof["styles"] if t in base.style and t in palette.style]
    if not stories:
        raise ValueError(f"{base.name}/{palette_id} share no profile style")
    story = sorted(stories)[0]
    rng = StreamBank(seed)
    tname = treatment or rng("treatment").weighted(
        prof.get("treatment_by_tier", {}).get(quality_tier, {"felt": 1}))
    treat = lib.treatment(tname)
    chosen = _weighted_decals(rng, lib, fam, quality_tier, base, story,
                              palette.id, prof.get("class_weights", {}),
                              tuple(prof.get("class_deny", ())))
    directions, dropped = _render(base, chosen, palette, lib.tone_for(base), treat)
    mats = [m for m, ids in fam.get("materials", {}).items() if palette_id in ids]
    return Garment(seed, base, story, palette, tuple(chosen), dropped, directions,
                   family, base.shape_variant, quality_tier,
                   mats[0] if mats else "", tname, profile)


def _legacy_decals(rng, lib, base, story):
    """The pre-family decal roll, unchanged and still the path with no tier."""
    legal = [d for d in lib.decals
             if d.slot == base.slot and not d.pending and not d.variants
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
    return chosen


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


def _render(base: Base, decals, palette: Palette, tone: "ToneProfile | None" = None,
            treatment: "Treatment | None" = None):
    # Colour identity comes from the palette; value rhythm from the tone
    # profile, if the base declares one.  Two axes, composed here and nowhere
    # else, so a palette file never has to know about a base.
    if tone is not None:
        palette = tone.apply(palette)
    w, h = base.size
    out, dropped = {}, []
    for view in base.views:
        cells = dict(base.view(view))
        # Material first: it restyles the base's own surface, and a decal placed
        # afterwards sits ON that surface rather than being textured by it.
        if treatment is not None:
            cells = treatment.apply(cells)
        # The pristine treated surface. `cells` accumulates decals as the loop
        # runs, and integration must read the surface a piece is landing ON, not
        # one an earlier piece has already written into.
        surface = dict(cells)
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
            seated, occl, note = integrate(placed, surface, d.kind, d.edge)
            if seated is None:
                dropped.append((d.name, view, note))
                continue
            for c, depth in (occl or {}).items():
                role, step = cells.get(c, surface.get(c, ("body", 3)))
                cells[c] = (role, min(5, step + depth))
            cells.update(seated)
        out[view] = _paint(cells, palette, w, h)
    # Whichever profile view the base did not author is mirrored from the one it
    # did.  Left-from-right is the Fashion Sense `Flipped` convention, which the
    # approved Cottagecore beret uses; right-from-left is the historical fallback
    # every base drawn before the four-view contract depends on.  A base that
    # authors both keeps both.
    if "right" not in out:
        out["right"] = _mirror(out["left"])
    if "left" not in out:
        out["left"] = _mirror(out["right"])
    return out, tuple(dropped)


def build_tier(family: str, shape_variant: str, palette_id: str, quality_tier: str,
               seed: int = 0, lib: Library | None = None,
               style: str | None = None) -> Garment:
    """Hold family, shape and palette FIXED and let the quality tier move.

    This is the assembly the axis-independence check needs: if quality is a real
    axis, the same shape in the same palette must be able to differ only in how
    much decoration it carries.  If it were secretly a preset selector, the base
    or the palette would change underneath, and this signature makes that
    impossible to hide.
    """
    lib = lib or load()
    fam = lib.family(family)
    base = next((b for b in lib.family_bases(family)
                 if b.shape_variant == shape_variant), None)
    if base is None:
        raise ValueError(f"family {family!r} has no shape {shape_variant!r}")
    palette = next((p for p in lib.palettes if p.id == palette_id), None)
    if palette is None:
        raise ValueError(f"no curated palette {palette_id!r}")
    stories = [t for t in base.style if t in palette.style and (style is None or t == style)]
    if not stories:
        raise ValueError(f"{base.name} and {palette_id} share no style tag")
    story = sorted(stories)[0]
    rng = StreamBank(seed)
    chosen = _tier_decals(rng, lib, fam, quality_tier, base, story, palette_id)
    directions, dropped = _render(base, chosen, palette, lib.tone_for(base))
    mats = [m for m, ids in fam.get("materials", {}).items() if palette_id in ids]
    return Garment(seed, base, story, palette, tuple(chosen), dropped, directions,
                   family, base.shape_variant, quality_tier, mats[0] if mats else "")


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
