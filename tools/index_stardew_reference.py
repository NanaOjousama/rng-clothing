#!/usr/bin/env python3
"""Mirror the official Stardew/SMAPI technical references into references/stardew-official/.

Deliberately SCOPED.  The full Stardew wiki is thousands of gameplay pages;
mirroring it would bury the modding documentation it exists to surface.  Only
the Modding: namespace pages this project actually reasons about are fetched,
listed explicitly below so the scope is reviewable rather than implicit.

Three layers, in the order the technical authority hierarchy trusts them:

    wiki/       official Modding: pages, as wikitext (the wiki's own source)
    smapi/      SMAPI docs/ and the src/ subset that documents the API surface
    (assembly)  a metadata index of the INSTALLED game assembly, built
                separately by tools/AssemblyIndex -- see its README.  That
                index outranks any wiki page for a class or member question
                because it is read from the binary the game is actually running.

Re-run after a Stardew or SMAPI update.  Everything written here is
regenerable, and only wiki/ and smapi/ are committed: the assembly index is
gitignored because it is derived from game files.

    python3 tools/index_stardew_reference.py            # wiki + smapi
    python3 tools/index_stardew_reference.py --wiki     # wiki only
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "references" / "stardew-official"
API = "https://stardewvalleywiki.com/mediawiki/api.php"
UA = "RNG_clothing-reference-mirror/1.0 (local modding reference; contact via project)"

# The scope, explicit and reviewable.  Grouped by the question each answers.
PAGES = {
    "core": [
        "Modding:Index",
        "Modding:Modder Guide",
        "Modding:Modder Guide/Get Started",
        "Modding:Modder Guide/Game Fundamentals",
        "Modding:Modder Guide/Test and Troubleshoot",
        "Modding:Common tasks",
    ],
    "smapi-api": [
        "Modding:Modder Guide/APIs",
        "Modding:Modder Guide/APIs/Manifest",
        "Modding:Modder Guide/APIs/Events",
        "Modding:Modder Guide/APIs/Content",
        "Modding:Modder Guide/APIs/Config",
        "Modding:Modder Guide/APIs/Data",
        "Modding:Modder Guide/APIs/Translation",
        "Modding:Modder Guide/APIs/Multiplayer",
        "Modding:Modder Guide/APIs/Reflection",
        "Modding:Modder Guide/APIs/Harmony",
        "Modding:Modder Guide/APIs/Integrations",
        "Modding:Modder Guide/APIs/Logging",
        "Modding:Modder Guide/APIs/Utilities",
        "Modding:Modder Guide/APIs/Input",
    ],
    "content": [
        "Modding:Content Patcher",
        "Modding:Items",
        "Modding:Object data",
        "Modding:Hats",
        "Modding:Shirts",
        "Modding:Pants",
        "Modding:Boots",
        "Modding:Tailoring",
        "Modding:Recipe data",
        "Modding:Common data field types",
        "Modding:Migrate to Stardew Valley 1.6",
    ],
    "compatibility": [
        "Modding:Mod compatibility",
        "Modding:Player Guide/Key Bindings",
    ],
}

# SMAPI: docs/ is the technical documentation; this src/ subset is the API
# surface (events, interfaces, framework contracts) a mod is written against.
SMAPI_REPO = "https://github.com/Pathoschild/SMAPI.git"
SMAPI_SPARSE = ["docs", "src/SMAPI/Events", "src/SMAPI/Framework/Events", "src/SMAPI.Toolkit"]
SMAPI_ROOT_CS = "src/SMAPI"          # top-level interface files only, not the whole tree


def fetch(titles: list[str]) -> dict[str, str | None]:
    """Wikitext for each title.  None means the page does not exist."""
    out: dict[str, str | None] = {}
    for i in range(0, len(titles), 20):                  # the API caps a batch
        batch = titles[i:i + 20]
        q = urllib.parse.urlencode({
            "action": "query", "prop": "revisions", "rvprop": "content",
            "rvslots": "main", "format": "json", "redirects": "1",
            "titles": "|".join(batch)})
        req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as fh:
            data = json.load(fh)
        # normalized titles let a redirect answer under the name we asked for
        # normalization AND redirects both rename a title on the way back;
        # map either kind home so a redirect stub is stored under the real page
        alias = {n["to"]: n["from"] for n in data["query"].get("normalized", [])}
        alias.update({r["to"]: r["from"] for r in data["query"].get("redirects", [])})
        for page in data["query"]["pages"].values():
            title = alias.get(page.get("title"), page.get("title"))
            if "missing" in page:
                out[title] = None
                continue
            out[title] = page["revisions"][0]["slots"]["main"]["*"]
        time.sleep(1.0)                                  # be a polite client
    return out


def slug(title: str) -> str:
    return title.replace("Modding:", "").replace("/", "__").replace(" ", "-") + ".wiki"


def mirror_wiki() -> dict:
    got, missing = {}, []
    for group, titles in PAGES.items():
        (OUT / "wiki" / group).mkdir(parents=True, exist_ok=True)
        for title, text in fetch(titles).items():
            if text is None:
                missing.append(title)
                continue
            (OUT / "wiki" / group / slug(title)).write_text(text)
            got[title] = {"group": group, "file": f"wiki/{group}/{slug(title)}",
                          "bytes": len(text),
                          "url": "https://stardewvalleywiki.com/" +
                                 urllib.parse.quote(title.replace(" ", "_"))}
            print(f"  {group}/{slug(title)}  {len(text):,}B")
    for t in missing:
        print(f"  MISSING (title changed upstream?): {t}", file=sys.stderr)
    return {"pages": got, "missing": missing}


def mirror_smapi() -> dict:
    """Shallow sparse clone: the docs and the API-surface source, not all of SMAPI."""
    dest = OUT / "smapi"
    if (dest / ".git").exists():
        print("  updating existing clone")
        subprocess.run(["git", "-C", str(dest), "pull", "--depth", "1", "--ff-only"],
                       check=False, capture_output=True)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none",
                        "--sparse", SMAPI_REPO, str(dest)], check=True)
        subprocess.run(["git", "-C", str(dest), "sparse-checkout", "set",
                        *SMAPI_SPARSE], check=True)
    head = subprocess.run(["git", "-C", str(dest), "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    files = sum(1 for _ in dest.rglob("*") if _.is_file() and ".git" not in _.parts)
    return {"repo": SMAPI_REPO, "head": head, "sparse": SMAPI_SPARSE, "files": files}


def write_index(wiki: dict, smapi: dict | None) -> None:
    (OUT / "meta").mkdir(parents=True, exist_ok=True)
    (OUT / "meta" / "mirror.json").write_text(json.dumps(
        {"gathered": time.strftime("%Y-%m-%d"), "stardew": "1.6.15", "smapi": "4.5.2",
         "wiki": wiki, "smapi_clone": smapi}, indent=1))
    lines = [
        "# Stardew Valley / SMAPI — official technical reference (local mirror)",
        "",
        f"Gathered **{time.strftime('%Y-%m-%d')}** against the installed stack:",
        "**Stardew Valley 1.6.15 / SMAPI 4.5.2**. Regenerate with",
        "`python3 tools/index_stardew_reference.py`.",
        "",
        "Scoped on purpose: only the `Modding:` pages this project reasons about,",
        "plus SMAPI's docs and API-surface source. Not the whole wiki.",
        "",
        "## Layers, in technical-authority order",
        "",
        "| Layer | What it answers |",
        "|---|---|",
        "| `assembly/stardew_index.json` | classes/members of the **installed 1.6.15 assembly** (1093 types) — `IClickableMenu` controller snapping, `TailoringMenu` members. Outranks the wiki. Built by `tools/AssemblyIndex`; gitignored, because it derives from game files. |",
        "| `smapi/docs/`, `smapi/src/` | SMAPI's own documentation and API surface |",
        "| `wiki/` | official Modding: pages, as wikitext |",
        "",
        "## How to query",
        "",
        "```",
        "rg -i 'IClickableMenu' references/stardew-official/",
        "jq '.types[]|select(.name|test(\"Tailor\"))' \\",
        "   references/stardew-official/assembly/stardew_index.json",
        "```",
        "",
        "## Wiki pages mirrored",
        "",
    ]
    for group in PAGES:
        rows = {t: v for t, v in wiki["pages"].items() if v["group"] == group}
        if not rows:
            continue
        lines += [f"### {group}", ""]
        lines += [f"- [{t}]({v['url']}) → `{v['file']}`" for t, v in sorted(rows.items())]
        lines += [""]
    if wiki["missing"]:
        lines += ["### Not found upstream (title may have changed)", ""]
        lines += [f"- {t}" for t in wiki["missing"]] + [""]
    if smapi:
        lines += ["## SMAPI clone", "",
                  f"- `{smapi['repo']}` @ `{smapi['head']}`",
                  f"- sparse paths: {', '.join('`%s`' % p for p in smapi['sparse'])}",
                  f"- {smapi['files']} files", ""]
    (OUT / "INDEX.md").write_text("\n".join(lines))


def main(argv: list[str]) -> int:
    # Parse properly.  A bare `in argv` check meant `--help` fell through and
    # performed a full network re-mirror, which overwrote a hand-corrected
    # INDEX.md.  Anything that touches the network must be asked for explicitly.
    import argparse
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wiki", action="store_true", help="wiki pages only, skip the SMAPI clone")
    ap.add_argument("--smapi", action="store_true", help="SMAPI clone only, skip the wiki")
    args = ap.parse_args(argv)

    OUT.mkdir(parents=True, exist_ok=True)
    wiki = {"pages": {}, "missing": []}
    if not args.smapi:
        print("wiki:")
        wiki = mirror_wiki()
    smapi = None
    if not args.wiki:
        print("smapi:")
        try:
            smapi = mirror_smapi()
        except subprocess.CalledProcessError as exc:
            print(f"  clone failed: {exc}", file=sys.stderr)
    if args.smapi:
        # keep the existing page list rather than blanking it out of the index
        prev = OUT / "meta" / "mirror.json"
        if prev.exists():
            wiki = json.loads(prev.read_text()).get("wiki", wiki)
    write_index(wiki, smapi)
    print(f"\n{len(wiki['pages'])} wiki pages, "
          f"{smapi['files'] if smapi else 0} SMAPI files -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
