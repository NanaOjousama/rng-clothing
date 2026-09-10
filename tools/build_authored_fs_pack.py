"""Fashion Sense test pack for the four AUTHORED hat bases.

A clean in-game checkpoint of the authored assets exactly as they stand: this
script reads `authored/` and writes a pack.  It does not touch the art, the
palettes or the decals.

Matrix, kept small enough to inspect in one sitting:

    4 bases x 4 curated palettes   = 16 plain hats
    4 bases x its signature decal  =  4 more

Palettes per base are chosen for spread — a light, a dark, a warm and a cool —
from the ones whose style tags the base actually carries, so nothing in the
pack is a combination the combinator would refuse.

    python3 tools/build_authored_fs_pack.py [--install]
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from v5 import authored, hairpolicy                        # noqa: E402
from v5.pngio import write_rgba_png                        # noqa: E402

FIT = Path("authored/fit.json")

PACK = Path("test-packs/fashionsense/RNG-Authored-Hat-Checkpoint")
UNIQUE_ID = "RNGClothing.FashionSense.AuthoredHatCheckpoint"
MODS = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods")

# base -> (four palettes spanning light/dark/warm/cool, signature decal)
MATRIX = {
    "felt_hat": (["FORMAL_PEARL_MIDNIGHT", "GOTHIC_WINE_ASH",
                  "WORKWEAR_DENIM_RUST", "EMBER_SUN_CHARCOAL"], "band_plain"),
    "wide_brim_hat": (["FIELD_CANVAS_MOSS", "DESERT_CLAY_TURQUOISE",
                       "LUXURY_JADE_BRONZE", "AUTUMN_OCHRE_PLUM"],
                      "brim_edge"),
    "soft_cap": (["EVERYDAY_STONE_BLUE", "SPRING_SAGE_PETAL",
                  "WINTER_FROST_INK", "WORKWEAR_DENIM_RUST"], "crown_button"),
    "knit_cap": (["AUTUMN_OCHRE_PLUM", "COASTAL_SEAFOAM_CORAL",
                  "FIELD_CANVAS_MOSS", "PASTEL_PEACH_LILAC"], "top_pom"),
}

SHORT = {"felt_hat": "Felt", "wide_brim_hat": "Wide", "soft_cap": "Cap",
         "knit_cap": "Knit"}


def fit_for(base_name: str) -> tuple:
    """(dx, dy) for a base: its measured default plus the player's own offsets.

    Both are integers because Fashion Sense parses HeadPosition into ints and
    rejects the whole model — silently, loading no hats — if it sees a float.
    """
    fit = json.loads(FIT.read_text())
    d = fit["defaults"].get(base_name, {"HatOffsetX": 0, "HatOffsetY": 0})
    p = fit.get("player", {"HatOffsetX": 0, "HatOffsetY": 0})
    return (int(d["HatOffsetX"] + p.get("HatOffsetX", 0)),
            int(d["HatOffsetY"] + p.get("HatOffsetY", 0)))


def hat_json(g, name: str, index: int) -> dict:
    """The Fashion Sense model.  Four frames stacked at Y = 0/20/40/60.

    HeadPosition carries the fit pass's measured per-base offset (see
    authored/fit.json).  X stays 0 because a native 20x20 frame at Scale 4 is
    already centred on the head box; Y comes from the sweep, where NEGATIVE
    moved the hat down and each base's chosen value put its bottom edge at 39
    screen px below the head top — the figure the four reference hats measure.
    """
    w, h = g.base.size
    dx, dy = fit_for(g.base.name)
    if int(dx) != dx or int(dy) != dy:
        raise ValueError(f"{name}: HeadPosition must be integer; Position is "
                         f"int X/Y in Fashion Sense and a float makes it reject "
                         f"the whole model silently (got {dx},{dy})")
    hair = hairpolicy.for_base(g.base.name)
    keys = {"front": "FrontHat", "right": "RightHat",
            "left": "LeftHat", "back": "BackHat"}
    out = {
        "Name": name,
        # Declared so format-gated behaviour resolves against the version we
        # actually authored against, rather than the 1.0.0 default.
        "Format": "7.5.0",
        "Tags": ["RNG Clothing", "Authored Checkpoint", g.base.name, g.style,
                 g.palette.id, f"fit {dx:+d},{dy:+d}",
                 *(d.name for d in g.decals)],
    }
    missing = [d for d in ("front", "right", "left", "back")
               if d not in authored.ATLAS_ORDER]
    if missing:
        raise ValueError(f"{name}: missing directions {missing}; Fashion Sense "
                         f"draws nothing for a facing whose model is absent — "
                         f"there is no mirroring or fallback")
    for i, direction in enumerate(authored.ATLAS_ORDER):
        out[keys[direction]] = {
            "DisableGrayscale": True,
            **hairpolicy.flags(hair[direction]),
            "HatSize": {"Width": w, "Length": h},
            "StartingPosition": {"X": 0, "Y": i * h},
            "HeadPosition": {"X": dx, "Y": dy},
        }
    return out


def build(install: bool = False) -> dict:
    lib = authored.load()
    if PACK.exists():
        shutil.rmtree(PACK)
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)

    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Authored Hat Checkpoint",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "In-game checkpoint of the four authored hat bases, "
                       "each in four curated palettes, plus one decal variant "
                       "per base. Native 20x20.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"},
    }, indent=2))

    trace, index = [], 0
    for base_name, (palettes, signature) in MATRIX.items():
        for pal in palettes:
            entries = [(pal, ())]
            if pal == palettes[0]:
                entries.append((pal, (signature,)))
            for palette_id, decals in entries:
                g = authored.build(base_name, palette_id, decals, lib)
                index += 1
                tag = SHORT[base_name]
                short_pal = "".join(w[:1] for w in palette_id.split("_"))
                folder = (f"Auth{index:02d}{tag}{short_pal}"
                          + ("Decal" if decals else ""))
                d = PACK / "Hats" / folder
                d.mkdir(parents=True, exist_ok=True)
                # native 20x80 — Fashion Sense scales at draw time
                write_rgba_png(d / "hat.png", authored.atlas(g))
                label = (f"{tag} {index:02d} {g.palette.identity}"
                         + (f" + {signature}" if decals else ""))
                (d / "hat.json").write_text(json.dumps(
                    hat_json(g, label, index), indent=2))
                trace.append({
                    "folder": folder, "label": label, "base": base_name,
                    "palette": palette_id, "style": g.style,
                    "decals": [x.name for x in g.decals],
                    "dropped": [list(x) for x in g.dropped],
                })

    (PACK / "TRACEABILITY.json").write_text(json.dumps({
        "pack_unique_id": UNIQUE_ID,
        "source": "authored/ as of this build; no art or palette was modified",
        "entries": trace,
    }, indent=2))

    (PACK / "README.md").write_text(
        "# RNG Authored Hat Checkpoint\n\n"
        f"{len(trace)} hats: the four authored bases (`felt_hat`, "
        "`wide_brim_hat`, `soft_cap`, `knit_cap`), each in four curated "
        "palettes, plus one decal variant per base.\n\n"
        "Native **20x20**, four directions stacked at Y = 0/20/40/60, the "
        "vanilla `hats.png` frame size.\n\n"
        "Drop into `Mods/`. Fashion Sense caches content packs at load, so the "
        "game must be restarted after installing.\n\n"
        "| folder | base | palette | decal |\n|---|---|---|---|\n"
        + "\n".join(f"| `{t['folder']}` | {t['base']} | {t['palette']} | "
                    f"{', '.join(t['decals']) or '-'} |" for t in trace) + "\n")

    if install:
        dest = MODS / PACK.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(PACK, dest)
        print(f"installed -> {dest}")

    spill = sum(len(t["dropped"]) for t in trace)
    print(f"{len(trace)} hats, {spill} dropped decal cells -> {PACK}")
    return {"trace": trace}


if __name__ == "__main__":
    build(install="--install" in sys.argv)
