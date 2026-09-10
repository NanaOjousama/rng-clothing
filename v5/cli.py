"""Batch generation + contact sheet for the first Sailor prototype."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import quality
from .grammar import ATLAS_ORDER
from .library import sailor_top  # noqa: F401  (registers the contracts)
from .pipeline import generate_batch
from .pngio import blank_image, blit, draw_rect, draw_text, nearest_scale, write_rgba_png
from .projection import atlas, fs_metadata, mask_atlas

SCALE = 4
BG = (238, 236, 232, 255)
INK = (44, 42, 40, 255)
CELL_BG = (214, 211, 206, 255)


def _tile(garment):
    env = garment.spec.envelope
    w, h = env.width * SCALE, env.height * SCALE
    tile = blank_image(w * 3 + 8, h, CELL_BG)
    for i, direction in enumerate(("front", "right", "back")):
        rows = nearest_scale(garment.projection.directions[direction], SCALE)
        blit(tile, rows, i * (w + 4), 0)
    return tile


def contact_sheet(garments, columns: int = 6):
    tiles = [_tile(g) for g in garments]
    tw, th = len(tiles[0][0]), len(tiles[0])
    pad, label = 10, 10
    rows = (len(tiles) + columns - 1) // columns
    sheet = blank_image(columns * (tw + pad) + pad,
                        rows * (th + label + pad) + pad + 12, BG)
    draw_text(sheet, "V5 SAILOR-TOP  8X8 SCALE 4", pad, 2, color=INK)
    for i, (tile, g) in enumerate(zip(tiles, garments)):
        cx = pad + (i % columns) * (tw + pad)
        cy = 14 + pad + (i // columns) * (th + label + pad)
        blit(sheet, tile, cx, cy)
        mark = {quality.ACCEPT: "", quality.NEAR_DUPLICATE: " DUP",
                quality.IDENTITY_TOO_WEAK: " WEAK",
                quality.LEGIBILITY_FAILURE: " ILL"}[g.verdict.classification]
        draw_text(sheet, f"{g.spec.seed}{mark}", cx, cy + th + 1, color=INK)
    return sheet


def run(seeds, out_dir: Path, columns: int = 6, architecture: str | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    garments = generate_batch(seeds)
    if architecture:
        # A filter, not a force: the seeds keep resolving normally and we review
        # the subset that landed on this Architecture.
        garments = [g for g in garments if g.spec.architecture == architecture]

    fs_entries, records = [], []
    for g in garments:
        seed = g.spec.seed
        write_rgba_png(out_dir / f"sailor_{seed}.png", atlas(g.projection, SCALE))
        write_rgba_png(out_dir / f"sailor_{seed}_mask.png", mask_atlas(g.projection, SCALE))
        (out_dir / f"sailor_{seed}.json").write_text(
            json.dumps(g.spec.as_dict(), indent=2, default=str))
        fs_entries.append(fs_metadata(g.spec))
        records.append({
            "seed": seed,
            "classification": g.verdict.classification,
            "reasons": g.verdict.reasons,
            "warnings": list(g.verdict.warnings),
            "identity": {k: round(v, 1) for k, v in g.verdict.identity.items()},
            "colors": g.verdict.legibility["colors"],
            "nearest": g.verdict.nearest,
            "problems": list(g.problems),
            "aa_notes": g.art.notes,
            "spec": g.spec.as_dict(),
        })

    write_rgba_png(out_dir / "contact_sheet.png", contact_sheet(garments, columns))
    (out_dir / "content.json").write_text(json.dumps({"Shirts": fs_entries}, indent=2))

    counts: dict = {}
    for r in records:
        counts[r["classification"]] = counts.get(r["classification"], 0) + 1
    colors = sorted(r["colors"] for r in records)
    report = {
        "batch": len(records),
        "architecture_filter": architecture,
        "atlas_order": list(ATLAS_ORDER),
        "classification": counts,
        "colors": {"min": colors[0], "median": colors[len(colors) // 2],
                   "p90": colors[int(0.9 * (len(colors) - 1))], "max": colors[-1]},
        "projection_problems": sum(len(r["problems"]) for r in records),
        "garments": records,
    }
    (out_dir / "report.json").write_text(json.dumps(report, indent=2, default=str))
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description="V5 sailor prototype batch")
    ap.add_argument("--count", type=int, default=48)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--out", type=Path, default=Path("output/v5_sailor_batch_01"))
    ap.add_argument("--columns", type=int, default=6)
    ap.add_argument("--architecture", default=None,
                    help="review only garments that resolved to this Architecture")
    args = ap.parse_args(argv)
    report = run(range(args.start, args.start + args.count), args.out, args.columns,
                 args.architecture)
    print(json.dumps({k: v for k, v in report.items() if k != "garments"}, indent=2))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
