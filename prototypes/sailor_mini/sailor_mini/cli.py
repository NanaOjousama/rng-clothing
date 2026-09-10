"""CLI: python3 -m sailor_mini.cli build [--out DIR]"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .batch import BASE_SEED, PAIRS, PALETTE_FAMILY, REQUESTS
from .body import W
from .pngio import write_rgba_png
from .preview import (DIRECTIONS, Farmer, anatomy_sheet, contact_sheet,
                      gameplay_sheet, pair_sheet)
from .render import atlas, build_garment
from .resolve import derive, resolve

ROOT = Path(__file__).resolve().parents[1]
OUT_DEFAULT = ROOT / "out"


def _dump(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def dependency_probe(n: int) -> dict:
    """Roll n unpinned seeds to show the dependency filter actually rejects and rerolls.

    The twelve batch variants are fully pinned, so they never exercise the reroll
    path. This probe is the evidence that stage 3 does real work.
    """
    from collections import Counter
    fired, attempts, first_try = Counter(), [], 0
    for i in range(n):
        spec = resolve(derive(999_001, str(i)) % 10_000_000, spec_id=f"probe{i}")
        attempts.append(spec.attempt)
        first_try += spec.attempt == 0
        for r in spec.rejected:
            for v in r["violations"]:
                fired[v["rule"]] += 1
    return {
        "samples": n,
        "valid_on_first_roll": first_try,
        "needed_a_reroll": n - first_try,
        "max_attempts_used": max(attempts),
        "rejections_by_rule": dict(fired.most_common()),
        "total_rejected_candidates": sum(fired.values()),
    }


def build(out: Path) -> dict:
    farmer = Farmer()
    items, batch = [], {"base_seed": BASE_SEED, "count": len(REQUESTS), "variants": []}

    for i, (vid, label, pins) in enumerate(REQUESTS):
        seed = derive(BASE_SEED, vid) % 10_000_000
        spec = resolve(seed, spec_id=vid, pinned=pins, palette_family=PALETTE_FAMILY[vid])

        g = build_garment(spec)
        folder = out / "frames" / vid
        for d in DIRECTIONS:
            write_rgba_png(folder / f"{d}.png", g.images[d])
        write_rgba_png(folder / "atlas.png", atlas(g.images))
        _dump(out / "specs" / f"{vid}.json", spec.to_json())

        systems = sorted({g.frames[d].system[y][x] for d in DIRECTIONS
                          for y in range(W) for x in range(W) if g.frames[d].system[y][x]})
        unattributed = sum(1 for d in DIRECTIONS for y in range(W) for x in range(W)
                           if g.frames[d].role[y][x] and not g.frames[d].system[y][x])
        colors = len({p for d in DIRECTIONS for row in g.images[d] for p in row if p[3]})
        batch["variants"].append({
            "id": vid, "label": label, "seed": seed, "attempt": spec.attempt,
            "rejected_combinations": len(spec.rejected),
            "spec": spec.to_json(), "systems": systems,
            "unattributed_cells": unattributed, "distinct_colors": colors,
        })
        items.append({"id": vid, "label": label, "spec": spec, "images": g.images,
                      "frames": g.frames, "garment": g})

    batch["dependency_probe"] = dependency_probe(400)
    _dump(out / "batch.json", batch)
    sheets = out / "sheets"
    write_rgba_png(sheets / "SAILOR_CONTACT_12.png",
                   contact_sheet(items, "MINI SAILOR PROTOTYPE - 12 VARIANTS - ISOLATED 16X16 AT 5X"))
    write_rgba_png(sheets / "SAILOR_GAMEPLAY_12.png",
                   gameplay_sheet(items, farmer, "MINI SAILOR PROTOTYPE - GAMEPLAY SIZE ON FARMER"))
    write_rgba_png(sheets / "SAILOR_ANATOMY.png",
                   anatomy_sheet(items, "CONSTRUCTION ANATOMY - YELLOW = FREE EDGE, RED = OCCLUSION, NO OUTLINE ON ATTACHED EDGES"))
    by_id = {it["id"]: it for it in items}
    for a, b, var in PAIRS:
        write_rgba_png(sheets / f"SAILOR_PAIR_{var}.png", pair_sheet(by_id[a], by_id[b], var, farmer))
    return batch


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sailor_mini")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--out", default=str(OUT_DEFAULT))
    args = ap.parse_args(argv)
    batch = build(Path(args.out))
    for v in batch["variants"]:
        s = v["spec"]
        print(f"{v['id']:24s} attempt={v['attempt']} rejected={v['rejected_combinations']} "
              f"colors={v['distinct_colors']:2d} unattributed={v['unattributed_cells']} "
              f"{s['collar_width']:8s} {s['rear_flap_depth']:8s} {s['trim_style']:6s} {s['center_detail']:4s}")


if __name__ == "__main__":
    main()
