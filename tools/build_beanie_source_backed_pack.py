"""Build neutral Source-Backed V1 proof appearances for the two Beanie constructions."""
from __future__ import annotations
import json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v5 import source_backed as sbm
from v5.pngio import write_rgba_png

PACK = ROOT / "test-packs/fashionsense/RNG-Beanie-SourceBacked-V1"
UNIQUE_ID = "RNGClothing.FashionSense.BeanieSourceBackedV1"
MODS = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods")
ITEMS = (
    ("!!! NEW BEANIE V1 - CUFFED !!!", "beanie_cuffed"),
    ("!!! NEW BEANIE V1 - SLOUCH !!!", "beanie_slouch"),
)

def sync_install(pack_dir: Path, dest: Path):
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "Hats").mkdir(exist_ok=True)
    wanted = {p.name for p in (pack_dir / "Hats").iterdir()}
    for child in (dest / "Hats").iterdir():
        if child.name not in wanted:
            shutil.rmtree(child)
    for child in (pack_dir / "Hats").iterdir():
        target = dest / "Hats" / child.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(child, target)
    for name in ("manifest.json", "TRACEABILITY.json"):
        shutil.copyfile(pack_dir / name, dest / name)

def main():
    if (PACK / "Hats").exists():
        shutil.rmtree(PACK / "Hats")
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)
    (PACK / "manifest.json").write_text(json.dumps({
        "Name":"!!! NEW BEANIE V1 TEST !!!",
        "Author":"RNG Clothing","Version":"0.1.0",
        "Description":"NEW BEANIE V1 TEST - Cuffed and Slouch construction proofs.",
        "UniqueID":UNIQUE_ID,"UpdateKeys":[],
        "ContentPackFor":{"UniqueID":"PeacefulEnd.FashionSense","MinimumVersion":"7.5.0"}
    }, indent=2)+"\n")
    trace=[]
    for appearance,name in ITEMS:
        b=sbm.load_one(name)
        r=sbm.render(b)
        assert not r.dropped
        out=PACK/"Hats"/appearance
        out.mkdir(parents=True, exist_ok=True)
        write_rgba_png(out/"hat.png", sbm.sheet(r))
        tags=["NEW","BEANIE V1","TEST NOW","RNG Clothing","Beanie",name,
              "CUFFED" if name=="beanie_cuffed" else "SLOUCH",
              "neutral",f"{b.classification}-ONLY source"]
        (out/"hat.json").write_text(json.dumps(sbm.hat_json(r,appearance,tags),indent=2)+"\n")
        trace.append({
            "appearance":appearance,"base":name,"source":b.source_png,
            "source_md5":b.source_md5,"size":list(b.size),"views":list(b.views),
            "mirrored":b.mirrored,
            "placement":{v:b.placement(v) for v in sbm.MODEL_OF},
            "zones":b.semantic.zones,"dropped":list(r.dropped)
        })
        print(appearance,name,b.size,b.views,b.mirrored,"dropped",r.dropped)
    (PACK/"TRACEABILITY.json").write_text(json.dumps(trace,indent=2)+"\n")
    if "--install" in sys.argv:
        sync_install(PACK, MODS/PACK.name)
        print("installed ->",MODS/PACK.name)
    print("wrote",PACK)
if __name__=="__main__":
    main()
