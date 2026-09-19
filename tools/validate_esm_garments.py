#!/usr/bin/env python3
"""Offline validator for Enhanced Sewing Machine garment definitions."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from generator.png_utils import read_rgba_png

ASSETS = ROOT / "mods" / "EnhancedSewingMachine" / "assets"
GARMENTS = ASSETS / "garments"
REQUIRED = ("Front", "Right", "Back", "Left")


def resolve(directions: dict, name: str) -> dict:
    frame = directions.get(name)
    if not isinstance(frame, dict):
        raise ValueError(f"{name}: missing frame")
    mirror = frame.get("MirrorOf")
    if not mirror:
        return dict(frame)
    source = directions.get(mirror)
    if not isinstance(source, dict):
        raise ValueError(f"{name}: MirrorOf '{mirror}' is missing")
    if source.get("MirrorOf"):
        raise ValueError(f"{name}: mirror chains are not allowed")
    out = dict(frame)
    out["SourceX"] = source.get("SourceX", 0)
    out["SourceY"] = source.get("SourceY", 0)
    out.pop("MirrorOf", None)
    return out


def validate_one(path: Path) -> list[str]:
    d = json.loads(path.read_text())
    errors: list[str] = []
    gid = d.get("Id")
    if not gid:
        errors.append("Id missing")
    if d.get("Category") != "Hat":
        errors.append(f"unsupported Category={d.get('Category')!r}")
    fw, fh = d.get("FrameWidth"), d.get("FrameHeight")
    scale = d.get("RenderScale")
    if not isinstance(fw, int) or not isinstance(fh, int) or fw <= 0 or fh <= 0:
        errors.append("invalid frame size")
        return errors
    if not isinstance(scale, (int, float)) or scale <= 0:
        errors.append("invalid RenderScale")
    texture_rel = d.get("WornTexture")
    texture = ROOT / "mods" / "EnhancedSewingMachine" / str(texture_rel)
    if not texture.is_file():
        errors.append(f"missing texture {texture_rel}")
        return errors
    png = read_rgba_png(texture)
    directions = d.get("Directions") or {}
    for name in REQUIRED:
        try:
            frame = resolve(directions, name)
        except ValueError as ex:
            errors.append(str(ex))
            continue
        x, y = frame.get("SourceX", 0), frame.get("SourceY", 0)
        if x < 0 or y < 0 or x + fw > png["width"] or y + fh > png["height"]:
            errors.append(f"{name}: source outside {png['width']}x{png['height']}")
        ox, oy = frame.get("OffsetX", 0), frame.get("OffsetY", 0)
        if abs(ox) > 64 or abs(oy) > 64:
            errors.append(f"{name}: offset exceeds safety bound")
    return errors


def main() -> int:
    index = json.loads((GARMENTS / "index.json").read_text())
    files = index.get("Garments") or []
    seen: set[str] = set()
    failed = 0
    widths = {}
    for name in files:
        path = GARMENTS / name
        if not path.is_file():
            print(f"FAIL {name}: missing")
            failed += 1
            continue
        d = json.loads(path.read_text())
        gid = d.get("Id")
        if gid in seen:
            print(f"FAIL {name}: duplicate Id {gid}")
            failed += 1
            continue
        seen.add(gid)
        errors = validate_one(path)
        if errors:
            failed += 1
            print(f"FAIL {name}: " + "; ".join(errors))
            continue
        nominal = d["FrameWidth"] * 4 * float(d["RenderScale"])
        widths[gid] = nominal
        print(
            f"PASS {gid}: {d['FrameWidth']}x{d['FrameHeight']} "
            f"@ {d['RenderScale']} -> nominal {nominal:g}px"
        )

    if "dev.proof32" in widths and "dev.proof16" in widths:
        if widths["dev.proof32"] != widths["dev.proof16"]:
            print("FAIL proof size equivalence")
            failed += 1
        else:
            print(f"PASS 32@0.5 == 16@1.0 nominal width ({widths['dev.proof32']:g}px)")

    print(f"{len(files)-failed}/{len(files)} garment definitions valid")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
