"""Source-respecting Fisherman family extension for HAT_RENDERER_V1.

The user-approved four-view Fisherman pixels are the construction + shading
authority. Non-native palette candidates preserve the source's *continuous*
per-pixel luminance topology; they never bucket the hat into coarse
shadow/mid/light regions. Photo Tailor is used only for approved donor palette
evidence (base + outline colors).
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import median

from generator.photo_tailor_port import relative_luma, topology_boundary
from generator.source_respecting_hat_remix import RemixResult
from v5.pngio import read_rgba_png

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = ROOT / "generator/data/source_parts/hat_source_extensions.json"
PT_PROFILE = ROOT / "authored/templates/bucket_fisherman_navy16/pt_profile.json"
VIEWS = ("front", "right", "left", "back")


def load_spec() -> dict:
    return json.loads(EXTENSIONS.read_text())["families"]["bucket_fisherman"]


def source_frames() -> dict:
    spec = load_spec()
    out = {view: read_rgba_png(ROOT / spec["authoredFrames"][view]) for view in VIEWS}
    if out["left"] != [list(reversed(row)) for row in out["right"]]:
        raise RuntimeError("bucket_fisherman: approved Left no longer mirrors Right")
    return out


def _copy(frames: dict) -> dict:
    return {v: [list(row) for row in frames[v]] for v in VIEWS}


def _source_refs(frames: dict) -> tuple[float, float]:
    boundary, interior = [], []
    for view in VIEWS:
        frame = frames[view]
        for y, row in enumerate(frame):
            for x, p in enumerate(row):
                if not p[3]:
                    continue
                target = boundary if topology_boundary(frame, x, y) else interior
                target.append(relative_luma(p[:3]))
    if not boundary or not interior:
        raise RuntimeError("bucket_fisherman: source reference classes are empty")
    return float(median(boundary)), float(median(interior))


def _scaled_color(target_rgb, raw_ratio: float, contrast: float, clamp_range) -> tuple[int, int, int]:
    lo, hi = map(float, clamp_range)
    ratio = max(lo, min(hi, 1.0 + float(contrast) * (raw_ratio - 1.0)))
    return tuple(max(0, min(255, round(c * ratio))) for c in target_rgb)


def render(state: str = "Fisherman Navy 16", palette: str = "source_native") -> RemixResult:
    spec = load_spec()
    if state != spec["base"]:
        raise ValueError(f"bucket_fisherman: unknown source state {state!r}")
    if palette not in spec["candidatePalettes"]:
        raise ValueError(f"bucket_fisherman: unknown palette {palette!r}")

    raw = source_frames()
    if palette == "source_native":
        out = _copy(raw)
        changed = {v: set() for v in VIEWS}
        palette_trace = {
            "paletteAuthority": "exact_user_approved_source_pixels",
            "photoTailorRole": "none_for_source_native",
            "shadeTopology": "EXACT_SOURCE_PIXELS",
        }
    else:
        profile = json.loads(PT_PROFILE.read_text())
        info = profile["candidatePalettes"][palette]
        target_base = tuple(info["baseColor"])
        target_outline = tuple(info["outlineColor"])
        transfer = spec["paletteTransfer"]
        boundary_ref, interior_ref = _source_refs(raw)
        out = _copy(raw)
        changed = {v: set() for v in VIEWS}

        for view in VIEWS:
            frame = raw[view]
            for y, row in enumerate(frame):
                for x, p in enumerate(row):
                    if not p[3]:
                        continue
                    boundary = topology_boundary(frame, x, y)
                    source_luma = relative_luma(p[:3])
                    source_ref = boundary_ref if boundary else interior_ref
                    target_rgb = target_outline if boundary else target_base
                    contrast = transfer["boundaryContrast"] if boundary else transfer["interiorContrast"]
                    rgb = _scaled_color(
                        target_rgb,
                        source_luma / max(source_ref, 1e-9),
                        contrast,
                        transfer["ratioClamp"],
                    )
                    q = (rgb[0], rgb[1], rgb[2], p[3])
                    out[view][y][x] = q
                    if q != p:
                        changed[view].add((x, y))

        # Construction contract: keep the approved directional mirror exact.
        out["left"] = [list(reversed(row)) for row in out["right"]]
        changed["left"] = {
            (x, y)
            for y, row in enumerate(out["left"])
            for x, p in enumerate(row)
            if p != raw["left"][y][x]
        }
        palette_trace = {
            "paletteAuthority": "approved_donor_palette_evidence",
            "photoTailorRole": "palette_evidence_only",
            "photoTailorProfile": str(PT_PROFILE.relative_to(ROOT)),
            "shadeTopology": "CONTINUOUS_SOURCE_LUMA_NO_BUCKETS",
            "interiorContrast": transfer["interiorContrast"],
            "boundaryContrast": transfer["boundaryContrast"],
            "ratioClamp": transfer["ratioClamp"],
            "donor": info["donor"],
        }

    # Exact alpha must never change.
    for view in VIEWS:
        for y, row in enumerate(raw[view]):
            for x, p in enumerate(row):
                if p[3] != out[view][y][x][3]:
                    raise RuntimeError(f"bucket_fisherman/{view}: alpha drift")

    trace = {
        "constructionAuthority": "exact_user_approved_four_view_source_state",
        "lockedFeatures": spec["lockedConstruction"],
        "mutableFeature": "body_palette_continuous_luma_transfer",
        "genericProjectionUsed": False,
        "genericLineUsed": False,
        "sourceShadingTopologyPreserved": True,
        **palette_trace,
    }
    return RemixResult(
        family="bucket_fisherman",
        construction=state,
        source_state=state,
        palette=palette,
        component=None,
        frames=out,
        source_frames=raw,
        changed=changed,
        trace=trace,
    )
