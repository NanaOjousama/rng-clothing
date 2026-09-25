from __future__ import annotations
from PIL import Image

SIZE=20
PALETTE={
    "outline":(43,49,57,255),
    "deep":(60,69,80,255),
    "shadow":(78,90,104,255),
    "mid":(101,116,132,255),
    "light":(132,148,164,255),
    "hi":(163,177,190,255),
}

def mask_from_spans(spans):
    m=[[False]*SIZE for _ in range(SIZE)]
    for y,(x0,x1) in spans.items():
        for x in range(max(0,x0),min(SIZE-1,x1)+1):
            m[y][x]=True
    return m

def boundary(mask,x,y):
    if not mask[y][x]:
        return False
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        xx,yy=x+dx,y+dy
        if xx<0 or yy<0 or xx>=SIZE or yy>=SIZE or not mask[yy][xx]:
            return True
    return False

def shade(mask,facing):
    img=Image.new("RGBA",(SIZE,SIZE),(0,0,0,0))
    px=img.load()
    ys=[y for y in range(SIZE) for x in range(SIZE) if mask[y][x]]
    top=min(ys); bottom=max(ys)
    center=9.5 if facing in ("front","back") else 10.0
    for y in range(SIZE):
        for x in range(SIZE):
            if not mask[y][x]:
                continue
            if boundary(mask,x,y):
                px[x,y]=PALETTE["outline"]
                continue
            ny=(y-top)/max(1,bottom-top)
            dx=abs(x-center)
            if ny<0.34 and dx<=2.5:
                role="hi"
            elif ny<0.60 and dx<=4.0:
                role="light"
            elif ny>0.78:
                role="deep"
            elif x<center-4:
                role="shadow"
            else:
                role="mid"
            px[x,y]=PALETTE[role]
    return img

def mirror(img):
    return img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

def validate_frame(img):
    assert img.size==(SIZE,SIZE)
    alphas={px[3] for px in img.getdata()}
    assert alphas <= {0,255}
    assert img.getbbox() is not None
    x0,y0,x1,y1=img.getbbox()
    assert 0<=x0<x1<=SIZE and 0<=y0<y1<=SIZE
    assert x1-x0<=20 and y1-y0<=14
