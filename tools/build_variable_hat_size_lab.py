#!/usr/bin/env python3
"""Build a tiny ESM-only lab for validating variable logical hat frame sizes.

This does NOT modify the V5 generator. It takes two known-good authored V5 hats,
resamples their already-resolved 20x20 directional art to 16/20/24/32 logical
frames, and emits ESM runtime definitions with:

- frame-size-aware sprite anchors,
- a compensating RenderScale so physical worn size stays comparable,
- the same vanilla reference anchor and runtime fit offsets.

Purpose: prove the ESM 16..32 rendering/anchoring contract before production V5
is generalized to author native variable-size geometry.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v5 import authored
from v5.pngio import blank_image, blit, write_rgba_png

MOD = ROOT / "mods" / "EnhancedSewingMachine"
INDEX = MOD / "assets" / "garments" / "index.json"
DEFS = MOD / "assets" / "garments" / "lab"
ASSETS = MOD / "assets" / "generated" / "size_lab"
TRACE = ASSETS / "trace.json"
FIT = ROOT / "authored" / "fit.json"

SIZES = (16, 20, 24, 32)
BASES = ("soft_cap", "wide_brim_hat")
SOURCE_SIZE = 20
SOURCE_ANCHOR = (10.0, 16.0)
VANILLA_REFERENCE_ANCHOR = (10, 16)
PALETTE = "EVERYDAY_STONE_BLUE"


def resample_nearest(rows, out_w: int, out_h: int):
    in_h = len(rows)
    in_w = len(rows[0]) if in_h else 0
    if not in_w or not in_h:
        raise ValueError("empty source frame")
    out = []
    for y in range(out_h):
        sy = min(in_h - 1, int(y * in_h / out_h))
        row = []
        for x in range(out_w):
            sx = min(in_w - 1, int(x * in_w / out_w))
            row.append(rows[sy][sx])
        out.append(row)
    return out


def digest(rows) -> str:
    h = hashlib.sha256()
    for row in rows:
        for px in row:
            h.update(bytes(px))
    return h.hexdigest()


def load_fit():
    return json.loads(FIT.read_text()).get("defaults", {})


def choose_palette(lib, base_name: str) -> str:
    # Prefer the familiar control palette where compatible, otherwise take the
    # first curated palette sharing a style with the base.
    base = next(b for b in lib.bases if b.name == base_name)
    preferred = next((p for p in lib.palettes if p.id == PALETTE), None)
    if preferred and set(base.style) & set(preferred.style):
        return preferred.id
    for p in lib.palettes:
        if set(base.style) & set(p.style):
            return p.id
    raise ValueError(f"no compatible palette for {base_name}")


def build_one(base_name: str, size: int, lib, fits: dict):
    palette = choose_palette(lib, base_name)
    g = authored.build(base_name, palette, (), lib)

    frames = {d: resample_nearest(g.directions[d], size, size)
              for d in authored.ATLAS_ORDER}
    atlas = blank_image(size, size * 4, (0, 0, 0, 0))
    for i, d in enumerate(authored.ATLAS_ORDER):
        blit(atlas, frames[d], 0, i * size)

    short = digest(atlas)[:12]
    gid = f"lab.size.{base_name}.{size}.{short}"
    texture_rel = f"assets/generated/size_lab/{gid}.png"
    def_rel = f"lab/{gid}.json"

    fit = fits.get(base_name, {})
    offset_x = -int(fit.get("HatOffsetX", 0))
    offset_y = -int(fit.get("HatOffsetY", 0))

    # SpriteBatch origin scales with the source art. Keep the same semantic
    # point (10,16) from the 20px reference frame.
    # Runtime schema stores anchors as integer source pixels. Round the
    # proportional semantic anchor to the nearest source pixel for the lab.
    ax = round(SOURCE_ANCHOR[0] * size / SOURCE_SIZE)
    ay = round(SOURCE_ANCHOR[1] * size / SOURCE_SIZE)

    # Compensate source resolution so all cases occupy roughly the same world
    # size. 32px therefore draws at 0.625x the V5 render density; 16px at 1.25x.
    render_scale = SOURCE_SIZE / size

    dirs = {}
    for i, name in enumerate(("Front", "Right", "Left", "Back")):
        dirs[name] = {
            "SourceX": 0,
            "SourceY": size * i,
            "AnchorX": ax,
            "AnchorY": ay,
            "OffsetX": offset_x,
            "OffsetY": offset_y,
        }

    definition = {
        "Id": gid,
        "Category": "Hat",
        "DefinitionVersion": 1,
        "WornTexture": texture_rel,
        "FrameWidth": size,
        "FrameHeight": size,
        "RenderScale": render_scale,
        "VanillaReferenceAnchor": {
            "X": VANILLA_REFERENCE_ANCHOR[0],
            "Y": VANILLA_REFERENCE_ANCHOR[1],
        },
        "Directions": dirs,
        "Metadata": {
            "Family": g.base.family or g.base.name,
            "Construction": g.base.shape_variant or g.base.name,
            "Material": g.material or g.treatment or "",
            "Palette": g.palette.id,
            "Motif": "",
            "GeneratorId": "lab.variable_hat_size",
            "GeneratorVersion": 1,
            "GeneratorSeed": size,
            "Style": g.style,
            "QualityTier": "LAB",
            "Decals": "",
            # Registry may load it, tailoring selection must never roll it.
            "Classification": "REFERENCE_ONLY",
        },
    }

    return {
        "garment_id": gid,
        "definition_rel": def_rel,
        "texture_rel": texture_rel,
        "base": base_name,
        "frame_size": [size, size],
        "source_size": [SOURCE_SIZE, SOURCE_SIZE],
        "sprite_anchor": [ax, ay],
        "vanilla_reference_anchor": list(VANILLA_REFERENCE_ANCHOR),
        "render_scale": render_scale,
        "runtime_offset": [offset_x, offset_y],
        "_atlas": atlas,
        "_definition": definition,
    }


def main():
    lib = authored.load()
    fits = load_fit()

    DEFS.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)

    # Remove only prior outputs from this lab.
    for p in DEFS.glob("lab.size.*.json"):
        p.unlink()
    for p in ASSETS.glob("lab.size.*.png"):
        p.unlink()

    built = [build_one(base, size, lib, fits)
             for base in BASES for size in SIZES]

    for item in built:
        write_rgba_png(MOD / item["texture_rel"], item.pop("_atlas"))
        (MOD / "assets" / "garments" / item["definition_rel"]).write_text(
            json.dumps(item.pop("_definition"), indent=2) + "\n"
        )

    index = json.loads(INDEX.read_text())
    keep = [x for x in index.get("Garments", [])
            if not x.startswith("lab/lab.size.")]
    keep.extend(item["definition_rel"] for item in built)
    index["Garments"] = keep
    INDEX.write_text(json.dumps(index, indent=2) + "\n")

    TRACE.write_text(json.dumps(built, indent=2) + "\n")

    print(f"built {len(built)} variable-size lab hats")
    for x in built:
        print(
            f"  {x['base']:13s} {x['frame_size'][0]:2d}px "
            f"anchor=({x['sprite_anchor'][0]},{x['sprite_anchor'][1]}) "
            f"renderScale={x['render_scale']:.4f} "
            f"id={x['garment_id']}"
        )
    print(f"trace -> {TRACE}")


if __name__ == "__main__":
    main()
