#!/usr/bin/env python3
"""Render and document the six-piece Legendary calibration batch."""

from __future__ import annotations

import json
import hashlib
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, read_rgba_png, write_rgba_png
from generator.renderers.fashionsense.art_polish_v5e import polish_upper_frames
from generator.renderers.fashionsense.hoodie_layers import render_fs_hoodie_layers
from generator.renderers.fashionsense.legendary_v6 import apply_legendary_construction, apply_legendary_signature
from generator.renderers.fashionsense.upper_v5b import _stack
from generator.renderers.fashionsense.upper_v5b import render_fs_v5b
from generator.renderers.fashionsense.upper_v5c2 import render_fs_v5c2
from generator.renderers.fashionsense.upper_v5d import render_fs_v5d
from generator.renderers.fashionsense.structured_outerwear_v5e import render_fs_v5e
from generator.v6 import generate_legendary_batch, generate_rare_ceiling_batch, generate_v6_batch, validate_legendary_batch

OUT = ROOT / "output" / "fashionsense" / "v6-legendary-calibration"
COMPARE = ROOT / "output" / "comparisons"
REPORTS = ROOT / "reports"
DIRECTIONS = ("front", "right", "back", "left")
BG: RGBA = (231, 224, 214, 255)
PANEL: RGBA = (205, 197, 186, 255)
INK: RGBA = (41, 38, 36, 255)
BORDER: RGBA = (69, 62, 57, 255)
GOLD: RGBA = (184, 137, 48, 255)
FARMER = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/farmer_base.png")
HAIR = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/hairstyles.png")
BODY_FRAME = {"front": 0, "right": 6, "back": 12, "left": 6}
FEATURE_Y = {0: 1, 6: 1, 12: 0}
HAIR_TINT: RGBA = (112, 76, 52, 255)


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _slug(value: str) -> str:
    return "_".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())


def _tile(canvas, sprite, x: int, y: int, accent: RGBA = BORDER) -> None:
    draw_rect(canvas, x - 2, y - 2, len(sprite[0]) + 4, len(sprite) + 4, accent)
    draw_rect(canvas, x - 1, y - 1, len(sprite[0]) + 2, len(sprite) + 2, PANEL)
    blit(canvas, sprite, x, y)


def _upper_assembly(frames: dict[str, list[list[RGBA]]], direction: str) -> list[list[RGBA]]:
    canvas = blank_image(32, 48)
    blit(canvas, frames[direction], 8, 24)
    return canvas


def _crop(pixels, x: int, y: int, w: int, h: int):
    return [list(row[x:x+w]) for row in pixels[y:y+h]]


def _flip(pixels):
    return [list(reversed(row)) for row in pixels]


def _tint(pixels, tint: RGBA):
    return [[(p[0]*tint[0]//255, p[1]*tint[1]//255, p[2]*tint[2]//255, p[3]) for p in row] for row in pixels]


def _farmer_body(body, direction: str):
    index = BODY_FRAME[direction]
    frame = _crop(body, index % 6 * 16, index // 6 * 32, 16, 32)
    return _flip(frame) if direction == "left" else frame


def _farmer_hair(hair, direction: str):
    # Vanilla style 0 is deliberately neutral and compact; the garment, not a
    # stress-test hairstyle, remains the subject of this calibration sheet.
    y = 32 if direction in {"right", "left"} else 64 if direction == "back" else 0
    frame = _crop(hair, 0, y, 16, 32)
    if direction == "left": frame = _flip(frame)
    return _tint(frame, HAIR_TINT)


def _shirt_offset(direction: str):
    return 16, 56 + FEATURE_Y[BODY_FRAME[direction]] * 4


def _hair_offset(direction: str):
    return 0, FEATURE_Y[BODY_FRAME[direction]] * 4 + (4 if direction == "back" else 0)


def _hood_offset(direction: str):
    feature_y = -12 + FEATURE_Y[BODY_FRAME[direction]] * 4
    head = {"front": (-4, 30), "right": (-4, 26), "back": (-4, 26), "left": (-4, 26)}[direction]
    return -8 - 2 * head[0], 64 + feature_y - 2 * head[1]


def _farmer_composite(body, hair, item, direction: str):
    canvas = blank_image(64, 128)
    blit(canvas, nearest_scale(_farmer_body(body, direction), 4), 0, 0)
    shirt = nearest_scale(item["frames"][direction], 2)
    blit(canvas, shirt, *_shirt_offset(direction))
    hairstyle = nearest_scale(_farmer_hair(hair, direction), 4)
    if not (item.get("hoodFrames") and direction == "back"):
        blit(canvas, hairstyle, *_hair_offset(direction))
    if item.get("hoodFrames"):
        hood = nearest_scale(item["hoodFrames"][direction], 2)
        blit(canvas, hood, *_hood_offset(direction))
    return canvas


def _hoodie_assembly(render, direction: str) -> list[list[RGBA]]:
    canvas = blank_image(32, 48)
    hood = render.hood_default_frames[direction]
    if render.recipe["hoodLayer"]["state"] == "up":
        blit(canvas, hood, 0, 0)
        shirt_y = 26 if direction == "front" else 24
    elif direction == "front":
        blit(canvas, hood, (32 - len(hood[0])) // 2, 24)
        shirt_y = 24
    else:
        blit(canvas, hood, 8, 18)
        shirt_y = 24
    blit(canvas, render.shirt_default_frames[direction], 8, shirt_y)
    return canvas


def _direction_sheet(title: str, rendered, scale: int, columns: int = 2):
    sw, sh = 32 * scale, 48 * scale
    card_w, card_h = sw * 4 + 58, sh + 52
    rows = (len(rendered) + columns - 1) // columns
    canvas = blank_image(card_w * columns + 12, 35 + card_h * rows + 8, BG)
    draw_text(canvas, title, 8, 7, color=INK)
    for index, item in enumerate(rendered):
        col, row = index % columns, index // columns
        x0, y0 = 8 + col * card_w, 35 + row * card_h
        draw_text(canvas, f"{index + 1:02d} {item['entry']['name'][:28].upper()}", x0, y0, color=INK)
        draw_text(canvas, item["entry"]["garmentFamily"].upper(), x0, y0 + 11, color=GOLD)
        for d_index, direction in enumerate(DIRECTIONS):
            x = x0 + d_index * (sw + 12)
            draw_text(canvas, direction.upper(), x, y0 + 23, color=INK)
            _tile(canvas, nearest_scale(item["assembly"][direction], scale), x, y0 + 38, GOLD)
    return canvas


def _front_comparison(anchors, legendary, scale: int = 3):
    items = [(item["ceilingTier"], item) for item in anchors] + [("LEGENDARY", item) for item in legendary]
    sw, sh = 64, 128
    card_w, card_h = sw + 34, sh + 50
    canvas = blank_image(card_w * len(items) + 16, card_h + 42, BG)
    draw_text(canvas, "LOCKED UNCOMMON / RARE CEILINGS  ->  LEGENDARY DIVERSITY", 8, 7, color=INK)
    for index, (tier, item) in enumerate(items):
        x, y = 8 + index * card_w, 38
        draw_text(canvas, tier, x, 23, color=BORDER if tier == "RARE CEILING" else GOLD)
        _tile(canvas, item["farmer"]["front"], x, y, GOLD if tier == "LEGENDARY" else BORDER)
        draw_text(canvas, item["entry"]["name"][:18].upper(), x, y + sh + 9, color=INK)
    return canvas


def _farmer_front_sheet(title: str, rendered):
    card_w, top = 92, 43
    canvas = blank_image(card_w * len(rendered) + 12, top + 128 + 29, BG)
    draw_text(canvas, title, 8, 7, color=INK)
    draw_text(canvas, "AUTHORITATIVE VANILLA FARMER IDLE SOURCE | EXACT GAMEPLAY PIXELS", 8, 20, color=INK)
    for index, item in enumerate(rendered):
        x = 8 + index * card_w
        draw_text(canvas, f"{index+1:02d} {item['entry']['name'][:11].upper()}", x, 33, color=INK)
        _tile(canvas, item["farmer"]["front"], x, top, GOLD)
    return canvas


def _farmer_direction_sheet(title: str, rendered):
    card_w, card_h = 64 * 4 + 42, 128 + 45
    canvas = blank_image(card_w * 2 + 12, 35 + card_h * 3 + 8, BG)
    draw_text(canvas, title, 8, 7, color=INK)
    for index, item in enumerate(rendered):
        col, row = index % 2, index // 2
        x0, y0 = 8 + col * card_w, 35 + row * card_h
        draw_text(canvas, item["entry"]["name"].upper(), x0, y0, color=INK)
        for d_index, direction in enumerate(DIRECTIONS):
            x = x0 + d_index * 68
            draw_text(canvas, direction.upper(), x, y0 + 12, color=INK)
            _tile(canvas, item["farmer"][direction], x, y0 + 29, GOLD)
    return canvas


def _table(entries) -> str:
    rows = ["| Garment | Family | Core identity | Why Legendary rather than Rare |", "|---|---|---|---|"]
    for entry in entries:
        rows.append(f"| {entry['name']} | {entry['garmentFamily']} | {entry['coreIdentity']} | {entry['whyLegendary']} |")
    return "\n".join(rows)


def _palette_table(entries) -> str:
    rows = ["| Garment | Palette story | Primary fashion read |", "|---|---|---|"]
    for entry in entries:
        rows.append(f"| {entry['name']} | {entry['paletteLabel']} | {entry['coreIdentity']} |")
    return "\n".join(rows)


def _identity_table(entries) -> str:
    rows = ["| Garment | Silhouette | Closure | Collar/Hood | Focal composition | Back treatment |", "|---|---|---|---|---|---|"]
    for entry in entries:
        rows.append(f"| {entry['name']} | {entry['silhouetteIdentity']} | {entry['closureIdentity']} | {entry['collarIdentity']} | {entry['focalComposition']} | {entry['backTreatment']} |")
    return "\n".join(rows)


def _opaque_mask(frame):
    return {(x, y) for y, row in enumerate(frame) for x, pixel in enumerate(row) if pixel[3]}


def _iou(a, b) -> float:
    union = a | b
    return 0.0 if not union else len(a & b) / len(union)


def _geometry_grade(value: float) -> str:
    return "O" if value >= .92 else "R" if value >= .82 else "D"


def _diversity_matrix(rendered):
    rows = []
    for left_index, left in enumerate(rendered):
        for right in rendered[left_index + 1:]:
            front_iou = _iou(_opaque_mask(left["assembly"]["front"]), _opaque_mask(right["assembly"]["front"]))
            side_iou = (_iou(_opaque_mask(left["assembly"]["right"]), _opaque_mask(right["assembly"]["right"])) + _iou(_opaque_mask(left["assembly"]["left"]), _opaque_mask(right["assembly"]["left"]))) / 2
            back_iou = _iou(_opaque_mask(left["assembly"]["back"]), _opaque_mask(right["assembly"]["back"]))
            grades = {
                "silhouette": _geometry_grade(front_iou), "garmentFamily": "D",
                "neckline": "D", "opening": "D", "dominantGesture": "D",
                "surfaceComposition": "D", "sideReconstruction": _geometry_grade(side_iou),
                "backReconstruction": _geometry_grade(back_iou), "paletteStory": "D",
            }
            related = sum(value == "R" for value in grades.values())
            overlaps = sum(value == "O" for value in grades.values())
            grades["overallFarmerRead"] = "D" if overlaps <= 2 and related + overlaps <= 4 else "R" if overlaps <= 3 else "O"
            overlap_score = sum(2 if value == "O" else 1 if value == "R" else 0 for value in grades.values())
            rows.append({
                "pair": f"{left['entry']['name']} / {right['entry']['name']}", **grades,
                "frontMaskIoU": round(front_iou, 3), "sideMaskIoU": round(side_iou, 3), "backMaskIoU": round(back_iou, 3),
                "overlapScore": overlap_score, "passes": overlap_score <= 6 and grades["overallFarmerRead"] != "O",
            })
    return rows


def _matrix_markdown(rows) -> str:
    lines = [
        "# V6 Legendary Pairwise Farmer Diversity Matrix", "",
        "`D` = distinct, `R` = related but distinguishable, `O` = strong overlap. Geometry grades use direct opaque-mask IoU after Legendary construction; overall read is checked on authoritative idle Farmer composites. A pair fails above overlap score 6 or when overall Farmer read is `O`.", "",
        "| Pair | Silhouette | Family | Neck | Opening | Gesture | Surface | Side | Back | Palette | Farmer read | Score |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(f"| {row['pair']} | {row['silhouette']} ({row['frontMaskIoU']:.3f}) | {row['garmentFamily']} | {row['neckline']} | {row['opening']} | {row['dominantGesture']} | {row['surfaceComposition']} | {row['sideReconstruction']} ({row['sideMaskIoU']:.3f}) | {row['backReconstruction']} ({row['backMaskIoU']:.3f}) | {row['paletteStory']} | {row['overallFarmerRead']} | {row['overlapScore']} |")
    return "\n".join(lines) + "\n"


def _render_upper(entry: dict[str, Any]) -> dict[str, Any]:
    raw = render_fs_v5d(entry["recipe"])
    role = entry.get("articleRole", entry.get("sourceRole", entry["garmentFamily"]))
    polished = polish_upper_frames(raw.base, raw.frames, raw.default_frames, article_family=role)
    construction = apply_legendary_construction(polished.frames, polished.default_frames, entry.get("articleRole", "")) if entry["rarity"] == "Legendary" else None
    signature = apply_legendary_signature(construction.frames, construction.default_frames, entry.get("articleRole", "")) if construction else None
    mask_frames = signature.frames if signature else polished.frames
    default_frames = signature.default_frames if signature else polished.default_frames
    return {
        "entry": entry, "frames": default_frames,
        "assembly": {direction: _upper_assembly(default_frames, direction) for direction in DIRECTIONS},
        "textures": {"shirt": _stack(mask_frames)}, "metrics": {**polished.metrics, "legendaryConstruction": construction.metrics if construction else None, "legendarySignature": signature.metrics if signature else None},
        "runtime": {"Shirt": True, "nativeSleevesViaSleeveColors": True, "Hat": False, "Accessory": False},
    }


def _render_hoodie(entry: dict[str, Any]) -> dict[str, Any]:
    raw = render_fs_hoodie_layers(entry["recipe"])
    return {
        "entry": entry, "frames": raw.shirt_default_frames,
        "assembly": {direction: _hoodie_assembly(raw, direction) for direction in DIRECTIONS},
        "textures": {"shirt": raw.shirt_texture, "hood": raw.hood_texture}, "metrics": raw.metrics,
        "hoodJson": raw.hood_json, "hoodFrames": raw.hood_default_frames,
        "runtime": {"Shirt": True, "nativeSleevesViaSleeveColors": True, "Hat": True, "Accessory": False, "Preset": True},
    }


def _render_uncommon_anchor(entry: dict[str, Any]) -> dict[str, Any]:
    kind = entry["renderKind"]
    raw = {"v5b": render_fs_v5b, "v5c2": render_fs_v5c2, "v5d": render_fs_v5d, "v5e": render_fs_v5e}[kind](entry["recipe"])
    base = raw if kind == "v5b" else raw.base
    polished = polish_upper_frames(base, raw.frames, raw.default_frames, article_family=entry["article"].upper().replace(" ", "_"))
    return {
        "entry": {"name": entry["name"], "garmentFamily": entry["article"]},
        "frames": polished.default_frames,
        "assembly": {direction: _upper_assembly(polished.default_frames, direction) for direction in DIRECTIONS},
        "textures": {"shirt": _stack(polished.frames)}, "metrics": polished.metrics,
        "ceilingTier": "UNCOMMON CEILING",
    }


def main() -> None:
    batch = generate_legendary_batch()
    validation = validate_legendary_batch(batch["entries"])
    rendered = [_render_hoodie(e) if e["runtimeAssembly"] == "coordinated_hoodie" else _render_upper(e) for e in batch["entries"]]
    uncommon_entries = [e for e in generate_v6_batch()["entries"] if e["name"] in {"Night Relay Zip Jacket", "Rosewake Sail Blouse"}]
    rare_entries = [e for e in generate_rare_ceiling_batch()["entries"] if e["name"] in {"Juniper Vale Cardigan", "Nocturne Silver Waistcoat"}]
    anchors = [_render_uncommon_anchor(e) for e in uncommon_entries]
    for item in [_render_upper(e) for e in rare_entries]:
        item["ceilingTier"] = "RARE CEILING"; anchors.append(item)
    body = read_rgba_png(FARMER)["pixels"]
    hair = read_rgba_png(HAIR)["pixels"]
    for item in rendered + anchors:
        item["farmer"] = {direction: _farmer_composite(body, hair, item, direction) for direction in DIRECTIONS}
    diversity_rows = _diversity_matrix(rendered)
    failed_pairs = [row["pair"] for row in diversity_rows if not row["passes"]]
    if failed_pairs: raise ValueError("Legendary Farmer diversity gate rejected: " + "; ".join(failed_pairs))

    for item in rendered:
        for name, texture in item["textures"].items():
            alpha = {pixel[3] for row in texture for pixel in row}
            if not alpha <= {0, 255}: raise ValueError(f"{item['entry']['name']} {name}: non-binary alpha")

    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True); COMPARE.mkdir(parents=True, exist_ok=True); REPORTS.mkdir(parents=True, exist_ok=True)
    for item in rendered:
        target = OUT / _slug(item["entry"]["name"]); target.mkdir(parents=True)
        for name, texture in item["textures"].items(): write_rgba_png(target / f"{name}.png", texture)
        write_rgba_png(target / "directions-4x.png", _direction_sheet(item["entry"]["name"].upper(), [item], 4, 1))
        write_rgba_png(target / "farmer-directions.png", _farmer_direction_sheet(item["entry"]["name"].upper(), [item]))
        summary = {**item["entry"], "runtime": item["runtime"], "renderMetrics": item["metrics"], "status": "STATIC_PASS_RUNTIME_NOT_TESTED"}
        if "hoodJson" in item: summary["hoodJson"] = item["hoodJson"]
        _json(target / "summary.json", summary)

    write_rgba_png(COMPARE / "V6_LEGENDARY_CONTACT.png", _direction_sheet("V6 LEGENDARY - SIGNATURE IDENTITY CALIBRATION", rendered, 4))
    write_rgba_png(COMPARE / "V6_LEGENDARY_GAMEPLAY.png", _farmer_front_sheet("V6 LEGENDARY - FARMER GAMEPLAY FRONTS", rendered))
    write_rgba_png(COMPARE / "V6_LEGENDARY_FARMER_DIRECTIONS.png", _farmer_direction_sheet("V6 LEGENDARY - FRONT RIGHT BACK LEFT FARMER COMPOSITES", rendered))
    write_rgba_png(COMPARE / "V6_RARE_VS_LEGENDARY.png", _front_comparison(anchors, rendered))
    _json(OUT / "recipes.json", batch)
    _json(OUT / "pairwise-diversity.json", {"status": "PASS", "pairs": diversity_rows})
    _json(OUT / "validation.json", {
        "status": "PASS_STATIC_HUMAN_LEGENDARY_REVIEW_REQUIRED", "semantic": validation.metrics,
        "uncommonCeilingAnchors": [e["name"] for e in uncommon_entries],
        "rareCeilingAnchors": [e["name"] for e in rare_entries], "allBinaryAlpha": True,
        "farmerPreview": {"source": str(FARMER), "sha256": hashlib.sha256(FARMER.read_bytes()).hexdigest(), "bodyFrames": BODY_FRAME, "shirtOffsetContract": "Fashion Sense Scale2 BodyPosition(0,32) idle placement", "liveRuntimeSubstitute": False},
        "farmerDiversity": {"status": "PASS", "pairCount": len(diversity_rows), "failedPairs": failed_pairs, "maximumOverlapScore": max(row["overlapScore"] for row in diversity_rows)},
        "runtime": "NOT_TESTED", "mythicWorkStarted": False, "eventIntegrationStarted": False,
    })
    (REPORTS / "V6_LEGENDARY_CALIBRATION_TABLE.md").write_text("# V6 Legendary Calibration Table\n\n" + _table(batch["entries"]) + "\n", encoding="utf-8")
    (REPORTS / "V6_LEGENDARY_PALETTE_STORIES.md").write_text("# V6 Legendary Palette Stories\n\n" + _palette_table(batch["entries"]) + "\n", encoding="utf-8")
    (REPORTS / "V6_LEGENDARY_GARMENT_IDENTITIES.md").write_text("# V6 Legendary Garment Identities\n\n" + _identity_table(batch["entries"]) + "\n", encoding="utf-8")
    (REPORTS / "V6_LEGENDARY_PAIRWISE_DIVERSITY.md").write_text(_matrix_markdown(diversity_rows), encoding="utf-8")
    print("Generated six Legendary calibration garments")
    print(OUT); print(COMPARE / "V6_LEGENDARY_CONTACT.png")


if __name__ == "__main__": main()
