"""Milestone 2 in-game QC run for the Beret packs.

Run this with Stardew Valley open on a loaded save. It does the whole sequence
in the order the bridge requires, and refuses rather than capturing stale art:

  1. ping                        -- is the bridge answering at all?
  2. packs                       -- did SMAPI actually register both packs?
  3. refresh --pack --expect     -- reload FS and verify the count
  4. worn --pack                 -- front/right/back/left worn captures
  5. smapi-log --errors          -- anything Fashion Sense rejected silently

Both packs must have been installed to Mods/ BEFORE the game started. A pack
folder created after startup is listed by Fashion Sense but draws nothing, which
is indistinguishable from broken art (CLAUDE.md section 5). If step 2 says a pack
is missing, restart the game -- fs_reload cannot fix it.

    python3 tools/qc_beret_m2.py
"""
from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QC = os.path.join(ROOT, "tools", "qc.py")
PACKS = [("RNGClothing.FashionSense.BeretFamilyM1", 4),
         ("RNGClothing.FashionSense.BeretBatchM2", 48),
         ("RNGClothing.FashionSense.BeretCuteM3", 12)]


def run(*args, check=True):
    print(f"\n$ python3 tools/qc.py {' '.join(args)}")
    r = subprocess.run([sys.executable, QC, *args], cwd=ROOT,
                       capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    print(out.rstrip())
    if check and r.returncode != 0:
        print(f"\n-- stopped: `qc.py {args[0]}` exited {r.returncode}")
        sys.exit(r.returncode)
    return out


def main():
    run("ping")
    seen = run("packs")
    missing = [p for p, _ in PACKS if p not in seen]
    if missing:
        print(f"\n-- these packs are not registered: {missing}")
        print("   they were installed to Mods/ but the game has not been restarted "
              "since. Restart Stardew and run this again; fs_reload cannot "
              "register a pack that did not exist at startup.")
        sys.exit(2)
    for pack, expect in PACKS:
        run("refresh", "--pack", pack, "--expect", str(expect))
        run("worn", "--pack", pack)
    run("smapi-log", "--errors", check=False)
    print("\nCaptures are under qc_bridge/captures/. Measure seating with:")
    print("    python3 tools/qc.py compare <session-dir>")


if __name__ == "__main__":
    main()
