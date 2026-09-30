#!/usr/bin/env python3
"""Trucker onboarding proof through frozen HAT_RENDERER_V1.

Family-specific onboarding collapses noisy source RGBs into bounded semantic
ramps. The frozen renderer is then called unchanged for rarity enhancement.
Nothing here is a replacement production renderer.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generator.hat_hybrid_enhancements import enhance_frames
from v5.pngio import blank_image, blit, draw_text, nearest_scale, write_rgba_png
from v5.source.template_transfer import alpha_cells, load_contract, template_frames, verify_contract

TEMPLATE = ROOT / "generator/data/templates/trucker_pl02_editref24.json"
MASKS = ROOT / "authored/templates/trucker_pl02_editref24/component_masks.json"
OUT = ROOT / "experiments/trucker_hatrenderer_v1_proof_01"
VIEWS = ("front", "right", "back", "left")

# 4-tone body ramps; mesh intentionally uses 3 restrained tones.
PALETTES = {
    "TEAL_WORKWEAR": {
        "front_panel": [(35, 58, 63), (46, 91, 96), (67, 130, 130), (104, 167, 159)],
        "rear_mesh": [(38, 61, 58), (58, 100, 91), (94, 142, 124)],
        "brim": [(70, 48, 29), (115, 78, 39), (164, 116, 58), (205, 158, 82)],
        "top_button": [(70, 48, 29), (115, 78, 39), (164, 116, 58), (205, 158, 82)],
        "back_closure": [(38, 61, 58), (58, 100, 91), (94, 142, 124)],
    },
    "INDIGO_SAGE": {
        "front_panel": [(40, 44, 73), (58, 66, 112), (83, 92, 151), (119, 126, 184)],
        "rear_mesh": [(49, 62, 48), (78, 102, 72), (117, 139, 103)],
        "brim": [(67, 46, 30), (108, 76, 45), (151, 109, 66), (193, 151, 96)],
        "top_button": [(67, 46, 30), (108, 76, 45), (151, 109, 66), (193, 151, 96)],
        "back_closure": [(67, 46, 30), (108, 76, 45), (151, 109, 66), (193, 151, 96)],
    },
}

RECIPES = {
    "TEAL_WORKWEAR": ("common", {
        "materialTreatment": "plain", "pattern": "solid", "trim": "none",
        "motif": "none", "motifPlacement": "none", "attachment": "none", "hardware": "none",
    }),
    "INDIGO_SAGE": ("uncommon", {
        "materialTreatment": "plain", "pattern": "solid", "trim": "contrast",
        "motif": "none", "motifPlacement": "none", "attachment": "none", "hardware": "none",
    }),
}
def load_component_masks(path):
    data = json.loads(Path(path).read_text())
    return {
        view: {region: {tuple(p) for p in points} for region, points in regions.items()}
        for view, regions in data["views"].items()
    }


def verify_masks(frames, masks):
    report = {}
    for view, frame in frames.items():
        opaque = alpha_cells(frame)
        seen = set()
        counts = {}
        for region, cells in masks[view].items():
            if not cells <= opaque:
                raise ValueError(f"{view}/{region}: mask escaped source alpha")
            if seen & cells:
                raise ValueError(f"{view}/{region}: overlapping mask cells")
            seen |= cells
            counts[region] = len(cells)
        report[view] = {"opaque": len(opaque), "masked": len(seen), "protected": len(opaque-seen), "regions": counts}
    return report


def luma(rgb):
    return rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114


def copy_frames(frames):
    return {v: [list(row) for row in frames[v]] for v in frames}


def band_index(value, lo, hi, count):
    if count <= 1 or hi <= lo:
        return 0
    t = (value - lo) / (hi - lo)
    return min(count - 1, max(0, int(t * count)))


def bounded_golden(base, masks, ramps):
    """Collapse each semantic component to a bounded global luminance ramp."""
    out = copy_frames(base)
    audit = {}
    for region, ramp in ramps.items():
        samples = []
        for view in base:
            for x, y in masks[view].get(region, set()):
                samples.append(luma(base[view][y][x][:3]))
        if not samples:
            continue
        lo, hi = min(samples), max(samples)
        used = set()
        for view in base:
            for x, y in masks[view].get(region, set()):
                p = base[view][y][x]
                idx = band_index(luma(p[:3]), lo, hi, len(ramp))
                rgb = ramp[idx]
                out[view][y][x] = (*rgb, p[3])
                used.add(rgb)
        audit[region] = {
            "sourceColorCount": len({
                base[v][y][x][:3]
                for v in base for x, y in masks[v].get(region, set())
            }),
            "goldenColorCount": len(used),
            "rampLimit": len(ramp),
            "usedColors": [list(c) for c in sorted(used)],
        }
    return out, audit


def color_counts(frames, masks):
    report = {}
    for view in frames:
        report[view] = {}
        for region, cells in masks[view].items():
            report[view][region] = len({frames[view][y][x][:3] for x, y in cells})
    return report


def contact(rows):
    scale = 8
    fw = 24 * scale
    label_w = 170
    top = 44
    row_h = fw + 26
    out = blank_image(label_w + fw * 4 + 24, top + row_h * len(rows), (240, 238, 232, 255))
    draw_text(out, "TRUCKER -> FROZEN HAT_RENDERER_V1", 8, 8)
    for i, view in enumerate(VIEWS):
        draw_text(out, view, label_w + i * fw + 64, 28)
    for ri, row in enumerate(rows):
        y = top + ri * row_h
        draw_text(out, row["id"], 8, y + 12)
        draw_text(out, row["rarity"], 8, y + 28)
        for i, view in enumerate(VIEWS):
            blit(out, nearest_scale(row["frames"][view], scale), label_w + i * fw, y)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    contract = load_contract(TEMPLATE)
    contract_report = verify_contract(contract)
    base = template_frames(contract)
    masks = load_component_masks(MASKS)
    mask_report = verify_masks(base, masks)

    rows = [{"id": "SOURCE", "rarity": "n/a", "frames": base}]
    variants = []
    for ident in ("TEAL_WORKWEAR", "INDIGO_SAGE"):
        rarity, recipe = RECIPES[ident]
        golden, collapse = bounded_golden(base, masks, PALETTES[ident])
        final, enhancement = enhance_frames(golden, "trucker", recipe, rarity)
        dest = OUT / ident
        dest.mkdir(parents=True, exist_ok=True)
        for view in VIEWS:
            write_rgba_png(dest / f"{view}.png", final[view])
        variants.append({
            "id": ident,
            "rarity": rarity,
            "recipe": recipe,
            "onboardingPaletteCollapse": collapse,
            "perViewRegionColorCounts": color_counts(final, masks),
            "hatRendererV1": {
                "calledFrozenEnhancer": True,
                "sourceFamily": "trucker",
                "applied": enhancement.applied,
                "fallbackReason": enhancement.fallback_reason,
                "changedPixels": enhancement.changed_pixels,
                "changedRatio": enhancement.changed_ratio,
                "outlinePreserved": enhancement.outline_preserved,
                "alphaPreserved": enhancement.alpha_preserved,
                "regionMode": enhancement.region_mode,
            },
        })
        rows.append({"id": ident, "rarity": rarity, "frames": final})

    write_rgba_png(OUT / "TRUCKER_HAT_RENDERER_V1_CONTACT.png", contact(rows))
    report = {
        "schema": "trucker-hat-renderer-v1-proof/v1",
        "rendererContract": "HAT_RENDERER_V1",
        "rendererContractStatus": "FROZEN",
        "template": contract.id,
        "sourceMaskRendererUsed": False,
        "frozenProductionModulesModified": False,
        "contractVerification": contract_report,
        "maskVerification": mask_report,
        "variants": variants,
        "checks": {
            "boundedSemanticRamps": all(
                r["goldenColorCount"] <= r["rampLimit"]
                for v in variants for r in v["onboardingPaletteCollapse"].values()
            ),
            "outlinePreserved": all(v["hatRendererV1"]["outlinePreserved"] for v in variants),
            "alphaPreserved": all(v["hatRendererV1"]["alphaPreserved"] for v in variants),
            "noRendererRedesign": True,
        },
    }
    (OUT / "proof_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["checks"], indent=2))
    print(OUT / "TRUCKER_HAT_RENDERER_V1_CONTACT.png")


if __name__ == "__main__":
    main()
