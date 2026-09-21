"""Renderer for source-backed template recipes.

Rendering is intentionally conservative:
- target template owns every alpha cell;
- style donors contribute value-role spacing only;
- source motifs are reconstructed from source-family deltas, then mapped into
  a declared opaque target zone without copying source coordinates.
"""
from __future__ import annotations

from pathlib import Path
from collections import Counter

from v5.pngio import read_rgba_png, write_rgba_png
from v5.source.template_transfer import ContractError, TemplateContract, assert_geometry_preserved, template_frames

PROJECT = Path(__file__).resolve().parents[2]


def _lum(p):
    return (p[0] * 299 + p[1] * 587 + p[2] * 114) / 1000.0


def apply_style_profile(frame, style_profile: dict):
    """Remap target opaque values onto donor value-role vocabulary."""
    vocab = [tuple(c) for c in style_profile.get("vocabulary", [])]
    if len(vocab) < 2:
        raise ContractError("style profile has insufficient vocabulary")
    vocab = sorted(vocab, key=lambda c: (c[0] + c[1] + c[2]) / 3)
    values = sorted({_lum(p) for row in frame for p in row if p[3]})
    if not values:
        return [row[:] for row in frame]
    out = [row[:] for row in frame]
    for y, row in enumerate(frame):
        for x, p in enumerate(row):
            if not p[3]:
                continue
            rank = min(range(len(values)), key=lambda i: abs(values[i] - _lum(p)))
            vi = round(rank * (len(vocab) - 1) / max(1, len(values) - 1))
            r, g, b = vocab[vi]
            out[y][x] = (r, g, b, p[3])
    assert_geometry_preserved(frame, out)
    return out


def crop_frame(sheet, box):
    x0, y0, w, h = box
    return [row[x0:x0+w] for row in sheet[y0:y0+h]]


def extract_unique_motif(base_frame, variant_frame):
    """Extract colors/cells introduced by a variant relative to its base.

    The source family may also alter ordinary base shading. Unique variant
    colors are a stronger reconstruction signal for motif ink than raw diffs.
    """
    base_colors = {p[:3] for row in base_frame for p in row if p[3]}
    variant_counts = Counter(p[:3] for row in variant_frame for p in row if p[3])
    motif_colors = {rgb for rgb, n in variant_counts.items()
                    if rgb not in base_colors and n <= 8}
    cells = []
    for y, row in enumerate(variant_frame):
        for x, p in enumerate(row):
            if p[3] and p[:3] in motif_colors:
                cells.append((x, y, p))
    if not cells:
        raise ContractError("source motif has no sparse unique variant ink")
    minx = min(x for x,_,_ in cells); miny = min(y for _,y,_ in cells)
    return [(x-minx, y-miny, p) for x,y,p in cells]


def _fit_motif_on_alpha(frame, motif, anchor):
    """Find nearest placement where every motif cell stays on locked alpha."""
    w = max(x for x,_,_ in motif) + 1
    h = max(y for _,y,_ in motif) + 1
    ax, ay = anchor
    preferred = (ax - w // 2, ay - h // 2)
    candidates = []
    for radius in range(0, 9):
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if max(abs(dx), abs(dy)) != radius:
                    continue
                candidates.append((preferred[0] + dx, preferred[1] + dy))
    for ox, oy in candidates:
        if all(0 <= oy+y < len(frame) and 0 <= ox+x < len(frame[0])
               and frame[oy+y][ox+x][3] for x,y,_ in motif):
            return ox, oy
    raise ContractError("motif cannot fit inside locked target alpha near declared anchor")


def apply_motif(frame, motif, anchor):
    out = [row[:] for row in frame]
    ox, oy = _fit_motif_on_alpha(frame, motif, anchor)
    motif_values = sorted({_lum(p) for _,_,p in motif})
    target_values = sorted({_lum(p) for row in frame for p in row if p[3]})
    for x, y, p in motif:
        rank = min(range(len(motif_values)), key=lambda i: abs(motif_values[i] - _lum(p)))
        # Keep motif readable but within target/donor value vocabulary.
        ti = round(rank * (len(target_values)-1) / max(1, len(motif_values)-1))
        v = int(round(target_values[ti]))
        out[oy+y][ox+x] = (v, v, v, frame[oy+y][ox+x][3])
    assert_geometry_preserved(frame, out)
    return out, {"offset": [ox, oy], "cells": len(motif), "size": [
        max(x for x,_,_ in motif)+1, max(y for _,y,_ in motif)+1]}


def render_source_backed(template: TemplateContract, style_profile: dict, motif_source: dict, output_dir):
    """Render four locked-template frames from source-backed evidence."""
    frames = template_frames(template)
    base_sheet = read_rgba_png(Path(motif_source["base_png"]))
    variant_sheet = read_rgba_png(Path(motif_source["variant_png"]))
    boxes = motif_source["boxes"]
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {"template": template.id, "views": {}}
    for view, frame in frames.items():
        styled = apply_style_profile(frame, style_profile)
        src_view = view.capitalize()
        box = boxes[src_view]
        base = crop_frame(base_sheet, box)
        variant = crop_frame(variant_sheet, box)
        motif = extract_unique_motif(base, variant)
        anchor = template.anchors[view].get("crown_center") or template.anchors[view]["band_center"]
        rendered, placement = apply_motif(styled, motif, anchor)
        assert_geometry_preserved(frame, rendered)
        path = out_dir / f"{view}.png"
        write_rgba_png(path, rendered)
        report["views"][view] = {"path": str(path), "motif": placement}
    return report
