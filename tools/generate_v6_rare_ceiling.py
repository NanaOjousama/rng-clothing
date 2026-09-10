#!/usr/bin/env python3
"""Render and document the six-garment Rare ceiling calibration batch."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, write_rgba_png
from generator.renderers.fashionsense.art_polish_v5e import polish_upper_frames
from generator.renderers.fashionsense.upper_v5b import _stack
from generator.renderers.fashionsense.upper_v5d import render_fs_v5d
from generator.v6 import generate_rare_ceiling_batch, validate_rare_ceiling_batch

OUT = ROOT / "output" / "fashionsense" / "v6-rare-ceiling"
COMPARE = ROOT / "output" / "comparisons"
REPORTS = ROOT / "reports"
DIRECTIONS = ("front", "right", "back", "left")
BG: RGBA = (235, 227, 216, 255)
PANEL: RGBA = (211, 203, 191, 255)
INK: RGBA = (45, 42, 39, 255)
BORDER: RGBA = (73, 66, 60, 255)


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _slug(value: str) -> str:
    return "_".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())


def _tile(canvas, sprite, x: int, y: int) -> None:
    draw_rect(canvas, x - 2, y - 2, len(sprite[0]) + 4, len(sprite) + 4, BORDER)
    draw_rect(canvas, x - 1, y - 1, len(sprite[0]) + 2, len(sprite) + 2, PANEL)
    blit(canvas, sprite, x, y)


def _sheet(title: str, rendered, scale: int, columns: int = 2):
    size = 16 * scale; card_w = size * 4 + 54; card_h = size + 49
    rows = (len(rendered) + columns - 1) // columns
    canvas = blank_image(card_w * columns + 12, 32 + card_h * rows + 8, BG)
    draw_text(canvas, title, 8, 7, color=INK)
    for index, item in enumerate(rendered):
        col, row = index % columns, index // columns
        x0, y0 = 8 + col * card_w, 32 + row * card_h
        draw_text(canvas, f"{index + 1:02d} {item['entry']['name'][:27].upper()}", x0, y0, color=INK)
        draw_text(canvas, item["entry"]["garmentFamily"].upper(), x0, y0 + 11, color=INK)
        for d_index, direction in enumerate(DIRECTIONS):
            x = x0 + d_index * (size + 12)
            draw_text(canvas, direction[:1].upper(), x + size // 2, y0 + 22, color=INK)
            _tile(canvas, nearest_scale(item["frames"][direction], scale), x, y0 + 36)
    return canvas


def _table(entries) -> str:
    rows = ["| Garment | Family | Construction complexity | Why Rare rather than Legendary |", "|---|---|---|---|"]
    for entry in entries:
        rows.append(f"| {entry['name']} | {entry['garmentFamily']} | {entry['constructionComplexity']} | {entry['whyRareNotLegendary']} |")
    return "\n".join(rows)


def main() -> None:
    batch = generate_rare_ceiling_batch(); validation = validate_rare_ceiling_batch(batch["entries"])
    rendered = []
    for entry in batch["entries"]:
        raw = render_fs_v5d(entry["recipe"])
        polished = polish_upper_frames(raw.base, raw.frames, raw.default_frames, article_family=entry["garmentFamily"].upper().replace(" ", "_"))
        texture = _stack(polished.frames)
        alpha = sorted({p[3] for row in texture for p in row})
        if any(value not in {0, 255} for value in alpha): raise ValueError(f"{entry['name']}: non-binary alpha")
        rendered.append({"entry": entry, "frames": polished.default_frames, "texture": texture, "polish": polished.metrics, "alpha": alpha})

    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True); COMPARE.mkdir(parents=True, exist_ok=True); REPORTS.mkdir(parents=True, exist_ok=True)
    for item in rendered:
        target = OUT / _slug(item["entry"]["name"]); target.mkdir(parents=True)
        write_rgba_png(target / "shirt.png", item["texture"])
        write_rgba_png(target / "directions-6x.png", _sheet(item["entry"]["name"].upper(), [item], 6, 1))
        write_rgba_png(target / "gameplay-size.png", _sheet(item["entry"]["name"].upper() + " - 32PX", [item], 2, 1))
        _json(target / "summary.json", {
            **item["entry"], "recipe": item["entry"]["recipe"], "postV5EPolish": item["polish"],
            "runtimeAssembly": {"Shirt": True, "nativeSleevesViaSleeveColors": True, "customSleevesAtlas": False, "Hat": False, "Accessory": False, "stateBehavior": False},
            "status": "STATIC_PASS_RUNTIME_NOT_TESTED",
        })

    write_rgba_png(COMPARE / "V6_RARE_CEILING_CONTACT.png", _sheet("V6 RARE CEILING - ENLARGED DIRECT PIXELS", rendered, 4))
    write_rgba_png(COMPARE / "V6_RARE_CEILING_GAMEPLAY.png", _sheet("V6 RARE CEILING - EXACT 32PX GAMEPLAY FOOTPRINT", rendered, 2))
    _json(OUT / "recipes.json", batch)
    _json(OUT / "validation.json", {
        "status": "PASS_STATIC_HUMAN_CEILING_REVIEW_REQUIRED", "semantic": validation.metrics,
        "allPostV5EPolished": True, "allBinaryAlpha": True, "customSleevesExported": False,
        "runtime": "NOT_TESTED", "legendaryGenerationStarted": False,
    })
    (REPORTS / "V6_RARE_CEILING_TABLE.md").write_text("# V6 Rare Ceiling Table\n\n" + _table(batch["entries"]) + "\n", encoding="utf-8")
    print("Generated six Rare ceiling calibration garments")
    print(OUT); print(COMPARE)


if __name__ == "__main__": main()
