#!/usr/bin/env python3
"""Regenerate the active ESM compiled catalog and prove the bridge is deterministic."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v5 import authored  # noqa: E402
from tools.compile_esm_garments import (  # noqa: E402
    CATALOG,
    GARMENTS,
    GENERATOR_ID,
    GENERATOR_VERSION,
    MOD,
    compile_one,
    pixel_digest,
)
from v5.pngio import read_rgba_png  # noqa: E402


def main() -> int:
    if not CATALOG.is_file():
        print("FAIL catalog missing:", CATALOG)
        return 1

    cat = json.loads(CATALOG.read_text())
    errors = 0
    if cat.get("schema") != "esm-compiled-catalog/v1":
        print("FAIL catalog schema", cat.get("schema"))
        errors += 1
    if cat.get("generator_id") != GENERATOR_ID:
        print("FAIL generator id", cat.get("generator_id"))
        errors += 1
    if cat.get("generator_version") != GENERATOR_VERSION:
        print("FAIL generator version", cat.get("generator_version"))
        errors += 1

    lib = authored.load()
    seen = set()
    for item in cat.get("items", []):
        seed = int(item["seed"])
        compiled = compile_one(seed, lib)
        gid = item["garment_id"]
        if gid in seen:
            print("FAIL duplicate active id", gid)
            errors += 1
            continue
        seen.add(gid)

        problems = []
        if compiled["garment_id"] != gid:
            problems.append(f"regenerated id {compiled['garment_id']}")
        if compiled["pixel_digest"] != item.get("pixel_digest"):
            problems.append("regenerated pixel digest differs")
        if compiled["classification"] != "PRODUCTION":
            problems.append(f"classification={compiled['classification']}")

        texture = MOD / item["texture_rel"]
        definition = GARMENTS / item["definition_rel"]
        if not texture.is_file():
            problems.append("compiled texture missing")
        else:
            on_disk = read_rgba_png(texture)
            if pixel_digest(on_disk) != item["pixel_digest"]:
                problems.append("on-disk texture pixel digest differs")

        if not definition.is_file():
            problems.append("runtime definition missing")
        else:
            d = json.loads(definition.read_text())
            m = d.get("Metadata") or {}
            if d.get("Id") != gid:
                problems.append("definition Id differs")
            if m.get("GeneratorId") != GENERATOR_ID:
                problems.append("definition GeneratorId differs")
            if int(m.get("GeneratorVersion", -1)) != GENERATOR_VERSION:
                problems.append("definition GeneratorVersion differs")
            if int(m.get("GeneratorSeed", -1)) != seed:
                problems.append("definition GeneratorSeed differs")
            if m.get("Classification") != "PRODUCTION":
                problems.append("definition is not PRODUCTION")
            if d.get("WornTexture") != item["texture_rel"]:
                problems.append("definition texture path differs")
            if [d.get("FrameWidth"), d.get("FrameHeight")] != item["frame_size"]:
                problems.append("definition frame size differs")

        if problems:
            errors += 1
            print("FAIL", gid, "|", "; ".join(problems))
        else:
            print(
                "PASS", gid,
                f"| seed={seed} base={item['base']} palette={item['palette']} decals={item['decals']}"
            )

    count = len(cat.get("items", []))
    if cat.get("count") != count:
        print("FAIL catalog count field", cat.get("count"), "!=", count)
        errors += 1

    if errors:
        print(f"{errors} bridge validation failure(s)")
        return 1
    print(f"ALL {count} COMPILED GENERATOR GARMENTS REPRODUCE EXACTLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
