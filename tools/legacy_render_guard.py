"""Legacy render guard: every legacy authored render path, hashed.

Source-Backed V2 is built BESIDE the legacy path. This is what makes "legacy
output is unchanged" a measurement: 1996 renders -- every legacy base x palette
x treatment, slot-wide and family compose rolls, the cute_beret profile, and
the build_tier matrix -- hashed with their chosen base/palette/treatment/decals.

The fixture was captured before any V2 code existed.

    python3 tools/legacy_render_guard.py            # check against the fixture
    python3 tools/legacy_render_guard.py --write    # re-capture (only on purpose)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from v5 import authored as A  # noqa: E402

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "legacy_render_guard.json")


def _h(dirs):
    h = hashlib.sha256()
    for v in A.ATLAS_ORDER:
        for r in dirs[v]:
            for p in r:
                h.update(bytes(p))
    return h.hexdigest()


def _g(g):
    return (_h(g.directions) + ":" + g.base.name + ":" + g.palette.id + ":" + g.treatment + ":"
            + ",".join(d.name for d in g.decals))


def capture():
    lib = A.load()
    out = {}

    def attempt(key, fn):
        try:
            out[key] = fn()
        except ValueError as e:
            out[key] = "ERR:" + str(e)

    for b in lib.bases:
        for p in lib.palettes:
            attempt(f"render/{b.name}/{p.id}/none", lambda: _h(A._render(b, (), p, lib.tone_for(b))[0]))
            for t in sorted(lib.treatments):
                attempt(f"render/{b.name}/{p.id}/{t}",
                        lambda: _h(A._render(b, (), p, lib.tone_for(b), lib.treatment(t))[0]))
    for s in range(40):
        attempt(f"compose/HEAD/{s}", lambda: _g(A.compose(s, "HEAD", lib)))
    tiers = lib.tier_order()
    for s in range(12):
        for t in tiers:
            attempt(f"compose/beret/{t}/{s}", lambda: _g(A.compose(s, lib=lib, family="beret", quality_tier=t)))
            attempt(f"profile/cute/{t}/{s}",
                    lambda: _g(A.compose(s, lib=lib, family="beret", quality_tier=t, profile="cute_beret")))
    for shape in ("beret_01", "beret_02", "beret_03"):
        for p in lib.palettes:
            for t in tiers:
                attempt(f"tier/{shape}/{p.id}/{t}", lambda: _g(A.build_tier("beret", shape, p.id, t, 8, lib)))
    return out


def check():
    with open(FIXTURE) as fh:
        want = json.load(fh)
    got = capture()
    moved = sorted(k for k in want if got.get(k) != want[k])
    new = sorted(k for k in got if k not in want)
    return want, got, moved, new


def main():
    if "--write" in sys.argv:
        out = capture()
        with open(FIXTURE, "w") as fh:
            json.dump(out, fh, indent=0, sort_keys=True)
        print(f"wrote {len(out)} hashes -> {FIXTURE}")
        return 0
    want, got, moved, new = check()
    print(f"{len(want)} legacy renders checked; {len(moved)} moved; {len(new)} not in fixture")
    for k in moved[:20]:
        print(f"  MOVED {k}")
    return 1 if moved or new else 0


if __name__ == "__main__":
    sys.exit(main())
