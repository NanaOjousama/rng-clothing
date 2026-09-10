"""NEW AG — ART GRAMMAR (Pass 12).

Turns the semantic art plan into native 8x8 pixels:

  * role-based ramps (never arbitrary colour)
  * Grammar base lighting + declared local occlusion composed by MAX
  * material-aware highlight extent and edge behaviour
  * contrast-aware SELECTIVE edge treatment — no global dark outline pass
  * point accents protected from being shaded away

AG resolves ramp STEPS.  It never mints a colour the palette did not author.
"""

from __future__ import annotations

from .grammar import (RENDER_CLASS_HIGHLIGHT_BUDGET, RENDER_CLASS_LIGHT_MODEL,
                      RENDER_CLASS_OUTLINE, RENDER_CLASS_SHADING,
                      SEPARATION_SUFFICIENT, VIEWS,
                      base_lighting, form_lighting, luminance)
from .material import MATERIALS

TRANSPARENT = (0, 0, 0, 0)

# Share of the silhouette a fully glossy material may light, for render classes
# that budget their highlight.  120 vanilla hats put a median 6.9% of the front
# frame within 12 luminance of their brightest pixel, and the four hats the user
# picked as good put 5.2% there against our 20.5%.  Multiplied by the material's
# own highlight_extent this puts wool at ~3% and satin at ~11%.
HIGHLIGHT_BUDGET_SHARE = 0.12


def _neighbours(cell):
    x, y = cell
    return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))


def rasterize_view(spec, construction, art, view: str,
                   render_class: str = "torso_8x8") -> dict:
    env = construction.env
    palette = spec.palette
    material = MATERIALS[spec.material]
    sil = construction.silhouette[view]
    paint = art.paint[view]
    occlusion = construction.occlusion_field(view)

    # Base lighting is Grammar, selected by render class, never rolled.
    if RENDER_CLASS_SHADING.get(render_class) == "form":
        # Form follows CONSTRUCTION, not the trim decals painted on top of it:
        # a stripe across a yoke must not split the yoke into two lit masses.
        regions = art.structural.get(view) or {
            c: pc.feature.split(":")[0] for c, pc in paint.items()}
        # One specular pixel is allowed to break symmetry, and only for a
        # material glossy enough to earn it.
        spec_cell = None
        if material.highlight_extent >= 0.55:
            interior = sorted(c for c in sil
                              if all((c[0] + dx, c[1] + dy) in sil
                                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))))
            spec_cell = interior[0] if interior else None
        forms = {p.name: p.form for p in construction.pieces}
        lighting = form_lighting(sil, regions, env, forms=forms, specular=spec_cell,
                                 light_model=RENDER_CLASS_LIGHT_MODEL.get(
                                     render_class, "stacked"))
        # Authored micro-patterns win over the procedural field wherever a piece
        # has an opinion about its own interior.
        authored = set()
        for piece in construction.ordered():
            for cell, offset in piece.shading.get(view, {}).items():
                if cell in sil and regions.get(cell) == piece.name:
                    lighting[cell] = offset
                    authored.add(cell)
        keep = {c for c, v in lighting.items() if v < 0}
        if RENDER_CLASS_HIGHLIGHT_BUDGET.get(render_class):
            # A piece built from an authored interior has ALREADY sized its own
            # highlight, and re-capping it here would make two owners of the
            # same decision.  The render-class budget governs what is left: the
            # procedural field, i.e. pieces and Architectures with no template.
            spent = {c for c in keep if c in authored}
            keep = keep - authored
            # A highlight is a patch, not a band.  Spend the material's extent
            # on the cells nearest the lit shoulder — topmost first, then
            # leftmost, which is where the corpus puts it — and let the rest of
            # the form field fall back to the base step.  Deterministic: the
            # order is the cell order, never the iteration order of a set.
            budget = max(1, round(material.highlight_extent
                                  * HIGHLIGHT_BUDGET_SHARE * len(sil)))
            # Spend it INSIDE the silhouette.  An outlined render class darkens
            # its whole border afterwards, so a highlight placed on the crown's
            # top row is painted over and the hat ends up with no light step at
            # all — which measures as a huge "highlight" because the base colour
            # is then the brightest thing in the frame.
            border = {c for c in sil
                      if any((c[0] + dx, c[1] + dy) not in sil
                             for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
            outlined = RENDER_CLASS_OUTLINE.get(render_class)
            # Order of preference: what the CONSTRUCTION called a highlight
            # (the deepest lit offset an authored interior asked for) first,
            # then interior over border, then top-down and left-first.  An
            # outlined class darkens its whole border afterwards, so a
            # highlight placed there is painted over and the hat ends up with
            # no light step at all — which measures as a huge "highlight"
            # because the base colour is then the brightest thing in the frame.
            keep = set(sorted(keep, key=lambda c: (bool(outlined and c in border),
                                                   lighting[c],
                                                   c[1], c[0]))[:budget]) | spent
    else:
        lighting = base_lighting(sil, env)
        lit = sorted(c for c, v in lighting.items() if v < 0)
        keep = set(lit[: round(material.highlight_extent * len(lit))])

    steps: dict = {}
    for cell in sil:
        pc = paint.get(cell)
        if pc is None:
            continue
        protected = cell in art.point_accents.get(view, set()) or pc.role == "hardware"
        delta = occlusion.get(cell, 0)
        if not protected:
            lit_offset = lighting.get(cell, 0)
            if lit_offset < 0 and cell not in keep:
                lit_offset = 0
            delta += lit_offset
        steps[cell] = palette.shift(pc.role, pc.step, delta)

    colors = {c: palette.color(paint[c].role, s) for c, s in steps.items()}

    # --- contrast-aware selective edge treatment ---------------------------
    # Only FREE edges are candidates.  Attached edges never get a termination
    # just because two regions meet (section 33).  Where value contrast already
    # separates the regions we add nothing at all (section 34).
    #
    # Two-phase on purpose: every decision is read from the pre-pass colours and
    # applied afterwards.  Deciding and mutating in one pass makes the result
    # depend on iteration order, which shows up as a garment that is darker on
    # one side than the other for no authored reason.
    extra = 2 if material.edge_treatment == "crisp" else 1
    bumps: dict = {}
    for piece in construction.ordered():
        for cell in sorted(piece.free_edges.get(view, set())):
            if cell not in colors:
                continue
            for n in _neighbours(cell):
                if n not in colors or paint.get(n) is None:
                    continue
                if paint[n].feature == piece.name:
                    continue
                if n in art.point_accents.get(view, set()):
                    continue
                bump = 0
                probe = steps[n]
                while (abs(luminance(colors[cell]) - luminance(palette.color(paint[n].role, probe)))
                       < SEPARATION_SUFFICIENT and bump < extra):
                    nxt = palette.shift(paint[n].role, probe, 1)
                    if nxt == probe:
                        break
                    probe = nxt
                    bump += 1
                if bump > bumps.get(n, 0):
                    bumps[n] = bump
    for n, bump in bumps.items():
        steps[n] = palette.shift(paint[n].role, steps[n], bump)
        colors[n] = palette.color(paint[n].role, steps[n])

    # --- silhouette outline, per render class ------------------------------
    # A hat is a discrete object resting on the head and the corpus outlines it:
    # 117 of 120 vanilla hats have a border darker than their own interior
    # (median -59 luminance).  A shirt is part of the body and does the
    # opposite, which V5 asserts and tests.  Keyed by render class so neither
    # convention can leak into the other.
    if RENDER_CLASS_OUTLINE.get(render_class):
        border = [c for c in sil
                  if c in colors
                  and any((c[0] + dx, c[1] + dy) not in sil
                          for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        for cell in border:
            pc = paint.get(cell)
            if pc is None or cell in art.point_accents.get(view, set()):
                continue
            colors[cell] = palette.color(pc.role, palette.shift(pc.role, steps[cell], 2))

    return colors


def rasterize(spec, construction, art, render_class: str = "torso_8x8") -> dict:
    return {view: rasterize_view(spec, construction, art, view, render_class)
            for view in VIEWS}


def to_rows(colors: dict, env) -> list:
    return [[colors.get((x, y), TRANSPARENT) for x in range(env.width)]
            for y in range(env.height)]


def distinct_colors(raster: dict) -> set:
    return {c for view in raster.values() for c in view.values()}
