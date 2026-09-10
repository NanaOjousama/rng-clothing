"""EXPERIMENTAL Cap 2 pack using the row-8 extended motif mask.

A SEPARATE pack, deliberately. The approved 16-cell mask and the RNG-Cap2Fit
pack built from it are left exactly as they are, so both can be worn in the
same session and judged against each other on the farmer rather than in a
contact sheet.

Same seeds as RNG-Cap2Fit, so each cap differs from its counterpart ONLY in
where the motif is allowed to sit.
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
from build_cap2_fitting_pack import SEEDS

PACK = Path("test-packs/fashionsense/RNG-Cap2Row8")
UNIQUE_ID = "RNGClothing.FashionSense.Cap2Row8"
EXT_MASK = "authored/source_bases/cap2/motif_safe_mask_ext8.json"


def main():
    install = "--install" in sys.argv
    gen = Cap2Generator(authored.load())

    # swap in the extended mask BEFORE rolling, so placement, validation and the
    # emitted sidecar all agree on the same surface
    ext = {tuple(c) for c in json.load(open(EXT_MASK))["safe_cells"]}
    added = sorted(ext - gen.safe)
    gen.safe = ext
    print(f"extended mask: {len(gen.safe)} cells (+{len(added)} on row 8)")

    if PACK.exists():
        shutil.rmtree(PACK)
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)
    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Cap 2 (row-8 experiment)",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "EXPERIMENTAL. Same seeds as RNG-Cap2Fit, but the motif "
                       "safe mask includes row 8, so designs sit one row lower "
                       "and press against the peak. For judging in game.",
        "UniqueID": UNIQUE_ID, "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"}}, indent=2))

    trace = []
    for i, seed in enumerate(SEEDS, 1):
        spec = gen.roll(seed)
        frames = gen.render(spec)
        name = spec.label().replace("Cap2 ", "Cap2r8 ")
        folder = PACK / "Hats" / f"Cap{i:02d}"
        side = cap2_pack.write_cap(
            str(folder), spec, gen, frames, pack_id=UNIQUE_ID, name=name,
            price=250,
            description="A soft cap. Row-8 mask experiment.",
            tags=["RNG Clothing", "Cap 2", "Art by plurffle", "row8 experiment",
                  spec.rarity, spec.palette_id, spec.motif_id])
        bottom = max((c[1] for c in spec.motif_cells), default=None)
        trace.append({"folder": folder.name, "seed": seed, "name": name,
                      "item_id": side["item_id"], "motif": spec.motif_id,
                      "motif_bottom_row": bottom,
                      "lowered": spec.motif_lowered})
        print(f"  {folder.name}  {name}")
        print(f"      motif {spec.motif_id:10s} bottom row "
              f"{bottom if bottom is not None else '-'}  dropped={spec.motif_lowered}")
        print(f"      item  {side['item_id']}")
    (PACK / "trace.json").write_text(json.dumps(trace, indent=2))
    (PACK / "CREDITS.txt").write_text(
        "Base art: 'Cap 2' from More Accessories and Stuff, by plurffle.\n"
        "Silhouette, visor, crown, side profile and shading are unmodified.\n"
        "EXPERIMENTAL motif placement: row 8 admitted to the safe mask.\n")
    if install:
        dest = MODS / PACK.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(PACK, dest)
        print("installed ->", dest)


if __name__ == "__main__":
    main()
