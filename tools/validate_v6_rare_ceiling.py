#!/usr/bin/env python3
"""Validate Rare ceiling semantics and generated artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.png_utils import read_rgba_png
from generator.v6 import generate_rare_ceiling_batch, validate_rare_ceiling_batch

OUT = ROOT / "output" / "fashionsense" / "v6-rare-ceiling"


def main() -> None:
    batch = generate_rare_ceiling_batch(); semantic = validate_rare_ceiling_batch(batch["entries"])
    checks = []
    def check(name, passed, detail): checks.append((name, bool(passed), detail))
    check("six semantic Rare garments", semantic.passes and len(batch["entries"]) == 6, list(semantic.errors))
    check("six distinct garment families", semantic.metrics["familyCount"] == 6, semantic.metrics)
    check("no hoodie", semantic.metrics["hoodieCount"] == 0, semantic.metrics["hoodieCount"])
    check("no spectacle hooks", semantic.metrics["specialHookMaximum"] <= 1 and semantic.metrics["stateBehaviorCount"] == 0 and semantic.metrics["vfxCount"] == 0, semantic.metrics)
    check("reserved customization sockets", all(e["customization"]["MotifSocket"] == "reserved_empty" and {"ExteriorContour", "StructuralSeams"} <= set(e["customization"]["protected"]) for e in batch["entries"]), "semantic metadata only")
    validation = json.loads((OUT / "validation.json").read_text())
    check("generated static pass", validation["status"] == "PASS_STATIC_HUMAN_CEILING_REVIEW_REQUIRED", validation["status"])
    folders = [p for p in OUT.iterdir() if p.is_dir()]
    check("six output folders", len(folders) == 6, len(folders))
    for folder in folders:
        png = read_rgba_png(folder / "shirt.png")
        check(folder.name + " 16x64", (png["width"], png["height"]) == (16, 64), [png["width"], png["height"]])
        check(folder.name + " binary alpha", {p[3] for row in png["pixels"] for p in row} <= {0, 255}, "direct pixels")
    required = [ROOT / "output" / "comparisons" / "V6_RARE_CEILING_CONTACT.png", ROOT / "output" / "comparisons" / "V6_RARE_CEILING_GAMEPLAY.png", ROOT / "reports" / "V6_RARE_CEILING_TABLE.md", ROOT / "reports" / "V6_RARE_CEILING_REPORT.md"]
    check("required artifacts", all(path.exists() for path in required), [str(p) for p in required])
    for name, passed, detail in checks: print(("PASS" if passed else "FAIL") + "  " + name)
    if not all(passed for _, passed, _ in checks): raise SystemExit(1)


if __name__ == "__main__": main()
