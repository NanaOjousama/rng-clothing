#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from sf_pipeline.client import SpriteFusionClient, data_url

def read_key(args) -> str:
    if args.key_file:
        return Path(args.key_file).read_text().strip()
    key=os.environ.get("SPRITE_FUSION_API_KEY","").strip()
    if not key:
        raise SystemExit("Set SPRITE_FUSION_API_KEY or pass --key-file.")
    return key

def prepare_body(spec: dict) -> dict:
    operation=spec["operation"]
    body={"operation":operation}
    if "size" in spec:
        body["size"]=spec["size"]
    if operation in ("style-reference","edit"):
        body["prompt"]=spec.get("prompt","")
        inputs=[]
        for ref in spec.get("referenceRoles",[]):
            path=ROOT/ref["localPath"]
            inputs.append({"data_url":data_url(path)})
        if operation=="edit" and not inputs:
            raise SystemExit("edit requires at least one input")
        body["inputs"]=inputs
    elif operation=="direction-set":
        source=spec.get("sourceAssetId","")
        if not source:
            raise SystemExit("direction-set requires sourceAssetId")
        body["inputs"]=[{"asset_id":source}]
    else:
        raise SystemExit(f"Unsupported operation {operation}")
    return body


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("output_dir")
    ap.add_argument("--key-file")
    args=ap.parse_args()

    spec=json.loads(Path(args.spec).read_text())
    out=Path(args.output_dir)
    out.mkdir(parents=True,exist_ok=True)
    client=SpriteFusionClient(read_key(args))
    body=prepare_body(spec)
    (out/"request.json").write_text(json.dumps(spec,indent=2)+"\n")
    events=client.generate(body)
    (out/"events.json").write_text(json.dumps(events,indent=2)+"\n")

    outputs=[]
    for e in events:
        if e.get("type")!="output":
            continue
        asset=e.get("asset",{})
        idx=e.get("index",len(outputs))
        direction=asset.get("action",{}).get("direction")
        stem=direction or f"output_{idx:02d}"
        dest=out/f"{stem}.png"
        client.download(asset["assetUrl"],dest)
        outputs.append({
            "index":idx,
            "direction":direction,
            "asset_id":asset.get("id",""),
            "width":asset.get("width"),
            "height":asset.get("height"),
            "local_path":str(dest.relative_to(ROOT) if dest.is_relative_to(ROOT) else dest),
        })

    (out/"outputs.json").write_text(json.dumps(outputs,indent=2)+"\n")
    print("downloaded",len(outputs),"outputs to",out)


if __name__=="__main__":
    main()
