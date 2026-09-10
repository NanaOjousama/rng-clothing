"""One Fashion Sense exporter. Contract values come from data/runtime/fs_shirt_contract.json."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .pngio import RGBA, blank_image, write_rgba_png

FS_UNIQUE_ID = "RNGClothing.FashionSense.V5Phase1Bench"


def _folder(name: str) -> str:
    return "".join(part.capitalize() for part in "".join(c if c.isalnum() else " " for c in name).split())


def atlas(frames: dict[str, list[list[RGBA]]], order: list[str], size: int) -> list[list[RGBA]]:
    tex = blank_image(size, size * len(order))
    for i, d in enumerate(order):
        for y, row in enumerate(frames[d]):
            tex[i * size + y] = list(row)
    return tex


def shirt_json(name: str, sleeve_colors, *, contract: dict, tags, hide_sleeves: bool, eight: bool = False) -> dict:
    c = contract["vanilla_8x8"] if eight else contract
    size = c["logical_frame"][0]
    order = contract["atlas_order"]
    result = {"Name": name, "Format": contract["format"], "Tags": list(tags)}
    for i, d in enumerate(order):
        key = {"front": "FrontShirt", "right": "RightShirt", "left": "LeftShirt", "back": "BackShirt"}[d]
        result[key] = {
            "Scale": float(c["scale"]), "HideSleeves": bool(hide_sleeves), "DisableGrayscale": bool(contract["disable_grayscale"]),
            "SleeveColors": [list(x) for x in sleeve_colors],
            "StartingPosition": {"X": 0, "Y": i * size}, "BodyPosition": dict(c["body_position"]),
            "ShirtSize": {"Width": size, "Length": size},
        }
    return result


def write_pack(pack_dir: Path, items: list[dict], contract: dict, *, description: str) -> dict:
    """items: {name, frames, sleeve_colors, tags, hide_sleeves, eight(bool)}. Returns a manifest of written files."""
    pack_dir = Path(pack_dir)
    if pack_dir.exists(): shutil.rmtree(pack_dir)
    (pack_dir / "Shirts").mkdir(parents=True)
    presets, index = [], []
    for i, it in enumerate(items, 1):
        c = contract["vanilla_8x8"] if it.get("eight") else contract
        folder = pack_dir / "Shirts" / _folder(it["name"]); folder.mkdir()
        tex = atlas(it["frames"], contract["atlas_order"], c["logical_frame"][0])
        write_rgba_png(folder / "shirt.png", tex)
        (folder / "shirt.json").write_text(json.dumps(shirt_json(it["name"], it["sleeve_colors"], contract=contract, tags=it["tags"], hide_sleeves=it["hide_sleeves"], eight=it.get("eight", False)), indent=2) + "\n", encoding="utf-8")
        presets.append({"Name": f"V5P1 {i:02d} - {it['name']}", "Author": "RNG Clothing V5", "Version": 3,
                        "AccessoryIds": ["None", "None", "None"], "HairId": "None", "HatId": "None",
                        "ShirtId": f"{FS_UNIQUE_ID}/Shirt/{it['name']}", "SleevesId": "None", "PantsId": "None", "ShoesId": "None", "BodyId": "None",
                        "AppearanceToMaskColors": {}})
        index.append({"index": i, "name": it["name"], "folder": folder.name, "atlas": [len(tex[0]), len(tex)], "scale": c["scale"], "runtime": "NOT_TESTED"})
    (pack_dir / "manifest.json").write_text(json.dumps({
        "Name": "RNG Clothing V5 Phase 1 Bench (INTERNAL)", "Author": "RNG Clothing V5", "Version": "0.1.0", "Description": description,
        "UniqueID": FS_UNIQUE_ID, "UpdateKeys": [], "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    }, indent=2) + "\n", encoding="utf-8")
    (pack_dir / "preset_outfits.json").write_text(json.dumps(presets, indent=2) + "\n", encoding="utf-8")
    (pack_dir / "specimen-index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    (pack_dir / "README.md").write_text(
        "# RNG Clothing V5 Phase 1 Bench pack (INTERNAL, NOT FOR DISTRIBUTION)\n\n"
        "These shirts are architecture fixtures that intentionally reconstruct vanilla garment types. "
        "Copy this folder into `Stardew Valley/Mods`, restart SMAPI, open the Fashion Sense hand mirror and use the `V5P1` presets.\n\n"
        "Runtime status: NOT TESTED until a human loads it in game.\n", encoding="utf-8")
    return {"pack": str(pack_dir), "items": index}
