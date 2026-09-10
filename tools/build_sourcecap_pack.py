"""First source-derived baseball-cap base candidate, through the proven path.

A   'Cap 2' — the author's files, byte-for-byte
B   the same hat round-tripped through our pipeline (no recolour, no dissection,
    no geometry change, every per-direction property preserved)
C   'Cap (Snapback)' — verbatim, so the choice of construction can be judged
D   'Cap 1' — verbatim, same reason

A vs B is the acceptance test.  C and D are context: the requirement is that
the chosen construction visibly wears correctly in its ORIGINAL pack, and that
is a judgement that can only be made by looking at all of them worn.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import pngio
from v5.source import roundtrip
from build_authored_fs_pack import MODS

PACK = Path("test-packs/fashionsense/RNG-SourceCap")
UNIQUE_ID = "RNGClothing.FashionSense.SourceCap"
SUBJECT = "Cap 2"
CONTEXT = ["Cap (Snapback)", "Cap 1"]
PACK_PREFIX = "More Accessories"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def find(cat, name):
    return next(a for a in cat["appearances"]
                if a["name"] == name and a["pack"].startswith(PACK_PREFIX))


def verbatim(app, folder, label):
    d = PACK / "Hats" / folder
    d.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(app["json_path"], d / "hat.json")
    shutil.copyfile(app["png_path"], d / "hat.png")
    return {"folder": folder, "label": label, "mode": "verbatim",
            "json_sha": sha(app["json_path"]), "png_sha": sha(app["png_path"]),
            "json_sha_copied": sha(d / "hat.json"),
            "png_sha_copied": sha(d / "hat.png")}


def main():
    install = "--install" in sys.argv
    cat = json.load(open("source_catalog/catalog.json"))
    subject = find(cat, SUBJECT)

    if PACK.exists():
        shutil.rmtree(PACK)
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)
    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Source Cap Candidate",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Source-authored baseball caps: originals verbatim plus "
                       "one round-tripped through the generator.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"},
    }, indent=2))

    trace = [verbatim(subject, "A_Cap2_Original", "A Cap 2 ORIGINAL")]

    doc, atlas, rt = roundtrip.export(subject, name="B Cap 2 (Round Trip)")
    cmp = roundtrip.compare(subject, doc)
    b = PACK / "Hats" / "B_Cap2_RoundTrip"
    b.mkdir(parents=True, exist_ok=True)
    pngio.write_rgba_png(b / "hat.png", atlas)
    (b / "hat.json").write_text(json.dumps(doc, indent=2))
    trace.append({"folder": "B_Cap2_RoundTrip", "label": "B Cap 2 ROUND TRIP",
                  "mode": "roundtrip", "export": rt, "compare": cmp})

    for i, name in enumerate(CONTEXT):
        app = find(cat, name)
        folder = f"{'CD'[i]}_{name.replace(' ','').replace('(','').replace(')','')}"
        trace.append(verbatim(app, folder, f"{'CD'[i]} {name} ORIGINAL"))

    (PACK / "trace.json").write_text(json.dumps(
        {"subject": {"pack": subject["pack"], "author": subject["pack_author"],
                     "asset": subject["name"]}, "entries": trace}, indent=2))

    print(f"subject: {SUBJECT!r} — {subject['pack']} by {subject['pack_author']}")
    for t in trace:
        if t["mode"] == "verbatim":
            ok = (t["json_sha"] == t["json_sha_copied"]
                  and t["png_sha"] == t["png_sha_copied"])
            print(f"  {t['folder']:22s} verbatim  json {t['json_sha']} "
                  f"png {t['png_sha']}  {'BYTE-IDENTICAL' if ok else 'COPY MISMATCH'}")
        else:
            print(f"  {t['folder']:22s} round-trip  carried "
                  f"{sorted(t['export']['properties_carried'])}")
            print(f"  {'':22s}   dropped {t['export']['properties_dropped'] or 'nothing'}"
                  f"   differences {len(t['compare']['differences'])}")
    if install:
        dest = MODS / PACK.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(PACK, dest)
        print("installed ->", dest)


if __name__ == "__main__":
    main()
