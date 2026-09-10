"""CLI: python3 -m rngc.cli build-all [--out DIR]   |   python3 -m rngc.cli build <plan_id>"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .bench import Vanilla, reduce_2x2
from .colorize import colorize, sleeve_colors
from .compose import compose
from .data import DATA, Library
from .export_fs import write_pack
from .pngio import write_rgba_png
from .preview import DIRECTIONS, Farmer, collection_sheet, garment_sheet, resolution_sheet
from .validate import validate

REPO = Path(__file__).resolve().parents[1]
OUT_DEFAULT = REPO / "output" / "v5-phase1"
BENCH_VANILLA = {"bench_tee": 1, "bench_collared": 248, "bench_vest": 278, "bench_sailor": 259, "bench_overalls": 216}
VANILLA_SALIENCE_SET = {"Collared Shirt": 248, "Blue Buttoned Vest": 278, "Sailor Shirt": 259, "Plain Overalls": 216, "Green Vest": 20, "Vintage Polo": 198}
RESOLUTION_PLANS = ("bench_sailor", "bench_collared")


def _dump(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def build_plan(plan_id: str, lib: Library) -> dict:
    plan = lib.plans[plan_id]
    result = compose(plan, lib)
    pal = lib.palettes[plan.palette]
    frames = colorize(result, pal)
    report = validate(result, frames, lib)
    sleeves = sleeve_colors(pal, plan.sleeve_slot, lib.contract["sleeve_color_roles"])
    return {"plan": plan, "result": result, "frames": frames, "validation": report, "sleeves": sleeves, "palette": pal}


def build_all(out: Path) -> dict:
    lib = Library.load(DATA)
    farmer = Farmer(); vanilla = Vanilla()
    if not farmer.available: print("WARNING: installed Farmer assets not found; previews use a flat panel", file=sys.stderr)
    built = {pid: build_plan(pid, lib) for pid in sorted(lib.plans)}
    summary = {"plans": {}, "vanilla_available": vanilla.available, "farmer_available": farmer.available}

    for pid, b in built.items():
        folder = out / "garments" / pid
        write_rgba_png(folder / "shirt-atlas.png", __import__("rngc.export_fs", fromlist=["atlas"]).atlas(b["frames"], lib.contract["atlas_order"], 16))
        for d in DIRECTIONS: write_rgba_png(folder / f"{d}.png", b["frames"][d])
        _dump(folder / "plan.json", {"id": b["plan"].id, "name": b["plan"].name, "template": b["plan"].template, "blank": b["plan"].blank,
                                     "pieces": [{"id": p.id, "slot": p.slot} for p in b["plan"].pieces], "palette": b["plan"].palette,
                                     "sleeve_slot": b["plan"].sleeve_slot, "hide_sleeves": b["plan"].hide_sleeves})
        _dump(folder / "roleimage.json", {d: img.to_json(b["result"].piece_ids) for d, img in b["result"].images.items()})
        _dump(folder / "validation.json", b["validation"])
        vid = BENCH_VANILLA.get(pid)
        van = vanilla.frames(vid) if (vid and vanilla.available) else None
        reduced = {d: reduce_2x2(b["result"].images[d], b["frames"][d]) for d in DIRECTIONS}
        sheet = garment_sheet(f"{b['plan'].name.upper()} - {b['validation']['status']} - HUMAN REVIEW: AWAITING", b["frames"], farmer,
                              vanilla=van, vanilla_name=f"{vid} {vanilla.name(vid)}" if van else "", reduced=reduced)
        write_rgba_png(out / "sheets" / f"PHASE1_GARMENT_{pid}.png", sheet)
        summary["plans"][pid] = {"name": b["plan"].name, "status": b["validation"]["status"], "distinct_colors": b["validation"]["distinct_colors"],
                                 "pieces": [p.id for p in b["plan"].pieces], "template": b["plan"].template,
                                 "failed_checks": [c["check"] for c in b["validation"]["checks"] if c["status"] == "FAIL"],
                                 "warnings": [c["check"] for c in b["validation"]["checks"] if c["status"] == "WARN"],
                                 "salience": b["validation"]["salience"], "vanilla_counterpart": vid}

    bench_items = [{"label": built[p]["plan"].name, "sub": f"vanilla {BENCH_VANILLA[p]}", "frames": built[p]["frames"],
                    "vanilla": vanilla.frames(BENCH_VANILLA[p]) if vanilla.available else None} for p in BENCH_VANILLA if p in built]
    write_rgba_png(out / "sheets" / "PHASE1_BENCH_FIVE_VS_VANILLA.png", collection_sheet("PHASE 1 BENCHMARKS - V5 VS VANILLA - HUMAN REVIEW: AWAITING", bench_items, farmer))
    xprod = [pid for pid in built if pid.startswith("xprod_")]
    write_rgba_png(out / "sheets" / "PHASE1_CROSS_PRODUCTS.png", collection_sheet("PHASE 1 CROSS-PRODUCTS (UNAUTHORED COMBINATIONS) - STRUCTURAL ONLY",
                   [{"label": built[p]["plan"].name, "sub": built[p]["validation"]["status"], "frames": built[p]["frames"]} for p in xprod], farmer, vanilla_col=False))

    # resolution experiment
    entries = []
    for pid in RESOLUTION_PLANS:
        b = built[pid]; vid = BENCH_VANILLA[pid]
        entries.append({"label": b["plan"].name, "a16": b["frames"], "b8": {d: reduce_2x2(b["result"].images[d], b["frames"][d]) for d in DIRECTIONS},
                        "vanilla": vanilla.frames(vid) if vanilla.available else None})
    write_rgba_png(out / "sheets" / "PHASE1_RESOLUTION_EXPERIMENT.png", resolution_sheet("RESOLUTION EXPERIMENT - 16X16/SCALE2 VS 8X8/SCALE4", entries, farmer))

    # vanilla salience measurements
    if vanilla.available:
        summary["vanilla_salience"] = {f"{i} {n}": vanilla.identity_salience(i) for n, i in VANILLA_SALIENCE_SET.items()}

    # Fashion Sense bench pack (internal)
    items = []
    for pid, b in built.items():
        items.append({"name": b["plan"].name, "frames": b["frames"], "sleeve_colors": b["sleeves"], "tags": ["RNG Clothing V5", "Phase 1", "INTERNAL BENCH", *b["plan"].tags], "hide_sleeves": b["plan"].hide_sleeves})
    for pid in RESOLUTION_PLANS:
        b = built[pid]
        items.append({"name": b["plan"].name + " 8x8 EXPERIMENT", "frames": {d: reduce_2x2(b["result"].images[d], b["frames"][d]) for d in DIRECTIONS},
                      "sleeve_colors": b["sleeves"], "tags": ["RNG Clothing V5", "Phase 1", "RESOLUTION EXPERIMENT 8X8 SCALE 4"], "hide_sleeves": b["plan"].hide_sleeves, "eight": True})
    pack = write_pack(out / "bench" / "fs-pack" / "RNG-Clothing-V5-Phase1-Bench", items, lib.contract,
                      description="Internal V5 Phase 1 architecture fixtures. Not for distribution.")
    summary["fs_pack"] = pack
    summary["library"] = {"blanks": sorted(lib.blanks), "pieces": sorted(lib.pieces), "templates": sorted(lib.templates), "palettes": sorted(lib.palettes)}
    usage = {pid: [p for p in lib.plans if any(pp.id == pid for pp in lib.plans[p].pieces)] for pid in lib.pieces}
    summary["piece_usage"] = usage
    _dump(out / "phase1-summary.json", summary)
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(prog="rngc")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("build-all"); a.add_argument("--out", default=str(OUT_DEFAULT))
    b = sub.add_parser("build"); b.add_argument("plan_id"); b.add_argument("--out", default=str(OUT_DEFAULT))
    args = ap.parse_args(argv)
    if args.cmd == "build-all":
        s = build_all(Path(args.out))
        for pid, p in s["plans"].items(): print(f"{p['status']:4s} {pid:28s} colors={p['distinct_colors']:2d} fail={p['failed_checks']} warn={p['warnings']}")
        print("pack:", s["fs_pack"]["pack"])
    else:
        lib = Library.load(DATA); b = build_plan(args.plan_id, lib)
        print(json.dumps(b["validation"], indent=2))


if __name__ == "__main__":
    main()
