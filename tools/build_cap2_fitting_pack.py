"""Cap 2 pack for the fitting milestone: real inventory items + fitting sidecars.

Same controlled-random roller as every other Cap 2 proof -- the caps are not
hand-picked. What is new is that each cap declares `Item`, so it exists as a
real Stardew hat the vanilla sewing machine can hold, and carries fitting.json
for the fitting mod.
"""
from __future__ import annotations
import json, os, shutil, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v5 import authored
from v5.source import cap2_pack
from v5.source.cap2_gen import Cap2Generator
from build_authored_fs_pack import MODS

PACK = Path("test-packs/fashionsense/RNG-Cap2Fit")
UNIQUE_ID = "RNGClothing.FashionSense.Cap2Fit"
SEEDS = [530893608, 905331759, 846106117, 721353155, 402965280, 848440889]


def main():
    install = "--install" in sys.argv
    gen = Cap2Generator(authored.load())
    if PACK.exists():
        shutil.rmtree(PACK)
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)
    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Cap 2 (Fitting)",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Generated from 'Cap 2' by plurffle (More Accessories "
                       "and Stuff). Base art unmodified. Declares Item so the "
                       "caps are real in-game hats.",
        "UniqueID": UNIQUE_ID, "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"}}, indent=2))
    trace = []
    for i, seed in enumerate(SEEDS, 1):
        spec = gen.roll(seed)
        frames = gen.render(spec)
        name = spec.label()
        folder = PACK / "Hats" / f"Cap{i:02d}"
        side = cap2_pack.write_cap(
            str(folder), spec, gen, frames, pack_id=UNIQUE_ID, name=name,
            price=250,
            description="A soft cap. Adjustable at a sewing machine.",
            tags=["RNG Clothing", "Cap 2", "Art by plurffle",
                  spec.rarity, spec.palette_id, spec.motif_id])
        trace.append({"folder": folder.name, "seed": seed, "name": name,
                      "item_id": side["item_id"], "rarity": spec.rarity,
                      "motif": spec.motif_id, "closure": spec.closure_id,
                      "palette": spec.palette_id,
                      "default_head_position": side["hat"]["default_head_position"],
                      "motif_cells": side["motif"]["cells"]})
        print(f"  {folder.name}  {name}")
        print(f"      item  {side['item_id']}")
        print(f"      motif {spec.motif_id:10s} cells={len(side['motif']['cells'])}"
              f"  safe={len(side['motif']['safe_cells'])}"
              f"  default HP Front={side['hat']['default_head_position']['Front']}")
    (PACK / "trace.json").write_text(json.dumps(trace, indent=2))
    (PACK / "CREDITS.txt").write_text(
        "Base art: 'Cap 2' from More Accessories and Stuff, by plurffle.\n"
        "Silhouette, visor, crown, side profile and shading are unmodified.\n")
    if install:
        dest = MODS / PACK.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(PACK, dest)
        print("installed ->", dest)


if __name__ == "__main__":
    main()
