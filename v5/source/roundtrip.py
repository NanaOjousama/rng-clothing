"""SOURCE PACK ROUND-TRIP WEAR FIDELITY.

Exact pixel reconstruction is not enough.  A hat can rebuild to byte-identical
PNG data and still wear wrongly, because how an appearance WEARS is decided by
the model properties around the pixels -- where its head anchor sits, what
scale it draws at, whether it hides hair, whether it is flipped -- and none of
that is in the image.

This module exports a source appearance back out through our own pipeline while
preserving every one of those properties, so that A (the author's untouched
pack) and B (the same hat round-tripped) can be compared in-game.  If they
differ, the fault is ours.

WHAT IS PRESERVED VERBATIM
    every per-direction property the source declares, except StartingPosition

WHY StartingPosition IS THE ONE EXCEPTION
    it is a coordinate into the sheet, and the round-trip re-lays the sheet out
    (frames extracted by the source's own boxes, restacked in FS order).  The
    frame CONTENT is identical; only where it sits in the file changes, and the
    rewritten StartingPosition points at it.  Preserving the old value would
    point at the wrong pixels.

THE BUG THIS WAS WRITTEN TO CATCH
    the previous source exporter hardcoded HeadPosition {0, 0}.  293 of 462
    direction blocks in the source library declare a non-zero HeadPosition, so
    63% of source hats were being re-anchored by up to (-3, -4) sprite pixels --
    12 to 16 screen pixels of misplacement, applied to art that was correct.
"""
from __future__ import annotations

import json
import os

import sys
sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing")
from v5.source import audit, pngread

FS_ORDER = ["Front", "Right", "Left", "Back"]

# EVERY per-direction key except StartingPosition is carried verbatim.  The
# list below is not a filter -- it is the set we RECOGNISE, used to classify
# what a source declares so that anything unrecognised is reported rather than
# quietly passed along.
#
# Sources declare plenty we do not recognise, and it matters:
#
#   legacy draw-order   DrawAfterPlayer (190 blocks), DrawBeforeHair (102),
#                       DrawAfterSleeves (67), DrawBeforePlayer (55).  None of
#                       these exist on the current AppearanceModel or HatModel,
#                       so CURRENT Fashion Sense already ignores them on hats
#                       and accessories; only SleevesModel keeps DrawBeforeHair
#                       as an [Obsolete] setter.  These packs target FS 2.0-3.0.3
#                       and the framework is at 7.5.0.  That is version drift in
#                       the source, not a fault of ours -- and carrying them
#                       verbatim keeps A and B behaving identically, which is
#                       what the fidelity test measures.
#
#   author typos        DrawBeforePLAYER, DrawBeforePlayerPlayer.  Carried
#                       unchanged, because "faithful" includes faithful to
#                       mistakes; they are reported so they are visible.
#
# Translating legacy names to DrawOrderOverride would make these items layer as
# their authors intended on current FS.  That is an IMPROVEMENT, not fidelity,
# so it is deliberately not done here.
RECOGNISED = (
    "HeadPosition", "BodyPosition", "HatSize", "ShirtSize", "PantsSize",
    "SleevesSize", "AccessorySize", "ShoesSize", "HairSize", "BodySize",
    "Scale", "Flipped", "DisableGrayscale", "DisableSkinGrayscale",
    "HideHair", "UseBaldHead", "HidePlayerBase", "HideSleeves",
    "HideWhileSwimming", "HideWhileWearingBathingSuit", "HideWaterLine",
    "HideLegs", "HideShadow", "IsPrismatic", "PrismaticAnimationSpeedMultiplier",
    "RequireAnimationToFinish", "DrawOrderOverride", "ColorMasks",
    "ColorMaskLayers", "SkinToneMasks", "SleeveColors", "UseShirtColors",
    "DisableNativeOffset", "UniformAnimation", "IdleAnimation",
    "MovementAnimation", "Frames",
)

DIR_KEY = {"Hats": "Hat", "Shirts": "Shirt", "Pants": "Pants",
           "Sleeves": "Sleeve", "Accessories": "Accessory", "Shoes": "Shoes",
           "Hairs": "Hair"}


def source_blocks(app: dict) -> dict:
    """The raw per-direction JSON blocks, straight from the author's file."""
    doc, _ = _load(app["json_path"])
    if doc is None:
        return {}
    if isinstance(doc, list):
        doc = next((d for d in doc if d.get("Name") == app["name"]), doc[0])
    suffix = DIR_KEY.get(app["category"], "Hat")
    return {d: doc.get(f"{d}{suffix}") for d in FS_ORDER
            if isinstance(doc.get(f"{d}{suffix}"), dict)}


def _load(path):
    from v5.source.ingest import load_json
    return load_json(path)


def frames(app: dict) -> dict:
    """{Direction: [[rgba]]} cut with the source's own boxes."""
    px = pngread.read(app["png_path"])
    out = {}
    for d, box in app["analysis"]["boxes"].items():
        key = d if d in FS_ORDER else d.capitalize()
        out[key] = audit.cut(px, tuple(box))
    return out


def atlas(frame_map: dict, size: tuple) -> list:
    w, h = size
    rows = []
    for d in FS_ORDER:
        f = frame_map.get(d)
        for y in range(h):
            rows.append(list(f[y]) if f and y < len(f) else [(0, 0, 0, 0)] * w)
    return rows


def export(app: dict, name: str | None = None) -> tuple:
    """(json_doc, atlas_rows, report) — the hat re-emitted, nothing dropped."""
    blocks = source_blocks(app)
    frame_map = frames(app)
    size = tuple(next(iter(app["analysis"]["boxes"].values()))[2:])
    suffix = DIR_KEY.get(app["category"], "Hat")

    doc = {"Name": name or app["name"], "Format": "7.5.0",
           "Tags": ["RNG Clothing", "Round Trip", app["pack"],
                    f"Art by {app['pack_author']}"]}
    carried, unrecognised, rewritten = {}, {}, {}
    for i, d in enumerate(FS_ORDER):
        src = blocks.get(d)
        if src is None:
            # a direction the author did not declare draws nothing in-game;
            # inventing one here would make B differ from A on purpose
            continue
        out = {}
        for key, val in src.items():
            if key == "StartingPosition":
                continue                  # rewritten below; see module docstring
            out[key] = val                # verbatim, recognised or not
            carried.setdefault(key, []).append(d)
            if key not in RECOGNISED:
                unrecognised.setdefault(key, []).append(d)
        out["StartingPosition"] = {"X": 0, "Y": i * size[1]}
        rewritten[d] = {"from": src.get("StartingPosition"),
                        "to": out["StartingPosition"]}
        doc[f"{d}{suffix}"] = out

    report = {
        "source": {"pack": app["pack"], "author": app["pack_author"],
                   "asset": app["name"], "json": app["json_path"],
                   "png": app["png_path"]},
        "size": list(size),
        "directions_declared": sorted(blocks),
        "properties_carried": {k: sorted(v) for k, v in carried.items()},
        "properties_dropped": {},
        "properties_unrecognised": {k: sorted(v) for k, v in unrecognised.items()},
        "starting_position_rewritten": rewritten,
    }
    return doc, atlas(frame_map, size), report


def compare(app: dict, doc: dict) -> dict:
    """Every per-direction property, source value vs round-tripped value."""
    blocks = source_blocks(app)
    suffix = DIR_KEY.get(app["category"], "Hat")
    diffs, same = [], 0
    for d in FS_ORDER:
        src, out = blocks.get(d), doc.get(f"{d}{suffix}")
        if src is None and out is None:
            continue
        if src is None or out is None:
            diffs.append({"direction": d, "property": "(whole model)",
                          "source": src is not None, "roundtrip": out is not None})
            continue
        for key in sorted(set(src) | set(out)):
            if key == "StartingPosition":
                continue                      # rewritten by design, see above
            a, b = src.get(key), out.get(key)
            if a == b:
                same += 1
            else:
                diffs.append({"direction": d, "property": key,
                              "source": a, "roundtrip": b})
    return {"identical_properties": same, "differences": diffs}
