"""PHASE 2 + 3: group the source library into authored families, dissect each,
and run the mandatory reconstruction test over every variant.

Writes source_catalog/families.json.  Nothing in the source tree is touched.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5.source import decompose


def main():
    cat = json.load(open("source_catalog/catalog.json"))
    groups = defaultdict(list)
    for a in cat["appearances"]:
        if not a["analysis"].get("error") and a["analysis"].get("boxes"):
            groups[(a["pack"], a["category"], a["stem"])].append(a)

    out, failed = [], []
    for key, apps in sorted(groups.items()):
        if len(apps) < 2:
            continue
        try:
            fam = decompose.build_family(apps)
            if fam is None:
                continue
            rep = decompose.reconstruct_report(fam)
        except Exception as exc:                      # noqa: BLE001
            failed.append({"family": key[2], "pack": key[0], "error": str(exc)})
            continue
        rep["vocabulary"] = [list(c) for c in fam.vocab]
        rep["roles"] = fam.roles
        rep["tone"] = fam.tone
        rep["base_png"] = fam.base_app["png_path"]
        rep["directions"] = sorted(fam.base_frames)
        rep["credit"] = {"pack": fam.pack, "author": fam.author,
                         "pack_id": fam.base_app["pack_id"]}
        out.append(rep)

    os.makedirs("source_catalog", exist_ok=True)
    json.dump({"families": out, "failed": failed},
              open("source_catalog/families.json", "w"), indent=1)

    exact = sum(1 for f in out if f["all_exact"])
    modelled = sum(f["modelled_count"] for f in out)
    promoted = sum(len(f["promote_to_own_base"]) for f in out)
    variants = sum(len(f["variants"]) for f in out)
    print(f"modelled as base+delta: {modelled}   promoted to own base: {promoted}")
    cls = defaultdict(int)
    for f in out:
        for v in f["variants"]:
            cls[v["class"]] += 1
    print(f"families {len(out)}   variants {variants}   failed {len(failed)}")
    print(f"reconstruction exact: {exact}/{len(out)} families")
    for k, n in sorted(cls.items()):
        print(f"   {k:16s} {n}")
    print("\nfamilies with REUSABLE components:")
    for f in sorted(out, key=lambda f: -sum(
            1 for v in f["variants"] if v["class"] == "REUSABLE")):
        n = sum(1 for v in f["variants"] if v["class"] == "REUSABLE")
        if not n:
            break
        names = [v["variant"] for v in f["variants"] if v["class"] == "REUSABLE"]
        print(f"   {f['category']:12s} {f['family']:16s} {n}  "
              f"{f['pack'][:20]:22s} {names}")


if __name__ == "__main__":
    main()
