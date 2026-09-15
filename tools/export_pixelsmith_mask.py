"""Export an authored material mask from a Pixelsmith document.

Authoring workflow: a 20x80 Pixelsmith document with the source-backed base's
neutral sheet on the `base` layer and the mask painted, cell by cell, on a second
layer. Any non-empty cell on that layer is a mask cell. This tool only
TRANSCRIBES it -- frames are split by the base's authored views, nothing is
moved, thinned, filled or re-spaced -- into
authored/source_backed/<base>/materials/<treatment>.json.

A cell on a view the base mirrors at render (e.g. beret_02's left) is refused:
that view is produced from its opposite, so its mask is too.

    python3 tools/export_pixelsmith_mask.py beret02_plaid_mask --base beret_02 \
        --treatment plaid --factor 0.72 --provenance "..."
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from v5 import source_backed as sbm  # noqa: E402
from v5.authored import ATLAS_ORDER  # noqa: E402

LIBRARY = os.path.join(ROOT, "tools", "pixelsmith-workspace", "library")


def export(doc_id, base_name, treatment, factor, provenance):
    with open(os.path.join(LIBRARY, f"{doc_id}.chr.json")) as fh:
        doc = json.load(fh)
    layers = [l["id"] for l in doc["layers"] if l["id"] != "base"]
    if len(layers) != 1:
        raise SystemExit(f"{doc_id}: expected exactly one mask layer besides `base`, found {layers}")
    grid = doc["frames"][0]["layers"][layers[0]]
    b = sbm.load_one(base_name)
    fh_ = b.size[1]
    views = {}
    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            if not c:
                continue
            v = ATLAS_ORDER[y // fh_]
            if v in b.mirrored:
                raise SystemExit(f"mask cell ({x},{y}) is on `{v}`, which {base_name} mirrors from "
                                 f"`{b.mirrored[v]}`; paint the authored view instead")
            views.setdefault(v, []).append([x, y - ATLAS_ORDER.index(v) * fh_])
    out = {"treatment": treatment, "authored_for": base_name, "factor": factor,
           "views": {v: sorted(c) for v, c in sorted(views.items())},
           "mirrored_views": {v: f"mirrored from {s} at render, as the source draws it"
                              for v, s in b.mirrored.items()},
           "authoring_document": f"tools/pixelsmith-workspace/library/{doc_id}.chr.json#{layers[0]}",
           "provenance": provenance}
    d = os.path.join(ROOT, "authored", "source_backed", base_name, "materials")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{treatment}.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n")
    return path, out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("doc_id")
    ap.add_argument("--base", required=True)
    ap.add_argument("--treatment", required=True)
    ap.add_argument("--factor", type=float, required=True)
    ap.add_argument("--provenance", required=True)
    args = ap.parse_args()
    path, out = export(args.doc_id, args.base, args.treatment, args.factor, args.provenance)
    print(f"wrote {path}: " + ", ".join(f"{v} {len(c)}" for v, c in out["views"].items()))


if __name__ == "__main__":
    main()
