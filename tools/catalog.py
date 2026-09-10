#!/usr/bin/env python3
"""Read-only query layer over the approved source catalogue.

The source pixels are the construction authority (CLAUDE.md section 2), so this
is the tool that answers "what may V2 actually build with?".  It never writes:
every file is opened for reading, and the source packs stay read-only.

The point that matters most is APPROVAL STATE.  `families.json` classifies every
variant against its family base, and those classes are not decoration -- they
decide what may be composed:

    REUSABLE        the component transfers to other bases in its family.
                    Composable.
    BASE-SPECIFIC   drawn for exactly one base; it wandered when reused.
                    Composable ONLY onto that base.
    REFERENCE-ONLY  not a decoration on the base at all -- a different
                    construction (it usually REMOVES base cells).  Must not be
                    composed.  Read it for evidence; never build with it.

`--json` on any subcommand prints machine-readable output.

    python3 tools/catalog.py packs
    python3 tools/catalog.py families --category Hats
    python3 tools/catalog.py family "Bag"
    python3 tools/catalog.py components --class REUSABLE
    python3 tools/catalog.py find beanie
    python3 tools/catalog.py show "Beanie"
    python3 tools/catalog.py ramp "Beanie"
    python3 tools/catalog.py approval
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "source_catalog" / "catalog.json"
FAMILIES = ROOT / "source_catalog" / "families.json"

# What each class permits.  Kept here, next to the queries, so no caller has to
# remember it -- and so every listing can print the consequence, not just the label.
COMPOSABLE = {
    "REUSABLE": "composable onto any base in its family",
    "BASE-SPECIFIC": "composable ONLY onto its own base",
    "REFERENCE-ONLY": "NOT composable -- different construction, evidence only",
}


def load() -> tuple[dict, dict]:
    for p in (CATALOG, FAMILIES):
        if not p.exists():
            sys.exit(f"missing {p} -- the source catalogue has not been built")
    return json.loads(CATALOG.read_text()), json.loads(FAMILIES.read_text())


def out(rows, args, *cols) -> None:
    """Print as a table, or as JSON when asked."""
    if args.json:
        print(json.dumps(rows, indent=1))
        return
    if not rows:
        print("(no matches)")
        return
    if isinstance(rows, dict):
        for k, v in rows.items():
            print(f"{k:<28} {v}")
        return
    widths = {c: max(len(c), *(len(str(r.get(c, ""))) for r in rows)) for c in cols}
    print("  ".join(c.upper().ljust(widths[c]) for c in cols))
    for r in rows:
        print("  ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols))
    print(f"\n{len(rows)} row(s)")


def provenance(a: dict) -> dict:
    """Where a thing came from -- always reported alongside anything usable."""
    return {"pack": a.get("pack"), "author": a.get("pack_author") or a.get("author"),
            "pack_id": a.get("pack_id"), "png": a.get("png_path"),
            "json": a.get("json_path")}


def cmd_packs(cat, fam, args):
    out(cat["packs"], args, "pack", "pack_author", "version", "pack_id")


def cmd_families(cat, fam, args):
    rows = fam["families"]
    if args.category:
        rows = [f for f in rows if f["category"].lower() == args.category.lower()]
    if args.pack:
        rows = [f for f in rows if args.pack.lower() in f["pack"].lower()]
    if args.author:
        rows = [f for f in rows if args.author.lower() in (f.get("author") or "").lower()]
    rows = [dict(f, variants=len(f["variants"]),
                 reusable=sum(1 for v in f["variants"] if v.get("class") == "REUSABLE"),
                 ref_only=sum(1 for v in f["variants"] if v.get("class") == "REFERENCE-ONLY"))
            for f in rows]
    out(rows, args, "family", "category", "pack", "author", "base",
        "base_cells", "variants", "reusable", "ref_only", "modelled_count")


def cmd_family(cat, fam, args):
    hits = [f for f in fam["families"] if args.name.lower() in f["family"].lower()]
    if not hits:
        sys.exit(f"no family matching {args.name!r}")
    for f in hits:
        if args.json:
            print(json.dumps(f, indent=1))
            continue
        print(f"\n=== {f['family']}  ({f['category']}) ===")
        print(f"pack       {f['pack']}   author {f.get('author')}")
        print(f"base       {f['base']}  ({f['base_cells']} cells)")
        print(f"credit     {f.get('credit')}")
        print(f"modelled   {f.get('modelled_count')} of {len(f['variants'])}"
              f"   all_exact={f.get('all_exact')}"
              f"   promote_to_own_base={f.get('promote_to_own_base')}")
        if f.get("vocabulary"):
            print(f"vocabulary {f['vocabulary']}")
        if f.get("roles"):
            print(f"roles      {f['roles']}")
        if f.get("tone"):
            print(f"tone       {f['tone']}")
        print("\nvariants:")
        for v in f["variants"]:
            cls = v.get("class", "?")
            print(f"  [{cls:<14}] {v['variant']}")
            print(f"      +{v.get('added')} ~{v.get('changed')} -{v.get('removed')}"
                  f"  modelled={v.get('modelled')} exact={v.get('exact')}")
            print(f"      {COMPOSABLE.get(cls, 'unknown class')}")
            if v.get("reason"):
                print(f"      reason: {v['reason']}")


def cmd_components(cat, fam, args):
    """Variants, filtered by approval class.  Defaults to what is composable."""
    want = args.klass.upper() if args.klass else None
    rows = []
    for f in fam["families"]:
        for v in f["variants"]:
            cls = v.get("class")
            if want and cls != want:
                continue
            if want is None and cls == "REFERENCE-ONLY":
                continue                      # never offer non-composable by default
            rows.append({"variant": v["variant"], "class": cls, "family": f["family"],
                         "category": f["category"], "base": f["base"],
                         "pack": f["pack"], "author": f.get("author"),
                         "permits": COMPOSABLE.get(cls, "?"),
                         "modelled": v.get("modelled"), "exact": v.get("exact")})
    if not args.json and want is None:
        print("(showing composable variants only; --class REFERENCE-ONLY to see the rest)\n")
    out(rows, args, "variant", "class", "family", "base", "pack", "modelled", "exact")


def cmd_find(cat, fam, args):
    rows = cat["appearances"]
    if args.term:
        t = args.term.lower()
        rows = [a for a in rows if t in a["name"].lower() or t in a["folder"].lower()]
    if args.category:
        rows = [a for a in rows if a["category"].lower() == args.category.lower()]
    if args.pack:
        rows = [a for a in rows if args.pack.lower() in a["pack"].lower()]
    if args.author:
        rows = [a for a in rows if args.author.lower() in (a.get("pack_author") or "").lower()]
    if args.animated:
        rows = [a for a in rows if a.get("animated")]
    if args.color_masks:
        rows = [a for a in rows if a.get("color_masks")]
    if args.hide_hair:
        rows = [a for a in rows if a.get("hide_hair")]
    rows = [dict(a, size="x".join(map(str, a.get("png_size") or [])),
                 dirs=",".join((a.get("directions") or {}).keys()))
            for a in rows]
    out(rows, args, "name", "category", "pack", "pack_author", "size", "dirs", "animated")


def cmd_show(cat, fam, args):
    hits = [a for a in cat["appearances"] if args.name.lower() in a["name"].lower()]
    if not hits:
        sys.exit(f"no appearance matching {args.name!r}")
    for a in hits[: args.limit]:
        if args.json:
            print(json.dumps(a, indent=1))
            continue
        print(f"\n=== {a['name']}  ({a['category']}) ===")
        for k, v in provenance(a).items():
            print(f"  {k:<9} {v}")
        print(f"  size      {a.get('png_size')}   animated={a.get('animated')}"
              f"   color_masks={a.get('color_masks')}   hide_hair={a.get('hide_hair')}")
        if a.get("notes"):
            print(f"  notes     {a['notes']}")
        for d, meta in (a.get("directions") or {}).items():
            keep = {k: v for k, v in (meta or {}).items() if v is not None}
            print(f"  {d:<9} {keep}")
        frames = (a.get("analysis") or {}).get("frames") or {}
        for d, fr in frames.items():
            print(f"  [{d}] cells={fr.get('cells')} bbox={fr.get('bbox')} "
                  f"colours={fr.get('colours')} grey_share={fr.get('grey_share')}")
        # which families claim it, and therefore what it may be composed onto
        for f in fam["families"]:
            for v in f["variants"]:
                if v["variant"] == a["name"]:
                    print(f"  FAMILY    {f['family']} ({f['pack']}) -> "
                          f"[{v.get('class')}] {COMPOSABLE.get(v.get('class'), '?')}")
            # family names repeat across packs (two packs both ship a "Beanie"),
            # so always name the pack too or the answer is ambiguous
            if f["base"] == a["name"]:
                print(f"  FAMILY    {f['family']} ({f['pack']}) -> this is the family BASE")


def cmd_ramp(cat, fam, args):
    """Per-direction palettes as already measured from the source pixels."""
    hits = [a for a in cat["appearances"] if args.name.lower() in a["name"].lower()]
    if not hits:
        sys.exit(f"no appearance matching {args.name!r}")
    a = hits[0]
    frames = (a.get("analysis") or {}).get("frames") or {}
    if args.json:
        print(json.dumps({"name": a["name"], "provenance": provenance(a),
                          "frames": frames}, indent=1))
        return
    print(f"{a['name']}  ({a['category']}, {a['pack']} by {a.get('pack_author')})")
    for d, fr in frames.items():
        pal = fr.get("palette") or []
        print(f"\n[{d}]  {fr.get('cells')} cells, {fr.get('colours')} colours, "
              f"grey_share={fr.get('grey_share')}")
        for entry in pal:
            r, g, b, al, n = (list(entry) + [None] * 5)[:5]
            lum = None if r is None else round(0.299 * r + 0.587 * g + 0.114 * b, 1)
            print(f"   #{r:02x}{g:02x}{b:02x}  rgba({r},{g},{b},{al})  "
                  f"count={n}  luma={lum}")


def cmd_approval(cat, fam, args):
    counts: dict[str, int] = {}
    for f in fam["families"]:
        for v in f["variants"]:
            counts[v.get("class") or "?"] = counts.get(v.get("class") or "?", 0) + 1
    rows = {f"{k} ({COMPOSABLE.get(k,'?')})": v for k, v in sorted(counts.items())}
    rows["families"] = len(fam["families"])
    rows["appearances"] = len(cat["appearances"])
    rows["packs"] = len(cat["packs"])
    rows["failed ingests"] = len(fam.get("failed") or [])
    rows["source_root"] = cat["source_root"]
    out(rows, args)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("packs", help="source packs and their authors")
    sub.add_parser("approval", help="approval-class summary: what may be composed")

    p = sub.add_parser("families", help="families, with composable/reference counts")
    p.add_argument("--category"); p.add_argument("--pack"); p.add_argument("--author")

    p = sub.add_parser("family", help="one family in full, with every variant's class")
    p.add_argument("name")

    p = sub.add_parser("components", help="variants by approval class (composable by default)")
    p.add_argument("--class", dest="klass",
                   choices=["REUSABLE", "BASE-SPECIFIC", "REFERENCE-ONLY",
                            "reusable", "base-specific", "reference-only"])

    p = sub.add_parser("find", help="search appearances")
    p.add_argument("term", nargs="?", default="")
    p.add_argument("--category"); p.add_argument("--pack"); p.add_argument("--author")
    p.add_argument("--animated", action="store_true")
    p.add_argument("--color-masks", dest="color_masks", action="store_true")
    p.add_argument("--hide-hair", dest="hide_hair", action="store_true")

    p = sub.add_parser("show", help="one appearance: provenance, model, measured frames")
    p.add_argument("name"); p.add_argument("--limit", type=int, default=3)

    p = sub.add_parser("ramp", help="per-direction source palette, darkest-to-lightest data")
    p.add_argument("name")

    args = ap.parse_args(argv)
    cat, fam = load()
    return {"packs": cmd_packs, "families": cmd_families, "family": cmd_family,
            "components": cmd_components, "find": cmd_find, "show": cmd_show,
            "ramp": cmd_ramp, "approval": cmd_approval}[args.cmd](cat, fam, args) or 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
