#!/usr/bin/env python3
"""Static validator for V4.5 extended-garment capability fixtures."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.png_utils import encode_rgba_png, read_rgba_png
from generator.renderers.fashionsense import render_v45_prototype
from generator.v45 import generate_v45_prototypes, validate_v45_recipe


def add(condition, message, errors):
    if not condition: errors.append(message)


def main():
    errors = []; warnings = []; recipes_a = generate_v45_prototypes(); recipes_b = generate_v45_prototypes()
    add(recipes_a == recipes_b, "semantic prototype generation is not deterministic", errors)
    add(len(recipes_a) == 7, "expected exactly seven prototypes including one diagnostic coat tail", errors)
    counts = {article: sum(r["articleType"] == article for r in recipes_a) for article in {r["articleType"] for r in recipes_a}}
    add(counts == {"PANTS": 2, "SKIRT": 1, "FOOTWEAR": 2, "MANTLE": 1, "COAT_TAIL_COMPANION": 1}, f"prototype mix changed: {counts}", errors)
    hashes = {}; summaries = []
    for recipe in recipes_a:
        errors.extend(f"{recipe['id']}: {value}" for value in validate_v45_recipe(recipe))
        first = render_v45_prototype(recipe); second = render_v45_prototype(recipe)
        add(first.texture == second.texture, f"{recipe['id']}: pixel render is not deterministic", errors)
        add(first.static_contract_passes, f"{recipe['id']}: {'; '.join(first.static_errors)}", errors)
        slug = "_".join(re.sub(r"[^a-z0-9]+", " ", recipe["name"].lower()).split())
        path = ROOT / "output" / "fashionsense" / "v45-extended-garments" / slug / f"{slug}.png"
        add(path.exists(), f"{recipe['id']}: missing native texture", errors)
        if path.exists():
            png = read_rgba_png(path); expected = (len(first.texture[0]), len(first.texture))
            add((png["width"], png["height"]) == expected, f"{recipe['id']}: texture dimensions differ from renderer contract", errors)
            add(set(png["filters"]) == {0}, f"{recipe['id']}: PNG filtering is not encoder type 0", errors)
            add({p[3] for row in png["pixels"] for p in row} <= {0, 255}, f"{recipe['id']}: semitransparent logical pixels", errors)
            digest = hashlib.sha256(encode_rgba_png(first.texture)).hexdigest(); add(png["sha256"] == digest, f"{recipe['id']}: saved texture differs from renderer", errors); hashes[recipe["id"]] = digest
        summaries.append({"id": recipe["id"], "article": recipe["articleType"], "rarity": recipe["rarity"], "staticPass": first.static_contract_passes, "runtimeStatus": recipe["runtimeStatus"], "runtimeEvidence": "NOT_TESTED_IN_GAME"})
    add(len(set(hashes.values())) == 7, "prototype textures are not all unique", errors)
    pack = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V45-Extended-Prototypes"
    manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
    add(manifest["ContentPackFor"] == {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"}, "pack dependency contract changed", errors)
    appearance_files = sorted(list((pack / "Pants").glob("*/pants.json")) + list((pack / "Shoes").glob("*/shoes.json")) + list((pack / "Accessories").glob("*/accessory.json")))
    add(len(appearance_files) == 6, "test pack must contain exactly six runtime-testable appearances", errors)
    add(not any("CoatTail" in str(path) for path in appearance_files), "diagnostic coat tail leaked into installable pack", errors)
    for path in appearance_files:
        root = json.loads(path.read_text(encoding="utf-8")); stem = path.name.split(".")[0].title()
        texture = read_rgba_png(path.with_suffix(".png")); models = [(key, value) for key, value in root.items() if key.endswith(stem)]
        add(len(models) == 4, f"{path}: must provide four direction models", errors)
        for key, model in models:
            size_key = stem + "Size" if stem != "Accessory" else "AccessorySize"; size = model[size_key]
            start = model["StartingPosition"]; frame_count = texture["width"] // size["Width"]
            add(start["X"] == 0 and start["Y"] + size["Length"] <= texture["height"], f"{path}/{key}: source rectangle out of bounds", errors)
            frames = [record["Frame"] for record in model["IdleAnimation"] + model["MovementAnimation"]]
            add(all(0 <= frame < frame_count for frame in frames), f"{path}/{key}: animation frame exceeds texture row", errors)
            add(model["Scale"] == 4.0 and model["DisableGrayscale"] is True, f"{path}/{key}: logical scale/authored-color contract changed", errors)
            add(model["HideWhileSwimming"] is True and model["HideWhileWearingBathingSuit"] is True, f"{path}/{key}: unsafe water/bathing visibility", errors)
    warnings.extend(["All runtime behavior remains untested; static PASS is not an animation PASS.", "Compact movement phases do not cover tool, horse, sitting, bed, or fishing frames.", "Mantle accessory ordering must be reviewed in every direction and multiplayer."])
    report = {"status": "PASS_STATIC_CONTRACTS" if not errors else "FAIL", "errors": errors, "warnings": warnings,
              "installedFashionSenseTarget": "7.5.0", "runtimeEvidence": "NOT_TESTED_IN_GAME", "counts": counts,
              "installableAppearanceCount": len(appearance_files), "coatTailInPack": False, "textures": hashes, "prototypes": summaries,
              "claims": {"staticFormat": not errors, "walking": False, "tools": False, "horse": False, "sitting": False, "swimming": False, "multiplayer": False}}
    target = ROOT / "output" / "fashionsense" / "v45-extended-garments" / "full_validation.json"
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "errors": errors, "warnings": warnings}, indent=2)); raise SystemExit(1 if errors else 0)


if __name__ == "__main__": main()
