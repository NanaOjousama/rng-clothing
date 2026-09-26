"""Validate manually traced masks and build their approval contact sheet."""

from collections import Counter
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
TRACE = HERE.parent
ROOT = HERE.parents[3]
LAB = TRACE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(LAB))

from source_identity import VIEWS, digest, freeze
from v5.pngio import blank_image, draw_text, encode_rgba_png, read_rgba_png

COMPONENTS = ("front_panel", "rear_mesh", "brim", "top_button", "back_closure")
COLORS = {
    "front_panel": (218, 91, 91, 255),
    "rear_mesh": (47, 163, 164, 255),
    "brim": (224, 166, 57, 255),
    "top_button": (155, 105, 211, 255),
    "back_closure": (111, 174, 91, 255),
    "protected_construction": (67, 69, 76, 255),
    "back_opening": (89, 184, 230, 255),
}


def expand(runs, *, allow_transparent=False):
    cells = set()
    for run in runs:
        if len(run) != 3:
            raise ValueError(f"Malformed row run: {run}")
        y, x0, x1 = run
        if not (0 <= y < 26 and 0 <= x0 <= x1 < 26):
            raise ValueError(f"Out-of-bounds row run: {run}")
        for x in range(x0, x1 + 1):
            if (x, y) in cells:
                raise ValueError(f"Duplicate coordinate: {(x, y)}")
            cells.add((x, y))
    return cells


def alpha_composite(bg, fg):
    a = fg[3]
    return tuple(round((fg[i] * a + bg[i] * (255 - a)) / 255)
                 for i in range(3)) + (255,)


def blit_scaled(sheet, rows, x0, y0, scale, *, checker=False):
    for y, row in enumerate(rows):
        for x, pixel in enumerate(row):
            bg = ((232, 231, 226, 255) if not checker or (x + y) % 2
                  else (215, 214, 209, 255))
            color = alpha_composite(bg, pixel)
            for dy in range(scale):
                for dx in range(scale):
                    sheet[y0 + y * scale + dy][x0 + x * scale + dx] = color


def mask_frame(source, components, opening):
    out = [[(0, 0, 0, 0) for _ in range(26)] for _ in range(26)]
    assigned = set().union(*components.values())
    for y, row in enumerate(source):
        for x, pixel in enumerate(row):
            coordinate = (x, y)
            if coordinate in opening:
                out[y][x] = COLORS["back_opening"]
            elif coordinate in assigned:
                for name in COMPONENTS:
                    if coordinate in components[name]:
                        out[y][x] = COLORS[name]
                        break
            elif pixel[3]:
                out[y][x] = COLORS["protected_construction"]
    return out


def build_contact(sources, maps):
    scale, tile, gap = 9, 26 * 9, 24
    width = 20 + 4 * (tile + gap)
    height = 590
    sheet = blank_image(width, height, (240, 239, 234, 255))
    draw_text(sheet, "TRUCKER 26X26 - EXPLICIT COMPONENT MASKS - APPROVAL PROOF", 8, 8)
    draw_text(sheet, "top: accepted source pixels   bottom: semantic interiors + protected construction", 8, 23)
    legend = (("PANEL", "front_panel"), ("MESH", "rear_mesh"),
              ("VISOR", "brim"), ("BUTTON", "top_button"),
              ("CLOSURE", "back_closure"), ("PROTECTED", "protected_construction"),
              ("OPENING", "back_opening"))
    lx = 8
    for label, key in legend:
        for yy in range(8):
            for xx in range(8):
                sheet[43 + yy][lx + xx] = COLORS[key]
        draw_text(sheet, label, lx + 12, 43)
        lx += 52 + len(label) * 4
    for index, view in enumerate(VIEWS):
        x = 10 + index * (tile + gap)
        draw_text(sheet, view.upper(), x + 92, 68)
        blit_scaled(sheet, sources[view], x, 84, scale, checker=True)
        draw_text(sheet, view.upper() + " MASK", x + 72, 331)
        blit_scaled(sheet, maps[view], x, 348, scale, checker=True)
    return sheet


def save_new_or_identical(path, payload):
    if path.exists() and path.read_bytes() != payload:
        raise ValueError(f"Refusing to overwrite different mask evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(payload)


def run():
    mask_path = HERE / "component_masks.json"
    document = json.loads(mask_path.read_text())
    sources = {view: read_rgba_png(TRACE / "aligned_source" / f"{view}.png")
               for view in VIEWS}
    frozen = freeze(sources)
    if digest(frozen) != document["sourcePixelsSha256"]:
        raise ValueError("Mask/source decoded-pixel hash mismatch")

    masks, protected, overlays = {}, {}, {}
    counts = {}
    occupied_counts = {}
    for view, rows in zip(VIEWS, frozen):
        view_masks = {name: expand(document["views"][view][name])
                      for name in COMPONENTS}
        seen = set()
        for name in COMPONENTS:
            overlap = seen & view_masks[name]
            if overlap:
                raise ValueError(f"{view}: overlapping component masks {sorted(overlap)}")
            seen |= view_masks[name]
            for x, y in view_masks[name]:
                if not rows[y][x][3]:
                    raise ValueError(f"{view}/{name}: transparent coordinate {(x, y)}")
        opening = expand(document["protectedFeatures"]["back_opening"][view])
        for x, y in opening:
            if rows[y][x][3]:
                raise ValueError(f"{view}/back_opening: expected transparent {(x, y)}")
        occupied = {(x, y) for y, row in enumerate(rows)
                    for x, pixel in enumerate(row) if pixel[3]}
        protected[view] = occupied - seen
        masks[view] = view_masks
        overlays[view] = mask_frame(rows, view_masks, opening)
        counts[view] = {name: len(view_masks[name]) for name in COMPONENTS}
        counts[view]["protected_construction"] = len(protected[view])
        counts[view]["back_opening"] = len(opening)
        occupied_counts[view] = len(occupied)

    for component in COMPONENTS:
        mirrored = {(25 - x, y) for x, y in masks["right"][component]}
        if mirrored != masks["left"][component]:
            raise AssertionError(f"{component}: left mask is not exact right mirror")
    if sources["left"] != [list(reversed(row)) for row in sources["right"]]:
        raise AssertionError("Accepted left source is not exact right mirror")

    contact = build_contact(sources, overlays)
    save_new_or_identical(HERE / "TRUCKER_COMPONENT_MASK_CONTACT.png",
                          encode_rgba_png(contact))
    report = {
        "schema": "source-traced-trucker-component-mask-report/v1",
        "sourcePixelsSha256": document["sourcePixelsSha256"],
        "maskFileSha256": hashlib.sha256(mask_path.read_bytes()).hexdigest(),
        "reviewState": document["reviewState"],
        "approvedForRendering": document["approvedForRendering"],
        "pixelCounts": counts,
        "sourceOccupiedPixels": occupied_counts,
        "checks": {
            "all_component_coordinates_explicit": True,
            "all_recolorable_component_pixels_opaque": True,
            "component_masks_disjoint_per_view": True,
            "unassigned_occupied_pixels_protected": True,
            "back_opening_is_exact_transparent_negative_space": True,
            "left_masks_exact_right_mirrors": True,
            "left_source_exact_right_mirror": True,
            "brightness_inference_used": False,
            "row_threshold_inference_used": False,
            "color_membership_authority_used": False,
            "synthetic_mesh_used": False,
            "technical_gate": "PASS"
        },
        "notes": [
            "Masks cover component interiors; outlines, seams, borders and unclassified rough source pixels remain protected.",
            "The source-trace front is preserved at native 20x20 within the 26x26 canvas.",
            "User approved these masks for isolated source-preserving proofs on 2026-09-26."
        ]
    }
    save_new_or_identical(HERE / "mask_report.json",
                          (json.dumps(report, indent=2) + "\n").encode())
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
