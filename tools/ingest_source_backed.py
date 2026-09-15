"""Ingest a source sheet as a SOURCE-BACKED V2 base (see v5/source_backed.py).

Beside, not instead of, tools/ingest_hat_base.py: the legacy base under
authored/bases/ is not touched and legacy output does not move.

What it writes, under authored/source_backed/<name>/:

    source_backed.json   manifest: source path + md5 (the preserved byte-identical
                         copy the legacy ingest already keeps), family/shape/style,
                         zones + anchors, placement override (empty), provenance
    semantic/<view>.png  the (role, step) map, index-coded -- the SAME stepper and
                         zone derivation as the legacy ingest, stored separately

What it does NOT write: any source pixel. The source sheet and hat.json stay the
canonical artwork; views, flips, placement and colouring are read from them at
load time.

    python3 tools/ingest_source_backed.py            # beret_02 and beret_01
    python3 tools/ingest_source_backed.py beret_02
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from ingest_hat_base import BODY, SPECS, derive_zones, rgb, stepper  # noqa: E402
from v5 import source_backed as sbm  # noqa: E402
from v5.pngio import read_rgba_png, write_rgba_png  # noqa: E402

TARGETS = ("beret_02", "beret_01")


def ingest(name):
    spec = SPECS[name]
    fam = spec["family"]
    keep = os.path.join("authored", "source_bases", fam, name, "source")
    png, js = os.path.join(keep, "hat.png"), os.path.join(keep, "hat.json")
    prov_path = os.path.join(ROOT, "authored", "source_bases", fam, name, "provenance.json")
    prov = json.load(open(prov_path))
    got = sbm.md5(os.path.join(ROOT, png))
    assert got == prov["source"]["md5"] == sbm.md5(os.path.join(ROOT, spec["source"])), \
        f"{name}: preserved copy is not the source"

    models = {k: v for k, v in sbm.read_fs_json(os.path.join(ROOT, js)).items()
              if k in sbm.MODEL_OF.values()}
    fw = int(next(iter(models.values()))["HatSize"]["Width"])
    fh = int(next(iter(models.values()))["HatSize"]["Length"])
    authored_y, mirrored = sbm.fs_views(models, fh)
    sheet = read_rgba_png(os.path.join(ROOT, png))
    frames = {v: [r[:fw] for r in sheet[y:y + fh]] for v, y in authored_y.items()}

    shades = sorted({p[:3] for r in sheet for p in r if p[3]})
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

    man = {
        "schema": sbm.SCHEMA,
        "name": name,
        "family": fam,
        "shape_variant": name,
        "slot": "HEAD",
        "classification": spec["classification"],
        "style": sorted(json.load(open(os.path.join(ROOT, "authored", "bases", name, "base.json")))["style"]),
        "source": {"png": png, "md5": got, "json": js, "json_md5": sbm.md5(os.path.join(ROOT, js)),
                   "frame_size": [fw, fh], "origin": spec["source"]},
        "views_note": "read from the source hat.json at load: authored "
                      f"{sorted(authored_y)}, mirrored {mirrored}",
        "semantic_map": {"dir": "semantic", "policy": spec["normalise"], "ramp": BODY,
                         "source_grey_to_step": {"#%02x%02x%02x" % s: smap[s[0]] for s in shades},
                         "role": "describes the source for recolouring/composition; never replaces it"},
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
        print(f"== {name}  {man['source']['png']}  md5 {man['source']['md5']}")
        print(f"   authored {sorted(ay)}  mirrored {mir}  "
              f"placement {[(v, b.placement(v)) for v in ('front', 'right', 'left', 'back')]}")
        print(f"   render fields {[(v, b.render_fields(v)) for v in b.views]}  rgb-keyed {b.rgb_keyed_fields()}")


if __name__ == "__main__":
    main()
