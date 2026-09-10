"""The controlled proof batch for the cap2 family."""
from __future__ import annotations

import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from v5 import authored, pngio
from cap2_family import load_family, render, DIRS

OUT = "output/cap2_family"
BG=(26,28,32,255); INK=(233,233,228,255); DIM=(122,126,132,255)
CH1=(48,52,58,255); CH2=(38,41,46,255)

VARIANTS = [
    ("Cap2 Classic",   None,                     "bar"),
    ("Cap2 Navy Star",  "EVERYDAY_STONE_BLUE",   "star"),
    ("Cap2 Ochre Shield","AUTUMN_OCHRE_PLUM",    "shield"),
    ("Cap2 Seafoam Ball","COASTAL_SEAFOAM_CORAL","ball"),
    ("Cap2 Sage Heart",  "SPRING_SAGE_PETAL",    "heart"),
    ("Cap2 Navy Letter", "EVERYDAY_STONE_BLUE",  "letter_a"),
    ("Cap2 Ochre Bar",   "AUTUMN_OCHRE_PLUM",    "bar"),
    ("Cap2 Seafoam Plain","COASTAL_SEAFOAM_CORAL", None),
]

def main():
    base, frames, vocab, grammar, motifs, app = load_family()
    lib = authored.load()
    def checker(w,h,s=2):
        return [[(CH1 if ((x//s+y//s)%2) else CH2) for x in range(w)] for y in range(h)]
    def tile(f,sc,l,sub="",c=INK):
        h,w=len(f),len(f[0]); bg=checker(w,h)
        comp=[[f[y][x] if f[y][x][3] else bg[y][x] for x in range(w)] for y in range(h)]
        art=pngio.nearest_scale(comp,sc)
        img=pngio.blank_image(max(len(art[0]),104),len(art)+22,BG); pngio.blit(img,art,0,0)
        pngio.draw_text(img,l,1,len(art)+3,color=c)
        if sub: pngio.draw_text(img,sub,1,len(art)+13,color=DIM)
        return img
    def title(t,w=960,c=INK):
        im=pngio.blank_image(w,12,BG); pngio.draw_text(im,t,0,1,color=c); return im
    def rowof(ts,gap=8):
        h=max(len(t) for t in ts); w=sum(len(t[0]) for t in ts)+gap*(len(ts)-1)
        r=pngio.blank_image(w,h,BG); x=0
        for t in ts: pngio.blit(r,t,x,0); x+=len(t[0])+gap
        return r
    rows=[title("CAP 2 FAMILY  -  base 'Cap 2' by plurffle (More Accessories and Stuff), locked")]
    rows.append(title("motif set at 8x  (4x3 zone, base vocabulary, front only)", c=DIM))
    ts=[]
    for name in [m for m in motifs["motifs"]
                 if motifs["motifs"][m].get("status","").startswith("APPROVED")]:
        f=render(base, vocab, grammar, motifs, name, None)
        crop=[[f["Front"][y][x] for x in range(6,14)] for y in range(7,14)]
        ts.append(tile(crop,10,name,motifs["motifs"][name]["category"][:18]))
    rows.append(rowof(ts))
    rows.append(title("variants at GAMEPLAY SCALE (4x)", c=DIM))
    ts=[]
    for label,pal_id,motif in VARIANTS:
        tint=None
        if pal_id:
            tint=next(p for p in lib.palettes if p.id==pal_id).ramps["body"][3]
        f=render(base, vocab, grammar, motifs, motif, tint)
        ts.append(tile(f["Front"],4,label.replace("Cap2 ",""), motif or "no emblem"))
    rows.append(rowof(ts))
    for label,pal_id,motif in VARIANTS:
        tint=None
        if pal_id:
            tint=next(p for p in lib.palettes if p.id==pal_id).ramps["body"][3]
        f=render(base, vocab, grammar, motifs, motif, tint)
        rows.append(title(f"   {label}   emblem: {motif or 'none'}", c=DIM))
        rows.append(rowof([tile(f[d],6,d) for d in DIRS]))
    pad=12;gap=10
    W=max(len(r[0]) for r in rows)+pad*2; H=sum(len(r) for r in rows)+gap*(len(rows)-1)+pad*2
    sh=pngio.blank_image(W,H,BG); y=pad
    for r in rows: pngio.blit(sh,r,pad,y); y+=len(r)+gap
    os.makedirs(OUT,exist_ok=True)
    pngio.write_rgba_png(f"{OUT}/variants.png",sh)
    print(f"wrote {OUT}/variants.png  ({len(VARIANTS)} variants)")

if __name__ == "__main__":
    main()
