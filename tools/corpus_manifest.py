#!/usr/bin/env python3
"""Hash-manifest the third-party art corpora that git deliberately does not carry.

The approved source packs are the construction authority, but they are other
authors' work: republishing them from this repo is not ours to do, and they are
most of the tree by size.  They are therefore synced out of band (rsync,
Syncthing, a copied drive) while THIS manifest is committed -- so any machine can
prove it holds the same corpus, and a silent divergence between the PC and the
Steam Deck cannot quietly change what the generator builds from.

    python3 tools/corpus_manifest.py write     # record the current corpora
    python3 tools/corpus_manifest.py verify    # compare this machine to the record

`verify` exits non-zero on any difference, so it can gate a session.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "source_catalog" / "corpus_manifest.json"

# Exactly the paths .gitignore excludes as third-party art.  Keep the two in step.
CORPORA = [
    "generator conent",                 # approved source packs -- the authority
    "references/benchmark",
    "references/ref_codex",
    "references/style-profiles",
    "references/lifestyle",
    "references/hoodie",
    "motif",
]
SKIP_SUFFIX = {".tmp", ".swp"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scan() -> dict:
    out = {}
    for rel in CORPORA:
        base = ROOT / rel
        if not base.is_dir():
            out[rel] = {"present": False}
            continue
        files = {}
        for f in sorted(base.rglob("*")):
            if not f.is_file() or f.suffix in SKIP_SUFFIX:
                continue
            files[str(f.relative_to(base))] = {"sha256": digest(f), "bytes": f.stat().st_size}
        out[rel] = {"present": True, "files": len(files),
                    "bytes": sum(v["bytes"] for v in files.values()), "hashes": files}
    return out


def cmd_write() -> int:
    data = scan()
    MANIFEST.write_text(json.dumps(
        {"note": "Third-party art corpora, synced out of band and not in git. "
                 "Regenerate with tools/corpus_manifest.py write.",
         "corpora": data}, indent=1))
    for rel, d in data.items():
        print(f"  {rel:<28} " + ("absent" if not d["present"]
              else f"{d['files']:>5} files  {d['bytes'] / 1e6:>8.1f} MB"))
    print(f"-> {MANIFEST}")
    return 0


def cmd_verify() -> int:
    if not MANIFEST.exists():
        sys.exit(f"no manifest at {MANIFEST} -- run `write` on the machine that has "
                 "the authoritative corpora first")
    want = json.loads(MANIFEST.read_text())["corpora"]
    have = scan()
    bad = 0
    for rel, w in want.items():
        h = have.get(rel, {"present": False})
        if not w.get("present"):
            continue
        if not h.get("present"):
            print(f"MISSING corpus: {rel}")
            bad += 1
            continue
        wf, hf = w["hashes"], h["hashes"]
        missing = sorted(set(wf) - set(hf))
        extra = sorted(set(hf) - set(wf))
        changed = sorted(k for k in set(wf) & set(hf) if wf[k]["sha256"] != hf[k]["sha256"])
        if missing or extra or changed:
            bad += 1
            print(f"{rel}: {len(missing)} missing, {len(extra)} extra, {len(changed)} changed")
            for k in (missing[:5] + changed[:5]):
                print(f"    {k}")
        else:
            print(f"{rel}: ok ({w['files']} files)")
    if bad:
        print(f"\n{bad} corpus/corpora differ from the manifest. The source packs are "
              "the construction authority -- reconcile before generating anything.")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("write", "verify"):
        print(__doc__)
        return 2
    return cmd_write() if argv[0] == "write" else cmd_verify()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
