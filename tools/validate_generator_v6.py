#!/usr/bin/env python3
"""Independent static validation for generated V6 artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.png_utils import read_rgba_png
from generator.v6 import generate_v6_batch, validate_v6_batch

OUT = ROOT / "output" / "v6-production-batch"


def main() -> None:
    batch = generate_v6_batch(); result = validate_v6_batch(batch["entries"])
    checks = []
    def check(name, passed, detail): checks.append({"name": name, "passed": bool(passed), "detail": detail})
    check("semantic diversity gate", result.passes, list(result.errors))
    check("exact tier counts", result.metrics["tierCounts"] == {"Common": 12, "Uncommon": 12, "Rare+": 6}, result.metrics["tierCounts"])
    records = json.loads((OUT / "design-rarity-table.json").read_text())
    check("thirty exported summaries", len(records) == 30, len(records))
    check("locked renderer split", all((r["tier"] == "Common" and r["logicalSize"] == 8 and r["displayScale"] == 4) or (r["tier"] != "Common" and r["logicalSize"] == 16 and r["displayScale"] == 2) for r in records), [(r["tier"], r["logicalSize"], r["displayScale"]) for r in records])
    check("all static art gates", all(r["quality"]["passesStaticArtGate"] for r in records), [r["id"] for r in records if not r["quality"]["passesStaticArtGate"]])
    check("all binary alpha", all(r["quality"]["binaryAlpha"] for r in records), "direct logical pixels only")
    check("all directional reconstruction", all(r["quality"]["directionalReconstruction"] for r in records), [r["id"] for r in records if not r["quality"]["directionalReconstruction"]])
    expected = [ROOT / "output" / "comparisons" / name for name in ("V6_COMMON_CONTACT.png", "V6_UNCOMMON_CONTACT.png", "V6_RARE_PLUS_CONTACT.png", "V6_GAMEPLAY_SIZE_30.png")]
    check("comparison artifacts", all(path.exists() for path in expected), [str(path) for path in expected])
    for path in expected:
        png = read_rgba_png(path); check(f"valid png {path.name}", png["width"] > 0 and png["height"] > 0, [png["width"], png["height"]])
    check("reports", all((ROOT / "reports" / name).exists() for name in ("V6_DESIGN_RARITY_TABLE.md", "V6_DIVERSITY_REJECTION_REPORT.md", "V6_PRODUCTION_BATCH_REPORT.md")), "required reports")
    for item in checks: print(("PASS" if item["passed"] else "FAIL") + "  " + item["name"])
    if not all(item["passed"] for item in checks): raise SystemExit(1)


if __name__ == "__main__": main()
