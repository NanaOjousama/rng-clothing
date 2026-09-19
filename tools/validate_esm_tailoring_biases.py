#!/usr/bin/env python3
"""Validate the current ESM Textile/Inspiration bias catalog against compiled garments."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "mods" / "EnhancedSewingMachine"
BIAS = MOD / "assets" / "tailoring" / "biases.json"
CATALOG = MOD / "assets" / "generated" / "COMPILED_CATALOG.json"


def tokens(value):
    if not value:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x)]
    return [x.strip() for x in str(value).split(",") if x.strip()]


def lookup(table, key):
    if not key:
        return 0
    key = key.lower()
    return sum(int(v) for k, v in (table or {}).items() if k.lower() == key)


def adjust(item, profile):
    score = 0
    score += lookup(profile.get("FamilyWeights"), item.get("family"))
    score += lookup(profile.get("ConstructionWeights"), item.get("construction"))
    score += lookup(profile.get("MaterialWeights"), item.get("material"))
    score += lookup(profile.get("StyleWeights"), item.get("style"))
    score += lookup(profile.get("PaletteWeights"), item.get("palette"))
    for motif in item.get("motif_classes") or []:
        score += lookup(profile.get("MotifWeights"), motif)
    for decal in item.get("decals") or []:
        score += lookup(profile.get("DecalWeights"), decal)
    return score


def compatible(item, profile):
    construction = (item.get("construction") or "").lower()
    denied = {x.lower() for x in profile.get("DeniedConstructions", [])}
    allowed = {x.lower() for x in profile.get("AllowedConstructions", [])}
    if construction in denied:
        return False
    if allowed and construction not in allowed:
        return False
    return True


def main():
    bias = json.loads(BIAS.read_text())
    cat = json.loads(CATALOG.read_text())
    items = [x for x in cat.get("items", []) if x.get("classification") == "PRODUCTION"]
    failures = 0

    if not items:
        print("FAIL no PRODUCTION compiled garments")
        return 1

    for kind in ("Textiles", "Inspirations"):
        profiles = bias.get(kind) or {}
        if not profiles:
            print("FAIL no", kind)
            failures += 1
            continue
        for pid, profile in profiles.items():
            values = [adjust(x, profile) for x in items if compatible(x, profile)]
            if not values:
                print(f"FAIL {kind}/{pid}: no compatible garments")
                failures += 1
            elif max(values) == min(values):
                print(f"FAIL {kind}/{pid}: profile has no discriminating effect on active pool")
                failures += 1
            else:
                print(f"PASS {kind}/{pid}: adjustment range {min(values)}..{max(values)}")

    print("\nPair top weights (bias, not deterministic RNG result):")
    for tid, textile in bias["Textiles"].items():
        for iid, insp in bias["Inspirations"].items():
            scored = []
            for item in items:
                if not compatible(item, textile) or not compatible(item, insp):
                    continue
                weight = max(
                    1,
                    int(textile.get("BaseWeight", 100))
                    + int(insp.get("BaseWeight", 100))
                    + adjust(item, textile)
                    + adjust(item, insp),
                )
                scored.append((weight, item["garment_id"]))
            scored.sort(reverse=True)
            top = ", ".join(f"{gid}:{weight}" for weight, gid in scored[:3])
            print(f"  {tid} + {iid} -> {top}")

    if failures:
        print(f"\n{failures} tailoring bias validation failure(s)")
        return 1

    print(f"\nPASS all {len(bias['Textiles'])} Textile and {len(bias['Inspirations'])} Inspiration profiles affect the {len(items)}-garment active pool")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
