"""Per-base motif audit pack: soft_cap ONLY.

Every legal motif and every legal pair on one base, so the question stops being
"does this motif work" and becomes "does this motif work HERE".  A motif that
reads on a knitted crown can fragment on a cap's flat band row, and the only
way to know is to put the whole legal space in front of the game.

    10 singles + 22 pairs + 4 palette probes + 1 plain control = 37

Palettes are canonical per style so that the variable between entries is the
MOTIF, not the colour story; the four probes deliberately re-test motifs under
a second palette to expose contrast dependency.

    python3 tools/build_softcap_audit_pack.py --install
"""
from __future__ import annotations

import itertools
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from v5 import authored                                    # noqa: E402
from v5.pngio import write_rgba_png                        # noqa: E402
from build_authored_fs_pack import fit_for                 # noqa: E402

PACK = Path("test-packs/fashionsense/RNG-SoftCap-Motif-Audit")
UNIQUE_ID = "RNGClothing.FashionSense.SoftCapMotifAudit"
MODS = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods")
BASE = "soft_cap"

CANON = {"casual": "EVERYDAY_STONE_BLUE", "work": "FIELD_CANVAS_MOSS",
         "cottagecore": "SPRING_SAGE_PETAL", "smart": "WINTER_FROST_INK"}
# second palette per style, to separate "this motif is weak" from "this motif
# is weak on this colour story"
PROBE = {"casual": "DESERT_CLAY_TURQUOISE", "cottagecore": "AUTUMN_OCHRE_PLUM",
         "work": "WORKWEAR_DENIM_RUST", "smart": "EVERYDAY_STONE_BLUE"}
PROBE_MOTIFS = ["band_striped", "crown_button", "flower_daisy", "pom_small"]


def entries(lib):
    cap = next(b for b in lib.bases if b.name == BASE)
    legal = []
    for d in sorted(lib.decals, key=lambda d: d.name):
        if d.slot != "HEAD" or not d.fits_base(cap):
            continue
        shared = sorted(set(cap.style) & set(d.style))
        if shared and any(authored._placement(cap, d, v) for v in d.views):
            legal.append((d, shared))

    out = [([], sorted(cap.style)[0], "control")]
    for d, shared in legal:
        out.append(([d.name], shared[0], "single"))
    for (a, sa), (b, sb) in itertools.combinations(legal, 2):
        if authored.region_of(a) == authored.region_of(b):
            continue
        shared = sorted(set(sa) & set(sb))
        if shared:
            out.append(([a.name, b.name], shared[0], "pair"))
    for name in PROBE_MOTIFS:
        d, shared = next((x for x in legal if x[0].name == name), (None, None))
        if d:
            out.append(([name], shared[0], "probe"))
    return out


def hat_json(g, name: str, kind: str) -> dict:
    w, h = g.base.size
    dx, dy = fit_for(g.base.name)
    keys = {"front": "FrontHat", "right": "RightHat",
            "left": "LeftHat", "back": "BackHat"}
    out = {"Name": name,
           "Tags": ["RNG Clothing", "SoftCap Audit", kind, g.style,
                    g.palette.id, *(d.name for d in g.decals)]}
    for i, direction in enumerate(authored.ATLAS_ORDER):
        out[keys[direction]] = {
            "DisableGrayscale": True, "HideHair": False,
            "HatSize": {"Width": w, "Length": h},
            "StartingPosition": {"X": 0, "Y": i * h},
            "HeadPosition": {"X": int(dx), "Y": int(dy)},
        }
    return out


def build(install: bool = False) -> None:
    lib = authored.load()
    if PACK.exists():
        shutil.rmtree(PACK)
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)
    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Soft Cap Motif Audit",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Every legal motif and pair on the soft_cap base.",
        "UniqueID": UNIQUE_ID, "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"},
    }, indent=2))

    trace = []
    for i, (motifs, style, kind) in enumerate(entries(lib), 1):
        palette = (PROBE if kind == "probe" else CANON)[style]
        g = authored.build(BASE, palette, motifs, lib, style=style)
        if g.dropped:
            raise SystemExit(f"{motifs} drops: {g.dropped}")
        regions = [authored.region_of(d) for d in g.decals]
        if len(regions) != len(set(regions)):
            raise SystemExit(f"{motifs} share a region")
        tag = "".join(m.split("_")[0][:3].title() for m in motifs) or "Plain"
        folder = f"Cap{i:02d}{tag}{'P' if kind == 'probe' else ''}"
        d = PACK / "Hats" / folder
        d.mkdir(parents=True, exist_ok=True)
        write_rgba_png(d / "hat.png", authored.atlas(g))
        (d / "hat.json").write_text(json.dumps(
            hat_json(g, f"Cap {i:02d} " + (" + ".join(motifs) or "plain"), kind),
            indent=2))
        trace.append({"folder": folder, "kind": kind, "motifs": motifs,
                      "style": style, "palette": palette})

    (PACK / "TRACEABILITY.json").write_text(json.dumps(
        {"pack_unique_id": UNIQUE_ID, "base": BASE, "entries": trace}, indent=2))
    if install:
        dest = MODS / PACK.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(PACK, dest)
        print(f"installed -> {dest}")
    kinds = {}
    for t in trace:
        kinds[t["kind"]] = kinds.get(t["kind"], 0) + 1
    print(f"{len(trace)} hats -> {PACK}  {kinds}")


if __name__ == "__main__":
    build(install="--install" in sys.argv)
