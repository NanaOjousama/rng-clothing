"""Source-fidelity trace: follow one source-backed base through every stage.

The generator exists to compose from source sprites that already look good. If a
good source comes out uglier, something on the way is modifying too much. This
walks a base through the pipeline and holds each stage to what it is ALLOWED to
change, so the first stage that changes anything else is named, not guessed.

--path v2 (Source-Backed V2, v5/source_backed.py):

    S1 source      preserved byte-identical source sheet
    S2 ingest      the V2 base's stored source pixels         must equal S1
    S3 neutral     render(), nothing applied                  must equal S1
    S4 palette     bake                                       alpha unchanged; every pixel
                                                              = source x tint (FS grayscale)
    S5 material    authored mask for this base, if any        changes only mask cells, by a
                                                              value ratio (shading order kept)
    S6 motif       decals via legacy placement/integration    changes only seated/shaded cells
    S7 pack        the written Fashion Sense sheet            must equal the render

--path legacy (the six-step authored path, kept for comparison):

    S1 source, S2 ingested, S3 neutral, S4 palette, S5 material, S6 pack, S7 worn

The only documented transformation is layout: frames restacked to front/right/
left/back, and a view the source draws `Flipped` materialised as its mirror.

    python3 tools/trace_source_fidelity.py                    # v2, beret_02
    python3 tools/trace_source_fidelity.py --base beret_01
    python3 tools/trace_source_fidelity.py --path legacy
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from v5 import authored
from v5 import source_backed as sbm
from v5.pngio import blank_image, blit, nearest_scale, read_rgba_png, write_rgba_png

ORDER = authored.ATLAS_ORDER
OPPOSITE = {"left": "right", "right": "left"}
FS = 20


def lstar(c):
    f = lambda v: ((v / 255 + 0.055) / 1.055) ** 2.4 if v / 255 > 0.04045 else v / 255 / 12.92
    y = 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])
    return 116 * y ** (1 / 3) - 16 if y > 0.008856 else 903.3 * y


def hexc(c):
    return "#%02x%02x%02x" % tuple(c[:3])


def provenance(name, family="beret"):
    path = os.path.join(ROOT, "authored", "source_bases", family, name, "provenance.json")
    with open(path) as fh:
        return json.load(fh)


def stack(views: dict):
    img = blank_image(FS, FS * len(ORDER))
    for i, v in enumerate(ORDER):
        blit(img, views[v], 0, i * FS)
    return img


def restack(views: dict, mirrored):
    """The documented layout transform: fill each mirrored view from its opposite."""
    views = dict(views)
    for v in mirrored:
        views[v] = authored._mirror(views[OPPOSITE[v]])
    return stack(views)


# --- legacy stages -----------------------------------------------------------------

def s1_source(name):
    prov = provenance(name)
    src = prov["source"]
    sheet = read_rgba_png(os.path.join(ROOT, src["preserved_copy"]))
    views = {v: [r[:] for r in sheet[y:y + FS]] for v, y in src["layout"].items()}
    return restack(views, prov["directions"]["mirrored"])


def s2_ingested(name):
    prov = provenance(name)
    d = os.path.join(ROOT, "authored", "bases", name)
    views = {v: read_rgba_png(os.path.join(d, f"{v}.png")) for v in prov["directions"]["authored"]}
    return restack(views, prov["directions"]["mirrored"])


def index_palette():
    with open(os.path.join(ROOT, "authored", "index.json")) as fh:
        idx = json.load(fh)
    ramps = {role: [tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) for h in ramp]
             for role, ramp in idx["roles"].items()}
    return authored.Palette("AUTHORING_INDEX", "the index's own greys", (), ramps)


def base_of(lib, name):
    return next(b for b in lib.bases if b.name == name)


def render(lib, base, palette, tone=None, treatment=None):
    dirs, dropped = authored._render(base, (), palette, tone, treatment)
    assert not dropped, dropped
    return stack(dirs)


def s3_neutral(lib, base):
    return render(lib, base, index_palette())


def s7_worn(capture_dir, pack_sheet, scale=4):
    """Sample the 4x hat-only capture back to logical pixels.

    `hat_only` is worn-minus-nohat, so it also holds hair and skin the hat
    changes. Only pixels whose colour is in the pack sheet's own colour set count
    as hat; the rest are reported as non-hat changes. Registration is the offset
    with the most exact colour matches against the pack frame -- the capture's
    bounds include those hair pixels, so its bounding box is not the hat's.
    Returns (sheet, notes)."""
    with open(os.path.join(capture_dir, "render_state.json")) as fh:
        state = json.load(fh)
    hat_colours = {p[:3] for r in pack_sheet for p in r if p[3]}
    out, notes = blank_image(FS, FS * len(ORDER)), {}
    for i, v in enumerate(ORDER):
        d = state["directions"][v]
        cap = read_rgba_png(d["hat_only"])
        b = d["hat_only_bounds"]
        frame = pack_sheet[i * FS:(i + 1) * FS]
        grid = {}
        for j in range(b["height"] // scale):
            for k in range(b["width"] // scale):
                px = cap[b["y"] + j * scale + 1][b["x"] + k * scale + 1]
                if px[3]:
                    grid[(k, j)] = px
        hat = {c: p for c, p in grid.items() if p[:3] in hat_colours}
        best = None
        for oy in range(-FS, FS):
            for ox in range(-FS, FS):
                hits = sum(1 for (k, j), p in hat.items()
                           if 0 <= k + ox < FS and 0 <= j + oy < FS and frame[j + oy][k + ox] == p)
                if best is None or hits > best[0]:
                    best = (hits, ox, oy)
        hits, ox, oy = best
        for (k, j), p in hat.items():
            if 0 <= k + ox < FS and 0 <= j + oy < FS:
                out[i * FS + j + oy][k + ox] = p
        opaque = sum(1 for y in range(FS) for x in range(FS) if frame[y][x][3])
        notes[v] = {"exact_4x": b["width"] % scale == 0 and b["height"] % scale == 0,
                    "offset": [ox, oy], "pack_opaque": opaque, "hat_px_in_capture": len(hat),
                    "exact_matches": hits, "non_hat_changed_px": len(grid) - len(hat),
                    "pack_px_not_visible": opaque - hits}
    return out, notes


# --- V2 stages and their expectations ------------------------------------------------

def changed_cells(a, b):
    return {(x, y) for y in range(len(a)) for x in range(FS) if a[y][x] != b[y][x]}


def allowed_sheet_cells(r, kinds):
    """Sheet coordinates of every cell a render's operations were authorised to change."""
    out = set()
    for i, v in enumerate(ORDER):
        for k in kinds:
            out |= {(x, y + i * FS) for x, y in r.changes[v][k]}
    return out


def v2_stages(name, palette_id="EVERYDAY_STONE_BLUE", material="plaid", decal_names=None,
              material_mask=None):
    """Build every V2 stage and the rule each one must obey.

    Returns a list of dicts: {name, sheet, unexpected:set, notes}. `unexpected`
    holds every pixel the stage changed WITHOUT authorisation."""
    lib = authored.load()
    sb = sbm.load_one(name)
    if material_mask is not None:
        sb = sbm.SourceBackedBase(**{**sb.__dict__, "materials": {material: material_mask}})
    pal = next(p for p in lib.palettes if p.id == palette_id)
    src = s1_source(name)
    stages = [{"name": "S1_source", "sheet": src, "unexpected": set(), "notes": {}}]

    ingest = restack({v: sb.source[v] for v in sb.views}, sb.mirrored)
    stages.append({"name": "S2_ingest", "sheet": ingest, "unexpected": changed_cells(src, ingest),
                   "notes": {"rule": "stored source pixels == source"}})

    neutral = sbm.render(sb)
    ns = sbm.sheet(neutral)
    stages.append({"name": "S3_neutral", "sheet": ns, "unexpected": changed_cells(src, ns),
                   "notes": {"rule": "neutral render == source", "baked": neutral.baked}})

    rp = sbm.render(sb, pal)
    ps = sbm.sheet(rp)
    tint = pal.color(sbm.TINT_ROLE, sbm.TINT_STEP)
    want = [[sbm._tint(p, tint) if p[3] else p for p in r] for r in ns]
    alpha = {(x, y) for y in range(len(ns)) for x in range(FS) if (ns[y][x][3] > 0) != (ps[y][x][3] > 0)}
    stages.append({"name": "S4_palette", "sheet": ps, "unexpected": changed_cells(want, ps) | alpha,
                   "notes": {"rule": "alpha unchanged; pixel = source x tint", "tint": hexc(tint),
                             "alpha_changed": len(alpha)}})

    prev, prev_r = ps, rp
    try:
        rm = sbm.render(sb, pal, material)
        ms = sbm.sheet(rm)
        allowed = allowed_sheet_cells(rm, ("material",))
        unexpected = changed_cells(ps, ms) - allowed
        shading = shading_report(ps, ms, allowed)
        if shading["order_inversions"]:
            unexpected |= set(shading["inverted_cells"])
        stages.append({"name": "S5_material", "sheet": ms, "unexpected": unexpected,
                       "notes": {"rule": "only mask cells change, by a value ratio", "mask_cells": len(allowed),
                                 "shading": {k: v for k, v in shading.items() if k != "inverted_cells"}}})
        prev, prev_r = ms, rm
    except sbm.Incompatible as exc:
        stages.append({"name": "S5_material", "sheet": ps, "unexpected": set(),
                       "notes": {"rule": "refused, not re-fitted", "incompatible": str(exc)}})

    decals = pick_decals(lib, sb, decal_names)
    rd = sbm.render(sb, pal, prev_r.material or None, decals)
    ds = sbm.sheet(rd)
    allowed = allowed_sheet_cells(rd, ("decal", "occlusion"))
    stages.append({"name": "S6_motif", "sheet": ds, "unexpected": changed_cells(prev, ds) - allowed,
                   "notes": {"rule": "only seated/shaded decal cells change",
                             "decals": [d.name for d in decals], "dropped": list(rd.dropped),
                             "allowed_cells": len(allowed)}})

    with tempfile.TemporaryDirectory() as tmp:
        write_rgba_png(os.path.join(tmp, "hat.png"), sbm.sheet(rd))
        with open(os.path.join(tmp, "hat.json"), "w") as fh:
            json.dump(sbm.hat_json(rd, "trace"), fh)
        pk = read_rgba_png(os.path.join(tmp, "hat.png"))
        with open(os.path.join(tmp, "hat.json")) as fh:
            pj = json.load(fh)
    stages.append({"name": "S7_pack", "sheet": pk, "unexpected": changed_cells(ds, pk),
                   "notes": {"rule": "pack sheet == render",
                             "HeadPosition": {k: v["HeadPosition"] for k, v in pj.items() if isinstance(v, dict)},
                             "DisableGrayscale": {k: v.get("DisableGrayscale") for k, v in pj.items()
                                                  if isinstance(v, dict)}}})
    return stages


def shading_report(before, after, cells):
    """Does a material keep the underlying form shading? Among the changed cells,
    any pair whose value order flips relative to before is shading destroyed."""
    cs = sorted(cells, key=lambda c: (c[1], c[0]))
    lb = {c: lstar(before[c[1]][c[0]]) for c in cs}
    la = {c: lstar(after[c[1]][c[0]]) for c in cs}
    inv = set()
    for i, p in enumerate(cs):
        for q in cs[i + 1:]:
            if p[1] // FS != q[1] // FS:
                continue
            if lb[p] < lb[q] - 0.5 and la[p] > la[q] + 0.5:
                inv |= {p, q}
    shifts = [la[c] - lb[c] for c in cs]
    return {"order_inversions": len(inv), "inverted_cells": sorted(inv),
            "max_abs_dL": round(max((abs(s) for s in shifts), default=0.0), 1)}


def pick_decals(lib, sb, names=None):
    """One surface motif and one attachment that place on this base in every view
    they claim -- the combinator's own can_place, on the semantic map."""
    if names is not None:
        return [next(d for d in lib.decals if d.name == n) for n in names]
    legal = [d for d in lib.decals if d.slot == sb.semantic.slot and not d.pending
             and d.fits_base(sb.semantic) and authored.can_place(sb.semantic, d)]
    out = []
    for kind in ("surface", "attachment"):
        c = sorted((d for d in legal if d.kind == kind), key=lambda d: d.name)
        if c:
            out.append(c[0])
    return out


def first_unexpected_stage(stages):
    return next((s["name"] for s in stages if s["unexpected"]), None)


# --- measurement (legacy report) ------------------------------------------------------

def compare(a, b):
    """How far sheet b is from sheet a, in terms of what makes a sprite itself."""
    alpha = rgb = 0
    classes = {}
    pairs = []
    for y in range(len(a)):
        for x in range(FS):
            pa, pb = a[y][x], b[y][x]
            if (pa[3] > 0) != (pb[3] > 0):
                alpha += 1
                continue
            if not pa[3]:
                continue
            if pa[:3] != pb[:3]:
                rgb += 1
            classes.setdefault(pa[:3], {}).setdefault(pb[:3], 0)
            classes[pa[:3]][pb[:3]] += 1
            for dx, dy in ((1, 0), (0, 1)):
                X, Y = x + dx, y + dy
                if X >= FS or Y >= len(a) or Y // FS != y // FS:
                    continue
                qa, qb = a[Y][X], b[Y][X]
                if qa[3] and qb[3] and qa[:3] != pa[:3]:
                    pairs.append((abs(lstar(pa) - lstar(qa)), abs(lstar(pb) - lstar(qb))))
    splits = {hexc(c): {hexc(k): n for k, n in t.items()} for c, t in classes.items() if len(t) > 1}
    dominant = {c: max(t, key=t.get) for c, t in classes.items()}
    merged = {}
    for c, d in dominant.items():
        merged.setdefault(d, []).append(hexc(c))
    merges = {hexc(d): cs for d, cs in merged.items() if len(cs) > 1}
    order = sorted(classes, key=lstar)
    inversions = [(hexc(p), hexc(q)) for i, p in enumerate(order) for q in order[i + 1:]
                  if lstar(dominant[p]) > lstar(dominant[q]) + 0.5]
    ramp = [{"from": hexc(c), "L_from": round(lstar(c), 1), "to": hexc(dominant[c]),
             "L_to": round(lstar(dominant[c]), 1), "px": sum(classes[c].values())} for c in order]
    edge_a = sorted(p[0] for p in pairs)
    edge_b = sorted(p[1] for p in pairs)
    med = lambda s: s[len(s) // 2] if s else 0.0
    return {"alpha_changed": alpha, "rgb_changed": rgb, "splits": splits, "merges": merges,
            "value_order_inversions": inversions, "ramp": ramp,
            "edge_contrast_median": [round(med(edge_a), 1), round(med(edge_b), 1)],
            "edge_pairs": len(pairs)}


def diff_image(a, b, scale=8, flag=None):
    """Grey = unchanged opaque, red = colour changed, blue = alpha changed,
    magenta = changed WITHOUT authorisation (V2 `flag` set)."""
    img = blank_image(FS, len(a), (255, 255, 255, 255))
    for y in range(len(a)):
        for x in range(FS):
            pa, pb = a[y][x], b[y][x]
            if flag and (x, y) in flag:
                img[y][x] = (230, 0, 230, 255)
            elif (pa[3] > 0) != (pb[3] > 0):
                img[y][x] = (40, 90, 255, 255)
            elif pa[3] or pb[3]:
                img[y][x] = (225, 40, 40, 255) if pa[:3] != pb[:3] else (200, 200, 200, 255)
    return nearest_scale(img, scale)


def strip(sheets, gap=2, bg=(236, 236, 236, 255)):
    img = blank_image(len(sheets) * (FS + gap) - gap, FS * len(ORDER), (255, 255, 255, 255))
    for i, s in enumerate(sheets):
        for y in range(len(s)):
            for x in range(FS):
                img[y][x + i * (FS + gap)] = s[y][x] if s[y][x][3] else bg
    return img


def write_strips(out, named, flags=None):
    for n, s in named:
        write_rgba_png(os.path.join(out, f"{n}.png"), s)
    sheets = [s for _, s in named]
    write_rgba_png(os.path.join(out, "stages_native.png"), strip(sheets))
    write_rgba_png(os.path.join(out, "stages_x8.png"), nearest_scale(strip(sheets), 8))
    diffs = [diff_image(p, s, 1, (flags or {}).get(n)) for (_, p), (n, s) in zip(named, named[1:])]
    write_rgba_png(os.path.join(out, "diffs_vs_previous_x8.png"), nearest_scale(strip(diffs), 8))


def main_v2(args):
    out = args.out or os.path.join(ROOT, "experiments", "source_fidelity", "v2", args.base)
    os.makedirs(out, exist_ok=True)
    stages = v2_stages(args.base, args.palette, args.treatment,
                       args.decals.split(",") if args.decals else None)
    write_strips(out, [(s["name"], s["sheet"]) for s in stages],
                 {s["name"]: s["unexpected"] for s in stages})
    report = {"path": "source_backed_v2", "base": args.base,
              "first_unexpected_stage": first_unexpected_stage(stages),
              "stages": [{"name": s["name"], "unexpected_px": len(s["unexpected"]),
                          "unexpected": sorted(s["unexpected"])[:20], "notes": s["notes"]} for s in stages],
              "vs_source": {s["name"]: compare(stages[0]["sheet"], s["sheet"]) for s in stages[1:]}}
    with open(os.path.join(out, "report.json"), "w") as fh:
        json.dump(report, fh, indent=1, default=list)
    print(f"{args.base}  [Source-Backed V2]  palette={args.palette}  material={args.treatment}")
    for s in stages:
        n = s["notes"]
        extra = {k: v for k, v in n.items() if k not in ("rule",)}
        print(f"  {s['name']:11} unexpected {len(s['unexpected']):3}  rule: {n.get('rule', '-')}"
              + (f"  {json.dumps(extra, default=list)[:220]}" if extra else ""))
    print(f"FIRST UNEXPECTED STAGE: {report['first_unexpected_stage']}")
    print(f"wrote {out}")
    return 0 if report["first_unexpected_stage"] is None else 1


def main_legacy(args):
    out = args.out or os.path.join(ROOT, "experiments", "source_fidelity", args.base)
    os.makedirs(out, exist_ok=True)
    lib = authored.load()
    base = base_of(lib, args.base)
    pal = next(p for p in lib.palettes if p.id == args.palette)
    tone = lib.tone_for(base)
    stages = [("S1_source", s1_source(args.base)),
              ("S2_ingested", s2_ingested(args.base)),
              ("S3_neutral", s3_neutral(lib, base)),
              ("S4_palette", render(lib, base, pal, tone)),
              ("S5_material", render(lib, base, pal, tone, lib.treatment(args.treatment)))]
    notes = {"base": args.base, "palette": args.palette, "tone_profile": base.tone_profile,
             "treatment": args.treatment}
    if args.pack:
        pack = os.path.join(ROOT, args.pack)
        stages.append(("S6_pack", read_rgba_png(os.path.join(pack, "hat.png"))))
        if args.capture:
            worn, wnotes = s7_worn(os.path.join(ROOT, args.capture), stages[-1][1])
            stages.append(("S7_worn", worn))
            notes["worn_sampling"] = wnotes
    report = {"notes": notes, "vs_previous": {}, "vs_source": {}}
    src = stages[0][1]
    for (pn, p), (n, s) in zip(stages, stages[1:]):
        report["vs_previous"][f"{pn}->{n}"] = compare(p, s)
        report["vs_source"][n] = compare(src, s)
    write_strips(out, stages)
    with open(os.path.join(out, "report.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    print(f"{args.base}  [legacy six-step]  palette={args.palette}  treatment={args.treatment}")
    for n, r in report["vs_source"].items():
        print(f"  {n:12} vs source: alpha {r['alpha_changed']:3}  rgb {r['rgb_changed']:3}  "
              f"merges {len(r['merges'])}  edge dL median {r['edge_contrast_median']}")
    print(f"wrote {out}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", choices=("v2", "legacy"), default="v2")
    ap.add_argument("--base", default="beret_02")
    ap.add_argument("--palette", default="EVERYDAY_STONE_BLUE")
    ap.add_argument("--treatment", default="plaid")
    ap.add_argument("--decals", help="comma-separated decal names (v2); default: one placeable surface + attachment")
    ap.add_argument("--pack", default="")
    ap.add_argument("--capture", default="")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    return main_v2(args) if args.path == "v2" else main_legacy(args)


if __name__ == "__main__":
    sys.exit(main())
