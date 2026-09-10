"""PART 6 — capture the two calibration groups through the real renderer.

  A  a representative vanilla sample, chosen by MEASURED geometry (brimmed /
     brimless / tall / short / wide / narrow / caps / rounded / pointed / soft)
     rather than by name, plus the six reconstruction targets.
  B  the four hats the user picked as visually good, wrapped QC-only.

Same farmer, same hairstyle, same location, same idle frame, same zoom as the
V5 run, so the three groups are directly comparable.
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, "tools")
sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing")
from qc import require, send                                       # noqa: E402

HAIRSTYLE = 38
REFERENCE = ["RefBoysCap", "RefSweetGent", "RefHyoung11", "RefKookoroo8"]
REF_PACK = "RNGClothing.QCOnly.ReferenceHats"


def capture(label: str) -> str | None:
    out = send("capture_all_directions", label=label, timeout=120)
    if not out.get("ok"):
        print(f"    FAILED: {out.get('message')}")
        return None
    return out.get("directory")


def main() -> int:
    sel = json.load(open("/home/deck/.claude/jobs/426d8000/tmp/vanilla_sel.json"))
    require("set_scene", hairstyle=HAIRSTYLE, direction="front", freeze="true")

    print(f"=== GROUP A — {len(sel)} vanilla hats")
    for n, (hat_id, group) in enumerate(sorted(sel.items(), key=lambda kv: int(kv[0])), 1):
        r = send("equip_vanilla_hat", id=hat_id)
        if not r.get("ok"):
            print(f"[{n}] vanilla {hat_id}: {r.get('message')}")
            continue
        label = f"VAN{int(hat_id):03d}_{group.replace('/', '_')}"
        print(f"[{n}/{len(sel)}] vanilla {hat_id} {group}")
        capture(label)

    require("clear_hat")
    print(f"\n=== GROUP B — {len(REFERENCE)} reference hats")
    for n, name in enumerate(REFERENCE, 1):
        r = send("equip_hat", id=f"{REF_PACK}/Hat/{name}")
        if not r.get("ok"):
            print(f"[{n}] {name}: {r.get('message')}")
            continue
        print(f"[{n}/{len(REFERENCE)}] {name}")
        capture(f"REF_{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
