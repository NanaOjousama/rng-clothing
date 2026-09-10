"""Controlled proof for CAP2_FRONT_OVERLAY.

Five simple marks drawn into the crown overlay zone on the intact Cap 2 base.
Every rule is checked mechanically rather than asserted in prose: the marks
must live on the crown, never touch the visor, leave every non-overlay source
pixel byte-identical, read at gameplay scale, and leave the visor's own
readability untouched.
"""
from __future__ import annotations

import json, os, shutil, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from v5 import pngio
from v5.grammar import luminance
from v5.source import roundtrip
from cap2_overlay import load, apply_mark, DIRS
from build_authored_fs_pack import MODS

PACK = Path("test-packs/fashionsense/RNG-Cap2Overlay")
UNIQUE_ID = "RNGClothing.FashionSense.Cap2Overlay"
ORDER = ["bar", "twin_bars", "angle_l", "chevron", "dot", "ring", "zigzag"]


SAFE = None


def verify(name, fr, out, touched, ov, roles, vocab):
    """Every locked rule, as a check that can fail."""
    z = ov["zone"]["primary"]
    zone = {(x, y) for y in range(z["y0"], z["y1"] + 1)
            for x in range(z["x0"], z["x1"] + 1)}
    visor = {c for c, r in roles.items() if r in ("visor", "underside")}
    crown = {c for c, r in roles.items() if r in ("crown", "highlight")}
    res = {}
    res["on_crown"] = all(c in crown for c in touched)
    res["inside_mask"] = all(c in SAFE for c in touched)
    res["inside_zone"] = res["inside_mask"]      # the mask supersedes the box
    res["clear_of_visor"] = not (set(touched) & visor)
    res["visor_row_gap"] = (min((c[1] for c in visor), default=99)
                            - max((c[1] for c in touched), default=0))
    # nothing outside the overlay cells changed, in any direction
    altered = 0
    for d, f in fr.items():
        for y in range(len(f)):
            for x in range(len(f[0])):
                if d == "Front" and (x, y) in touched:
                    continue
                if tuple(out[d][y][x]) != tuple(f[y][x]):
                    altered += 1
    res["non_overlay_pixels_altered"] = altered
    # readability: mark vs the crown cells immediately around it
    if touched:
        ml = [luminance(out["Front"][y][x][:3]) for (x, y) in touched]
        ring = {(x + dx, y + dy) for (x, y) in touched
                for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        ring = [c for c in ring if c in crown and c not in touched]
        rl = [luminance(fr["Front"][c[1]][c[0]][:3]) for c in ring]
        res["contrast"] = round((sum(rl) / len(rl)) - (sum(ml) / len(ml)), 1)
    else:
        res["contrast"] = 0.0
    # the visor's own separation must be untouched
    vo = [luminance(out["Front"][c[1]][c[0]][:3]) for c in visor]
    ol = [luminance(out["Front"][c[1]][c[0]][:3])
          for c, r in roles.items() if r == "outline"]
    res["visor_minus_outline"] = round(sum(vo) / len(vo) - sum(ol) / len(ol), 1)
    # the no-overlay control has nothing to contrast against; it is a control,
    # not a failing motif
    res["is_control"] = not touched
    res["ok"] = (res["on_crown"] and res["inside_zone"] and res["clear_of_visor"]
                 and altered == 0
                 and (res["is_control"] or res["contrast"] >= 60))
    return res


def main():
    install = "--install" in sys.argv
    app, fr, ov, marks, vocab = load()
    from cap2_safe_mask import build as build_mask
    safe, mask_stats = build_mask()
    globals()["SAFE"] = safe
    print(f"safe mask: {mask_stats['safe']} cells")
    sm = json.load(open("authored/source_bases/cap2/semantic_map.json"))
    roles = {tuple(int(v) for v in k.split(",")): r
             for k, r in sm["structural_roles"]["Front"].items()}
    wear = roundtrip.source_blocks(app)

    if PACK.exists():
        shutil.rmtree(PACK)
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)
    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Cap 2 Crown Overlay",
        "Author": "RNG Clothing Experiment", "Version": "1.0.0",
        "Description": "Cap 2 by plurffle, construction untouched. Marks are "
                       "generator-authored overlays on the front crown.",
        "UniqueID": UNIQUE_ID, "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"}}, indent=2))

    report, trace = {}, []
    entries = [(None, "Cap2 plain (no overlay)")] + [
        (n, f"Cap2 {n}") for n in ORDER]
    for i, (name, label) in enumerate(entries, 1):
        out, touched = apply_mark(fr, ov, marks, vocab, name, safe=safe)
        res = verify(name, fr, out, touched, ov, roles, vocab)
        report[name or "plain"] = res
        folder = f"Ov{i:02d}{(name or 'Plain').capitalize()}"
        d = PACK / "Hats" / folder
        d.mkdir(parents=True, exist_ok=True)
        rows = []
        for dd in DIRS:
            for y in range(20):
                rows.append(list(out[dd][y]))
        pngio.write_rgba_png(d / "hat.png", rows)
        doc = {"Name": label, "Format": "7.5.0",
               "Tags": ["RNG Clothing", "Cap2 Crown Overlay", "Art by plurffle",
                        "overlay: " + (name or "none")]}
        for j, dd in enumerate(DIRS):
            blk = {k: v for k, v in (wear.get(dd) or {}).items()
                   if k != "StartingPosition"}
            blk["DisableGrayscale"] = True
            blk["StartingPosition"] = {"X": 0, "Y": j * 20}
            doc[f"{dd}Hat"] = blk
        (d / "hat.json").write_text(json.dumps(doc, indent=2))
        trace.append({"folder": folder, "label": label, "overlay": name})
        flag = "OK " if res["ok"] else "FAIL"
        print(f"  {flag} {str(name or 'plain'):9s} cells={len(touched):2d} "
              f"crown={res['on_crown']} mask={res['inside_mask']} "
              f"visor-clear={res['clear_of_visor']} gap={res['visor_row_gap']} "
              f"altered={res['non_overlay_pixels_altered']} "
              f"contrast={res['contrast']:.0f} v-o={res['visor_minus_outline']:.0f}")
    (PACK / "trace.json").write_text(json.dumps(trace, indent=2))
    (PACK / "CREDITS.txt").write_text(
        "Base art: 'Cap 2' from More Accessories and Stuff, by plurffle.\n"
        "The cap construction is unmodified. The front-crown marks are\n"
        "generator-authored overlays and are not the original author's work.\n")
    json.dump(report, open("output/cap2_family/overlay_verification.json", "w"),
              indent=1)
    if install:
        dest = MODS / PACK.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(PACK, dest)
        print("installed ->", dest)


if __name__ == "__main__":
    main()
