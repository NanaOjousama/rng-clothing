#!/usr/bin/env python3
from pathlib import Path
import json, sys
import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from generator.photo_tailor_port import recolor_four_facing
from run_experiment import contact, wear_sheet, rows, image, largest_share, sha, PALETTE

VIEWS = ("front", "right", "back", "left")
SELECT = {"front": 0, "right": 1, "back": 3, "left": 4}


def split_six(im):
    tw, th = im.width // 2, im.height // 3
    return [im.crop(((i % 2)*tw, (i // 2)*th, (i % 2 + 1)*tw, (i // 2 + 1)*th)) for i in range(6)]


def largest_component(binary):
    n, labels, stats, _ = cv2.connectedComponentsWithStats(binary.astype(np.uint8), 8)
    if n <= 1:
        return binary.astype(bool)
    idx = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return labels == idx


def silhouette(tile):
    arr = np.asarray(tile.convert("RGB"), dtype=np.int16)
    corners = np.array([arr[2,2], arr[2,-3], arr[-3,2], arr[-3,-3]])
    bg = np.median(corners, axis=0)
    dist = np.sqrt(np.sum((arr - bg) ** 2, axis=2))
    raw = dist > 24
    raw = cv2.morphologyEx(raw.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3,3),np.uint8), iterations=1)
    return largest_component(raw)


def reduce_mask(mask, max_w=24, max_h=18):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return np.zeros((26,26), dtype=bool)
    crop = mask[ys.min():ys.max()+1, xs.min():xs.max()+1]
    h, w = crop.shape
    scale = min(max_w / w, max_h / h)
    nw, nh = max(1, round(w*scale)), max(1, round(h*scale))
    reduced = Image.fromarray((crop*255).astype(np.uint8)).resize((nw,nh), Image.Resampling.BOX)
    small = np.asarray(reduced) >= 72
    out = np.zeros((26,26), dtype=bool)
    ox, oy = (26-nw)//2, min(25-nh, 3)
    out[oy:oy+nh, ox:ox+nw] = small
    return out


def frame_from_mask(mask):
    im = Image.new("RGBA", (26,26), (0,0,0,0))
    for y in range(26):
        for x in range(26):
            if not mask[y,x]: continue
            edge = any(nx<0 or nx>=26 or ny<0 or ny>=26 or not mask[ny,nx]
                       for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
            im.putpixel((x,y), (55,55,58,255) if edge else (175,180,184,255))
    return im


def raw_contact(tiles, path):
    thumb = 220
    out = Image.new("RGB", (3*thumb, 2*thumb + 30), "white")
    d = ImageDraw.Draw(out)
    labels = ["+30", "+90", "+150", "+210", "+270", "+330"]
    for i, tile in enumerate(tiles):
        im = tile.convert("RGB").resize((thumb,thumb), Image.Resampling.LANCZOS)
        x, y = (i%3)*thumb, 24+(i//3)*thumb
        out.paste(im,(x,y)); d.text((x+5,5 if i<3 else 5+thumb), labels[i], fill="black")
    out.save(path)


def main(raw_path):
    raw_path = Path(raw_path)
    tag = ''.join(str(SELECT[v]) for v in VIEWS)
    outdir = raw_path.parent / f"construction_from_zero123_{tag}"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir/"template_frames").mkdir(exist_ok=True)
    raw = Image.open(raw_path).convert("RGB")
    tiles = split_six(raw)
    raw_contact(tiles, outdir/"00_multiview_raw_contact.png")
    geom = {}
    for v, idx in SELECT.items():
        geom[v] = frame_from_mask(reduce_mask(silhouette(tiles[idx])))
    contact(geom, outdir/"01_ai_construction_geometry.png", "ZERO123 SINGLE-REF -> 26px CONSTRUCTION GEOMETRY")
    styled_rows = recolor_four_facing({v:rows(geom[v]) for v in VIEWS}, pattern="solid", palette=PALETTE)
    styled = {v:image(styled_rows[v]) for v in VIEWS}
    for v in VIEWS:
        styled[v].save(outdir/"template_frames"/f"{v}.png")
    contact(styled, outdir/"02_photo_tailor_normalized.png", "PHOTO TAILOR NORMALIZED / AI GEOMETRY LOCKED")
    wear_sheet(styled, outdir/"03_stardew_fit_preview.png")
    qc = {}
    for v in VIEWS:
        a = styled[v].getchannel("A"); box = a.getbbox()
        opaque = sum(1 for p in a.getdata() if p > 15)
        qc[v] = {"bbox":list(box) if box else None, "opaquePixels":opaque,
                 "largestComponentShare":round(largest_share(styled[v]),4), "sourceTile":SELECT[v]}
    qc["technicalPass"] = all(qc[v]["opaquePixels"] >= 40 and qc[v]["largestComponentShare"] >= .90 for v in VIEWS)
    contract = {
        "schema":"experimental-ai-construction-template/v1", "family":"trucker_cap",
        "status":"EXPERIMENTAL_REVIEW_REQUIRED", "frameSize":[26,26],
        "viewProvider":{"model":"sudo-ai/zero123plus-v1.2","inputPolicy":"single reference only",
                        "fixedAzimuths":[30,90,150,210,270,330],"selectedTiles":SELECT},
        "pipeline":["single reference","Zero123++ multiview","foreground silhouette recovery",
                    "26px area reduction","Photo Tailor normalization","Stardew wear-fit preview"],
        "frames":{v:{"path":f"template_frames/{v}.png","sha256":sha(outdir/"template_frames"/f"{v}.png")} for v in VIEWS},
        "qc":qc,
        "promotionRule":"Never auto-promote; visual geometry and in-game approval required."
    }
    (outdir/"construction_template.json").write_text(json.dumps(contract,indent=2)+"\n")
    (outdir/"RESULT.txt").write_text(("TECHNICAL PASS\n" if qc["technicalPass"] else "TECHNICAL FAIL\n")+
        "Technical pass only means valid connected 26px geometry, not visual approval.\n")
    print(json.dumps(qc,indent=2)); print("OUTPUT",outdir)


if __name__ == "__main__":
    if len(sys.argv) not in (2,3):
        raise SystemExit("usage: postprocess_zero123.py RAW_MULTIVIEW.png [front,right,back,left tile indexes]")
    if len(sys.argv) == 3:
        vals = [int(x) for x in sys.argv[2].split(',')]
        if len(vals) != 4 or any(x < 0 or x > 5 for x in vals):
            raise SystemExit("mapping must contain four tile indexes from 0..5")
        SELECT.update(dict(zip(VIEWS, vals)))
    main(sys.argv[1])
