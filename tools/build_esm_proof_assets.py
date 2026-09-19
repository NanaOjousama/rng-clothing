#!/usr/bin/env python3
"""Build deterministic Enhanced Sewing Machine proof assets.

These are original debug sprites created from simple geometric rules. They are
not derived from Fashion Sense, Stardew art, or third-party packs.
"""
from pathlib import Path
import struct, zlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "mods" / "EnhancedSewingMachine" / "assets"

def write_png(path, w, h, pixels):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw.extend(pixels[y*w+x])
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind+data) & 0xffffffff)
    payload = b"\x89PNG\r\n\x1a\n"
    payload += chunk(b"IHDR", struct.pack(">IIBBBBB", w,h,8,6,0,0,0))
    payload += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    payload += chunk(b"IEND", b"")
    path.write_bytes(payload)

TRANSPARENT=(0,0,0,0)
OUTLINE=(54,42,38,255)
SHADOW=(114,82,58,255)
MID=(174,128,82,255)
LIGHT=(224,176,112,255)
ACCENT=(220,90,62,255)

def canvas(w,h):
    return [TRANSPARENT]*(w*h)

def px(img,w,x,y,c):
    if 0 <= x < w and 0 <= y < len(img)//w:
        img[y*w+x]=c

def fill_rect(img,w,x0,y0,x1,y1,c):
    for y in range(y0,y1+1):
        for x in range(x0,x1+1):
            px(img,w,x,y,c)

def draw_front(img,w,oy):
    # low rounded crown, bottom contact around y=25
    for y,x0,x1 in [(9,11,20),(10,8,23),(11,6,25),(12,5,26),(13,4,27),
                     (14,4,27),(15,4,27),(16,4,27),(17,4,27),(18,5,26),
                     (19,5,26),(20,6,25),(21,7,24),(22,8,23)]:
        fill_rect(img,w,x0,oy+y,x1,oy+y, OUTLINE)
    for y in range(11,22):
        inset = 1 if y < 20 else 2
        fill_rect(img,w,6+inset,oy+y,25-inset,oy+y,MID if y < 17 else SHADOW)
    fill_rect(img,w,10,oy+12,21,oy+14,LIGHT)
    # brim
    fill_rect(img,w,7,oy+23,24,oy+23,OUTLINE)
    fill_rect(img,w,5,oy+24,26,oy+25,OUTLINE)
    fill_rect(img,w,7,oy+24,24,oy+24,MID)
    fill_rect(img,w,10,oy+15,11,oy+16,ACCENT)

def draw_right(img,w,oy):
    for y,x0,x1 in [(10,8,20),(11,6,22),(12,5,23),(13,4,24),(14,4,24),
                     (15,4,24),(16,4,24),(17,4,24),(18,5,23),(19,5,23),
                     (20,6,22),(21,7,21),(22,8,20)]:
        fill_rect(img,w,x0,oy+y,x1,oy+y,OUTLINE)
    for y in range(12,22):
        fill_rect(img,w,6,oy+y,22,oy+y,MID if y < 17 else SHADOW)
    fill_rect(img,w,8,oy+12,18,oy+14,LIGHT)
    # right-facing brim
    fill_rect(img,w,19,oy+22,27,oy+22,OUTLINE)
    fill_rect(img,w,19,oy+23,29,oy+24,OUTLINE)
    fill_rect(img,w,20,oy+23,27,oy+23,MID)
    px(img,w,12,oy+15,ACCENT)

def draw_back(img,w,oy):
    for y,x0,x1 in [(9,11,20),(10,8,23),(11,6,25),(12,5,26),(13,4,27),
                     (14,4,27),(15,4,27),(16,4,27),(17,4,27),(18,5,26),
                     (19,5,26),(20,6,25),(21,7,24),(22,8,23),(23,9,22),
                     (24,10,21),(25,11,20)]:
        fill_rect(img,w,x0,oy+y,x1,oy+y,OUTLINE)
    for y in range(11,24):
        fill_rect(img,w,7,oy+y,24,oy+y,MID if y < 17 else SHADOW)
    fill_rect(img,w,10,oy+12,21,oy+14,LIGHT)
    # center seam and closure cue
    for y in range(12,23):
        px(img,w,16,oy+y,OUTLINE)
    fill_rect(img,w,13,oy+22,19,oy+23,OUTLINE)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    carrier=canvas(20,80)
    write_png(OUT/"carrier_hat_20x80.png",20,80,carrier)
    atlas=canvas(32,96)
    draw_front(atlas,32,0)
    draw_right(atlas,32,32)
    draw_back(atlas,32,64)
    write_png(OUT/"proof_hat_32.png",32,96,atlas)

    # Second regression asset: derive a genuine 16x16-per-view atlas from the
    # project-owned 32px diagnostic art. This is intentionally simple test art,
    # not a production resize pipeline.
    atlas16=canvas(16,48)
    for y in range(48):
        for x in range(16):
            atlas16[y*16+x] = atlas[(y*2)*32 + (x*2)]
    write_png(OUT/"proof_hat_16.png",16,48,atlas16)

    print("wrote", OUT/"carrier_hat_20x80.png")
    print("wrote", OUT/"proof_hat_32.png")
    print("wrote", OUT/"proof_hat_16.png")

if __name__ == "__main__":
    main()
