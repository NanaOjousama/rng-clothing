#!/usr/bin/env python3
"""Build V4.6 lower-body contracts from the installed FS 7.5 examples.

Only source-frame contracts and binary coverage geometry are retained. Source
colors and artwork are not copied into generated garments.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import read_rgba_png


EXAMPLES = ROOT / "FASHION SENSE" / "FashionSense-stable" / "FashionSense" / "Examples" / "[FS] Example Pack"
OUT = ROOT / "generator" / "data" / "fashionsense" / "v46"
FRAME_W, FRAME_H, COLUMNS = 16, 32, 6
DIRECTIONS = ("Front", "Back", "Right", "Left")


def strip_json_comments(text: str) -> str:
    out: list[str] = []
    quoted = escaped = line = block = False
    i = 0
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if line:
            if ch in "\r\n":
                line = False
                out.append(ch)
            i += 1
            continue
        if block:
            if ch == "*" and nxt == "/":
                block = False
                i += 2
            else:
                i += 1
            continue
        if not quoted and ch == "/" and nxt == "/":
            line = True
            i += 2
            continue
        if not quoted and ch == "/" and nxt == "*":
            block = True
            i += 2
            continue
        out.append(ch)
        if ch == '"' and not escaped:
            quoted = not quoted
        escaped = ch == "\\" and not escaped
        if ch != "\\":
            escaped = False
        i += 1
    return "".join(out)


def load_json(path: Path) -> dict:
    return json.loads(strip_json_comments(path.read_text(encoding="utf-8-sig")))


def spans_for_frame(pixels, frame: int) -> list[dict]:
    x0 = (frame % COLUMNS) * FRAME_W
    y0 = (frame // COLUMNS) * FRAME_H
    rows = []
    for y in range(FRAME_H):
        runs = []
        start = None
        for x in range(FRAME_W + 1):
            opaque = x < FRAME_W and pixels[y0 + y][x0 + x][3] > 0
            if opaque and start is None:
                start = x
            elif not opaque and start is not None:
                runs.append([start, x - 1])
                start = None
        if runs:
            rows.append({"y": y, "spans": runs})
    return rows


def bounds(rows: list[dict]) -> list[int] | None:
    if not rows:
        return None
    xs = [x for row in rows for span in row["spans"] for x in span]
    return [min(xs), rows[0]["y"], max(xs), rows[-1]["y"]]


def anatomy(rows: list[dict], kind: str) -> dict:
    cells = [(x, row["y"]) for row in rows for a, b in row["spans"] for x in range(a, b + 1)]
    if not cells:
        return {"upperAnchors": [], "lowerContacts": [], "segments": []}
    top = min(y for _, y in cells); bottom = max(y for _, y in cells)
    upper = sorted(x for x, y in cells if y == top); lower = sorted(x for x, y in cells if y == bottom)
    segments = []
    for name, subset in (("screen_left", [(x, y) for x, y in cells if x <= 7]), ("screen_right", [(x, y) for x, y in cells if x >= 8])):
        if subset:
            xs = [x for x, _ in subset]; ys = [y for _, y in subset]
            segments.append({"name": name, "semantic": "leg" if kind == "pants" else "foot", "bounds": [min(xs), min(ys), max(xs), max(ys)], "cells": len(subset)})
    return {"upperAnchors": [[x, top] for x in upper], "lowerContacts": [[x, bottom] for x in lower], "segments": segments}


def build(kind: str, folder: str, stem: str) -> tuple[dict, dict]:
    json_path = EXAMPLES / folder / stem / f"{kind}.json"
    png_path = EXAMPLES / folder / stem / f"{kind}.png"
    raw = load_json(json_path)
    png = read_rgba_png(png_path)
    frame_capacity = (png["width"] // FRAME_W) * (png["height"] // FRAME_H)
    models = {}
    used_frames = set()
    suffix = "Pants" if kind == "pants" else "Shoes"
    for direction in DIRECTIONS:
        source = raw[direction + suffix]
        animations = source.get("UniformAnimation", [])
        used_frames.update(entry["Frame"] for entry in animations)
        models[direction.lower()] = {
            "startingPosition": source["StartingPosition"],
            "bodyPosition": source.get("BodyPosition", {"X": 0, "Y": 0}),
            "size": source[suffix + "Size"],
            "disableNativeOffset": source.get("DisableNativeOffset", False),
            "hideWhileSwimming": source.get("HideWhileSwimming", True),
            "hideWhileWearingBathingSuit": source.get("HideWhileWearingBathingSuit", True),
            "uniformAnimation": animations,
        }
    coverage = {}
    for frame in range(max(used_frames) + 1):
        rows = spans_for_frame(png["pixels"], frame)
        coverage[str(frame)] = {
            "bounds": bounds(rows),
            "rowSpans": rows,
            "opaqueCells": sum(b - a + 1 for row in rows for a, b in row["spans"]),
            "anatomy": anatomy(rows, kind),
        }
    contract = {
        "article": "FITTED_PANTS" if kind == "pants" else "FOOTWEAR",
        "fashionSenseVersion": "7.5.0",
        "installedStardewVersion": "1.6.15.24356",
        "source": {
            "kind": "installed Fashion Sense official developer example",
            "json": str(json_path.relative_to(ROOT)),
            "png": str(png_path.relative_to(ROOT)),
            "jsonSha256": hashlib.sha256(json_path.read_bytes()).hexdigest(),
            "pngSha256": png["sha256"],
        },
        "texture": {"width": png["width"], "height": png["height"], "frameWidth": FRAME_W, "frameHeight": FRAME_H, "columns": COLUMNS, "capacity": frame_capacity},
        "models": models,
        "usedFrames": sorted(used_frames),
        "intentionallyEmptyUsedFrames": sorted(frame for frame in used_frames if coverage[str(frame)]["opaqueCells"] == 0),
        "maxUsedFrame": max(used_frames),
        "coverage": coverage,
        "claims": {
            "staticContract": "authoritative installed FS example",
            "generatedPrototypeRuntime": "NOT_TESTED",
            "coverageMeaning": "binary article envelope only; no source colors or motifs retained",
        },
    }
    grammar = {
        "formatVersion": "4.6",
        "article": contract["article"],
        "frameContract": "lower_body_frame_contracts.json",
        "zones": (["waistband", "hip", "upper_leg", "knee", "lower_leg", "ankle", "side_panel", "utility_seam", "trim", "accent"] if kind == "pants" else ["toe", "vamp", "ankle", "shaft", "cuff", "sole", "strap", "buckle_hint", "trim", "material_contrast"]),
        "motionRules": {
            "sourceSelection": "UniformAnimation resolves current Farmer state/frame to a full 16x32 authored source frame",
            "coverage": "all decoration is clipped to, or deterministically extended from, the per-frame coverage envelope",
            "direction": "FS selects a facing model; each model retains its official condition map",
            "water": "appearance hides while swimming and while bathing clothes are active",
            "nativeOffset": "disabled because pose placement is already encoded in each full source frame",
        },
        "status": "EXPERIMENTAL",
    }
    return contract, grammar


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pants, pants_grammar = build("pants", "Pants", "SimplePantsTemplate")
    shoes, shoes_grammar = build("shoes", "Shoes", "ShoesTemplate")
    aggregate = {
        "formatVersion": "4.6",
        "fashionSenseVersion": "7.5.0",
        "installedStardewVersion": "1.6.15.24356",
        "frameGeometry": {"width": FRAME_W, "height": FRAME_H, "columns": COLUMNS, "logicalScale": 4},
        "contracts": {"FITTED_PANTS": pants, "FOOTWEAR": shoes},
        "runtimeStatus": "NOT_TESTED",
    }
    for name, value in (("lower_body_frame_contracts.json", aggregate), ("pants_motion_grammar.json", pants_grammar), ("footwear_motion_grammar.json", shoes_grammar)):
        (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote V4.6 contracts: pants frames 0..{pants['maxUsedFrame']}, footwear 0..{shoes['maxUsedFrame']}")


if __name__ == "__main__":
    main()
