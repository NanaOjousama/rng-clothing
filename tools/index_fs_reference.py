"""Turn the official Fashion Sense wiki into a machine-readable property matrix.

The wiki documents each appearance type on its own page, in the same table
shape.  Parsing those tables gives the complete property surface per type
without depending on any one page having been read in full, and makes it
possible to diff what the framework supports against what our exporter emits.
"""
from __future__ import annotations

import json
import os
import re

WIKI = "references/fashion-sense-official/wiki-git"
OUT = "references/fashion-sense-official"

TYPES = {
    "Hat-Model-Properties.md": "Hats",
    "Shirt-Model-Properties.md": "Shirts",
    "Pants-Model-Properties.md": "Pants",
    "Sleeves-Model-Properties.md": "Sleeves",
    "Shoes-Model-Properties.md": "Shoes",
    "Accessory-Model-Properties.md": "Accessories",
    "Hair-Model-Properties.md": "Hairs",
    "Body-Model-Properties.md": "Bodies",
}

ROW = re.compile(r"^\s*`([^`]+)`\s*\|\s*`?([^|`]*)`?\s*\|(.*)\|\s*`?([^|`]*)`?\s*$")


def parse(path):
    props = {}
    for line in open(path, encoding="utf-8"):
        if not line.strip().startswith("`"):
            continue
        m = ROW.match(line.rstrip("\n"))
        if not m:
            continue
        name, required, desc, default = m.groups()
        desc = re.sub(r"<br/?>", " ", desc)
        desc = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", desc).strip()
        props[name.strip()] = {
            "required": required.strip().lower() == "true",
            "default": default.strip(),
            "description": desc[:400],
        }
    return props


def main():
    matrix, pages = {}, {}
    for fn, category in TYPES.items():
        p = os.path.join(WIKI, fn)
        if os.path.isfile(p):
            matrix[category] = parse(p)
            pages[category] = ("https://github.com/Floogen/FashionSense/wiki/"
                               + fn[:-3])
    # every property, and which types carry it
    everywhere, by_prop = {}, {}
    for cat, props in matrix.items():
        for name, meta in props.items():
            by_prop.setdefault(name, {"types": [], "default": meta["default"],
                                      "description": meta["description"]})
            by_prop[name]["types"].append(cat)
    for name, meta in by_prop.items():
        if len(meta["types"]) == len(matrix):
            everywhere[name] = meta

    json.dump({"pages": pages, "by_type": matrix, "by_property": by_prop,
               "universal": sorted(everywhere)},
              open(os.path.join(OUT, "property_matrix.json"), "w"), indent=1)

    print(f"appearance types: {len(matrix)}")
    for cat, props in sorted(matrix.items()):
        req = [k for k, v in props.items() if v["required"]]
        print(f"  {cat:12s} {len(props):3d} properties   required: {req}")
    print(f"\nproperties common to ALL {len(matrix)} types ({len(everywhere)}):")
    print("   " + ", ".join(sorted(everywhere)))
    only = {k: v for k, v in by_prop.items() if len(v["types"]) < len(matrix)}
    print(f"\ntype-specific properties ({len(only)}):")
    for k, v in sorted(only.items(), key=lambda kv: (len(kv[1]['types']), kv[0])):
        print(f"   {k:34s} {','.join(sorted(v['types']))}")


if __name__ == "__main__":
    main()
