"""SOURCE PACK ROUND-TRIP WEAR FIDELITY — the A/B/C in-game test.

    A  the author's file, byte-for-byte
    B  the same hat ingested and re-exported through our pipeline
    C  our current generated soft_cap, as the known-bad comparison

A and B must look IDENTICAL when worn.  Not "reconstruct to the same PNG" —
that was already true of the broken exporter, which is the whole reason this
test exists.  How a hat wears is decided by the model properties around the
pixels, and those are what a round-trip has to carry.

All three go in ONE pack so a single capture session covers them: same scene,
same hairstyle, same lighting, same pose.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored, hairpolicy, pngio
from v5.source import roundtrip
from build_authored_fs_pack import fit_for, MODS

PACK = Path("test-packs/fashionsense/RNG-RoundTrip")
UNIQUE_ID = "RNGClothing.FashionSense.RoundTrip"
SUBJECT = ("Beanie", "More Accessories")     # name, pack prefix


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def main():
    install = "--install" in sys.argv
    cat = json.load(open("source_catalog/catalog.json"))
    app = next(a for a in cat["appearances"]
               if a["name"] == SUBJECT[0] and a["pack"].startswith(SUBJECT[1]))

    if PACK.exists():
        shutil.rmtree(PACK)
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)
    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Round-Trip Wear Fidelity",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "A: original author files verbatim. B: the same hat "
                       "round-tripped through our pipeline. C: our soft_cap.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"},
    }, indent=2))

    report = {"subject": {"pack": app["pack"], "author": app["pack_author"],
                          "asset": app["name"]}}

    # ---- A: the author's own files, copied without a single byte changed ----
    a_dir = PACK / "Hats" / "A_Original"
    a_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(app["json_path"], a_dir / "hat.json")
    shutil.copyfile(app["png_path"], a_dir / "hat.png")
    report["A"] = {
        "json_sha": sha(app["json_path"]), "png_sha": sha(app["png_path"]),
        "json_sha_copied": sha(a_dir / "hat.json"),
        "png_sha_copied": sha(a_dir / "hat.png"),
        "note": "byte-identical to the source; only the enclosing pack differs",
    }

    # ---- B: the same hat, through our pipeline ----
    doc, atlas, rt = roundtrip.export(app, name=f"{app['name']} (Round Trip)")
    cmp = roundtrip.compare(app, doc)
    b_dir = PACK / "Hats" / "B_RoundTrip"
    b_dir.mkdir(parents=True, exist_ok=True)
    pngio.write_rgba_png(b_dir / "hat.png", atlas)
    (b_dir / "hat.json").write_text(json.dumps(doc, indent=2))
    report["B"] = {"export": rt, "property_compare": cmp}

    # ---- C: our current generated soft_cap, the known-bad reference ----
    cap = authored.build("soft_cap", "EVERYDAY_STONE_BLUE")
    c_dir = PACK / "Hats" / "C_SoftCap"
    c_dir.mkdir(parents=True, exist_ok=True)
    pngio.write_rgba_png(c_dir / "hat.png", authored.atlas(cap))
    w, h = cap.base.size
    dx, dy = fit_for("soft_cap")
    hair = hairpolicy.for_base("soft_cap")
    cdoc = {"Name": "C soft_cap (ours, comparison)", "Format": "7.5.0",
            "Tags": ["RNG Clothing", "Round Trip", "comparison"]}
    for i, d in enumerate(authored.ATLAS_ORDER):
        cdoc[f"{d.capitalize()}Hat"] = {
            "DisableGrayscale": True,
            **hairpolicy.flags(hair[d]),
            "HatSize": {"Width": w, "Length": h},
            "StartingPosition": {"X": 0, "Y": i * h},
            "HeadPosition": {"X": int(dx), "Y": int(dy)},
        }
    (c_dir / "hat.json").write_text(json.dumps(cdoc, indent=2))
    report["C"] = {"base": "soft_cap", "head_position": [int(dx), int(dy)]}

    (PACK / "roundtrip_report.json").write_text(json.dumps(report, indent=2))

    print(f"subject: {app['name']!r} — {app['pack']} by {app['pack_author']}")
    print(f"  A  verbatim copy   json {report['A']['json_sha']} "
          f"-> {report['A']['json_sha_copied']}  "
          f"png {report['A']['png_sha']} -> {report['A']['png_sha_copied']}")
    print(f"  B  round-tripped   carried {sorted(rt['properties_carried'])}")
    print(f"     dropped {rt['properties_dropped'] or 'nothing'}   "
          f"property differences vs source: {len(cmp['differences'])}")
    print(f"  C  soft_cap        HeadPosition {report['C']['head_position']}")
    if install:
        dest = MODS / PACK.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(PACK, dest)
        print("installed ->", dest)


if __name__ == "__main__":
    main()
