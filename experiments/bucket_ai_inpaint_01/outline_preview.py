import sys
from PIL import Image, ImageDraw
BG = (196, 214, 188, 255)
man = Image.open('spritefusion/mannequin_1x.png').convert('RGBA')
van = Image.open('v3/vanilla_worn.png').convert('RGBA').resize((64, 64), Image.NEAREST)
def on(h=None):
    f = Image.new('RGBA', (64, 64), BG); f.alpha_composite(van if h is None else man)
    if h is not None: f.alpha_composite(Image.open(h).convert('RGBA'))
    return f
names = sys.argv[2:]; box, k = (21, 12, 43, 30), 12; tw, th = (box[2]-box[0])*k, (box[3]-box[1])*k
rows = [('VANILLA', None)] + [(n, n) for n in names]
cols = len(rows) // 2 + (len(rows) % 2) if len(rows) > 4 else len(rows)
sh = Image.new('RGBA', (10 + cols*(tw+10), ((len(rows)+cols-1)//cols)*(th+26) + 10), (40, 40, 48, 255)); d = ImageDraw.Draw(sh)
for i, (label, h) in enumerate(rows):
    x, y = 10 + (i % cols)*(tw+10), 10 + (i // cols)*(th+26)
    d.text((x, y), label.replace('_1x.png', ''), fill='white'); sh.paste(on(h).crop(box).resize((tw, th), Image.NEAREST), (x, y+14))
sh.save(sys.argv[1])
