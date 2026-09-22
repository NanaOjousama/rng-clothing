#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sf_pipeline.model import PromotionStatus
from sf_pipeline.promotion import can_transition

REGISTRY = ROOT / "sf_pipeline/registry.json"


def load_registry() -> dict:
    if not REGISTRY.exists():
        return {"schema": "rng-clothing-sf-registry/v1", "assets": {}}
    return json.loads(REGISTRY.read_text())


def save_registry(data: dict) -> None:
    REGISTRY.write_text(json.dumps(data, indent=2) + "\n")


def cmd_show(args):
    data = load_registry()
    assets = data["assets"]
    if args.id:
        print(json.dumps(assets.get(args.id, {}), indent=2))
        return
    for key in sorted(assets):
        print(key, assets[key].get("status", ""))


def cmd_register(args):
    data = load_registry()
    assets = data["assets"]
    if args.id in assets:
        raise SystemExit(f"{args.id} already exists")
    assets[args.id] = {
        "status": PromotionStatus.GENERATED_UNREVIEWED.value,
        "candidateManifest": args.candidate_manifest,
        "directionManifest": "",
        "candidateMechanicalPassed": False,
        "directionMechanicalPassed": False,
        "humanArtApproved": False,
        "esmWearApproved": False,
        "history": [{"status": PromotionStatus.GENERATED_UNREVIEWED.value, "note": args.note}],
    }
    save_registry(data)
    print("registered", args.id)


def cmd_transition(args):
    data = load_registry()
    asset = data["assets"].get(args.id)
    if asset is None:
        raise SystemExit(f"Unknown asset {args.id}")

    current = PromotionStatus(asset["status"])
    new = PromotionStatus(args.status)
    if not can_transition(current, new):
        raise SystemExit(f"Invalid transition {current.value} -> {new.value}")

    if new == PromotionStatus.PRODUCTION_APPROVED:
        if not asset.get("candidateMechanicalPassed"):
            raise SystemExit("candidate mechanical QC is required")
        if not asset.get("directionMechanicalPassed"):
            raise SystemExit("direction mechanical QC is required")
        if not asset.get("humanArtApproved"):
            raise SystemExit("human art approval is required")
        if not asset.get("esmWearApproved"):
            raise SystemExit("ESM wear approval is required")
        if not asset.get("directionManifest"):
            raise SystemExit("direction manifest is required")

    asset["status"] = new.value
    asset.setdefault("history", []).append({"status": new.value, "note": args.note})
    save_registry(data)
    print(args.id, "=>", new.value)


def cmd_mark(args):
    data = load_registry()
    asset = data["assets"].get(args.id)
    if asset is None:
        raise SystemExit(f"Unknown asset {args.id}")
    if args.candidate_mechanical is not None:
        asset["candidateMechanicalPassed"] = args.candidate_mechanical
    if args.direction_mechanical is not None:
        asset["directionMechanicalPassed"] = args.direction_mechanical
    if args.art is not None:
        asset["humanArtApproved"] = args.art
    if args.wear is not None:
        asset["esmWearApproved"] = args.wear
    if args.direction_manifest:
        asset["directionManifest"] = args.direction_manifest
    save_registry(data)
    print(json.dumps(asset, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("show")
    p.add_argument("id", nargs="?")
    p.set_defaults(fn=cmd_show)

    p = sub.add_parser("register")
    p.add_argument("id")
    p.add_argument("candidate_manifest")
    p.add_argument("--note", default="")
    p.set_defaults(fn=cmd_register)

    p = sub.add_parser("transition")
    p.add_argument("id")
    p.add_argument("status", choices=[x.value for x in PromotionStatus])
    p.add_argument("--note", default="")
    p.set_defaults(fn=cmd_transition)

    p = sub.add_parser("mark")
    p.add_argument("id")
    p.add_argument("--candidate-mechanical", type=lambda s: s.lower() == "true")
    p.add_argument("--direction-mechanical", type=lambda s: s.lower() == "true")
    p.add_argument("--art", type=lambda s: s.lower() == "true")
    p.add_argument("--wear", type=lambda s: s.lower() == "true")
    p.add_argument("--direction-manifest", default="")
    p.set_defaults(fn=cmd_mark)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
