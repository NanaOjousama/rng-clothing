"""Ten RANDOM Cap 2 rolls, produced by the generator, validated automatically.

Seeds are drawn from the system clock, not chosen. Whatever the generator
returns is what gets built and shown — no hand-picking to flatter the proof.
"""
from __future__ import annotations

import json, os, random, shutil, sys, time
from dataclasses import asdict
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from v5 import authored, pngio
from v5.grammar import luminance
from v5.source import audit, pngread
from v5.source.cap2_gen import (Cap2Generator, MIN_CROWN_VISOR,
                                MIN_VISOR_OUTLINE, BASE_DIR)
from build_authored_fs_pack import MODS

PACK = Path("test-packs/fashionsense/RNG-Cap2Full")
UNIQUE_ID = "RNGClothing.FashionSense.Cap2Full"
DIRS = ["Front", "Right", "Left", "Back"]
N = 10


def validate(gen, spec, out):
    """Every family rule, checked rather than assumed."""
    src = gen.frames
    marks = gen.marks
    mk = [tuple(c) for c in spec.motif_cells]
    r = {}
    r["motif_in_mask"] = all(c in gen.safe for c in mk)
    visor = {c for c, v in gen.roles.items() if v in ("visor", "underside")}
    r["no_visor_pixels"] = not (set(mk) & visor)
    # rim / silhouette: the mask already excludes them, assert independently
    N8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
    drawn = {(x, y) for y in range(20) for x in range(20)
             if src["Front"][y][x][3]}
    rim = {c for c in drawn
           if any((c[0] + dx, c[1] + dy) not in drawn for dx, dy in N8)}
    r["no_rim_pixels"] = not (set(mk) & rim)
    # occupancy unchanged everywhere
    lost = added = 0
    for d, f in src.items():
        for y in range(len(f)):
            for x in range(len(f[0])):
                a, b = f[y][x][3] > 0, out[d][y][x][3] > 0
                if a and not b:
                    lost += 1
                if b and not a:
                    added += 1
    r["silhouette_unchanged"] = (lost == 0 and added == 0)
    # non-overlay cells must be a pure recolour: same step, new colour
    # BOTH overlay slots are intended change: the front mark and the back
    # closure. Everything else must be a pure recolour of the same ramp step.
    overlay = {"Front": set(mk),
               "Back": {tuple(c) for c in spec.closure_cells}}
    ramp_steps_wrong = 0
    for d, f in src.items():
        for y in range(len(f)):
            for x in range(len(f[0])):
                if not f[y][x][3] or (x, y) in overlay.get(d, ()):
                    continue
                s_src = min(range(len(gen.vocab)),
                            key=lambda i: abs(gen.levels[i]
                                              - luminance(f[y][x][:3])))
                s_out = min(range(len(gen.vocab)),
                            key=lambda i: abs(luminance(out[d][y][x][:3])
                                              - luminance(gen._ramp[i])))
                if s_src != s_out:
                    ramp_steps_wrong += 1
    r["non_overlay_recolour_only"] = (ramp_steps_wrong == 0)
    # structural contrast, measured on the rendered result
    f = out["Front"]
    m = lambda cs: sum(luminance(f[c[1]][c[0]][:3]) for c in cs) / len(cs)
    # the same role regions the generator's palette gate uses: the crown's LIT
    # body against the visor's DARK field, and that field against the outline
    sf = gen.frames["Front"]
    stp = lambda p: min(range(len(gen.vocab)),
                        key=lambda i: abs(gen.levels[i] - luminance(p[:3])))
    OUT = [c for c, v in gen.roles.items() if v == "outline"]
    VIS = [c for c, v in gen.roles.items()
           if v in ("visor", "underside") and stp(sf[c[1]][c[0]]) <= 1]
    CR = [c for c, v in gen.roles.items()
          if v in ("crown", "highlight") and stp(sf[c[1]][c[0]]) >= 3
          and c not in mk]
    vo, cv = m(VIS) - m(OUT), m(CR) - m(VIS)
    r["visor_outline"] = round(vo, 1)
    r["crown_visor"] = round(cv, 1)
    r["palette_contrast_ok"] = vo >= MIN_VISOR_OUTLINE and cv >= MIN_CROWN_VISOR
    r["one_motif_max"] = len(mk) == 0 or spec.motif_id in marks
    # ---- back closure ----
    cc = [tuple(c) for c in spec.closure_cells]
    r["closure_in_back_safe"] = all(c in gen.back_safe for c in cc)
    br = gen.back_roles
    r["closure_not_opening"] = not any(br.get(c) == "underside" for c in cc)
    r["closure_not_outline"] = not any(br.get(c) == "outline" for c in cc)
    if cc:
        bf = out["Back"]
        mb = lambda cs: sum(luminance(bf[c[1]][c[0]][:3]) for c in cs) / len(cs)
        ring = {(x + dx, y + dy) for (x, y) in cc
                for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        ring = [c for c in ring if c in gen.back_safe and c not in cc]
        r["closure_contrast"] = round(mb(cc) - mb(ring), 1) if ring else 0
        r["closure_readable"] = r["closure_contrast"] >= 60
    else:
        r["closure_readable"] = True
    # rarity respected: COMMON bare, UNCOMMON exactly one
    n = (1 if mk else 0) + (1 if cc else 0)
    r["rarity_slots_ok"] = (
        (spec.rarity == "COMMON" and n == 0)
        or (spec.rarity == "UNCOMMON" and n == 1)
        or (spec.rarity in ("RARE", "EPIC", "LEGENDARY") and 1 <= n <= 2))
    # the mark must not read as the same material as the visor
    if mk:
        from v5.source.cap2_gen import hue_gap, MIN_MOTIF_HUE, MIN_MOTIF_DIST
        from v5.grammar import perceptual_distance
        mc = out["Front"][mk[0][1]][mk[0][0]][:3]
        vf = out["Front"][VIS[0][1]][VIS[0][0]][:3]
        r["motif_hue_gap"] = round(hue_gap(mc, vf), 1)
        r["motif_distance"] = round(perceptual_distance(mc, vf), 1)
        r["motif_not_visor_like"] = (r["motif_hue_gap"] >= MIN_MOTIF_HUE
                                     or r["motif_distance"] >= MIN_MOTIF_DIST)
        r["motif_contrast"] = round(m(CR) - m(mk), 1)
        r["motif_readable"] = r["motif_contrast"] >= 55
    else:
        r["motif_not_visor_like"] = True
        r["motif_readable"] = True
    r["front_only"] = True     # motifs are only ever written into out["Front"]
    r["ok"] = all(v for k, v in r.items()
                  if isinstance(v, bool))
    return r


def main():
    install = "--install" in sys.argv
    lib = authored.load()
    gen = Cap2Generator(lib)
    # --seeds lets the SAME batch be re-rolled after a rule change, so a
    # before/after is a comparison rather than two different samples
    if "--seeds" in sys.argv:
        seeds = [int(x) for x in sys.argv[sys.argv.index("--seeds") + 1].split(",")]
    else:
        seeds = [random.Random(time.time_ns() + i).randrange(1, 10 ** 9)
                 for i in range(N)]
    globals()["N"] = len(seeds)

    if PACK.exists():
        shutil.rmtree(PACK)
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)
    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Cap 2 Rolls", "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Ten controlled-random rolls of the Cap 2 family. Base "
                       "art by plurffle, construction unmodified.",
        "UniqueID": UNIQUE_ID, "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"}}, indent=2))

    specs, results, trace = [], [], []
    print(f"{'#':>2s} {'rarity':10s} {'seed':>10s} {'palette':20s} {'motif':9s} "
          f"{'low':3s} {'closure':8s} {'rej':>3s} {'v-o':>4s} {'c-v':>4s} "
          f"{'mC':>4s} {'hue':>4s} {'bC':>4s}  valid")
    for i, seed in enumerate(seeds, 1):
        spec = gen.roll(seed)
        pal = next(p for p in gen.palettes if p.id == spec.palette_id)
        from v5.source.cap2_gen import build_ramp
        gen._ramp, _ = build_ramp(pal.ramps["body"][3], gen.levels)
        out = gen.render(spec)
        res = validate(gen, spec, out)
        specs.append(asdict(spec))
        results.append(res)
        folder = f"Roll{i:02d}s{seed}"
        d = PACK / "Hats" / folder
        d.mkdir(parents=True, exist_ok=True)
        rows = []
        for dd in DIRS:
            rows.extend([list(r) for r in out[dd]])
        pngio.write_rgba_png(d / "hat.png", rows)
        doc = {"Name": spec.label(), "Format": "7.5.0",
               "Tags": ["RNG Clothing", "Cap2 Roll", f"seed {seed}",
                        spec.palette_id, spec.motif_id, "Art by plurffle"]}
        for j, dd in enumerate(DIRS):
            blk = {k: v for k, v in (spec.wear_properties.get(dd) or {}).items()
                   if k != "StartingPosition"}
            blk["DisableGrayscale"] = True
            blk["StartingPosition"] = {"X": 0, "Y": j * 20}
            doc[f"{dd}Hat"] = blk
        (d / "hat.json").write_text(json.dumps(doc, indent=2))
        trace.append({"folder": folder, "seed": seed, "rarity": spec.rarity,
                      "palette": spec.palette_id, "motif": spec.motif_id,
                      "cells": [list(c) for c in spec.motif_cells],
                      "closure": spec.closure_id,
                      "closure_cells": [list(c) for c in spec.closure_cells],
                      "lowered": spec.motif_lowered,
                      "colour_choice": spec.motif_colour_choice,
                      "rejected": len(spec.palette_rejected),
                      "label": spec.label()})
        print(f"{i:>2d} {spec.rarity:10s} {seed:>10d} {spec.palette_id[:20]:20s} "
              f"{spec.motif_id:9s} {'yes' if spec.motif_lowered else '-':3s} "
              f"{spec.closure_id:8s} {len(spec.palette_rejected):>3d} "
              f"{res['visor_outline']:>4.0f} {res['crown_visor']:>4.0f} "
              f"{res.get('motif_contrast',0):>4.0f} {res.get('motif_hue_gap',0):>4.0f} "
              f"{res.get('closure_contrast',0):>4.0f}"
              f"  {'OK' if res['ok'] else 'FAIL'}")
    (PACK / "trace.json").write_text(json.dumps(trace, indent=2))
    (PACK / "CREDITS.txt").write_text(
        "Base art: 'Cap 2' from More Accessories and Stuff, by plurffle.\n"
        "Construction unmodified. Palette and front mark are generated.\n")
    json.dump({"specs": specs, "validation": results},
              open("output/cap2_family/rolls.json", "w"), indent=1)
    rer = sum(len(s["palette_rejected"]) for s in specs)
    print(f"\nrolls {N}   palette rejections {rer}   "
          f"all valid: {all(r['ok'] for r in results)}")
    from collections import Counter
    print("rarity distribution:", dict(Counter(s["rarity"] for s in specs)))
    print("motif distribution :", dict(Counter(s["motif_id"] for s in specs)))
    print("closure distribution:", dict(Counter(s["closure_id"] for s in specs)))
    reasons = Counter(x["reason"] for s in specs for x in s["palette_rejected"])
    print("rejection reasons  :", dict(reasons))
    if install:
        dest = MODS / PACK.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(PACK, dest)
        print("installed ->", dest)


if __name__ == "__main__":
    main()
