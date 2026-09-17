"""Ingest source hats as SOURCE-BACKED V2 bases (see v5/source_backed.py).

The source pixels remain canonical. This tool writes only semantic maps plus a
manifest, and keeps an ignored byte-identical source copy beside provenance so
local builds can pin the exact third-party input without committing that art.

Existing beret targets still resolve through ingest_hat_base.SPECS. New targets
may be declared directly here; they do NOT need a legacy six-step authored base.
That keeps Source-Backed V2 independent from the destructive legacy renderer.

    python3 tools/ingest_source_backed.py
    python3 tools/ingest_source_backed.py cap_baseball cap_snapback
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from ingest_hat_base import BODY, SPECS, derive_zones, rgb, stepper  # noqa: E402
from v5 import source_backed as sbm  # noqa: E402
from v5.pngio import read_rgba_png, write_rgba_png  # noqa: E402

# Source-Backed-only targets. These intentionally do not enter authored/bases/.
DIRECT_SPECS = {
    "cap_baseball": {
        "family": "cap",
        "source": "generator content/[FS] More Accessories and Stuff Pack/Hats/Cap2/hat.png",
        "source_json": "generator content/[FS] More Accessories and Stuff Pack/Hats/Cap2/hat.json",
        "internal_name": "More Accessories and Stuff / Cap 2",
        "normalise": "rank",
        "style": ["casual", "smart", "work"],
        "classification": "REFERENCE",
        "classification_reason":
            "plurffle source selected as the provisional Baseball master after live worn audit "
            "session 20260916-203154. Source pixels are construction authority; held at "
            "REFERENCE until redistribution/shipping clearance is explicit.",
        "attribution": "plurffle — [FS] More Accessories and Stuff, Cap 2",
    },
    "cap_snapback": {
        "family": "cap",
        "source": "generator content/[FS] More Accessories and Stuff Pack/Hats/CapSnapback/hat.png",
        "source_json": "generator content/[FS] More Accessories and Stuff Pack/Hats/CapSnapback/hat.json",
        "internal_name": "More Accessories and Stuff / Cap (Snapback)",
        "normalise": "rank",
        "style": ["casual", "festival", "smart"],
        "classification": "REFERENCE",
        "classification_reason":
            "plurffle source selected as a distinct Snapback construction after live worn audit "
            "session 20260916-203154. Source pixels are construction authority; held at "
            "REFERENCE until redistribution/shipping clearance is explicit.",
        "attribution": "plurffle — [FS] More Accessories and Stuff, Cap (Snapback)",
    },
}

TARGETS = ("beret_02", "beret_01", "cap_baseball", "cap_snapback")


def _md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _spec(name):
    if name in DIRECT_SPECS:
        return DIRECT_SPECS[name]
    return SPECS[name]


def _preserve_source(name, spec):
    fam = spec["family"]
    src_png = os.path.join(ROOT, spec["source"])
    src_json = os.path.join(ROOT, spec["source_json"])
    keep = os.path.join(ROOT, "authored", "source_bases", fam, name, "source")
    os.makedirs(keep, exist_ok=True)
    for src, leaf in ((src_png, "hat.png"), (src_json, "hat.json")):
        dst = os.path.join(keep, leaf)
        if not os.path.exists(dst) or _md5(dst) != _md5(src):
            shutil.copy2(src, dst)
        if _md5(dst) != _md5(src):
            raise AssertionError(f"{name}: preserved {leaf} is not byte-identical")
    return src_png, src_json, os.path.join(keep, "hat.png"), os.path.join(keep, "hat.json")


def ingest(name):
    spec = _spec(name)
    fam = spec["family"]
    direct = name in DIRECT_SPECS
    if direct:
        src_png, src_json, png, js = _preserve_source(name, spec)
        style = sorted(spec["style"])
    else:
        # Preserve the original beret ingest contract exactly: its rich provenance
        # and ignored source copy were established by ingest_hat_base.py already.
        keep = os.path.join(ROOT, "authored", "source_bases", fam, name, "source")
        png, js = os.path.join(keep, "hat.png"), os.path.join(keep, "hat.json")
        src_png, src_json = os.path.join(ROOT, spec["source"]), os.path.join(ROOT, spec["source_json"])
        prov = json.load(open(os.path.join(ROOT, "authored", "source_bases", fam, name, "provenance.json")))
        got = _md5(png)
        assert got == prov["source"]["md5"] == _md5(src_png), f"{name}: preserved copy is not the source"
        style = sorted(json.load(open(os.path.join(ROOT, "authored", "bases", name, "base.json")))["style"])
    models = {k: v for k, v in sbm.read_fs_json(js).items() if k in sbm.MODEL_OF.values()}
    if not models:
        raise ValueError(f"{name}: source JSON has no Fashion Sense hat model blocks")
    fw = int(next(iter(models.values()))["HatSize"]["Width"])
    fh = int(next(iter(models.values()))["HatSize"]["Length"])
    authored_y, mirrored = sbm.fs_views(models, fh)
    sheet = read_rgba_png(png)
    if len(sheet[0]) != fw:
        raise ValueError(f"{name}: source width {len(sheet[0])}, model width {fw}")
    frames = {v: [r[:fw] for r in sheet[y:y + fh]] for v, y in authored_y.items()}

    shades = sorted({p[:3] for r in sheet for p in r if p[3]})
    if any(not (c[0] == c[1] == c[2]) for c in shades):
        raise ValueError(f"{name}: semantic ingest currently expects a greyscale tint-mask source")
    smap = stepper(shades, spec["normalise"])
    ramp = [rgb(c) for c in BODY]
    out = os.path.join(ROOT, "authored", "source_backed", name)
    os.makedirs(os.path.join(out, "semantic"), exist_ok=True)
    sem = {}
    for v, f in frames.items():
        g = [[(ramp[smap[p[0]]] + (255,)) if p[3] else (0, 0, 0, 0) for p in r] for r in f]
        write_rgba_png(os.path.join(out, "semantic", f"{v}.png"), g)
        sem[v] = g
    zones = {v: derive_zones(g) for v, g in sem.items()}
    anchors = {}
    for z in ("crown_top", "side", "band"):
        got_z = {v: [zones[v][z][0], zones[v][z][1]] for v in zones if z in zones[v]}
        if got_z:
            anchors[z] = got_z

    if direct:
        prov_dir = os.path.join(ROOT, "authored", "source_bases", fam, name)
        os.makedirs(prov_dir, exist_ok=True)
        prov = {
            "id": name,
            "family": fam,
            "classification": spec["classification"],
            "classification_reason": spec["classification_reason"],
            "attribution": spec["attribution"],
            "source": {
                "path": spec["source"],
                "internal_name": spec["internal_name"],
                "md5": _md5(src_png),
                "json_md5": _md5(src_json),
                "size": [len(sheet[0]), len(sheet)],
                "layout": authored_y,
                "read_only": True,
                "preserved_copy": f"authored/source_bases/{fam}/{name}/source/hat.png",
                "preserved_copy_md5": _md5(png),
            },
            "directions": {
                "authored": sorted(authored_y),
                "mirrored": mirrored,
                "note": "read directly from the source Fashion Sense model blocks",
            },
            "source_backed": {
                "neutral_pixels": "canonical source pixels; semantic map never replaces them",
                "normalisation_policy": spec["normalise"],
                "semantic_only": True,
            },
        }
        with open(os.path.join(prov_dir, "provenance.json"), "w") as fh_:
            json.dump(prov, fh_, indent=2)
            fh_.write("\n")

    man = {
        "schema": sbm.SCHEMA,
        "name": name,
        "family": fam,
        "shape_variant": name,
        "slot": "HEAD",
        "classification": spec["classification"],
        "style": style,
        "source": {
            "png": f"authored/source_bases/{fam}/{name}/source/hat.png",
            "md5": _md5(png),
            "json": f"authored/source_bases/{fam}/{name}/source/hat.json",
            "json_md5": _md5(js),
            "frame_size": [fw, fh],
            "origin": spec["source"],
        },
        "views_note": "read from the source hat.json at load: authored "
                      f"{sorted(authored_y)}, mirrored {mirrored}",
        "semantic_map": {
            "dir": "semantic",
            "policy": spec["normalise"],
            "ramp": BODY,
            "source_grey_to_step": {"#%02x%02x%02x" % s: smap[s[0]] for s in shades},
            "role": "describes the source for recolouring/composition; never replaces it",
        },
        "anchors": anchors,
        "zones": zones,
        "placement_override": {},
        "placement_note": "empty: the source hat.json HeadPosition is the default. An override "
                          "must name its in-game QC evidence.",
        "provenance": f"{spec['classification']}-ONLY: {spec['attribution']} ({spec['source']}). "
                      f"See authored/source_bases/{fam}/{name}/provenance.json",
    }
    with open(os.path.join(out, sbm.MANIFEST), "w") as fh_:
        json.dump(man, fh_, indent=2)
        fh_.write("\n")
    return man, authored_y, mirrored


def main():
    for name in sys.argv[1:] or TARGETS:
        man, ay, mir = ingest(name)
        b = sbm.load_one(name)
        print(f"== {name}  {man['source']['origin']}  md5 {man['source']['md5']}")
        print(f"   authored {sorted(ay)}  mirrored {mir}  "
              f"placement {[(v, b.placement(v)) for v in ('front', 'right', 'left', 'back')]}")
        print(f"   neutral source-backed load OK; render fields "
              f"{[(v, b.render_fields(v)) for v in b.views]}")


if __name__ == "__main__":
    main()
