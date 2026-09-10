"""Curated in-game checkpoint for the DECORATION layer.

Not an exhaustive batch: a chosen set that spreads four bases across several
motif types, with a plain control for each base so a motif's effect can be
judged against the same hat without it.

Excluded on purpose:
  * brim_edge — its in-game failure was measured on the pre-rework art and it
    has never been captured since, so it stays out of a checkpoint meant to
    validate things we believe in.
  * side_pin — read as a highlight in game; it has since been reclassified as
    an attachment, but that version is offline-only too.

Everything else is unchanged: fitted offsets from authored/fit.json, the
reference-derived tone profiles, the curated palettes and the existing pipeline.

    python3 tools/build_decorated_checkpoint_pack.py --install
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from v5 import authored                                    # noqa: E402
from v5.pngio import write_rgba_png                        # noqa: E402
from build_authored_fs_pack import fit_for                 # noqa: E402

PACK = Path("test-packs/fashionsense/RNG-Authored-Decoration-Checkpoint")
UNIQUE_ID = "RNGClothing.FashionSense.AuthoredDecorationCheckpoint"
MODS = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods")

SHORT = {"felt_hat": "Felt", "wide_brim_hat": "Wide", "soft_cap": "Cap",
         "knit_cap": "Knit"}

# (base, style, palette, motifs)  — a mix of one-motif hats, two-motif hats in
# NON-COMPETING regions, and two plain controls.  Only motifs that scored KEEP
# in the library review are used; brim_edge and side_pin are excluded because
# their in-game evidence is either bad or missing.
CURATED = [
    # --- felt_hat ---------------------------------------------------------
    ("felt_hat", "formal", "GOTHIC_WINE_ASH", []),                       # control
    ("felt_hat", "formal", "GOTHIC_WINE_ASH", ["band_buckled"]),
    ("felt_hat", "formal", "FORMAL_PEARL_MIDNIGHT", ["buckle_square"]),
    ("felt_hat", "work", "WORKWEAR_DENIM_RUST", ["band_plain", "crown_patch"]),
    ("felt_hat", "smart", "WINTER_FROST_INK", ["brim_band"]),
    ("felt_hat", "formal", "CELESTIAL_INDIGO_STAR", ["band_laced"]),

    # --- wide_brim_hat ----------------------------------------------------
    ("wide_brim_hat", "cottagecore", "AUTUMN_OCHRE_PLUM", ["band_woven"]),
    ("wide_brim_hat", "festival", "LUXURY_JADE_BRONZE",
     ["band_striped", "side_feather"]),
    ("wide_brim_hat", "festival", "DESERT_CLAY_TURQUOISE", ["brim_lace"]),
    ("wide_brim_hat", "cottagecore", "SPRING_SAGE_PETAL",
     ["band_braided", "ribbon_tail"]),

    # --- soft_cap ---------------------------------------------------------
    ("soft_cap", "smart", "EVERYDAY_STONE_BLUE", ["band_plain", "crown_button"]),
    ("soft_cap", "casual", "DESERT_CLAY_TURQUOISE", ["band_striped"]),

    # --- knit_cap ---------------------------------------------------------
    ("knit_cap", "casual", "COASTAL_SEAFOAM_CORAL", []),                 # control
    ("knit_cap", "cottagecore", "SPRING_SAGE_PETAL", ["cuff_stripe", "top_pom"]),
    ("knit_cap", "cottagecore", "AUTUMN_OCHRE_PLUM", ["pom_tassel"]),
    ("knit_cap", "work", "FIELD_CANVAS_MOSS", ["cuff_stripe", "pom_small"]),

    # --- diagnostics for the borderline motifs --------------------------
    # band_woven fragmented on the wide brim but is clean on a cap: same motif,
    # different base, captured side by side to see whether that holds.
    ("soft_cap", "cottagecore", "AUTUMN_OCHRE_PLUM", ["band_woven"]),
    # brim_lace alternates light/dark and fragmented; brim_band is the SOLID
    # run of the same idea.  They cannot share a palette — lace is
    # cottagecore/festival and the band is formal/smart/work, disjoint sets —
    # so the comparison is same BASE, nearest legal palettes, and the question
    # is only whether alternation fragments where a solid run does not.
    ("wide_brim_hat", "cottagecore", "SPRING_SAGE_PETAL", ["brim_lace"]),
    ("wide_brim_hat", "work", "FIELD_CANVAS_MOSS", ["brim_band"]),
    # the braided band and the ribbon tail fragmented together; isolate each
    ("wide_brim_hat", "cottagecore", "SPRING_SAGE_PETAL", ["band_braided"]),
    ("wide_brim_hat", "cottagecore", "SPRING_SAGE_PETAL", ["ribbon_tail"]),
]


def hat_json(g, name: str) -> dict:
    w, h = g.base.size
    dx, dy = fit_for(g.base.name)
    keys = {"front": "FrontHat", "right": "RightHat",
            "left": "LeftHat", "back": "BackHat"}
    out = {"Name": name,
           "Tags": ["RNG Clothing", "Decoration Checkpoint", g.base.name,
                    g.style, g.palette.id, f"fit {dx:+d},{dy:+d}",
                    *(d.name for d in g.decals)]}
    for i, direction in enumerate(authored.ATLAS_ORDER):
        out[keys[direction]] = {
            "DisableGrayscale": True,
            "HideHair": False,
            "HatSize": {"Width": w, "Length": h},
            "StartingPosition": {"X": 0, "Y": i * h},
            # ints only: Fashion Sense rejects a float here and silently loads
            # no hats from the pack
            "HeadPosition": {"X": int(dx), "Y": int(dy)},
        }
    return out


def build(install: bool = False) -> None:
    lib = authored.load()
    if PACK.exists():
        shutil.rmtree(PACK)
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)
    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Authored Decoration Checkpoint",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Curated decorated hats: four authored bases, a plain "
                       "control each, and the motifs that read at native scale.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"},
    }, indent=2))

    trace = []
    for i, (base, style, palette, motifs) in enumerate(CURATED, 1):
        g = authored.build(base, palette, motifs, lib, style=style)
        if g.dropped:
            raise SystemExit(f"{base}+{motifs} drops cells: {g.dropped}")
        regions = [authored.region_of(d) for d in g.decals]
        if len(regions) != len(set(regions)):
            raise SystemExit(f"{base}+{motifs} puts two motifs in one region: {regions}")
        tag = "".join(m.split("_")[0][:3].title() for m in motifs) or "Plain"
        folder = f"Dec{i:02d}{SHORT[base]}{tag}"
        d = PACK / "Hats" / folder
        d.mkdir(parents=True, exist_ok=True)
        write_rgba_png(d / "hat.png", authored.atlas(g))
        label = f"{SHORT[base]} {i:02d} " + (" + ".join(motifs) or "plain")
        (d / "hat.json").write_text(json.dumps(hat_json(g, label), indent=2))
        trace.append({"folder": folder, "base": base, "style": style,
                      "palette": palette, "motifs": motifs})

    (PACK / "TRACEABILITY.json").write_text(json.dumps(
        {"pack_unique_id": UNIQUE_ID,
         "excluded": {"brim_edge": "reads as two dots at native scale"},
         "entries": trace}, indent=2))
    if install:
        dest = MODS / PACK.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(PACK, dest)
        print(f"installed -> {dest}")
    print(f"{len(trace)} curated hats -> {PACK}")
    for t in trace:
        print(f"  {t['folder']:22s} {t['base']:14s} {t['style']:12s} "
              f"{t['palette'][:22]:24s} {t['motifs']}")


if __name__ == "__main__":
    build(install="--install" in sys.argv)
