"""Fashion Sense pack for the FIT pass: each base at its proposed default,
plus the variants needed to settle two things the docs do not tell us.

1. THE SIGN.  Fashion Sense's HeadPosition.Y moves the hat, but which way is
   down is not documented and the one earlier attempt to use it was reverted as
   a measurement artifact.  So each base ships at +Y and -Y, and the capture
   says which is which.  Guessing costs a restart; measuring costs one entry.

2. SCALE.  Our frames are 20x20 at Scale 4, which is 1:1 with the farmer's own
   pixel grid.  Any other scale resamples the hat against a 4x farmer, and the
   HeadPosition.X that centres the frame stops being an integer:
       X = (width - 20 * (4 / Scale)) / 2
       Scale 4 -> 0.0     Scale 5 -> +2.0     Scale 3 -> -3.33
   Two scale probes are included so the artefacts are visible rather than
   argued about.

    python3 tools/build_authored_fit_pack.py --install
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from v5 import authored                                    # noqa: E402
from v5.pngio import write_rgba_png                        # noqa: E402

PACK = Path("test-packs/fashionsense/RNG-Authored-Hat-Fit")
UNIQUE_ID = "RNGClothing.FashionSense.AuthoredHatFit"
MODS = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods")
FIT = Path("authored/fit.json")

# one palette per base, so the sweep reads as position rather than colour
PALETTE = {"felt_hat": "WORKWEAR_DENIM_RUST", "wide_brim_hat": "FIELD_CANVAS_MOSS",
           "soft_cap": "EVERYDAY_STONE_BLUE", "knit_cap": "AUTUMN_OCHRE_PLUM"}
SHORT = {"felt_hat": "Felt", "wide_brim_hat": "Wide", "soft_cap": "Cap",
         "knit_cap": "Knit"}


def head_x(width: int, scale: float) -> float:
    """The X that centres a frame on the head box, per the FS model."""
    return (width - 20 * (4 / scale)) / 2


# Fashion Sense parses HeadPosition into integer fields.  A float — even 0.0 —
# makes it report the whole model as invalid JSON and load NO hats from the
# pack, silently as far as the game is concerned: the capture came back with
# worn == nohat for all fourteen entries.  So every value written here is an
# int, and a scale whose centring is fractional is rounded with the error
# recorded rather than written as a float.


def model(g, name: str, dy: int, dx: int = 0, scale: float = 4.0) -> dict:
    w, h = g.base.size
    keys = {"front": "FrontHat", "right": "RightHat",
            "left": "LeftHat", "back": "BackHat"}
    x = int(round(head_x(w, scale) + dx))
    out = {"Name": name,
           "Tags": ["RNG Clothing", "Fit Pass", g.base.name, g.palette.id,
                    f"dy {dy:+d}", f"scale {scale:g}"]}
    for i, direction in enumerate(authored.ATLAS_ORDER):
        out[keys[direction]] = {
            "DisableGrayscale": True,
            "HideHair": False,
            "HatSize": {"Width": w, "Length": h},
            "StartingPosition": {"X": 0, "Y": i * h},
            "HeadPosition": {"X": x, "Y": int(dy)},
        }
    if scale != 4.0:
        out["Scale"] = scale
    return out


def build(install: bool = False, scale_probes: bool = True,
          pack: Path = PACK, unique_id: str = UNIQUE_ID) -> None:
    lib = authored.load()
    fit = json.loads(FIT.read_text())
    player = fit["player"]

    if pack.exists():
        shutil.rmtree(pack)
    (pack / "Hats").mkdir(parents=True, exist_ok=True)
    (pack / "manifest.json").write_text(json.dumps({
        "Name": "RNG Authored Hat Fit",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Seating pass: each authored base at its proposed "
                       "default offset, its opposite-sign twin, and two scale "
                       "probes.",
        "UniqueID": unique_id,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"},
    }, indent=2))

    trace, n = [], 0
    for base_name, d in fit["defaults"].items():
        g = authored.build(base_name, PALETTE[base_name], (), lib)
        dy = d["HatOffsetY"] + player["HatOffsetY"]
        dx = d["HatOffsetX"] + player["HatOffsetX"]
        if scale_probes:
            # the probe pack carries ONLY the probes: duplicate folder names
            # across two packs would collide in the capture labels
            variants = ([("scale5", dy, dx, 5.0), ("scale3", dy, dx, 3.0)]
                        if base_name == "soft_cap" else [])
        else:
            variants = [("default", dy, dx, 4.0),
                        ("opposite", -dy, dx, 4.0),
                        ("zero", 0, dx, 4.0)]
        for label, vdy, vdx, vscale in variants:
            n += 1
            folder = f"Fit{n:02d}{SHORT[base_name]}{label.title()}"
            fd = pack / "Hats" / folder
            fd.mkdir(parents=True, exist_ok=True)
            write_rgba_png(fd / "hat.png", authored.atlas(g))
            name = f"{SHORT[base_name]} {label} dy{vdy:+d} s{vscale:g}"
            (fd / "hat.json").write_text(json.dumps(
                model(g, name, vdy, vdx, vscale), indent=2))
            trace.append({"folder": folder, "base": base_name, "label": label,
                          "dy": vdy, "dx": vdx, "scale": vscale,
                          "head_x": round(head_x(g.base.size[0], vscale) + vdx, 2)})

    (pack / "TRACEABILITY.json").write_text(json.dumps(
        {"pack_unique_id": unique_id, "fit": fit, "entries": trace}, indent=2))
    if install:
        dest = MODS / pack.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(pack, dest)
        print(f"installed -> {dest}")
    print(f"{len(trace)} entries -> {pack}")
    for t in trace:
        print(f"  {t['folder']:24s} {t['base']:14s} dy {t['dy']:+d}  "
              f"scale {t['scale']:g}  headX {t['head_x']}")


if __name__ == "__main__":
    inst = "--install" in sys.argv
    build(install=inst, scale_probes=False)
    build(install=inst, scale_probes=True,
          pack=Path("test-packs/fashionsense/RNG-Authored-Hat-ScaleProbe"),
          unique_id="RNGClothing.FashionSense.AuthoredHatScaleProbe")
