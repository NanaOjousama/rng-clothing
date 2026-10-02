#!/usr/bin/env python3
"""Build all crown_brim variants, validate them, and write previews.

    python3 prototypes/hat_recipe_engine_01/build.py

Outputs (prototypes/hat_recipe_engine_01/out/):
    <variant>.template.json      region + role maps per view, params, view rules
    <variant>_20x80.png          preview-palette strip, vanilla hats.png order
    CONTACT_SHEET.png            templates (roles / regions / 4 palettes) next to nearest references
    WORN_PREVIEW.png             offline worn preview at 1x / 2x / 4x, each hat above its references
    COMPARE_6X.png               head-crop pairs: generated (row) above references (rows below it)
    validation.json              every check, every number

Exit status is non-zero if any hard check fails.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from engine import build_template, serialise  # noqa: E402
from preview import (PALETTES, blank_image, blit, draw_text, mod_bank, nearest_scale,  # noqa: E402
                     render_strip, vanilla_bank, vanilla_strip, worn_row)
from validate import validate_all  # noqa: E402

from v5.pngio import write_rgba_png  # noqa: E402

OUT = HERE / "out"
BG = (58, 58, 68, 255)
LABEL = (230, 230, 230, 255)
NEAREST = {"bucket": 102, "fisherman": 55, "sun": 4}


def load_variants():
    recipe = json.loads((HERE / "recipes/crown_brim.json").read_text())
    out = {}
    for name, v in recipe["variants"].items():
        p = dict(recipe["defaults"])
        p.update(v["params"])
        v.setdefault("preview_palette", "olive")
        out[name] = (p, v)
    return recipe, out


def _strip_h(strip):
    """20x80 vertical -> 80x20 horizontal (front right left back)."""
    out = blank_image(86, 20)
    for i in range(4):
        blit(out, strip[i * 20:(i + 1) * 20], i * 22, 0)
    return out


def contact_sheet(tpls, refs):
    s = 6
    cols = ["ROLES", "REGIONS", "OLIVE", "DENIM", "STRAW", "CHARCOAL"]
    cell_w, cell_h = 86 * s + 24, 20 * s + 40
    rows = list(tpls) + ["REF"]
    sheet = blank_image(len(cols) * cell_w + 20, len(tpls) * cell_h * 1 + 3 * cell_h + 60, BG)
    for ci, c in enumerate(cols):
        draw_text(sheet, c, 20 + ci * cell_w, 10, scale=3, color=LABEL)
    for ri, (name, tpl) in enumerate(tpls.items()):
        y = 50 + ri * cell_h
        strips = [render_strip(tpl, mode="roles"), render_strip(tpl, mode="regions")] + \
                 [render_strip(tpl, pal) for pal in PALETTES]
        for ci, st in enumerate(strips):
            blit(sheet, nearest_scale(_strip_h(st), s), 20 + ci * cell_w, y + 26)
        draw_text(sheet, name.upper(), 20, y + 4, scale=3, color=LABEL)
    y0 = 50 + len(tpls) * cell_h + 10
    draw_text(sheet, "NEAREST REFERENCES (EVIDENCE ONLY - NOT COMPOSED)", 20, y0, scale=3, color=LABEL)
    for k, (label, st) in enumerate(refs):
        x = 20 + (k % 3) * (cell_w * 2)
        y = y0 + 40 + (k // 3) * cell_h
        draw_text(sheet, label.upper(), x, y, scale=2, color=LABEL)
        blit(sheet, nearest_scale(_strip_h(st), s), x, y + 20)
    return sheet


def worn_sheet(tpls, metas, refs):
    """Each generated hat (matched preview palette) directly above its references.

    Left block: native 1x, the scale that matters.  Middle: 2x.  Right: Stardew's
    normal 4x zoom.  Offline composite, not a QC Bridge capture."""
    ref = dict(refs)
    order = [("bucket", ["vanilla bucket hat (102)"]),
             ("fisherman", ["vanilla fishing hat (55)"]),
             ("sun", ["plurffle straw hat", "plurffle sun hat", "vanilla straw hat (4)"])]
    rows = []
    for name, rnames in order:
        if name in tpls:
            rows.append((f"{name.upper()} (GENERATED)", render_strip(tpls[name], metas[name]["preview_palette"])))
            rows += [(r.upper(), ref[r]) for r in rnames if r in ref]
    game = blank_image(96, 40 * len(rows), (126, 150, 110, 255))
    for i, (_, st) in enumerate(rows):
        blit(game, worn_row(st), 0, i * 40)
    x2, x4 = nearest_scale(game, 2), nearest_scale(game, 4)
    w = 20 + 96 + 30 + len(x2[0]) + 30 + len(x4[0]) + 20
    sheet = blank_image(w, len(x4) + 70, BG)
    xs = [20, 20 + 96 + 30, 20 + 96 + 30 + len(x2[0]) + 30]
    for x, img, lab in zip(xs, (game, x2, x4), ("1X NATIVE", "2X", "4X - NORMAL ZOOM")):
        draw_text(sheet, lab, x, 12, scale=2, color=LABEL)
        blit(sheet, img, x, 50)
    for i, (lab, _) in enumerate(rows):
        draw_text(sheet, lab, xs[2] + 6, 50 + i * 160 + 4, scale=2, color=(20, 30, 20, 255))
    return sheet


def compare_sheet(tpls, metas, refs, scale=6):
    """Head-crop pairs: each generated hat (matched palette) directly above its references."""
    ref = dict(refs)
    rows = []
    for name, rnames in (("bucket", ["vanilla bucket hat (102)"]), ("fisherman", ["vanilla fishing hat (55)"]),
                         ("sun", ["plurffle straw hat", "plurffle sun hat", "vanilla straw hat (4)"])):
        rows.append(render_strip(tpls[name], metas[name]["preview_palette"]))
        rows += [ref[r] for r in rnames if r in ref]
    out = blank_image(86 + 100, 24 * len(rows), (150, 150, 160, 255))
    for i, st in enumerate(rows):
        blit(out, _strip_h(st), 0, i * 24 + 2)
        blit(out, [r[:96] for r in worn_row(st)[0:24]], 88, i * 24)
    return nearest_scale(out, scale)


def main():
    recipe, variants = load_variants()
    OUT.mkdir(exist_ok=True)
    tpls = {}
    for name, (p, meta) in variants.items():
        tpl = build_template(p)
        tpls[name] = tpl
        data = serialise(tpl, f"crown_brim/{name}")
        data["identity"] = meta["identity"]
        data["nearest_references"] = meta["nearest_references"]
        (OUT / f"{name}.template.json").write_text(json.dumps(data, indent=1) + "\n")
        write_rgba_png(OUT / f"{name}_20x80.png", render_strip(tpl, meta["preview_palette"]))

    bank = vanilla_bank()
    bank.update(mod_bank())
    report = validate_all(tpls, bank)
    (OUT / "validation.json").write_text(json.dumps(report, indent=1) + "\n")

    refs = [(f"vanilla {n} ({i})", vanilla_strip(i)) for n, i in
            (("bucket hat", 102), ("fishing hat", 55), ("straw hat", 4))]
    refs += [(k.replace(":", " ").lower(), v) for k, v in mod_bank().items()]
    write_rgba_png(OUT / "CONTACT_SHEET.png", contact_sheet(tpls, refs))
    metas = {n: m for n, (_, m) in variants.items()}
    write_rgba_png(OUT / "WORN_PREVIEW.png", worn_sheet(tpls, metas, refs))
    write_rgba_png(OUT / "COMPARE_6X.png", compare_sheet(tpls, metas, refs))

    failed = [f"{v}:{c}" for v, r in report["variants"].items()
              for c, res in r["checks"].items() if res["hard"] and not res["pass"]]
    failed += [c for c, res in report["family"].items() if res["hard"] and not res["pass"]]
    for v, r in report["variants"].items():
        print(f"{v:10s}", "  ".join(f"{c}={'PASS' if res['pass'] else 'FAIL'}"
                                    for c, res in r["checks"].items()))
    for c, res in report["family"].items():
        print(f"family     {c}={'PASS' if res['pass'] else 'FAIL'}  {res.get('detail', '')}")
    print("hard failures:", failed or "none")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
