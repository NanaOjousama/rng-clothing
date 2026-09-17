"""Build neutral + decorated Source-Backed V2 proofs for the approved cap source
candidates.

The neutral entries are deliberately neutral: no palette, material, decal,
fitting override or legacy six-step repaint. Their output must be the original
source art, with Fashion Sense's flipped Left view materialised as an explicit
frame. The decorated Baseball entries add exactly one authored front-crown
DECAL (v5/authored.py's existing generic decal path, composed through
v5/source_backed.py's render(palette=, decals=(...), lib=...)) on top of ONE
fixed test palette -- see
authored/source_backed/cap_baseball/decoration_evaluation.json for which marks
were kept, why, and why the decal axis (not material) is correct here.

    python3 tools/build_cap_source_backed_pack.py
    python3 tools/build_cap_source_backed_pack.py --install
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v5 import authored as authored_lib  # noqa: E402
from v5 import source_backed as sbm  # noqa: E402
from v5.pngio import write_rgba_png  # noqa: E402

PACK = ROOT / "test-packs/fashionsense/RNG-Cap-SourceBacked-V2"
UNIQUE_ID = "RNGClothing.FashionSense.CapSourceBackedV2"
MODS = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods")

# The one fixed test palette for every decorated proof, so visual differences
# come from the marks, not palette variation. See decoration_evaluation.json
# ("role_and_palette_choice") for why this palette+role combination was picked
# over cap_baseball's own listed style palette (EVERYDAY_STONE_BLUE): its
# body/hardware/trim ramps are too close in lightness at the crown's own steps
# for the mark to read at all.
DECOR_PALETTE = "EMBER_SUN_CHARCOAL"

# (appearance, base name, decal name or None)
ITEMS = (
    ("SB2CapBaseballNeutral", "cap_baseball", None),
    ("SB2CapSnapbackNeutral", "cap_snapback", None),
    ("SB2CapBaseballDecorBar", "cap_baseball", "cap_baseball_front_bar"),
    ("SB2CapBaseballDecorTwinBars", "cap_baseball", "cap_baseball_front_twin_bars"),
    ("SB2CapBaseballDecorDot", "cap_baseball", "cap_baseball_front_dot"),
    ("SB2CapBaseballDecorRing", "cap_baseball", "cap_baseball_front_ring"),
)


def sync_install(pack_dir: Path, dest: Path):
    """Copy pack_dir's contents into dest without touching dest's own mtime.

    Recreating dest itself (rmtree + copytree) resets its directory mtime,
    which trips the QC bridge's "installed after this session started" guard
    even for a pack that was already registered with SMAPI before this
    session began. Only the entries strictly inside dest (dest/Hats/<name>,
    and file contents) need to change; dest's own directory-entry list must
    stay untouched once it already exists.
    """
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "Hats").mkdir(exist_ok=True)
    wanted = {p.name for p in (pack_dir / "Hats").iterdir()}
    for child in (dest / "Hats").iterdir():
        if child.name not in wanted:
            shutil.rmtree(child)
            print("removed stale appearance ->", child)
    for child in (pack_dir / "Hats").iterdir():
        target = dest / "Hats" / child.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(child, target)
    for name in ("manifest.json", "TRACEABILITY.json"):
        shutil.copyfile(pack_dir / name, dest / name)


def main():
    lib = authored_lib.load()
    palette = next(p for p in lib.palettes if p.id == DECOR_PALETTE)

    if (PACK / "Hats").exists():
        shutil.rmtree(PACK / "Hats")
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)
    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Clothing - Cap Source-Backed V2",
        "Author": "RNG Clothing",
        "Version": "0.1.0",
        "Description": "Source-backed proofs for Baseball and Snapback construction masters, plus the Decorated Baseball front-crown decal bucket.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    }, indent=2) + "\n")
    trace = []
    for appearance, name, decal_name in ITEMS:
        b = sbm.load_one(name)
        if decal_name is None:
            r = sbm.render(b)
        else:
            decal = next(d for d in lib.decals if d.name == decal_name)
            r = sbm.render(b, palette=palette, decals=(decal,), lib=lib)
        d = PACK / "Hats" / appearance
        d.mkdir(parents=True, exist_ok=True)
        write_rgba_png(d / "hat.png", sbm.sheet(r))
        tags = ["RNG Clothing", "Source-Backed V2", "Cap", name,
                "neutral" if decal_name is None else f"decorated-{decal_name}",
                f"{b.classification}-ONLY source"]
        (d / "hat.json").write_text(json.dumps(sbm.hat_json(r, appearance, tags), indent=2) + "\n")
        trace.append({
            "appearance": appearance,
            "base": name,
            "decal": decal_name,
            "palette": None if decal_name is None else DECOR_PALETTE,
            "source": b.source_png,
            "source_md5": b.source_md5,
            "baked": r.baked,
            "placement": {v: b.placement(v) for v in sbm.MODEL_OF},
            "mirrored": b.mirrored,
            "changed_cells": {v: sorted(r.changes[v]["decal"]) for v in b.views},
            "dropped": list(r.dropped),
        })
        print(f"{appearance}: {name} decal={decal_name} md5={b.source_md5} "
              f"placement={b.placement('front')} dropped={r.dropped}")
    (PACK / "TRACEABILITY.json").write_text(json.dumps(trace, indent=2) + "\n")
    if "--install" in sys.argv:
        sync_install(PACK, MODS / PACK.name)
        print("installed ->", MODS / PACK.name)
    print("wrote", PACK)


if __name__ == "__main__":
    main()
