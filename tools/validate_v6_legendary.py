#!/usr/bin/env python3
"""Static validation entry point for V6 Legendary calibration."""
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from generator.png_utils import read_rgba_png
from generator.v6 import generate_legendary_batch, validate_legendary_batch
batch = generate_legendary_batch()
result = validate_legendary_batch(batch["entries"])
errors = list(result.errors)
out = ROOT / "output" / "fashionsense" / "v6-legendary-calibration"
compare = ROOT / "output" / "comparisons"
locked_palettes = {
    "legendary_white_teal_graphite", "legendary_crimson_charcoal_ivory",
    "legendary_jade_cream_bronze", "legendary_pearl_midnight_gold",
    "legendary_frost_silver_black", "legendary_sunset_amber_indigo",
}
if {entry["paletteStory"] for entry in batch["entries"]} != locked_palettes: errors.append("locked Legendary palette set changed")
folders = [p for p in out.iterdir() if p.is_dir()] if out.exists() else []
if len(folders) != 6: errors.append(f"expected six rendered output folders, found {len(folders)}")
for folder in folders:
    png = read_rgba_png(folder / "shirt.png")
    if (png["width"], png["height"]) != (16, 64): errors.append(f"{folder.name}: shirt atlas is not 16x64")
    if not {pixel[3] for row in png["pixels"] for pixel in row} <= {0, 255}: errors.append(f"{folder.name}: non-binary alpha")
    if not (folder / "farmer-directions.png").exists(): errors.append(f"{folder.name}: Farmer direction preview missing")
required = (
    "V6_LEGENDARY_CONTACT.png", "V6_LEGENDARY_GAMEPLAY.png",
    "V6_LEGENDARY_FARMER_DIRECTIONS.png", "V6_RARE_VS_LEGENDARY.png",
)
for name in required:
    if not (compare / name).exists(): errors.append(f"missing comparison artifact {name}")
matrix_path = out / "pairwise-diversity.json"
if not matrix_path.exists(): errors.append("pairwise diversity JSON missing")
else:
    matrix = json.loads(matrix_path.read_text())
    if len(matrix.get("pairs", [])) != 15: errors.append("pairwise matrix must contain fifteen pairs")
    if any(not row.get("passes") for row in matrix.get("pairs", [])): errors.append("pairwise diversity gate contains a failed pair")
validation_path = out / "validation.json"
if validation_path.exists():
    static = json.loads(validation_path.read_text())
    if static.get("farmerDiversity", {}).get("status") != "PASS": errors.append("Farmer diversity status is not PASS")
    if len(static.get("uncommonCeilingAnchors", [])) != 2 or len(static.get("rareCeilingAnchors", [])) != 2: errors.append("locked lower-tier anchors incomplete")
else: errors.append("generated validation JSON missing")
payload = {"passes": not errors, "errors": errors, "warnings": result.warnings, "metrics": result.metrics, "staticRaster": {"folders": len(folders), "pairwisePairs": 15, "farmerComposite": True}}
print(json.dumps(payload, indent=2))
raise SystemExit(0 if not errors else 1)
