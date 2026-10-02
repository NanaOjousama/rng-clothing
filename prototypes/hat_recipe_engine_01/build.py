#!/usr/bin/env python3
"""Build all crown_brim variants, validate them, and write previews.

    python3 prototypes/hat_recipe_engine_01/build.py

Outputs (prototypes/hat_recipe_engine_01/out/):
    <variant>.template.json      region + role maps per view, params, view rules
    <variant>_20x80.png          preview-palette strip, vanilla hats.png order
    CONTACT_SHEET.png            templates (roles / regions / 4 palettes) next to nearest references
    WORN_PREVIEW.png             offline worn preview, 1x game zoom x4 and close-up, with vanilla neighbours
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


def worn_sheet(tpls, refs):
    """Top: every row at Stardew's normal 4x zoom (judge here).  Bottom: 1x actual pixels."""
    rows = [(n, render_strip(t, pal)) for n, t in tpls.items()
            for pal in ("olive", "straw")] + refs
    game = blank_image(96 * 2, 40 * ((len(rows) + 1) // 2), (126, 150, 110, 255))
    for i, (_, st) in enumerate(rows):
        blit(game, worn_row(st), (i % 2) * 96, (i // 2) * 40)
    big = nearest_scale(game, 4)
    sheet = blank_image(len(big[0]) + 40 + len(game[0]) + 20, len(big) + 80, BG)
    draw_text(sheet, "WORN - 4X (NORMAL ZOOM)", 20, 10, scale=3, color=LABEL)
    blit(sheet, big, 20, 50)
    draw_text(sheet, "1X", len(big[0]) + 40, 10, scale=3, color=LABEL)
    blit(sheet, game, len(big[0]) + 40, 50)
    labels = [f"{n.upper()} {pal.upper()}" for n in tpls for pal in ("olive", "straw")] + \
             [l.upper() for l, _ in refs]
    for i, l in enumerate(labels):
        draw_text(sheet, l, 20 + (i % 2) * 96 * 4 + 4, 50 + (i // 2) * 160 + 2, scale=2, color=(20, 30, 20, 255))
    return sheet


def main():
    recipe, variants = load_variants()
    OUT.mkdir(exist_ok=True)
    tpls = {}
    for name, (p, meta) in variants.items():
        tpl = build_template(p)
        tpls[name] = tpl
        data = serialise(tpl, f"crown_brim/{name}")
        data["identity"] = meta["identity"]
        data["nearest_vanilla"] = meta["nearest_vanilla"]
        (OUT / f"{name}.template.json").write_text(json.dumps(data, indent=1) + "\n")
        write_rgba_png(OUT / f"{name}_20x80.png", render_strip(tpl, "olive"))

    bank = vanilla_bank()
    bank.update(mod_bank())
    report = validate_all(tpls, bank)
    (OUT / "validation.json").write_text(json.dumps(report, indent=1) + "\n")

    refs = [(f"vanilla {n} ({i})", vanilla_strip(i)) for n, i in
            (("bucket hat", 102), ("fishing hat", 55), ("straw hat", 4))]
    refs += [(k.replace(":", " "), v) for k, v in mod_bank().items()]
    write_rgba_png(OUT / "CONTACT_SHEET.png", contact_sheet(tpls, refs))
    write_rgba_png(OUT / "WORN_PREVIEW.png", worn_sheet(tpls, refs[:3]))

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
