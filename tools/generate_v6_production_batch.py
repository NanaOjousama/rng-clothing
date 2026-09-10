#!/usr/bin/env python3
"""Generate the bounded 30-garment V6 production/evaluation batch."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, text_width, write_rgba_png
from generator.renderers.fashionsense.art_polish_v5e import polish_upper_frames
from generator.renderers.fashionsense.upper_v5b import _stack, render_fs_v5b
from generator.renderers.fashionsense.upper_v5c2 import render_fs_v5c2
from generator.renderers.fashionsense.upper_v5d import render_fs_v5d
from generator.renderers.fashionsense.structured_outerwear_v5e import render_fs_v5e
from generator.v2_recipe_engine import load_v2_data
from generator.v2_renderer import render_v2_recipe
from generator.v6 import generate_v6_batch, validate_v6_batch

OUT = ROOT / "output" / "v6-production-batch"
COMPARE = ROOT / "output" / "comparisons"
REPORTS = ROOT / "reports"
DIRECTIONS = ("front", "right", "back", "left")
BG: RGBA = (235, 227, 216, 255)
PANEL: RGBA = (211, 203, 191, 255)
INK: RGBA = (45, 42, 39, 255)
BORDER: RGBA = (73, 66, 60, 255)


@dataclass
class V6Rendered:
    entry: dict[str, Any]
    frames: dict[str, list[list[RGBA]]]
    texture: list[list[RGBA]]
    logical_size: int
    display_scale: int
    polish: dict[str, Any]
    quality: dict[str, Any]


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _slug(value: str) -> str:
    return "_".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())


def _luma(pixel: RGBA) -> float:
    return 0.2126 * pixel[0] + 0.7152 * pixel[1] + 0.0722 * pixel[2]


def _quality(frames: dict[str, list[list[RGBA]]], texture, logical_size: int) -> dict[str, Any]:
    pixels = [p for row in texture for p in row]
    alpha_values = sorted({p[3] for p in pixels})
    opaque = [p for p in pixels if p[3]]
    colors = {p[:3] for p in opaque}
    luminances = [_luma(p) for p in opaque]
    hashes = {d: hashlib.sha256(bytes(channel for row in frames[d] for pixel in row for channel in pixel)).hexdigest() for d in DIRECTIONS}
    direction_ok = hashes["front"] != hashes["back"] and hashes["front"] not in {hashes["right"], hashes["left"]}
    contrast = round(max(luminances) - min(luminances), 2) if luminances else 0
    return {
        "binaryAlpha": set(alpha_values) <= {0, 255},
        "alphaValues": alpha_values,
        "logicalSize": [logical_size, logical_size],
        "opaqueLogicalPixelsPerDirection": {d: sum(p[3] > 0 for row in frames[d] for p in row) for d in DIRECTIONS},
        "activeRgbColors": len(colors),
        "luminanceRange": contrast,
        "directionalReconstruction": direction_ok,
        "passesStaticArtGate": set(alpha_values) <= {0, 255} and direction_ok and contrast >= 45 and len(colors) <= (18 if logical_size == 16 else 12),
    }


def _render(entry: dict[str, Any]) -> V6Rendered:
    if entry["tier"] == "Common":
        render = render_v2_recipe(entry["recipe"], load_v2_data())
        quality = _quality(render.default_composites, render.native_pixels, 8)
        return V6Rendered(entry, render.default_composites, render.native_pixels, 8, 4, {
            "grammar": "VANILLA_V2_DISCIPLINED_EQUIVALENT",
            "postV5EShadeMutation": False,
            "reason": "Locked Common route must remain vanilla; equivalent silhouette/contrast/cluster gates apply without FS fields.",
        }, quality)

    kind = entry["renderKind"]
    raw = {"v5b": render_fs_v5b, "v5c2": render_fs_v5c2, "v5d": render_fs_v5d, "v5e": render_fs_v5e}[kind](entry["recipe"])
    base = raw if kind == "v5b" else raw.base
    polish = polish_upper_frames(base, raw.frames, raw.default_frames, article_family=entry["article"].upper().replace(" ", "_"))
    texture = _stack(polish.frames)
    quality = _quality(polish.default_frames, texture, 16)
    return V6Rendered(entry, polish.default_frames, texture, 16, 2, polish.metrics, quality)


def _tile(canvas, sprite, x: int, y: int) -> None:
    draw_rect(canvas, x - 2, y - 2, len(sprite[0]) + 4, len(sprite) + 4, BORDER)
    draw_rect(canvas, x - 1, y - 1, len(sprite[0]) + 2, len(sprite) + 2, PANEL)
    blit(canvas, sprite, x, y)


def _tier_sheet(title: str, rendered: list[V6Rendered]) -> list[list[RGBA]]:
    scale_size = 32; card_w = 166; card_h = 67; columns = 2
    rows = (len(rendered) + columns - 1) // columns
    canvas = blank_image(card_w * columns + 16, 34 + rows * card_h + 8, BG)
    draw_text(canvas, title, 8, 7, color=INK)
    for index, item in enumerate(rendered):
        col, row = index % columns, index // columns
        x0, y0 = 8 + col * card_w, 34 + row * card_h
        draw_text(canvas, f"{index + 1:02d} {item.entry['name'][:22].upper()}", x0, y0, color=INK)
        draw_text(canvas, item.entry["article"][:25].upper(), x0, y0 + 11, color=INK)
        for d_index, direction in enumerate(DIRECTIONS):
            sprite = nearest_scale(item.frames[direction], item.display_scale)
            _tile(canvas, sprite, x0 + d_index * 39, y0 + 28)
    return canvas


def _combined_sheet(rendered: list[V6Rendered]) -> list[list[RGBA]]:
    columns = 6; card_w = 104; card_h = 63; rows = 5
    canvas = blank_image(columns * card_w + 12, 35 + rows * card_h + 8, BG)
    draw_text(canvas, "V6 THIRTY GARMENTS - EXACT 32PX GAMEPLAY FOOTPRINT", 8, 7, color=INK)
    for index, item in enumerate(rendered):
        col, row = index % columns, index // columns
        x0, y0 = 8 + col * card_w, 35 + row * card_h
        draw_text(canvas, f"{item.entry['tier'].upper()} {index + 1:02d}", x0, y0, color=INK)
        draw_text(canvas, item.entry["name"][:15].upper(), x0, y0 + 11, color=INK)
        _tile(canvas, nearest_scale(item.frames["front"], item.display_scale), x0 + 30, y0 + 27)
    return canvas


def _directions_sheet(item: V6Rendered, scale: int) -> list[list[RGBA]]:
    size = item.logical_size * scale; gap = 14; margin = 12; top = 38
    canvas = blank_image(margin * 2 + size * 4 + gap * 3, top + size + 12, BG)
    draw_text(canvas, item.entry["name"].upper(), 7, 6, color=INK)
    draw_text(canvas, "FRONT | RIGHT | BACK | LEFT", 7, 18, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = margin + index * (size + gap)
        _tile(canvas, nearest_scale(item.frames[direction], scale), x, top)
    return canvas


def _markdown_table(rendered: list[V6Rendered]) -> str:
    rows = ["| # | Tier | Name | Article | Renderer | Primary design | Palette |", "|---:|---|---|---|---|---|---|"]
    for index, item in enumerate(rendered, 1):
        e = item.entry
        rows.append(f"| {index} | {e['tier']} | {e['name']} | {e['article']} | {e['sourceEngine']} | {e['axes']['primary']} | {e['axes']['palette']} |")
    return "\n".join(rows)


def main() -> None:
    batch = generate_v6_batch(); semantic = validate_v6_batch(batch["entries"])
    rendered = [_render(entry) for entry in batch["entries"]]
    if not all(item.quality["passesStaticArtGate"] for item in rendered):
        failed = [item.entry["id"] for item in rendered if not item.quality["passesStaticArtGate"]]
        raise ValueError(f"V6 static art gate rejected {failed}")
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True); COMPARE.mkdir(parents=True, exist_ok=True); REPORTS.mkdir(parents=True, exist_ok=True)
    for item in rendered:
        tier_dir = item.entry["tier"].lower().replace("+", "-plus")
        target = OUT / tier_dir / _slug(item.entry["name"])
        target.mkdir(parents=True)
        write_rgba_png(target / "native-texture.png", item.texture)
        write_rgba_png(target / "directions-nearest.png", _directions_sheet(item, 8 if item.logical_size == 8 else 6))
        write_rgba_png(target / "gameplay-footprint.png", _directions_sheet(item, item.display_scale))
        _json(target / "summary.json", {**item.entry, "polish": item.polish, "quality": item.quality})

    common = [item for item in rendered if item.entry["tier"] == "Common"]
    uncommon = [item for item in rendered if item.entry["tier"] == "Uncommon"]
    rare = [item for item in rendered if item.entry["tier"] == "Rare+"]
    write_rgba_png(COMPARE / "V6_COMMON_CONTACT.png", _tier_sheet("V6 COMMON - VANILLA 8X8 AT 4X", common))
    write_rgba_png(COMPARE / "V6_UNCOMMON_CONTACT.png", _tier_sheet("V6 UNCOMMON - FS 16X16 AT 2X", uncommon))
    write_rgba_png(COMPARE / "V6_RARE_PLUS_CONTACT.png", _tier_sheet("V6 RARE PLUS - PREMIUM FS 16X16 AT 2X", rare))
    write_rgba_png(COMPARE / "V6_GAMEPLAY_SIZE_30.png", _combined_sheet(rendered))

    table_records = [{
        "index": index, "id": item.entry["id"], "tier": item.entry["tier"], "name": item.entry["name"],
        "article": item.entry["article"], "renderer": item.entry["sourceEngine"], "axes": item.entry["axes"],
        "logicalSize": item.logical_size, "displayScale": item.display_scale, "quality": item.quality,
    } for index, item in enumerate(rendered, 1)]
    _json(OUT / "design-rarity-table.json", table_records)
    _json(OUT / "recipes.json", batch)
    _json(OUT / "validation.json", {
        "status": "PASS_STATIC_HUMAN_SELECTION_REQUIRED", "counts": semantic.metrics["tierCounts"],
        "diversity": semantic.metrics, "warnings": list(semantic.warnings),
        "artGateFailures": [], "runtimeStatus": "NOT_BATCH_TESTED", "productionPromotion": "NONE_AUTOMATIC",
    })

    strongest = [
        "v6-common-02", "v6-common-04", "v6-common-05", "v6-common-08", "v6-common-11",
        "v6-uncommon-02", "v6-uncommon-03", "v6-uncommon-04", "v6-uncommon-05",
        "v6-uncommon-07", "v6-uncommon-08", "v6-uncommon-09", "v6-uncommon-10", "v6-uncommon-11",
        "v6-rareplus-02", "v6-rareplus-03", "v6-rareplus-04", "v6-rareplus-05", "v6-rareplus-06",
    ]
    promising = [item.entry["id"] for item in rendered if item.entry["id"] not in strongest]
    by_id = {item.entry["id"]: item.entry for item in rendered}
    ranking = {
        "strongest": [{"id": rid, "name": by_id[rid]["name"]} for rid in strongest],
        "promisingButNeedsPolish": [{"id": rid, "name": by_id[rid]["name"]} for rid in promising],
        "rejectFromFinalExport": [],
        "rejectedBeforeFinalExport": [
            {"name": "Rainline Zip Hoodie", "reason": "collapsed to a zipped shirt at exact gameplay footprint"},
            {"name": "duplicate Common sweater candidate", "reason": "same fit, neckline, ribbing, and panel grammar with only palette change"},
            {"name": "duplicate Common button-shirt candidate", "reason": "same silhouette, placket, lower band, and construction with only palette change"},
        ],
    }
    _json(OUT / "self-ranking.json", ranking)

    table_md = "# V6 Design and Rarity Table\n\n" + _markdown_table(rendered) + "\n"
    (REPORTS / "V6_DESIGN_RARITY_TABLE.md").write_text(table_md, encoding="utf-8")
    (REPORTS / "V6_DIVERSITY_REJECTION_REPORT.md").write_text(
        "# V6 Diversity and Rejection Report\n\n"
        f"The final batch contains 12 Common, 12 Uncommon, and 6 Rare+ garments. The maximum within-tier eight-axis similarity is **{semantic.metrics['maximumWithinTierSimilarity']:.3f}**. "
        "Common permits a slightly higher similarity ceiling because its locked brief intentionally excludes garment-category creep and decorative systems; it still varies fit, neckline, panel split, hem treatment, palette, and primary construction.\n\n"
        "## Diversity evidence\n\n" + "\n".join(f"- {axis}: {count} distinct values" for axis, count in semantic.metrics["uniqueAxisCounts"].items()) +
        f"\n- Center-panel dominance: {semantic.metrics['centerPanelCount']} of 30.\n- Exact duplicate names or semantic signatures: none.\n- Rejected before final export: Rainline Zip Hoodie (read as a zipped shirt at 32px), one duplicate-prone Common sweater, and one duplicate-prone Common button shirt.\n- Final exported static rejects: none.\n\n"
        "## Gate boundaries\n\nAll 30 pass binary-alpha, value-contrast, palette-restraint, and front/side/back reconstruction checks. These are guardrails, not proof of beauty. No batch garment is promoted to production or runtime pass automatically.\n",
        encoding="utf-8",
    )
    report = """# V6 Production Batch and Quality Gate

## Outcome

V6 generated exactly 30 deterministic garments under the locked renderer split: 12 Common vanilla shirts, 12 Uncommon single/simple Fashion Sense articles, and 6 Rare+ premium Fashion Sense garments. No event, reward, installation, or runtime integration was added.

All exported garments pass the static direct-pixel, binary-alpha, value-contrast, palette-restraint, direction-reconstruction, and batch-diversity gates. Static passing is not a production promotion and does not replace live Farmer review.

## Rarity read

- **Common** stays deliberately small: 8x8 logical vanilla shirt art at the normal 4x display footprint. Variation comes from fit, neckline, placket/yoke/block construction, ribbing, and palette—not added garment categories.
- **Uncommon** moves to 16x16 Scale-2 Fashion Sense art. Its visible jump comes from collars, openings, layered fronts, knit bands, vest frames, jacket panels, and reconstructed side/back views.
- **Rare+** uses the strongest current article grammars at the same 32px footprint. Its premium read comes from construction hierarchy and coordinated regions rather than denser noise. The set intentionally does not consume future animation/VFX or maximal-layer headroom.

The equal-footprint sheet shows a credible tier jump, though rarity is clearest when comparing within related article roles rather than treating an intentionally bold Common color block as automatically inferior to every muted Rare+ palette.

## Visual review

The strongest Common pieces are Harbor Block Tee, Bluebell Fitted Tee, Hearth Ribbed Sweater, Cedar Placket Shirt, and Ivory Harbor Sail Top. Each communicates one compact idea immediately.

The strongest Uncommon pieces are Coralglass Club Shirt, Bluebell Ridge Knit, Fernpaw Relaxed Knit, Silver Reed Waistcoat, Rosewood Morning Cardigan, Cinderlane Moto Jacket, Night Relay Zip Jacket, Rosewake Sail Blouse, and Saffron Harbor Bomber. These best demonstrate that Uncommon is where article variety becomes visibly exciting.

The strongest Rare+ pieces are Midnight Laurel Blazer, Copperwick Gentleman Top, Amethyst Wayfarer Tunic, Emberward Tabard Armor, and Berry Static Cross-Zip Top. Their openings, focal regions, and silhouettes remain distinct without relying on palette alone.

Sunfield Pathfinder remains **promising but needs live art review**. Its native-arm attachment is frozen and proven, but the jacket/vest distinction depends partly on the assembled Farmer arms and therefore cannot be judged conclusively from the isolated shirt square. Cloudberry Pouch Hoodie is also promising rather than strongest: the pouch reads, but a simple single-layer Uncommon hood cannot match the Rare+ coordinated hood template.

Tidewire Rolled Shirt and Brassleaf Work Vest remain useful but less distinctive than their strongest same-tier siblings. Several Commons are intentionally plain and belong in the promising tier because their appeal depends on clean dye choices more than unique construction.

## Self-ranking

### Strongest

""" + "\n".join(f"- {by_id[rid]['name']} ({by_id[rid]['tier']})" for rid in strongest) + """

### Promising but needs polish or live review

""" + "\n".join(f"- {by_id[rid]['name']} ({by_id[rid]['tier']})" for rid in promising) + """

### Reject

- No garment in the final exported thirty is an automatic reject.
- Rainline Zip Hoodie was rejected before export because it read as a zipped shirt at gameplay size.
- Duplicate-prone Common sweater and button-shirt candidates were rerolled before export.

## Critical limitations

- This is still a static production-candidate batch. It does not prove animation, dye behavior, or assembled gameplay appeal for every item.
- Uncommon long-sleeve intent uses the safe native Farmer sleeve path in future runtime packaging; the rejected custom Sleeves atlas remains excluded.
- Some simple articles remain dependent on palette choice. They pass the basic-shirt brief but are not the first production candidates.
- Post-V5E polish improves edge roles and contrast but cannot turn a weak semantic concept into a strong garment. The pre-export Rainline rejection demonstrates that the human gameplay-footprint gate is still necessary.

## Recommendation

Use the strongest list as the first candidate pool, then select a smaller cross-tier subset for live Farmer screenshots. Do not package all thirty for production before that review.
"""
    (REPORTS / "V6_PRODUCTION_BATCH_REPORT.md").write_text(report, encoding="utf-8")
    print(f"Generated V6 production batch: {len(rendered)} garments")
    print(OUT); print(COMPARE)


if __name__ == "__main__": main()
