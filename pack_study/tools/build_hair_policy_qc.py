#!/usr/bin/env python3
"""Build an isolated FS hair-visibility A/B pack from the already installed QC2 hats.

Never edits the source hat folders. A and B preserve every source property and
sprite byte; only Name and four per-view HideHair flags differ.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil

PAIRS = (("01", "Propeller Cap"), ("05", "Messy Straw"), ("10", "Blue Straw"))
VIEWS = ("FrontHat", "RightHat", "LeftHat", "BackHat")
ID = "PackStudy.HairPolicyQC"

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def build(source: Path, output: Path) -> list[dict]:
    if source.resolve() == output.resolve() or output.resolve().is_relative_to(source.resolve()):
        raise ValueError("Output must be separate from source")
    if not (source / "manifest.json").is_file():
        raise FileNotFoundError(f"QC2 source pack not found: {source}")
    sources = {}
    for number, label in PAIRS:
        found = sorted((source / "Hats").glob(f"PSQC2 {number} */hat.json"))
        if len(found) != 1:
            raise RuntimeError(f"Expected exactly one QC2 {number} hat, found {len(found)}")
        sources[number] = (label, found[0].parent)
    if output.exists():
        # Only accept rebuilding over our own generated pack.
        manifest = output / "manifest.json"
        if not manifest.is_file() or json.loads(manifest.read_text(encoding="utf-8")).get("UniqueID") != ID:
            raise RuntimeError(f"Refusing to overwrite non-HairPolicyQC output: {output}")
        shutil.rmtree(output)
    (output / "Hats").mkdir(parents=True)
    original_manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    original_manifest.update({
        "Name": "PackStudy Hair Policy A-B QC",
        "Version": "0.1.0",
        "Description": "Six controlled hair-on/off variants of three QC2 hats; test only",
        "UniqueID": ID,
    })
    (output / "manifest.json").write_text(json.dumps(original_manifest, indent=2) + "\n", encoding="utf-8")
    entries = []
    for number, (label, hat_folder) in sources.items():
        original_json = json.loads((hat_folder / "hat.json").read_text(encoding="utf-8"))
        source_sha = sha256(hat_folder / "hat.png")
        for enabled in (False, True):
            suffix = "HAIR OFF" if enabled else "HAIR ON"
            name = f"HPQC {number} {label} - {suffix}"
            dst = output / "Hats" / name
            dst.mkdir()
            doc = json.loads(json.dumps(original_json))
            doc["Name"] = name
            for view in VIEWS:
                if view not in doc:
                    raise RuntimeError(f"Missing view {view} in {hat_folder}")
                doc[view]["HideHair"] = enabled
            (dst / "hat.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
            shutil.copy2(hat_folder / "hat.png", dst / "hat.png")
            assert sha256(dst / "hat.png") == source_sha
            entries.append({"name": name, "source": hat_folder.name, "hide_hair": enabled, "sprite_sha256": source_sha})
    (output / "test_index.json").write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    (output / "README.txt").write_text(
        "PackStudy controlled Fashion Sense hair-visibility A/B test.\n"
        "Exactly six hats: cap, messy straw, blue straw; HAIR ON versus HAIR OFF.\n"
        "All original hat pixels and all frame sizes / offsets are identical.\n"
        "Only name and HideHair properties vary.\n"
        "Use the Fashion Sense Hand Mirror Hats tab. Compare different hairstyles and\n"
        "all 4 directions. Don't judge silhouette problems as hair errors.\n"
        "QC2 is separate, untouched. This is an optional test pack, not final content.\n",
        encoding="utf-8",
    )
    return entries

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    entries = build(a.source, a.output)
    print(f"Built {len(entries)} hats at {a.output}")
    for e in entries:
        print(f"  {e['name']}: hide_hair={e['hide_hair']}")
