"""Source-traced neutral trucker template: geometry is not redrawn.

Every output pixel is copied from a supplied source view through a declared
whole-view nearest-neighbor transform, then hue-neutralized in place. The only
geometric exception is the requested left mirror of the right source.
"""
from pathlib import Path
import hashlib
import json
import math
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from v5.pngio import blank_image, draw_text, encode_rgba_png, read_rgba_png

SIZE = 26
VIEWS = ("front", "right", "left", "back")
T = (0, 0, 0, 0)
REF_DIR = Path("/run/media/deck/USD00/New Folder (2)")
SOURCES = {
    # The front stays at its supplied 20x20 native resolution. A 20->16
    # downscale drops authored construction pixels and is not source tracing.
    "front": {"file": "rd20_front_original.png", "scale_to": [20, 20], "offset": [3, 3]},
    "right": {"file": "pl26_right.png", "scale_to": [26, 26], "offset": [0, 0]},
    "back": {"file": "pl26_back.png", "scale_to": [26, 26], "offset": [0, 0]}
}
HASHES = {
    "rd20_front_original.png": "5d0b5635bdcf41b844310678529c7bb827a78d9c6f2178d8e586a7dbacc33a87",
    "pl26_right.png": "266c31beb841ae974d5d57bb152f9eee862b0c3e36b302910ad4f9cf2a3bc33f",
    "pl26_back.png": "b848715071b4e41223b8104f1e7d9e8fab3e11d93bcfd00b09c275780a4dfbd8"
}


def save_new_or_identical(path, payload):
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError(f"Refusing to overwrite different source-trace evidence: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def save_derived(path, payload):
    """Refresh reproducible derived evidence after source hashes are verified."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != payload:
        path.write_bytes(payload)


def nearest_whole_view(source, target_size, offset):
    """Uniform whole-view resize; no crop, contour edit, or per-region move."""
    source_h, source_w = len(source), len(source[0])
    target_w, target_h = target_size
    ox, oy = offset
    if not (0 <= ox and 0 <= oy and ox + target_w <= SIZE and oy + target_h <= SIZE):
        raise ValueError("Transform does not fit the canonical canvas")
    out = [[T for _ in range(SIZE)] for _ in range(SIZE)]
    provenance = {}
    for y in range(target_h):
        sy = min(source_h - 1, math.floor(y * source_h / target_h))
        for x in range(target_w):
            sx = min(source_w - 1, math.floor(x * source_w / target_w))
            out[oy + y][ox + x] = source[sy][sx]
            provenance[(ox + x, oy + y)] = (sx, sy)
    return out, provenance


def mirror(rows):
    return [list(reversed(row)) for row in rows]


def neutral(pixel):
    """Keep alpha and source value relationship; remove only hue/saturation."""
    r, g, b, a = pixel
    if not a:
        return pixel
    # Continuous source-relative luminance means no geometry or authored value
    # landmarks are flattened into a new generic shading system.
    value = round(.2126 * r + .7152 * g + .0722 * b)
    return (value, value, value, a)


def runs(rows):
    cells = {(x, y) for y, row in enumerate(rows) for x, p in enumerate(row) if p[3]}
    result = []
    for y in range(SIZE):
        xs = sorted(x for x, yy in cells if yy == y)
        if not xs: continue
        start = prior = xs[0]
        for x in xs[1:]:
            if x != prior + 1:
                result.append([y, start, prior]); start = x
            prior = x
        result.append([y, start, prior])
    return result


def blit(sheet, sprite, x0, y0, scale):
    for y, row in enumerate(sprite):
        for x, p in enumerate(row):
            if p[3]:
                for dy in range(scale):
                    for dx in range(scale): sheet[y0 + y*scale + dy][x0 + x*scale + dx] = p


def contact(aligned, construction):
    scale, tile, gap = 8, SIZE * 8, 18
    sheet = blank_image(4*(tile+gap)+20, 530, (239,238,232,255))
    draw_text(sheet, "SOURCE-TRACED TRUCKER TEMPLATE - NATIVE PIXELS", 8, 8)
    draw_text(sheet, "top: source geometry, centered only   bottom: same pixels, neutral value palette", 8, 23)
    for row, (label, frames, y0) in enumerate((("ALIGNED SOURCE", aligned, 59),
                                                ("NEUTRAL TRACE", construction, 305))):
        draw_text(sheet, label, 8, y0 - 18)
        for i, view in enumerate(VIEWS):
            x = 10 + i*(tile+gap)
            draw_text(sheet, view.upper(), x+82, y0-18)
            blit(sheet, frames[view], x, y0, scale)
    return sheet


def run():
    for name, expected in HASHES.items():
        if hashlib.sha256((REF_DIR / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Source reference drift: {name}")
    aligned, provenance = {}, {}
    for view, spec in SOURCES.items():
        source = read_rgba_png(REF_DIR / spec["file"])
        rows, coords = nearest_whole_view(source, tuple(spec["scale_to"]), tuple(spec["offset"]))
        aligned[view], provenance[view] = rows, coords
    aligned["left"] = mirror(aligned["right"])
    provenance["left"] = {(SIZE-1-x, y): (sx, sy) for (x, y), (sx, sy) in provenance["right"].items()}
    construction = {view: [[neutral(p) for p in row] for row in aligned[view]] for view in VIEWS}
    # Neutral conversion is color-only and must leave every alpha byte exact.
    for view in VIEWS:
        if bytes(p[3] for row in aligned[view] for p in row) != bytes(p[3] for row in construction[view] for p in row):
            raise AssertionError(f"{view}: alpha drift")
    if aligned["left"] != mirror(aligned["right"]):
        raise AssertionError("Derived left mirror drift")

    for kind, frames in (("aligned_source", aligned), ("neutral_template", construction)):
        for view in VIEWS:
            path = HERE / kind / f"{view}.png"
            payload = encode_rgba_png(frames[view])
            if kind == "aligned_source":
                save_new_or_identical(path, payload)
            else:
                save_derived(path, payload)
            if read_rgba_png(path) != frames[view]: raise AssertionError(f"{kind}/{view}: export drift")
    save_derived(HERE / "SOURCE_TRACE_CONTACT.png", encode_rgba_png(contact(aligned, construction)))
    report = {
        "schema": "source-traced-trucker-template/v1", "frame_size": [SIZE, SIZE],
        "source_hashes": HASHES,
        "transforms": {**SOURCES, "left": {"derived_from": "right", "operation": "exact_horizontal_mirror"}},
        "guarantees": {
            "no_hand_drawn_geometry": True,
            "only_whole_view_scale_recenter_or_mirror": True,
            "neutralization_moves_no_pixel": True,
            "alpha_exact_after_neutralization": True,
            "left_exact_right_mirror": True
        },
        "preserved_occupancy_masks": {view: runs(construction[view]) for view in VIEWS},
        "semantic_masks": {
            "status": "USER_APPROVED_2026-09-26",
            "path": "component_masks_01/component_masks.json",
            "sha256": "a4acf7306317545e7f6725cc08e4260402ab8e20f3dd76d8601acbc9853d305c",
            "authority": "explicit coordinates reviewed against these fixed source pixels"
        },
        "pixel_provenance": "Each non-left transformed target coordinate maps to source floor(target * source_size / target_size), plus declared offset; left mirrors right provenance.",
        "note": "This is a construction base for the same source hat in different colors. It is not a new silhouette."
    }
    save_derived(HERE / "source_trace_contract.json", (json.dumps(report, indent=2)+"\n").encode())
    print(json.dumps(report["guarantees"], indent=2))


if __name__ == "__main__": run()
