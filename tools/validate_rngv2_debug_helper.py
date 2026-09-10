#!/usr/bin/env python3
"""Static validation for the test-only RNG Clothing V2 SMAPI command helper."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "test-helpers" / "RNG-Clothing-V2-DebugCommands" / "ModEntry.cs"
HELPER_DIR = ROOT / "test-packs" / "vanilla" / "RNG-Clothing-V2-DebugCommands"
DLL = HELPER_DIR / "RNGClothingV2.DebugCommands.dll"
MANIFEST = HELPER_DIR / "manifest.json"
HELPER_README = HELPER_DIR / "README.md"
PACK_DIR = ROOT / "test-packs" / "vanilla" / "RNG-Clothing-V2"
PACK_CONTENT = PACK_DIR / "content.json"
PACK_README = PACK_DIR / "README.md"

EXPECTED = [
    ("Stonefield Essential Tee", "(S)RNGClothing.V2.StonefieldEssentialTee"),
    ("Stonefield Rib-Knit Sweater", "(S)RNGClothing.V2.StonefieldRibKnitSweater"),
    ("Stonefield Tailored Shirt", "(S)RNGClothing.V2.StonefieldTailoredShirt"),
    ("Stonefield Layer Jacket", "(S)RNGClothing.V2.StonefieldLayerJacket"),
    ("Stonefield Sailor-Yoke Top", "(S)RNGClothing.V2.StonefieldSailorYokeTop"),
    ("Meadow Everyday Tee", "(S)RNGClothing.V2.MeadowEverydayTee"),
    ("Woodland Yoke Sweater", "(S)RNGClothing.V2.WoodlandYokeSweater"),
    ("Meadow Placket Shirt", "(S)RNGClothing.V2.MeadowPlacketShirt"),
    ("Mistral Lapel Layer Jacket", "(S)RNGClothing.V2.MistralLapelLayerJacket"),
    ("Garnet Yoke Top", "(S)RNGClothing.V2.GarnetYokeTop"),
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    expected_files = {
        "README.md",
        "RNGClothingV2.DebugCommands.dll",
        "manifest.json",
    }
    actual_files = {
        path.name for path in HELPER_DIR.iterdir() if path.is_file()
    }
    if actual_files != expected_files:
        raise AssertionError(
            f"debug-helper distribution should contain only {sorted(expected_files)}, "
            f"found {sorted(actual_files)}"
        )

    manifest = load_json(MANIFEST)
    if manifest.get("UniqueID") != "RNGClothing.V2.DebugCommands":
        raise AssertionError("wrong debug-helper UniqueID")
    if manifest.get("EntryDll") != DLL.name:
        raise AssertionError("manifest EntryDll does not match the built assembly")
    dependencies = manifest.get("Dependencies", [])
    if dependencies != [{"UniqueID": "RNGClothing.V2", "IsRequired": True}]:
        raise AssertionError("debug helper must require the separate RNGClothing.V2 pack")
    if "TEST ONLY" not in manifest.get("Name", ""):
        raise AssertionError("manifest does not clearly identify the helper as test-only")

    source = SOURCE.read_text(encoding="utf-8")
    source_pairs = re.findall(
        r'new\("([^"]+)", "(\(S\)RNGClothing\.V2\.[^"]+)"\)', source
    )
    if source_pairs != EXPECTED:
        raise AssertionError(f"source command ordering differs from V2 ordering: {source_pairs}")
    for required in (
        '"rngv2"',
        'case "all"',
        'case "control"',
        'case "rarity"',
        "number >= 1",
        "number <= Shirts.Length",
        "ItemRegistry.Exists",
        "ItemRegistry.Create",
        "Utility.CollectOrDrop",
    ):
        if required not in source:
            raise AssertionError(f"source is missing required behavior: {required}")
    for forbidden in ("Data/Shirts", "EditData", "FashionSense", "TFWR"):
        if forbidden in source:
            raise AssertionError(f"test helper contains out-of-scope production behavior: {forbidden}")

    content = load_json(PACK_CONTENT)
    shirt_change = next(
        change
        for change in content["Changes"]
        if change.get("Action") == "EditData" and change.get("Target") == "Data/Shirts"
    )
    registered_ids = list(shirt_change["Entries"])
    expected_unqualified = [qualified[3:] for _, qualified in EXPECTED]
    if registered_ids != expected_unqualified:
        raise AssertionError("helper ordering/IDs differ from the V2 Content Patcher pack")

    binary = DLL.read_bytes()
    if len(binary) < 4096 or not binary.startswith(b"MZ"):
        raise AssertionError("built helper is not a plausible managed PE assembly")
    for name, qualified_id in EXPECTED:
        for value in (name, qualified_id):
            if value.encode("utf-16le") not in binary:
                raise AssertionError(f"built helper is missing compiled literal: {value}")

    helper_readme = HELPER_README.read_text(encoding="utf-8")
    pack_readme = PACK_README.read_text(encoding="utf-8")
    for command in ("rngv2 all", "rngv2 control", "rngv2 rarity", "rngv2 1", "rngv2 10"):
        if command not in helper_readme or command not in pack_readme:
            raise AssertionError(f"README command documentation is missing: {command}")

    digest = hashlib.sha256(binary).hexdigest()
    print("RNG Clothing V2 debug helper static validation: PASS")
    print("- compiled SMAPI assembly: PASS")
    print("- test-only manifest and required V2 dependency: PASS")
    print("- all/control/rarity/1..10 command routing: PASS")
    print("- 10 names and qualified IDs match the CP pack in order: PASS")
    print("- distribution contains only DLL, manifest, and README: PASS")
    print(f"- DLL SHA-256: {digest}")
    print("- runtime in game: UNTESTED")


if __name__ == "__main__":
    main()
