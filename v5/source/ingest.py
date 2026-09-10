"""READ-ONLY ingest of the authored Fashion Sense source library.

The pivot this serves: authored source art is the construction authority.  So
the first job is not to interpret anything — it is to record, exactly and
mechanically, what every pack actually contains, so that later phases argue
from the real files rather than from an assumption about them.

Nothing here writes into the source tree.  Every path is opened read-only and
the catalog is emitted elsewhere.

Fashion Sense pack shape (as found on disk, not as documented):

    <pack>/manifest.json
    <pack>/<Category>/<AppearanceName>/{<name>.json, <name>.png}

where Category is Hats / Shirts / Sleeves / Pants / Accessories, and the JSON
carries the per-direction frame descriptors.  Real packs deviate: BOM-prefixed
JSON, trailing commas, single appearance JSONs describing several appearances,
and PNG names that do not match their folder.  All of that is handled here
rather than being allowed to silently drop assets from the catalog.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, asdict

SOURCE_ROOT = "/run/media/deck/USD00/RNG_clothing/generator conent"

CATEGORIES = ("Hats", "Shirts", "Sleeves", "Pants", "Accessories", "Shoes",
              "Hairstyles", "Bodies")

# The per-direction blocks Fashion Sense recognises, by category.
DIRECTION_KEYS = {
    "Hats": ("FrontHat", "RightHat", "LeftHat", "BackHat"),
    "Shirts": ("FrontShirt", "RightShirt", "LeftShirt", "BackShirt"),
    "Sleeves": ("FrontSleeve", "RightSleeve", "LeftSleeve", "BackSleeve"),
    "Pants": ("FrontPants", "RightPants", "LeftPants", "BackPants"),
    "Accessories": ("FrontAccessory", "RightAccessory", "LeftAccessory",
                    "BackAccessory"),
    "Shoes": ("FrontShoes", "RightShoes", "LeftShoes", "BackShoes"),
}


def load_json(path: str):
    """Tolerant JSON read: BOM, trailing commas, // and /* */ comments.

    Content packs are hand-edited by their authors and several of these are
    not strict JSON.  Failing on them would silently shrink the catalog, which
    is exactly the kind of quiet data loss this pipeline must not have.
    """
    with open(path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8-sig", errors="replace")
    try:
        return json.loads(text), None
    except json.JSONDecodeError:
        pass
    stripped = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    stripped = re.sub(r"(^|[^:])//[^\n]*", r"\1", stripped)
    stripped = re.sub(r",(\s*[}\]])", r"\1", stripped)
    try:
        return json.loads(stripped), "repaired (comments/trailing commas)"
    except json.JSONDecodeError as exc:
        return None, f"unparseable: {exc}"


@dataclass
class Appearance:
    """One Fashion Sense appearance: its JSON block plus the PNG it points at."""
    pack: str
    pack_author: str
    pack_id: str
    category: str
    folder: str
    name: str
    json_path: str
    png_path: str | None
    png_size: tuple | None
    directions: dict = field(default_factory=dict)
    disable_grayscale: bool | None = None
    hide_hair: bool | None = None
    hat_size: dict | None = None
    head_position: dict | None = None
    frames: int | None = None
    animated: bool = False
    color_masks: list = field(default_factory=list)
    raw_keys: list = field(default_factory=list)
    notes: list = field(default_factory=list)


def _png_size(path):
    """Width/height straight from the IHDR — no decode, no dependency."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(24)
        if head[:8] != b"\x89PNG\r\n\x1a\n":
            return None
        return (int.from_bytes(head[16:20], "big"),
                int.from_bytes(head[20:24], "big"))
    except OSError:
        return None


def _appearance_blocks(doc):
    """A pack JSON may hold one appearance or a list of them."""
    if isinstance(doc, list):
        return doc
    for key in ("Appearances", "appearances"):
        if isinstance(doc.get(key), list):
            return doc[key]
    return [doc]


def scan_pack(pack_dir: str) -> tuple:
    manifest, err = load_json(os.path.join(pack_dir, "manifest.json"))
    manifest = manifest or {}
    meta = {
        "pack": manifest.get("Name", os.path.basename(pack_dir)).strip(),
        "pack_author": manifest.get("Author", "unknown"),
        "pack_id": manifest.get("UniqueID", os.path.basename(pack_dir)),
        "version": manifest.get("Version"),
        "description": manifest.get("Description"),
        "dir": pack_dir,
        "manifest_note": err,
    }
    out = []
    for category in CATEGORIES:
        cdir = os.path.join(pack_dir, category)
        if not os.path.isdir(cdir):
            continue
        for folder in sorted(os.listdir(cdir)):
            fdir = os.path.join(cdir, folder)
            if not os.path.isdir(fdir):
                continue
            files = sorted(os.listdir(fdir))
            jsons = [f for f in files if f.lower().endswith(".json")]
            pngs = [f for f in files if f.lower().endswith(".png")]
            for jf in jsons:
                doc, note = load_json(os.path.join(fdir, jf))
                if doc is None:
                    out.append(Appearance(
                        meta["pack"], meta["pack_author"], meta["pack_id"],
                        category, folder, jf[:-5],
                        os.path.join(fdir, jf), None, None,
                        notes=[note or "unparseable"]))
                    continue
                for block in _appearance_blocks(doc):
                    if not isinstance(block, dict):
                        continue
                    out.append(_appearance(meta, category, folder, fdir, jf,
                                           block, pngs, note))
    return meta, out


def _appearance(meta, category, folder, fdir, jf, block, pngs, note):
    name = block.get("Name") or block.get("AppearanceName") or jf[:-5]
    # the PNG a block points at, else the only one in the folder
    ref = block.get("Texture") or block.get("TexturePath")
    png = None
    if ref:
        cand = os.path.join(fdir, os.path.basename(str(ref)))
        if os.path.isfile(cand):
            png = cand
        elif not str(ref).lower().endswith(".png"):
            cand += ".png"
            png = cand if os.path.isfile(cand) else None
    if png is None:
        stem = [p for p in pngs if p[:-4].lower() == jf[:-5].lower()]
        png = os.path.join(fdir, (stem or pngs or [None])[0]) if pngs else None

    app = Appearance(
        meta["pack"], meta["pack_author"], meta["pack_id"], category, folder,
        str(name), os.path.join(fdir, jf), png, _png_size(png) if png else None,
        raw_keys=sorted(block.keys()),
        notes=[note] if note else [],
    )
    keys = DIRECTION_KEYS.get(category, ())
    for key in keys:
        d = block.get(key)
        if isinstance(d, dict):
            app.directions[key.replace(category[:-1] if category.endswith("s")
                                       else category, "")] = {
                "StartingPosition": d.get("StartingPosition"),
                "HatSize": d.get("HatSize"),
                "PantsSize": d.get("PantsSize"),
                "ShirtSize": d.get("ShirtSize"),
                "SleeveSize": d.get("SleeveSize"),
                "AccessorySize": d.get("AccessorySize"),
                "BodyPosition": d.get("BodyPosition"),
                "HeadPosition": d.get("HeadPosition"),
                "Frames": d.get("Frames"),
                "DisableGrayscale": d.get("DisableGrayscale"),
                "HideHair": d.get("HideHair"),
                "ColorMasks": d.get("ColorMasks"),
            }
            if d.get("Frames") and d["Frames"] > 1:
                app.animated = True
                app.frames = max(app.frames or 0, d["Frames"])
            if d.get("HatSize"):
                app.hat_size = d["HatSize"]
            if d.get("HeadPosition"):
                app.head_position = d["HeadPosition"]
            if d.get("DisableGrayscale") is not None:
                app.disable_grayscale = d["DisableGrayscale"]
            if d.get("HideHair") is not None:
                app.hide_hair = d["HideHair"]
            if d.get("ColorMasks"):
                app.color_masks.append({key: d["ColorMasks"]})
    for k in ("DisableGrayscale", "HideHair"):
        if block.get(k) is not None:
            setattr(app, k.lower().replace("disablegrayscale", "disable_grayscale")
                    .replace("hidehair", "hide_hair"), block[k])
    return app


def scan_all(root: str = SOURCE_ROOT):
    packs, apps = [], []
    for dirpath, dirnames, filenames in os.walk(root):
        if "manifest.json" in filenames:
            meta, found = scan_pack(dirpath)
            packs.append(meta)
            apps.extend(found)
            dirnames[:] = [d for d in dirnames
                           if not os.path.isfile(os.path.join(dirpath, d,
                                                              "manifest.json"))]
    return packs, apps


def catalog(root: str = SOURCE_ROOT) -> dict:
    packs, apps = scan_all(root)
    return {"source_root": root,
            "packs": packs,
            "appearances": [asdict(a) for a in apps]}
