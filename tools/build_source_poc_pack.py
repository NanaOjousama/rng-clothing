"""Fashion Sense pack for the authored-source proof of concept.

Exports the remix variants through the SAME pipeline shape the existing
authored exporter uses -- native frames, four directions stacked, integer
HeadPosition -- so the QC Bridge can capture them with no special handling.

Every hat.json carries its source provenance in Tags, so an item generated
from someone else's art can always be traced back to them.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored, pngio
from v5.source import library, render

PACK = Path("test-packs/fashionsense/RNG-SourcePoC")
UNIQUE_ID = "RNGClothing.FashionSense.SourcePoC"
MODS = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods")
FS_ORDER = ["Front", "Right", "Left", "Back"]

HATS = [("EVERYDAY_STONE_BLUE", ""), ("EVERYDAY_STONE_BLUE", "Leaf"),
        ("AUTUMN_OCHRE_PLUM", "Dotted"), ("SPRING_SAGE_PETAL", "Leaf"),
        ("COASTAL_SEAFOAM_CORAL", "")]
SHIRTS = [("Blouse", "COASTAL_SEAFOAM_CORAL"),
          ("Blouse (Frill Trim)", "AUTUMN_OCHRE_PLUM"),
          ("Blouse (Lacy)", "FORMAL_PEARL_MIDNIGHT")]


# Per-direction properties that decide how a garment WEARS.  They are carried
# from the source author's own declaration, because they are not recoverable
# from the pixels and getting them wrong misplaces correct art.
#
# This exporter used to hardcode HeadPosition {0, 0}.  293 of the 462 direction
# blocks in the source library declare a NON-ZERO HeadPosition, so 63% of
# source-derived hats were re-anchored by up to (-3, -4) sprite pixels -- 12 to
# 16 screen pixels -- which is why they wore badly despite reconstructing to
# byte-identical pixels.  Pixel fidelity was never the thing that was broken.
WEAR_PROPS = ("HeadPosition", "BodyPosition", "Scale", "Flipped",
              "HideHair", "UseBaldHead", "DrawOrderOverride",
              "HideWhileSwimming", "HideWhileWearingBathingSuit",
              "HidePlayerBase", "HideSleeves", "RequireAnimationToFinish")


def wear_from(base, direction):
    """The source's own wear properties for one direction, or safe defaults."""
    blk = base.wear_props(direction) if hasattr(base, "wear_props") else {}
    out = {k: v for k, v in blk.items() if k in WEAR_PROPS}
    out.setdefault("HeadPosition", {"X": 0, "Y": 0})
    for key in ("X", "Y"):
        v = out["HeadPosition"].get(key, 0)
        if int(v) != v:
            raise ValueError(f"HeadPosition.{key} must be an integer; a float "
                             f"makes Fashion Sense reject the whole model")
        out["HeadPosition"][key] = int(v)
    return out


def hat_json(name, size, credit, tags, base=None):
    w, h = size
    out = {"Name": name, "Format": "7.5.0",
           "Tags": tags + [credit["short"]]}
    for i, d in enumerate(FS_ORDER):
        out[f"{d}Hat"] = {
            "DisableGrayscale": True,      # we bake colour; FS must not tint
            **wear_from(base, d),
            "HatSize": {"Width": w, "Length": h},
            "StartingPosition": {"X": 0, "Y": i * h},
        }
    return out


def shirt_json(name, size, credit, tags, base=None):
    w, h = size
    out = {"Name": name, "Format": "7.5.0",
           "Tags": tags + [credit["short"]]}
    for i, d in enumerate(FS_ORDER):
        blk = {k: v for k, v in (base.wear_props(d) if base else {}).items()
               if k in WEAR_PROPS}
        blk.setdefault("BodyPosition", {"X": 0, "Y": 0})
        out[f"{d}Shirt"] = {
            "DisableGrayscale": True,
            **blk,
            "ShirtSize": {"Width": w, "Length": h},
            "StartingPosition": {"X": 0, "Y": i * h},
        }
    return out


def main():
    install = "--install" in sys.argv
    bases, comps = library.load()
    lib = authored.load()
    if PACK.exists():
        shutil.rmtree(PACK)
    for sub in ("Hats", "Shirts"):
        (PACK / sub).mkdir(parents=True, exist_ok=True)

    contributors = set()
    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Authored-Source Proof of Concept",
        "Author": "RNG Clothing Experiment",
        "Version": "0.1.0",
        "Description": "Generated from authored source art; see each item's "
                       "tags for the original pack and artist.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"},
    }, indent=2))

    trace, idx = [], 0
    beret = next(b for b in bases if b.name == "Beret")
    for pal_id, qual in HATS:
        pal = next(p for p in lib.palettes if p.id == pal_id)
        use = [c for c in comps if c.family == "Beret" and c.qualifier == qual]
        frames = render.render(beret, pal, use)
        idx += 1
        cred = render.credits_for(beret, use)
        contributors.update(cred["authors"])
        folder = f"Src{idx:02d}Beret{qual or 'Plain'}"
        d = PACK / "Hats" / folder
        d.mkdir(parents=True, exist_ok=True)
        pngio.write_rgba_png(d / "hat.png",
                             render.atlas(frames, FS_ORDER, beret.size))
        label = f"Beret {qual or 'Plain'} {pal.identity}"
        (d / "hat.json").write_text(json.dumps(
            hat_json(label, beret.size, cred,
                     ["RNG Clothing", "Authored Source", "Beret", pal_id],
                     base=beret),
            indent=2))
        trace.append({"folder": folder, "label": label, "base": beret.name,
                      "component": qual, "palette": pal_id,
                      "credit": cred})

    for base_name, pal_id in SHIRTS:
        base = next(b for b in bases if b.name == base_name)
        pal = next(p for p in lib.palettes if p.id == pal_id)
        frames = render.render(base, pal)
        idx += 1
        cred = render.credits_for(base)
        contributors.update(cred["authors"])
        folder = f"Src{idx:02d}" + base_name.replace(" ", "").replace("(", "").replace(")", "")
        d = PACK / "Shirts" / folder
        d.mkdir(parents=True, exist_ok=True)
        pngio.write_rgba_png(d / "shirt.png",
                             render.atlas(frames, FS_ORDER, base.size))
        label = f"{base_name} {pal.identity}"
        (d / "shirt.json").write_text(json.dumps(
            shirt_json(label, base.size, cred,
                       ["RNG Clothing", "Authored Source", pal_id],
                       base=base), indent=2))
        trace.append({"folder": folder, "label": label, "base": base_name,
                      "palette": pal_id, "credit": cred})

    (PACK / "CREDITS.txt").write_text(
        "This pack contains items generated from authored source art.\n\n"
        "Original artists: " + ", ".join(sorted(contributors)) + "\n\n"
        + "\n".join(f"{t['label']}\n    {t['credit']['text']}" for t in trace)
        + "\n")
    (PACK / "trace.json").write_text(json.dumps(trace, indent=2))
    for t in trace:
        print(f"  {t['folder']:26s} {t['label'][:36]:38s} {t['credit']['short']}")
    if install:
        dest = MODS / PACK.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(PACK, dest)
        print("installed ->", dest)


if __name__ == "__main__":
    main()
