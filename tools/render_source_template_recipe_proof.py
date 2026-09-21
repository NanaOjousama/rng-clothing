#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v5.pngio import blank_image, blit, nearest_scale, write_rgba_png
from v5.source.template_transfer import load_contract
from v5.source.source_backed_renderer import render_source_backed

recipe_path = ROOT / "experiments/source_template_recipe_proof/slouch_pl24_recipe.json"
recipe = json.loads(recipe_path.read_text())
lib = json.loads((ROOT / "source_catalog/SOURCE_TRANSFER_LIBRARY.json").read_text())
catalog = json.loads((ROOT / "source_catalog/catalog.json").read_text())

style = next(p for p in lib["parts"] if p.get("id") == recipe["styleDonor"])
base = next(a for a in catalog["appearances"] if a.get("pack")=="Cottagecore Set" and a.get("name")=="Beret")
leaf = next(a for a in catalog["appearances"] if a.get("pack")=="Cottagecore Set" and a.get("name")=="Beret (Leaf)")

motif_source = {
    "base_png": base["png_path"],
    "variant_png": leaf["png_path"],
    "boxes": base["analysis"]["boxes"],
}
out_dir = ROOT / "experiments/source_template_recipe_proof/rendered"
report = render_source_backed(
    load_contract(ROOT / "generator/data/templates/slouch_pl24.json"),
    style, motif_source, out_dir,
)
report["styleDonor"] = recipe["styleDonor"]
report["motifDonor"] = "Cottagecore Set::Beret (Leaf)"
report["geometryPolicy"] = "LOCKED_TEMPLATE_ALPHA"
report_path = ROOT / "experiments/source_template_recipe_proof/render_report.json"
report_path.write_text(json.dumps(report, indent=2) + "\n")

# Native four-view strip + enlarged QC strip.
views = ["front","right","left","back"]
frames = []
from v5.pngio import read_rgba_png
for view in views:
    frames.append(read_rgba_png(out_dir / f"{view}.png"))
sheet = blank_image(24*4, 24)
for i, frame in enumerate(frames):
    blit(sheet, frame, i*24, 0)
write_rgba_png(ROOT / "experiments/source_template_recipe_proof/rendered_strip.png", sheet)
write_rgba_png(ROOT / "experiments/source_template_recipe_proof/rendered_strip_x8.png", nearest_scale(sheet, 8))

recipe["status"] = "RENDERED_PROOF"
recipe["renderReport"] = "experiments/source_template_recipe_proof/render_report.json"
recipe["renderedFrames"] = {v: f"experiments/source_template_recipe_proof/rendered/{v}.png" for v in views}
recipe["note"] = "Rendered from locked PL24 construction, More Accessories and Stuff Beanie value-role vocabulary, and source-reconstructed Cottagecore Beret Leaf motif ink. Geometry remains locked."
recipe_path.write_text(json.dumps(recipe, indent=2) + "\n")
print(json.dumps(report, indent=2))
