"""Does Fashion Sense render cleanly at Scale 0.95 / 1.00 / 1.05?

Scale is a per-direction float on AppearanceModel (default 4f). It is NOT the
same axis as HeadPosition, and this project has never tested it: an earlier
note claimed "FS ignores Scale", but that experiment put Scale at the TOP LEVEL
of hat.json where it belongs to nothing.

The proposed fitting values are relative multipliers, so against the 4.0
default they are 3.8 / 4.0 / 4.2. Non-integer scale means the 20x20 sprite is
resampled, and the question is whether that stays crisp nearest-neighbour or
goes soft.

Identical art in every entry; only Scale differs.
"""
from __future__ import annotations
import json, os, shutil, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v5 import pngio
from v5.source import audit, pngread
from build_authored_fs_pack import MODS

PACK = Path("test-packs/fashionsense/RNG-ScaleTest")
UNIQUE_ID = "RNGClothing.FashionSense.ScaleTest"
DIRS = ["Front", "Right", "Left", "Back"]
CASES = [("SC100", "Scale 4.0 (default)", 4.0),
         ("SC095", "Scale 3.8 (=0.95x)", 3.8),
         ("SC105", "Scale 4.2 (=1.05x)", 4.2),
         ("SC200", "Scale 8.0 (=2x, sanity)", 8.0)]


def main():
    install = "--install" in sys.argv
    cat = json.load(open("source_catalog/catalog.json"))
    app = next(a for a in cat["appearances"]
               if a["name"] == "Cap 2" and a["pack"].startswith("More Acc"))
    px = pngread.read(app["png_path"])
    frames = {d: audit.cut(px, tuple(b))
              for d, b in app["analysis"]["boxes"].items()}
    if PACK.exists():
        shutil.rmtree(PACK)
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)
    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Scale Test", "Author": "RNG Clothing Experiment",
        "Version": "1.0.0", "Description": "Identical art, Scale varied.",
        "UniqueID": UNIQUE_ID, "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"}}, indent=2))
    rows = []
    for d in DIRS:
        rows.extend([list(r) for r in frames[d]])
    trace = []
    for folder, label, scale in CASES:
        p = PACK / "Hats" / folder
        p.mkdir(parents=True, exist_ok=True)
        pngio.write_rgba_png(p / "hat.png", rows)
        doc = {"Name": f"SC {label}", "Format": "7.5.0",
               "Tags": ["RNG Clothing", "scale test", label]}
        for j, dd in enumerate(DIRS):
            doc[f"{dd}Hat"] = {
                "DisableGrayscale": True,
                "HatSize": {"Width": 20, "Length": 20},
                "StartingPosition": {"X": 0, "Y": j * 20},
                "HeadPosition": {"X": 0, "Y": 0},
                "Scale": scale,
            }
        (p / "hat.json").write_text(json.dumps(doc, indent=2))
        trace.append({"folder": folder, "label": label, "scale": scale})
        print(f"  {folder:7s} {label:24s} Scale {scale}")
    (PACK / "trace.json").write_text(json.dumps(trace, indent=2))
    if install:
        dest = MODS / PACK.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(PACK, dest)
        print("installed ->", dest)


if __name__ == "__main__":
    main()
