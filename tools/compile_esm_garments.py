#!/usr/bin/env python3
"""Compile deterministic outputs from the existing V5 authored generator into
Enhanced Sewing Machine's runtime garment registry.

This is an OFFLINE build bridge. Stardew never runs Python or the generator.
The compiler resolves a generator seed to final pixels + metadata, then writes
an immutable, content-addressed texture and a runtime JSON definition.

Important persistence rule:
- generated texture/definition filenames include a digest of the resolved art;
- this tool never deletes old generated textures/definitions;
- rebuilding a seed after generator changes creates a NEW garment ID/path;
- old saved items can keep rendering their saved snapshot against the old asset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v5 import authored  # noqa: E402
from v5.pngio import write_rgba_png  # noqa: E402

MOD = ROOT / "mods" / "EnhancedSewingMachine"
GARMENTS = MOD / "assets" / "garments"
GENERATED_DEFS = GARMENTS / "generated"
GENERATED_ASSETS = MOD / "assets" / "generated" / "authored_v5"
INDEX = GARMENTS / "index.json"
CATALOG = MOD / "assets" / "generated" / "COMPILED_CATALOG.json"
FIT = ROOT / "authored" / "fit.json"

# Coverage-oriented first bridge batch: two outputs from each current
# PRODUCTION HEAD base. These are not hand-picked as final player content;
# they're a deterministic integration batch for proving generator -> runtime.
DEFAULT_SEEDS = (1000, 1007, 1003, 1004, 1002, 1016, 1005, 1014)
GENERATOR_ID = "v5.authored"
GENERATOR_VERSION = 1


def pixel_digest(rows) -> str:
    h = hashlib.sha256()
    for row in rows:
        for px in row:
            h.update(bytes(px))
    return h.hexdigest()


def engine_digest() -> str:
    h = hashlib.sha256()
    for rel in ("v5/authored.py", "v5/integration.py", "v5/rng.py"):
        p = ROOT / rel
        h.update(rel.encode("utf-8"))
        h.update(p.read_bytes())
    return h.hexdigest()


def slug(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")


def load_runtime_fit() -> dict:
    """Translate the old Fashion Sense fitting table into runtime offsets.

    FS HeadPosition is added to the SpriteBatch origin, so its sign is opposite
    our runtime's world-space logical Offset: FS Y=-2 moved the hat DOWN 8 px,
    therefore runtime OffsetY=+2 reproduces that approved seating.
    """
    raw = json.loads(FIT.read_text())
    return raw.get("defaults", {})


def compile_one(seed: int, lib, fit_defaults: dict | None = None) -> dict:
    g = authored.compose(seed, slot="HEAD", lib=lib)

    if g.base.classification != "PRODUCTION":
        raise ValueError(
            f"seed {seed}: {g.base.name} is {g.base.classification}, "
            "but the ESM production bridge accepts PRODUCTION bases only"
        )
    if g.dropped:
        raise ValueError(f"seed {seed}: renderer dropped authored cells: {g.dropped}")

    atlas = authored.atlas(g, scale=1)
    digest = pixel_digest(atlas)
    short = digest[:12]
    garment_id = f"gen.v5.{seed}.{slug(g.base.name)}.{short}"

    texture_rel = f"assets/generated/authored_v5/{garment_id}.png"
    texture_path = MOD / texture_rel
    def_rel = f"generated/{garment_id}.json"
    def_path = GARMENTS / def_rel

    w, h = g.base.size
    fit_defaults = fit_defaults if fit_defaults is not None else load_runtime_fit()
    fs_fit = fit_defaults.get(g.base.name, {})
    offset_x = -int(fs_fit.get("HatOffsetX", 0))
    offset_y = -int(fs_fit.get("HatOffsetY", 0))

    directions = {
        "Front": {
            "SourceX": 0, "SourceY": 0,
            "AnchorX": 10, "AnchorY": 16,
            "OffsetX": offset_x, "OffsetY": offset_y,
        },
        "Right": {
            "SourceX": 0, "SourceY": h,
            "AnchorX": 10, "AnchorY": 16,
            "OffsetX": offset_x, "OffsetY": offset_y,
        },
        "Left": {
            "SourceX": 0, "SourceY": h * 2,
            "AnchorX": 10, "AnchorY": 16,
            "OffsetX": offset_x, "OffsetY": offset_y,
        },
        "Back": {
            "SourceX": 0, "SourceY": h * 3,
            "AnchorX": 10, "AnchorY": 16,
            "OffsetX": offset_x, "OffsetY": offset_y,
        },
    }

    decal_names = [d.name for d in g.decals]
    motif_classes = []
    for d in g.decals:
        if d.motif_class and d.motif_class not in motif_classes:
            motif_classes.append(d.motif_class)

    definition = {
        "Id": garment_id,
        "Category": "Hat",
        "DefinitionVersion": 1,
        "WornTexture": texture_rel,
        "FrameWidth": w,
        "FrameHeight": h,
        # Current authored V5 HEAD art is designed in the same logical source
        # density as vanilla/Fashion Sense 4x. The runtime keeps its pixels at
        # native logical density rather than resizing the PNG.
        "RenderScale": 1.0,
        "VanillaReferenceAnchor": {"X": 10, "Y": 16},
        "Directions": directions,
        "Metadata": {
            "Family": g.base.family or g.base.name,
            "Construction": g.base.shape_variant or g.base.name,
            "Material": g.material or g.treatment or "",
            "Palette": g.palette.id,
            "Motif": ",".join(motif_classes),
            "GeneratorId": GENERATOR_ID,
            "GeneratorVersion": GENERATOR_VERSION,
            "GeneratorSeed": seed,
            "Style": g.style,
            "QualityTier": g.quality_tier or "",
            "Decals": ",".join(decal_names),
            "Classification": g.base.classification,
        },
    }

    return {
        "seed": seed,
        "garment_id": garment_id,
        "definition_rel": def_rel,
        "texture_rel": texture_rel,
        "pixel_digest": digest,
        "base": g.base.name,
        "family": g.base.family or g.base.name,
        "construction": g.base.shape_variant or g.base.name,
        "style": g.style,
        "palette": g.palette.id,
        "material": g.material or g.treatment or "",
        "quality_tier": g.quality_tier or "",
        "decals": decal_names,
        "motif_classes": motif_classes,
        "classification": g.base.classification,
        "frame_size": [w, h],
        "render_scale": 1.0,
        "runtime_offset": [offset_x, offset_y],
        "source_fs_fit": {
            "HatOffsetX": int(fs_fit.get("HatOffsetX", 0)),
            "HatOffsetY": int(fs_fit.get("HatOffsetY", 0)),
        },
        "_atlas": atlas,
        "_definition": definition,
        "_texture_path": texture_path,
        "_definition_path": def_path,
    }


def load_index() -> dict:
    if not INDEX.exists():
        return {"Garments": []}
    return json.loads(INDEX.read_text())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--seeds",
        help="comma-separated generator seeds; defaults to the bridge coverage batch",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    seeds = DEFAULT_SEEDS
    if args.seeds:
        seeds = tuple(int(x.strip()) for x in args.seeds.split(",") if x.strip())
    if not seeds:
        raise SystemExit("no seeds")

    lib = authored.load()
    fit_defaults = load_runtime_fit()
    compiled = [compile_one(seed, lib, fit_defaults) for seed in seeds]

    ids = [x["garment_id"] for x in compiled]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate generated garment ID in batch")

    for x in compiled:
        print(
            f"{x['seed']}: {x['garment_id']} | {x['base']} | {x['style']} | "
            f"{x['palette']} | decals={x['decals']}"
        )

    if args.dry_run:
        print(f"dry-run: {len(compiled)} garment(s), no files changed")
        return 0

    GENERATED_DEFS.mkdir(parents=True, exist_ok=True)
    GENERATED_ASSETS.mkdir(parents=True, exist_ok=True)
    CATALOG.parent.mkdir(parents=True, exist_ok=True)

    for x in compiled:
        # Content-addressed paths make overwrite safe: identical path means
        # identical resolved pixels for this seed/base signature.
        write_rgba_png(x["_texture_path"], x["_atlas"])
        x["_definition_path"].write_text(
            json.dumps(x["_definition"], indent=2) + "\n",
            encoding="utf-8",
        )

    index = load_index()
    # Keep hand-maintained/dev entries and replace only the ACTIVE generated
    # list. Old generated definitions/assets remain on disk for old saved items.
    preserved = [
        p for p in index.get("Garments", [])
        if not str(p).replace("\\", "/").startswith("generated/")
    ]
    active_generated = [x["definition_rel"] for x in compiled]
    INDEX.write_text(
        json.dumps({"Garments": preserved + active_generated}, indent=2) + "\n",
        encoding="utf-8",
    )

    public = []
    for x in compiled:
        public.append({k: v for k, v in x.items() if not k.startswith("_")})
    CATALOG.write_text(
        json.dumps(
            {
                "schema": "esm-compiled-catalog/v1",
                "generator_id": GENERATOR_ID,
                "generator_version": GENERATOR_VERSION,
                "engine_digest": engine_digest(),
                "slot": "HEAD",
                "count": len(public),
                "items": public,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"compiled {len(compiled)} garment(s)")
    print("registry ->", INDEX)
    print("catalog  ->", CATALOG)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
