#!/usr/bin/env python3
"""Capture all four directions for each HairPolicyQC hat at multiple hairstyles.

Requires the live in-game QC bridge; restores initial hairstyle, facing, and
Fashion Sense hat in a finally block. Unique hairstyle labels prevent overwrites.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qc

PACK = "PackStudy.HairPolicyQC"

def run(hairs: list[int]) -> None:
    session = qc.current_session()
    initial = qc.require("get_render_state")["state"]
    farmer = initial["farmer"]
    initial_hair = farmer["hairstyle"]
    initial_dir = farmer["facing_name"]
    original_hat_id = (initial.get("hat") or {}).get("fashion_sense_id")
    if original_hat_id == "None":
        original_hat_id = None
    print("Original hair:", initial_hair, "hat:", original_hat_id, "facing:", initial_dir, flush=True)
    out = Path(qc.CAPTURES) / session / "hair_policy_capture_index.json"
    if out.exists():
        old = json.loads(out.read_text())
        capture_index = old.get("captures", [])
    else:
        capture_index = []
    try:
        qc.refresh(pack=PACK, expect=6, pack_dir=qc.pack_dir_for(PACK), session=session)
        hats = [r for r in qc.require("list_hats")["hats"] if r.get("pack_id") == PACK]
        if len(hats) != 6:
            raise RuntimeError(f"Expected exactly 6 test hats, got {len(hats)}")
        for hair in hairs:
            print(f"\n=== Hairstyle {hair} ===", flush=True)
            qc.require("set_scene", hairstyle=hair, direction="front", freeze="true")
            for j, hat in enumerate(hats, start=1):
                label = f"hair{hair:03d}_{hat['folder']}"
                print(f" [{j}/6] {label}", flush=True)
                qc.require("equip_hat", id=hat["appearance_id"])
                answer = qc.require("capture_all_directions", label=label)
                capture_index.append({"hairstyle": hair, "name": hat["appearance_id"], "folder": label,
                                      "capture_dir": answer.get("directory")})
        out.write_text(json.dumps({"pack": PACK, "initial_hair": initial_hair,
                                   "initial_hat": original_hat_id, "captures": capture_index}, indent=2) + "\n")
        print(f"\nCOMPLETE {len(capture_index)} sets. Index: {out}", flush=True)
    finally:
        try:
            qc.require("set_scene", hairstyle=initial_hair, direction=initial_dir, freeze="false")
            if original_hat_id:
                qc.require("equip_hat", id=original_hat_id)
            else:
                qc.require("clear_hat")
            print("Restored original hair, direction and Fashion Sense hat", flush=True)
        except Exception as exc:
            print("WARNING: could not fully restore original farmer appearance:", exc, flush=True)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--hair", type=int, nargs="+", default=[0, 16, 38])
    opts = p.parse_args()
    run(opts.hair)
