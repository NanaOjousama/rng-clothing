"""QC-ONLY content pack wrapping the four hats chosen as visual references.

Strictly a measurement fixture:
  * lives under test-packs/qc-only/, never test-packs/fashionsense/
  * its own UniqueID namespace (RNGClothing.QCOnly.*)
  * the art is COPIED VERBATIM and is not ours — it exists so the hats can be
    equipped and captured through the real renderer, and must never be shipped,
    redistributed, or used as a source of pixels for generated output.

We are extracting reusable visual principles from these, not their designs.
"""
from __future__ import annotations

import json
import os
import shutil
import sys

sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing")
from v5.pngio import read_rgba_png                                # noqa: E402

SRC = "/run/media/deck/USD00/RNG_clothing/good hats/"
PACK = "test-packs/qc-only/RNG-QC-Reference-Hats"
UNIQUE_ID = "RNGClothing.QCOnly.ReferenceHats"

# (source png, folder/appearance name, where it came from)
HATS = [
    ("0_BoysCap.png",     "RefBoysCap",   "loose file, 20x80 FS hat sheet"),
    ("1_SweetGent.png",   "RefSweetGent", "loose file, 20x80 FS hat sheet"),
    ("hats_11/hat.png",   "RefHyoung11",  "hyoung_hats_11"),
    ("hats_8/hat.png",    "RefKookoroo8", "Kookoroo_8"),
]


def model(start_y: int) -> dict:
    return {
        "DisableGrayscale": True,
        "StartingPosition": {"X": 0, "Y": start_y},
        "HeadPosition": {"X": 0, "Y": 0},
        "HatSize": {"Width": 20, "Length": 20},
    }


def build() -> None:
    if os.path.exists(PACK):
        shutil.rmtree(PACK)
    os.makedirs(os.path.join(PACK, "Hats"))

    with open(os.path.join(PACK, "manifest.json"), "w") as fh:
        json.dump({
            "Name": "RNG QC Reference Hats (QC ONLY - DO NOT SHIP)",
            "Author": "RNG Clothing project (art by third parties)",
            "Version": "1.0.0",
            "Description": "Measurement fixture. Wraps four externally-authored "
                           "hats so they can be equipped and captured through the "
                           "real Fashion Sense renderer for visual calibration. "
                           "Art is not ours and must not be redistributed.",
            "UniqueID": UNIQUE_ID,
            "UpdateKeys": [],
            "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                               "MinimumVersion": "7.5.0"},
        }, fh, indent=2)

    rows = []
    for src, name, origin in HATS:
        path = os.path.join(SRC, src)
        im = read_rgba_png(path)
        w, h = len(im[0]), len(im)
        if (w, h) != (20, 80):
            raise SystemExit(f"{src} is {w}x{h}, expected 20x80")
        folder = os.path.join(PACK, "Hats", name)
        os.makedirs(folder)
        shutil.copyfile(path, os.path.join(folder, "hat.png"))
        hat = {"Name": name,
               "Tags": ["QC only", "visual reference", "not ours"]}
        for key, y in (("FrontHat", 0), ("RightHat", 20), ("LeftHat", 40), ("BackHat", 60)):
            hat[key] = model(y)
        with open(os.path.join(folder, "hat.json"), "w") as fh:
            json.dump(hat, fh, indent=2)
        rows.append((name, src, origin))

    with open(os.path.join(PACK, "README.md"), "w") as fh:
        fh.write("# QC ONLY — reference hats\n\n"
                 "Not release content. Not our art. Wrapped purely so these hats "
                 "can be equipped and captured through the real Fashion Sense "
                 "renderer, for visual calibration of generated headwear.\n\n"
                 "| appearance | source file | origin |\n|---|---|---|\n"
                 + "".join(f"| `{UNIQUE_ID}/Hat/{n}` | `{s}` | {o} |\n" for n, s, o in rows))
    print(f"{len(rows)} reference hats -> {PACK}")
    for n, s, o in rows:
        print(f"  {UNIQUE_ID}/Hat/{n:<14} <- {s}")


if __name__ == "__main__":
    build()
