#!/usr/bin/env python3
"""Static checks for rarity-to-renderer capability routing."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.rarity_renderer_policy import (
    load_rarity_renderer_policy,
    select_renderer_route,
    validate_renderer_assembly,
)


def main() -> None:
    policy = load_rarity_renderer_policy()
    budgets = json.loads(
        (ROOT / "generator" / "data" / "v3" / "rarity_budgets.json").read_text(
            encoding="utf-8"
        )
    )
    errors: list[str] = []
    expected = {
        "Common": ("vanilla", "VANILLA_STARDEW_SINGLE_ARTICLE"),
        "Uncommon": ("fashionsense", "FS_HD_SIMPLE_ARTICLE"),
        "Rare": ("fashionsense", "FS_RARE_PLUS_COMPLEX_GARMENT"),
    }
    for rarity, (backend, renderer_class) in expected.items():
        route = select_renderer_route(rarity, policy)
        if (route.backend, route.renderer_class) != (backend, renderer_class):
            errors.append(f"{rarity}: wrong renderer route")
        if budgets["rarities"][rarity].get("rendererRoute") != renderer_class:
            errors.append(f"{rarity}: V3 rarity budget disagrees with renderer policy")

    positive = (
        validate_renderer_assembly("Common"),
        validate_renderer_assembly("Uncommon", ("Shirt",)),
        validate_renderer_assembly(
            "Rare", ("Shirt", "Hat"), preset=True, state_behavior=True
        ),
        validate_renderer_assembly(
            "Rare", ("Shirt", "Sleeves", "Hat", "Accessory"),
            preset=True,
        ),
    )
    if not all(result.valid for result in positive):
        errors.append("one or more valid reference assemblies were rejected")

    negative = (
        validate_renderer_assembly("Common", ("Shirt",)),
        validate_renderer_assembly("Uncommon", ("Shirt", "Hat"), preset=True),
        validate_renderer_assembly("Uncommon", ("Shirt",), state_behavior=True),
        validate_renderer_assembly("Rare", ("Shirt", "Hat"), preset=False),
    )
    if any(result.valid for result in negative):
        errors.append("one or more forbidden cross-tier assemblies were accepted")

    template = policy.get("rarePlusTemplate", {})
    if template.get("architectureStatus") != "LOCKED_PENDING_FINAL_RUNTIME_CONFIRMATION":
        errors.append("RarePlus hoodie template must not be falsely marked frozen before live completion")
    if template.get("promotionStatus") != "EXPERIMENTAL":
        errors.append("RarePlus hoodie template must remain EXPERIMENTAL pending live checklist")

    result = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "routes": {
            rarity: select_renderer_route(rarity, policy).renderer_class
            for rarity in ("Common", "Uncommon", "Rare")
        },
        "rarePlusTemplate": template,
    }
    out = ROOT / "output" / "validation" / "rarity_renderer_architecture.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
