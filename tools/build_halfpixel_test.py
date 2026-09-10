"""Does Fashion Sense preserve crisp nearest-neighbour rendering at HALF-PIXEL
HeadPosition offsets?

Not assumed either way. `Position` is declared `int X, int Y`, but the draw
path passes Vector2 floats to SpriteBatch, so sub-pixel placement is at least
conceivable. The only honest answer comes from the game.

Nine entries, identical art, only HeadPosition differs:

    baseline            0, 0
    integer controls    X+1, X-1, Y+1, Y-1
    half-pixel tests    X+0.5, X-0.5, Y+0.5, Y-0.5

A half-pixel offset is 2 screen pixels at Scale 4. If it works, those entries
land 2px from baseline and stay crisp. If the value is rounded, they will be
pixel-identical to baseline or to a neighbouring integer entry. If it is
rejected, the model fails to load and draws nothing -- which is itself a
decisive result, and the failure mode this project has already been bitten by.
"""
from __future__ import annotations
import json, os, shutil, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v5 import pngio
from v5.source import audit, pngread
from build_authored_fs_pack import MODS

PACK = Path("test-packs/fashionsense/RNG-HalfPixel")
UNIQUE_ID = "RNGClothing.FashionSense.HalfPixel"
DIRS = ["Front", "Right", "Left", "Back"]

CASES = [
    ("HP0Base",   "baseline 0,0",   0,    0),
    ("HP1XPlus1", "X +1 (integer)", 1,    0),
    ("HP2XMin1",  "X -1 (integer)", -1,   0),
    ("HP3YPlus1", "Y +1 (integer)", 0,    1),
    ("HP4YMin1",  "Y -1 (integer)", 0,   -1),
    ("HP5XPlusH", "X +0.5",         0.5,  0),
    ("HP6XMinH",  "X -0.5",        -0.5,  0),
    ("HP7YPlusH", "Y +0.5",         0,    0.5),
    ("HP8YMinH",  "Y -0.5",         0,   -0.5),
]


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
        "Name": "RNG Half-Pixel Offset Test", "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Identical art, HeadPosition varied by whole and half pixels.",
        "UniqueID": UNIQUE_ID, "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"}}, indent=2))
    rows = []
    for d in DIRS:
        rows.extend([list(r) for r in frames[d]])
    trace = []
    for folder, label, dx, dy in CASES:
        p = PACK / "Hats" / folder
        p.mkdir(parents=True, exist_ok=True)
        pngio.write_rgba_png(p / "hat.png", rows)
        doc = {"Name": f"HP {label}", "Format": "7.5.0",
               "Tags": ["RNG Clothing", "half-pixel test", label]}
        for j, dd in enumerate(DIRS):
            doc[f"{dd}Hat"] = {
                "DisableGrayscale": True,
                "HatSize": {"Width": 20, "Length": 20},
                "StartingPosition": {"X": 0, "Y": j * 20},
                # written EXACTLY as given: 0.5 stays 0.5 in the JSON
                "HeadPosition": {"X": dx, "Y": dy},
            }
        (p / "hat.json").write_text(json.dumps(doc, indent=2))
        trace.append({"folder": folder, "label": label, "dx": dx, "dy": dy,
                      "is_half": (dx % 1 != 0) or (dy % 1 != 0)})
        print(f"  {folder:10s} {label:16s} HeadPosition {{X:{dx}, Y:{dy}}}")
    (PACK / "trace.json").write_text(json.dumps(trace, indent=2))
    if install:
        dest = MODS / PACK.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(PACK, dest)
        print("installed ->", dest)


if __name__ == "__main__":
    main()
