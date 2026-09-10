"""Controlled-random generator for the Cap 2 source-derived cap family.

A roll chooses only what the family permits: the Cap 2 base (never anything
else), a palette that survives the structural contrast constraints, and at most
one front-crown motif drawn strictly inside CAP2_FRONT_MOTIF_SAFE_MASK.

Determinism comes from `v5.rng.StreamBank`: each decision draws from its own
named stream, so adding a decision later cannot shift the values an earlier one
drew, and (seed -> spec) is a pure function. A spec carries everything needed
to rebuild the exact hat, including the source provenance and the Fashion Sense
wear properties the original author declared.

Palettes are REJECTED AND REROLLED, not silently accepted: multiplicative
tinting scales the authored value ladder by the tint's own luminance, and a
dark enough tint collapses the visor into its own outline. The constraint is
checked on the ramp the renderer will actually use.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict

import sys
sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing")
from v5.grammar import luminance, perceptual_distance
from v5.rng import StreamBank
from v5.source import audit, pngread

BASE_DIR = "authored/source_bases/cap2"
BACK_CLOSURE_ENABLED = False

# Structural floors, measured on this base. See emblem_grammar.json.
MIN_VISOR_OUTLINE = 20
MIN_CROWN_VISOR = 40

# RARITY decides decoration. Common caps carry no mark at all; the marks get
# stronger, not more numerous, as rarity rises -- the crown only ever holds one.
RARITY_WEIGHTS = {"COMMON": 50.0, "UNCOMMON": 25.0, "RARE": 15.0,
                  "EPIC": 7.0, "LEGENDARY": 3.0}

RARITY_POOL = {
    "COMMON": [],                                   # plain, always
    "UNCOMMON": ["dot", "bar", "twin_bars"],        # the simplest marks
    "RARE": ["ring", "chevron", "angle_l", "zigzag"],
    # EPIC and LEGENDARY are entitled to reserved special motifs, but none have
    # been approved: every candidate so far either collapsed into a blob at
    # gameplay scale or crossed the safe mask. Rather than invent one to fill
    # the slot, they draw from the RARE pool until a special motif earns its
    # place.
    "EPIC": ["ring", "chevron", "angle_l", "zigzag"],
    "LEGENDARY": ["ring", "chevron", "angle_l", "zigzag"],
}

# A motif must not read as the same material as the visor. Luminance alone
# cannot separate them -- the band between the visor field and the crown is
# narrow, so any readable dark mark sits near the visor in VALUE. Hue does the
# work, with perceptual distance as an alternative route.
MIN_MOTIF_CONTRAST = 60      # against the crown, so the mark reads
MIN_MOTIF_HUE = 60           # degrees from the visor field
MIN_MOTIF_DIST = 30          # or perceptual distance, if the hue is close
MOTIF_DROP = 70              # luminance below the crown

# Back closure: pale hardware on the fabric above the adjuster opening. A
# separate slot from the front motif; different views, so they never conflict.
MIN_CLOSURE_CONTRAST = 60

# Rarity decides HOW MANY details a cap carries, not how busy each one is. The
# ceiling is one front mark plus one back closure, and it never rises: higher
# rarity means slightly richer, not cluttered.
RARITY_SLOTS = {
    "COMMON":    {"any": False, "both": False},
    "UNCOMMON":  {"any": True,  "both": False},   # exactly one detail
    "RARE":      {"any": True,  "both": True},
    "EPIC":      {"any": True,  "both": True},
    "LEGENDARY": {"any": True,  "both": True},
}


def _hue(c):
    import colorsys
    return colorsys.rgb_to_hsv(c[0] / 255, c[1] / 255, c[2] / 255)[0] * 360


def hue_gap(a, b):
    d = abs(_hue(a) - _hue(b))
    return min(d, 360 - d)


def _mult(colour, grey):
    return tuple(min(255, round(c * grey / 255)) for c in colour[:3])


def build_ramp(tint, levels):
    """The renderer's ramp, with the outline role darkened until the visor reads.

    Only the outline is adjusted, and only downward; hue, crown and visor are
    left exactly as the multiply produced them.
    """
    ramp = [_mult(tint, lv) for lv in levels]
    factor = 1.0
    while (luminance(ramp[1]) - luminance(ramp[0])) < MIN_VISOR_OUTLINE \
            and factor > 0.05:
        factor -= 0.02
        ramp[0] = tuple(max(0, round(c * factor)) for c in _mult(tint, levels[0]))
    return ramp, round(factor, 2)


def palette_ok(ramp, regions) -> tuple:
    """(passes, measurements) against the structural floors.

    Measured on the ROLE REGIONS the base actually draws, not on single ramp
    steps. A ramp-step proxy disagreed with the rendered result by a factor of
    two: `crown` as a role includes ten cells at step 1 -- the same value as the
    visor field -- so averaging the whole role understates the separation, and
    comparing single steps overstates it. The regions below are the ones the
    floors were calibrated on: the crown's LIT body against the visor's DARK
    field, and that field against the outline.
    """
    m = lambda cells: (sum(luminance(ramp[s]) for s in cells) / len(cells))
    cv = m(regions["crown_lit"]) - m(regions["visor_field"])
    vo = m(regions["visor_field"]) - m(regions["outline"])
    return (vo >= MIN_VISOR_OUTLINE and cv >= MIN_CROWN_VISOR,
            {"visor_outline": round(vo, 1), "crown_visor": round(cv, 1)})


@dataclass
class Cap2Spec:
    """Everything needed to rebuild one hat, exactly."""
    seed: int
    family: str = "SOFT_CAP"
    base_id: str = "cap2"
    rarity: str = "COMMON"
    closure_id: str = "none"
    closure_cells: list = field(default_factory=list)
    palette_id: str = ""
    motif_id: str = "plain"
    motif_tier: str = "-"
    motif_cells: list = field(default_factory=list)
    motif_lowered: int = 0
    motif_colour_choice: int = 0
    palette_rejected: list = field(default_factory=list)
    contrast: dict = field(default_factory=dict)
    outline_factor: float = 1.0
    provenance: dict = field(default_factory=dict)
    wear_properties: dict = field(default_factory=dict)

    def label(self):
        m = "plain" if self.motif_id == "plain" else self.motif_id
        b = "" if self.closure_id == "none" else f"+{self.closure_id}"
        return (f"Cap2 {self.rarity[:4].title()} "
                f"{self.palette_id.split('_')[0].title()} {m}{b} #{self.seed}")


class Cap2Generator:
    def __init__(self, lib, catalog_path="source_catalog/catalog.json"):
        cat = json.load(open(catalog_path))
        self.app = next(a for a in cat["appearances"]
                        if a["name"] == "Cap 2"
                        and a["pack"].startswith("More Acc"))
        self.frames = {d: audit.cut(pngread.read(self.app["png_path"]),
                                    tuple(b))
                       for d, b in self.app["analysis"]["boxes"].items()}
        sm = json.load(open(f"{BASE_DIR}/semantic_map.json"))
        self.vocab = [tuple(c) for c in sm["base"]["vocabulary"]]
        self.levels = [luminance(c) for c in self.vocab]
        self.roles = {tuple(int(v) for v in k.split(",")): r
                      for k, r in sm["structural_roles"]["Front"].items()}
        self.safe = {tuple(c) for c in
                     json.load(open(f"{BASE_DIR}/motif_safe_mask.json"))["safe_cells"]}
        self.marks = json.load(open(f"{BASE_DIR}/overlay_marks.json"))["marks"]
        bc = json.load(open(f"{BASE_DIR}/back_closure.json"))
        self.closures = bc["shapes"]
        self.closure_index = bc["colour"]["index"]
        self.back_roles = {tuple(int(v) for v in k.split(",")): r
                           for k, r in sm["structural_roles"]["Back"].items()}
        drawn_b = set(self.back_roles)
        n8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
              if (dx, dy) != (0, 0)]
        self.back_safe = {
            c for c, role in self.back_roles.items()
            if role not in ("outline", "underside")
            and not any((c[0] + dx, c[1] + dy) not in drawn_b for dx, dy in n8)}
        fb = self.frames["Back"]
        stpb = lambda p: min(range(len(self.vocab)),
                             key=lambda i: abs(self.levels[i] - luminance(p[:3])))
        self.back_zone_steps = [stpb(fb[y][x]) for sh in self.closures.values()
                                for (x, y) in sh["cells"]]
        self.palettes = sorted(lib.palettes, key=lambda p: p.id)
        # role regions as STEP INDICES, so a contrast test needs only a ramp
        f = self.frames["Front"]
        stp = lambda p: min(range(len(self.vocab)),
                            key=lambda i: abs(self.levels[i] - luminance(p[:3])))
        self.regions = {"crown_lit": [], "visor_field": [], "outline": []}
        for c, role in self.roles.items():
            s_ = stp(f[c[1]][c[0]])
            if role in ("crown", "highlight") and s_ >= 3:
                self.regions["crown_lit"].append(s_)
            elif role in ("visor", "underside") and s_ <= 1:
                self.regions["visor_field"].append(s_)
            elif role == "outline":
                self.regions["outline"].append(s_)
        from v5.source import roundtrip
        self.wear = roundtrip.source_blocks(self.app)

    # Candidate motif colours, tried in order. Accent before trim because a
    # mark in the garment's own cloth reads as part of the garment; at these
    # values that means reading as more visor.
    MOTIF_CANDIDATES = [("accent", 3, MOTIF_DROP), ("accent", 2, MOTIF_DROP),
                        ("trim", 3, MOTIF_DROP), ("accent", 3, MOTIF_DROP - 15),
                        ("hardware", 2, MOTIF_DROP)]

    def motif_colour(self, ramp, palette, choice=0):
        from v5.authored import _at_luminance
        role, idx, drop = self.MOTIF_CANDIDATES[choice]
        crown = self.crown_luminance(ramp)
        base = palette.ramps.get(role, palette.ramps["accent"])[idx]
        return _at_luminance(base, max(8.0, crown - drop))

    def crown_luminance(self, ramp):
        return sum(luminance(ramp[s]) for s in self.regions["crown_lit"]) \
            / len(self.regions["crown_lit"])

    def motif_ok(self, ramp, palette) -> tuple:
        """Find a motif colour that cannot be mistaken for the dark structure.

        The mark must clear BOTH dark roles below it -- the visor field and the
        outline -- because "blends with the visor" and "blends with the rim"
        look identical on the farmer. Luminance alone cannot separate them: the
        band between the visor and the crown is narrow, so any readable dark
        mark sits near the visor in VALUE. Hue does the separating, with
        perceptual distance as an alternative route.

        Colour candidates are tried in order before the palette is rejected --
        the instruction is to pick a different motif colour OR reroll, in that
        order.
        """
        crown = self.crown_luminance(ramp)
        best = None
        for i in range(len(self.MOTIF_CANDIDATES)):
            col = self.motif_colour(ramp, palette, i)
            contrast = crown - luminance(col)
            hv, dv = hue_gap(col, ramp[1]), perceptual_distance(col, ramp[1])
            ho, do = hue_gap(col, ramp[0]), perceptual_distance(col, ramp[0])
            clears_visor = hv >= MIN_MOTIF_HUE or dv >= MIN_MOTIF_DIST
            clears_outline = ho >= MIN_MOTIF_HUE or do >= MIN_MOTIF_DIST
            meas = {"motif_colour_choice": i,
                    "motif_role": self.MOTIF_CANDIDATES[i][0],
                    "motif_contrast": round(contrast, 1),
                    "motif_hue_gap": round(min(hv, ho), 1),
                    "motif_distance": round(min(dv, do), 1)}
            if contrast >= MIN_MOTIF_CONTRAST and clears_visor and clears_outline:
                return True, meas
            if best is None:
                best = meas
        return False, best

    def closure_colour(self, palette):
        """Pale hardware — metal, not cloth, and never the opening shadow."""
        return tuple(palette.ramps["hardware"][self.closure_index])[:3]

    def closure_ok(self, ramp, palette) -> tuple:
        back = (sum(luminance(ramp[s]) for s in self.back_zone_steps)
                / len(self.back_zone_steps))
        c = luminance(self.closure_colour(palette)) - back
        return c >= MIN_CLOSURE_CONTRAST, {"closure_contrast": round(c, 1)}

    def place(self, motif_id):
        """Cells for a motif at the LOWEST legal placement in the safe mask.

        A mark high on the dome reads as part of the crown's top edge; lower is
        where a real cap prints. So the shape is pushed down as far as it will
        go while every cell stays legal, and not one row further.

        In practice only `bar` can move. The mask is rows 5-7: row 8 is
        excluded in full because every row-8 cell is orthogonally adjacent to
        the visor at row 9. Any motif that already reaches row 7 is therefore
        at its floor. Nothing is stretched, reshaped or clipped to manufacture
        a lower placement -- a motif that cannot drop simply does not drop.
        """
        cells = [tuple(c) for c in self.marks[motif_id]["cells"]]
        drop = 0
        while all((x, y + drop + 1) in self.safe for (x, y) in cells):
            drop += 1
        if drop:
            cells = [(x, y + drop) for (x, y) in cells]
        return cells, drop

    def roll(self, seed: int) -> Cap2Spec:
        rng = StreamBank(seed)
        spec = Cap2Spec(seed=seed)
        spec.provenance = {
            "pack": self.app["pack"], "author": self.app["pack_author"],
            "asset": self.app["name"], "png": self.app["png_path"],
            "note": "base construction unmodified; motif is generator-authored",
        }
        spec.wear_properties = self.wear

        # rarity first: it decides whether a mark exists at all, and a plain cap
        # imposes no motif constraint on the palette
        spec.rarity = rng("rarity").weighted(RARITY_WEIGHTS)
        slots = RARITY_SLOTS[spec.rarity]
        pool = RARITY_POOL[spec.rarity]
        want_front = want_back = False
        if slots["both"]:
            want_front = rng("slot:front").chance(0.75)
            want_back = rng("slot:back").chance(0.55)
            if not (want_front or want_back):
                want_front = True             # a rare cap is never bare
        elif slots["any"]:
            want_front = rng("slot:which").chance(0.55)
            want_back = not want_front        # exactly one
        spec.motif_id = (rng("motif").choice(sorted(pool))
                         if (want_front and pool) else "plain")
        spec.motif_tier = spec.rarity
        spec.closure_id = (rng("closure").choice(sorted(self.closures))
                           if want_back and BACK_CLOSURE_ENABLED else "none")
        if spec.closure_id != "none":
            spec.closure_cells = [tuple(c) for c in
                                  self.closures[spec.closure_id]["cells"]]
            for c in spec.closure_cells:
                if c not in self.back_safe:
                    raise ValueError(f"closure {spec.closure_id}: {c} is "
                                     "outside the back safe area")

        if spec.motif_id != "plain":
            spec.motif_cells, spec.motif_lowered = self.place(spec.motif_id)
        else:
            spec.motif_cells, spec.motif_lowered = [], False

        # palette: draw, test, reroll. Each attempt draws from its own stream so
        # a rejection cannot perturb any other decision.
        for attempt in range(len(self.palettes) * 2):
            pal = rng(f"palette:{attempt}").choice(self.palettes)
            ramp, factor = build_ramp(pal.ramps["body"][3], self.levels)
            ok, meas = palette_ok(ramp, self.regions)
            if not ok:
                spec.palette_rejected.append(
                    {"palette": pal.id, "reason": "structural contrast", **meas})
                continue
            if spec.motif_id != "plain":
                mok, mmeas = self.motif_ok(ramp, pal)
                meas = {**meas, **mmeas}
                if not mok:
                    spec.palette_rejected.append(
                        {"palette": pal.id,
                         "reason": "motif would read as the same material as "
                                   "the visor", **meas})
                    continue
            if spec.closure_id != "none":
                cok, cmeas = self.closure_ok(ramp, pal)
                meas = {**meas, **cmeas}
                if not cok:
                    spec.palette_rejected.append(
                        {"palette": pal.id, "reason": "back closure would not "
                         "read against the back fabric", **meas})
                    continue
            spec.palette_id, spec.contrast = pal.id, meas
            spec.motif_colour_choice = meas.get("motif_colour_choice", 0)
            spec.outline_factor = factor
            break
        else:
            raise RuntimeError(f"seed {seed}: no palette satisfied the rules")
        return spec

    def render(self, spec: Cap2Spec) -> dict:
        pal = next(p for p in self.palettes if p.id == spec.palette_id)
        ramp, _ = build_ramp(pal.ramps["body"][3], self.levels)
        out = {}
        for d, f in self.frames.items():
            rows = [[(0, 0, 0, 0)] * len(f[0]) for _ in f]
            for y in range(len(f)):
                for x in range(len(f[0])):
                    p = f[y][x]
                    if not p[3]:
                        continue
                    step = min(range(len(self.vocab)),
                               key=lambda i: abs(self.levels[i]
                                                 - luminance(p[:3])))
                    rows[y][x] = (*ramp[step], 255)
            out[d] = rows
        if spec.motif_id != "plain":
            pal_obj = next(p for p in self.palettes if p.id == spec.palette_id)
            colour = self.motif_colour(ramp, pal_obj, spec.motif_colour_choice)
            for c in spec.motif_cells:
                x, y = int(c[0]), int(c[1])
                if (x, y) not in self.safe:
                    raise ValueError(f"{spec.motif_id}: cell {x},{y} outside "
                                     "CAP2_FRONT_MOTIF_SAFE_MASK")
                out["Front"][y][x] = (*colour, 255)
        if BACK_CLOSURE_ENABLED and spec.closure_id != "none":
            pal_obj = next(p for p in self.palettes if p.id == spec.palette_id)
            hw = self.closure_colour(pal_obj)
            for (x, y) in spec.closure_cells:
                if (x, y) not in self.back_safe:
                    raise ValueError(f"closure cell {x},{y} outside the back "
                                     "safe area")
                out["Back"][y][x] = (*hw, 255)
        return out
