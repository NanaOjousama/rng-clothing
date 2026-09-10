"""Fashion Sense pack for ONE question: does the wider cap still wear naturally?

Three hats, same palette, same offsets, no decoration:

    Cap01Orig    the approved 10-wide cap, rebuilt from the recovered art
    Cap02Wide    +1 cell per side; fixed the sides, left the head on top
    Cap03Tall    +1 crown row and a 4-cell apex; still buried under the hair
    Cap04Flare   aperture flared to the head width  <- the candidate
    Cap05Felt    felt_hat, the seating control every earlier session used

Putting the original in the SAME session is the point: FS bakes fit at pack
load, and capture lighting/pose vary between sessions, so an across-session
comparison of two caps is not a comparison of two caps.  Here the only thing
that differs between the first two entries is the two cells of width.

Nothing about the art, palette, tone, offsets or zones is touched by this
script — it reads `authored/` and `authored/fit.json` and writes a pack.

    python3 tools/build_softcap_size_pack.py [--install]
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from v5 import authored                                     # noqa: E402
from v5.pngio import write_rgba_png                         # noqa: E402
from build_authored_fs_pack import fit_for, hat_json, MODS   # noqa: E402
from review_softcap_enlargement import orig_cells, paint     # noqa: E402

PACK = Path("test-packs/fashionsense/RNG-SoftCap-Size")
UNIQUE_ID = "RNGClothing.FashionSense.SoftCapSize"
PAL = "EVERYDAY_STONE_BLUE"


def original_atlas(lib):
    """The approved cap's four frames, painted through its own tone profile."""
    cap = next(b for b in lib.bases if b.name == "soft_cap")
    pal = next(p for p in lib.palettes if p.id == PAL)
    tone = lib.tone_for(cap)
    oc = orig_cells()
    rows = []
    for view in authored.ATLAS_ORDER:
        rows.extend(paint(oc[view], pal, tone))
    return rows


# The width-only step, kept so the three-way in-game comparison isolates each
# change: original -> wider -> wider and one row taller.
WIDE_ONLY = {
    "front": ["", "", "", "",
              ".........33.........",
              "......22444422......",
              ".....2456666542.....",
              "....244555666552....",
              "....244433335662....",
              "....244345543552....",
              "....233433334332....",
              "....22.......222...."],
    "left": ["", "", "", "",
             ".........33.........",
             "......33444432......",
             ".....3555555432.....",
             "..33335666554432....",
             ".354436665545442....",
             ".345545555454432....",
             "..32244332222222...."],
    "back": ["", "", "", "", "",
             "......33333333......",
             ".....3445555443.....",
             "....344454565443....",
             "....344445455553....",
             "....144444545441....",
             "....133444444331....",
             "....133311113331....",
             "....131......131....",
             ".....1111111111....."],
}


# The pre-flare candidate, kept so the in-game A/B isolates the aperture change
# alone: same crown, same height, same apex, same peak tip.
TALL = {
    "front": ["", "", "",
              "........3443........",
              "......22444422......",
              ".....2456666542.....",
              "....244555666552....",
              "....244455566552....",
              "....244433335662....",
              "....244345543552....",
              "....233433334332....",
              "....22.......222...."],
    "left": ["", "", "",
             "........3443........",
             "......33444432......",
             ".....3555555432.....",
             "..33335666554432....",
             ".354436665545442....",
             ".345536655545442....",
             ".345545555454432....",
             "..32244332222222...."],
    "back": ["", "", "", "",
             "......33333333......",
             ".....3445555443.....",
             "....344454565443....",
             "....344445455553....",
             "....144444545441....",
             "....133444444331....",
             "....133311113331....",
             "....131......131....",
             ".....1111111111....."],
}


def _atlas_from_art(lib, art):
    cap = next(b for b in lib.bases if b.name == "soft_cap")
    pal = next(p for p in lib.palettes if p.id == PAL)
    tone = lib.tone_for(cap)
    cells = {}
    for view, rows in art.items():
        cells[view] = {(x, y): ("body", int(ch) - 1)
                       for y, line in enumerate(rows)
                       for x, ch in enumerate(line) if ch != "."}
    cells["right"] = {(19 - x, y): v for (x, y), v in cells["left"].items()}
    rows = []
    for view in authored.ATLAS_ORDER:
        rows.extend(paint(cells[view], pal, tone))
    return rows


def wide_only_atlas(lib):
    return _atlas_from_art(lib, WIDE_ONLY)


def build(install: bool = False) -> dict:
    lib = authored.load()
    if PACK.exists():
        shutil.rmtree(PACK)
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)
    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG SoftCap Size Check",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Original vs +1-cell-per-side soft_cap, plus the felt "
                       "seating control. One palette, no decoration.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"},
    }, indent=2))

    cap = authored.build("soft_cap", PAL, (), lib)
    felt = authored.build("felt_hat", PAL, (), lib)
    entries = [
        ("Cap01Orig", "Cap 01 ORIGINAL 10-wide", original_atlas(lib), cap),
        ("Cap02Wide", "Cap 02 WIDE only", wide_only_atlas(lib), cap),
        ("Cap03Tall", "Cap 03 WIDE + crown row", _atlas_from_art(lib, TALL), cap),
        ("Cap04Flare", "Cap 04 FLARED aperture", authored.atlas(cap), cap),
        ("Cap05Felt", "Cap 05 felt control", authored.atlas(felt), felt),
    ]
    trace = []
    for i, (folder, label, atlas, g) in enumerate(entries, 1):
        d = PACK / "Hats" / folder
        d.mkdir(parents=True, exist_ok=True)
        write_rgba_png(d / "hat.png", atlas)
        (d / "hat.json").write_text(json.dumps(hat_json(g, label, i), indent=2))
        dx, dy = fit_for(g.base.name)
        trace.append({"folder": folder, "label": label, "base": g.base.name,
                      "palette": PAL, "fit": [dx, dy]})
        print(f"  {folder}  {label}  fit {dx:+d},{dy:+d}")

    (PACK / "trace.json").write_text(json.dumps(trace, indent=2))
    if install:
        dest = MODS / PACK.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(PACK, dest)
        print(f"installed -> {dest}")
    return {"pack": str(PACK), "hats": trace}


if __name__ == "__main__":
    build("--install" in sys.argv)
