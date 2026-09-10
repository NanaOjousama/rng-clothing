"""Emit a Cap 2 roll as a Fashion Sense pack the sewing machine can actually see.

Two things are added here that the earlier proof packs did not have.

ITEM. A Fashion Sense appearance is invisible to the rest of the game until it
declares `Item` -- only then does it become a real inventory item with an id of
the form `<PackId>/Hat/<Name>/Item`, referenced as `(H)<that>`. Without it a
generated cap cannot be held, sold, or put in a tailoring slot, so the fitting
mod would have nothing to hook. `SpritePosition` and `SpriteSize` are both
REQUIRED by Fashion Sense (Item-Properties.md); the inventory icon is the Front
frame, which sits at the top of our atlas.

FITTING SIDECAR. `fitting.json` is ours, not Fashion Sense's -- FS ignores
unknown files in a pack folder. It carries what the fitting mod needs and
cannot otherwise recover:

  * the authored default HeadPosition per direction, so Reset can restore the
    generated default EXACTLY rather than assuming {0,0};
  * the motif's cells and colour;
  * the safe mask, so the mod can enforce the same per-pixel rule the
    generator enforced, instead of re-deriving it and drifting;
  * `base_pixels` -- the colour each safe cell has with NO motif on it. Moving
    a motif means repainting the cells it left behind, and only the generator
    knows what was underneath.

The pack's own hat.json is never rewritten by the mod: a player's fitting is
stored separately and applied at runtime, so re-rolling the same seed still
reproduces the same cap.
"""
from __future__ import annotations

import json
import os

DIRS = ["Front", "Right", "Left", "Back"]
FRAME = 20


def atlas(frames, size: int = FRAME):
    """Stack the four directions top to bottom, in DIRS order."""
    rows = []
    for d in DIRS:
        f = frames[d]
        for y in range(size):
            rows.append(list(f[y]) if y < len(f) else [(0, 0, 0, 0)] * size)
    return rows


def slug(name: str) -> str:
    """A name safe to embed in a Stardew item id.

    Fashion Sense derives the automatic id from the appearance Name, and our
    labels carry spaces and a '#' seed marker. Qualified ids are parsed as
    '(H)<id>' and travel through shop data and console commands, so the id gets
    a sanitised form while DisplayName keeps the readable one.
    """
    keep = [c if (c.isalnum() or c in "-_.") else "_" for c in name]
    out = "".join(keep)
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_")


def item_id(pack_id: str, name: str) -> str:
    """The id we declare explicitly, rather than letting FS derive one."""
    return f"{pack_id}/Hat/{slug(name)}/Item"


def hat_json(name: str, wear: dict, *, pack_id: str, price: int = 0,
             description: str = "", tags=None, item: bool = True) -> dict:
    """The FS hat.json for one cap, with `Item` so it exists in the world."""
    doc = {"Name": name, "Format": "7.5.0", "Tags": list(tags or [])}
    if item:
        doc["Item"] = {
            "Id": item_id(pack_id, name),
            "DisplayName": name,
            "Description": description,
            "Price": price,
            # REQUIRED by FS. The Front frame is the inventory icon.
            "SpritePosition": {"X": 0, "Y": 0},
            "SpriteSize": {"Width": FRAME, "Length": FRAME},
        }
    for j, d in enumerate(DIRS):
        blk = {k: v for k, v in (wear.get(d) or {}).items()
               if k != "StartingPosition"}
        blk["DisableGrayscale"] = True            # colour is baked into the art
        blk["StartingPosition"] = {"X": 0, "Y": j * FRAME}
        doc[f"{d}Hat"] = blk
    return doc


def default_head_positions(wear: dict) -> dict:
    """The authored HeadPosition per direction, defaulting the way FS does.

    Recorded explicitly so Reset restores the generated default and not a
    guess. 63% of the source hats rely on a non-zero HeadPosition, so assuming
    {0,0} here would silently move most caps.
    """
    out = {}
    for d in DIRS:
        hp = (wear.get(d) or {}).get("HeadPosition") or {}
        out[d] = {"X": int(hp.get("X", 0)), "Y": int(hp.get("Y", 0))}
    return out


def fitting_json(spec, gen, frames, *, pack_id: str, name: str) -> dict:
    """The fitting sidecar. `frames` is the RENDERED cap, motif already on it."""
    safe = sorted(gen.safe)
    front = frames["Front"]
    motif = {tuple(c) for c in spec.motif_cells}

    # What each safe cell looks like with no motif on it. Cells the motif
    # currently covers are recovered from the palette ramp rather than read
    # back off the frame, because the frame no longer holds the original there.
    from v5.grammar import luminance
    pal = next(p for p in gen.palettes if p.id == spec.palette_id)
    from v5.source.cap2_gen import build_ramp
    ramp, _ = build_ramp(pal.ramps["body"][3], gen.levels)
    src = gen.frames["Front"]
    base_pixels = {}
    for (x, y) in safe:
        p = src[y][x]
        if not p[3]:
            continue
        step = min(range(len(gen.vocab)),
                   key=lambda i: abs(gen.levels[i] - luminance(p[:3])))
        base_pixels[f"{x},{y}"] = [*ramp[step], 255]

    colour = None
    if spec.motif_id != "plain":
        colour = list(gen.motif_colour(ramp, pal, spec.motif_colour_choice))

    return {
        "format": 1,
        "player_fitting": True,
        "_comment": "Written by the RNG Clothing generator for the fitting "
                    "mod. Not read by Fashion Sense.",
        "base": spec.base_id,
        "seed": spec.seed,
        "rarity": spec.rarity,
        "appearance_id": f"{pack_id}/Hat/{name}",
        "item_id": item_id(pack_id, name),
        "frame": {"size": FRAME, "directions": DIRS,
                  "front_origin": {"X": 0, "Y": 0}},
        "hat": {
            "range": 3,
            "default_head_position": default_head_positions(spec.wear_properties),
        },
        "motif": {
            "id": spec.motif_id,
            "cells": [list(c) for c in sorted(motif)],
            "colour": colour,
            "safe_cells": [list(c) for c in safe],
            "base_pixels": base_pixels,
        },
    }


def write_cap(folder: str, spec, gen, frames, *, pack_id: str, name: str,
              price: int = 0, description: str = "", tags=None) -> dict:
    """Write hat.png / hat.json / fitting.json for one cap. Returns the sidecar."""
    from v5 import pngio
    os.makedirs(folder, exist_ok=True)
    pngio.write_rgba_png(os.path.join(folder, "hat.png"), atlas(frames))
    doc = hat_json(name, spec.wear_properties, pack_id=pack_id, price=price,
                   description=description, tags=tags)
    with open(os.path.join(folder, "hat.json"), "w") as fh:
        json.dump(doc, fh, indent=2)
    side = fitting_json(spec, gen, frames, pack_id=pack_id, name=name)
    with open(os.path.join(folder, "fitting.json"), "w") as fh:
        json.dump(side, fh, indent=2)
    from dataclasses import asdict
    with open(os.path.join(folder, "spec.json"), "w") as fh:
        json.dump(asdict(spec), fh, indent=2)
    return side
