"""Fashion Sense pack for the cap2 family proof batch."""
from __future__ import annotations
import json, os, shutil, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v5 import authored, pngio
from v5.source import roundtrip
from cap2_family import load_family, render, atlas, DIRS
from cap2_variants import VARIANTS
from build_authored_fs_pack import MODS

PACK = Path("test-packs/fashionsense/RNG-Cap2Family")
UNIQUE_ID = "RNGClothing.FashionSense.Cap2Family"

def main():
    install = "--install" in sys.argv
    base, frames, vocab, grammar, motifs, app = load_family()
    lib = authored.load()
    wear = roundtrip.source_blocks(app)      # the author's own wear properties
    if PACK.exists(): shutil.rmtree(PACK)
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)
    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Cap 2 Family",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Generated from 'Cap 2' by plurffle (More Accessories "
                       "and Stuff). Base art unmodified; palette and front "
                       "emblem are the only variables.",
        "UniqueID": UNIQUE_ID, "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"}}, indent=2))
    trace=[]
    for i,(label,pal_id,motif) in enumerate(VARIANTS,1):
        tint = (next(p for p in lib.palettes if p.id==pal_id).ramps["body"][3]
                if pal_id else None)
        f = render(base, vocab, grammar, motifs, motif, tint)
        folder = f"Cap{i:02d}" + label.replace("Cap2 ","").replace(" ","")
        d = PACK / "Hats" / folder
        d.mkdir(parents=True, exist_ok=True)
        pngio.write_rgba_png(d / "hat.png", atlas(f))
        doc = {"Name": label, "Format": "7.5.0",
               "Tags": ["RNG Clothing", "Cap 2 Family", "Art by plurffle",
                        pal_id or "source greyscale", motif or "no emblem"]}
        for j,dd in enumerate(DIRS):
            blk = {k:v for k,v in (wear.get(dd) or {}).items()
                   if k != "StartingPosition"}
            blk["DisableGrayscale"] = True     # colour is baked
            blk["StartingPosition"] = {"X":0,"Y":j*20}
            doc[f"{dd}Hat"] = blk
        (d / "hat.json").write_text(json.dumps(doc, indent=2))
        trace.append({"folder":folder,"label":label,"palette":pal_id,"emblem":motif})
        print(f"  {folder:22s} {label:24s} emblem={motif or '-':12s} pal={pal_id or 'source'}")
    (PACK/"trace.json").write_text(json.dumps(trace, indent=2))
    (PACK/"CREDITS.txt").write_text(
        "Base art: 'Cap 2' from More Accessories and Stuff, by plurffle.\n"
        "Silhouette, visor, crown, side profile and shading are the original "
        "author's work and are unmodified.\nPalette and front emblem are "
        "generated.\n")
    if install:
        dest = MODS / PACK.name
        if dest.exists(): shutil.rmtree(dest)
        shutil.copytree(PACK, dest); print("installed ->", dest)

if __name__ == "__main__":
    main()
