"""v3: mannequin = farmer with the vanilla Bucket Hat's hair policy (hairstyle 38 -> 30),
hat removed. Two mask variants x three hats, compared against the real vanilla Bucket Hat.

  python3 v3.py prep <capture_dir>       base + both masks
  python3 v3.py run                      6 RD inpaints ($0.18 each), key from RD_API_KEY
  python3 v3.py sheet                    cut-outs + V3_CONTACT.png
"""
import base64, json, os, sys, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageFilter, ImageDraw
S, BG = 4, (196, 214, 188)
OUT = 'v3'
HATS = {'olive': (1101, 'olive green canvas with a darker olive band'),
        'pink':  (2202, 'soft pastel pink with a tiny white daisy'),
        'denim': (3303, 'faded navy denim with a lighter band')}
VARIANTS = {
  'exact': 'a simple bucket hat, stardew valley style, dark outline, {c}',
  'loose': 'a simple bucket hat with a flat wide brim that flares out past the crown, '
           'low crown, stardew valley style, dark outline, {c}'}

def flat(im):
    f = Image.new('RGBA', im.size, BG + (255,)); f.alpha_composite(im.convert('RGBA')); return f

def prep(cap):
    os.makedirs(OUT, exist_ok=True)
    json.dump({'capture_dir': cap}, open(f'{OUT}/capture.json', 'w'))
    flat(Image.open(f'{cap}/front_nohat_policy.png')).convert('RGB').save(f'{OUT}/base.png')
    flat(Image.open(f'{cap}/front_worn.png')).convert('RGB').save(f'{OUT}/vanilla_worn.png')
    # true hat = worn vs policy mannequin (front_hatonly diffs against the
    # normal-hair nohat, so it also counts the 38 -> 30 hair swap as hat)
    w, m = Image.open(f'{cap}/front_worn.png').convert('RGBA'), Image.open(f'{cap}/front_nohat_policy.png').convert('RGBA')
    hat = Image.new('L', w.size, 0); hp, wp, mp = hat.load(), w.load(), m.load()
    for y in range(w.size[1]):
        for x in range(w.size[0]):
            if wp[x, y] != mp[x, y]: hp[x, y] = 255
    masks = {'exact': hat, 'loose': hat.filter(ImageFilter.MaxFilter(9))}  # +1 game px
    for v, m in masks.items():
        a = Image.new('RGBA', m.size, (0, 0, 0, 0)); a.paste((255, 255, 255, 255), (0, 0), m)
        a.save(f'{OUT}/mask_{v}.png')   # RD reads alpha: opaque white = regenerate
        b = m.getbbox(); print(v, 'mask game px', (b[2]-b[0])//S, 'x', (b[3]-b[1])//S)

def call(v, name):
    seed, colour = HATS[name]
    b64 = lambda p: base64.b64encode(open(p, 'rb').read()).decode()
    body = {'input_image': b64(f'{OUT}/base.png'), 'mask_image': b64(f'{OUT}/mask_{v}.png'),
            'prompt': VARIANTS[v].format(c=colour), 'seed': seed}
    req = urllib.request.Request('https://api.retrodiffusion.ai/v2/edit/tools/inpainting',
        data=json.dumps(body).encode(), method='POST',
        headers={'X-RD-Token': os.environ['RD_API_KEY'], 'Content-Type': 'application/json'})
    r = json.load(urllib.request.urlopen(req, timeout=300))
    urllib.request.urlretrieve(r['output_urls'][0], f'{OUT}/out_{v}_{name}.png')
    json.dump({'prompt': body['prompt'], 'seed': seed, 'inference_id': r.get('inference_id')},
              open(f'{OUT}/out_{v}_{name}.json', 'w'), indent=1)
    return v, name, r.get('remaining_balance')

def run():
    with ThreadPoolExecutor(1) as ex:  # 6-way parallel got an HTTP 500 (still charged)
        for res in ex.map(lambda a: call(*a), [(v, n) for v in VARIANTS for n in HATS]):
            print(*res)

def cutout(v, name):
    base = Image.open(f'{OUT}/base.png').convert('RGBA'); bp = base.load()
    out = Image.open(f'{OUT}/out_{v}_{name}.png').convert('RGBA'); op = out.load()
    mp = Image.open(f'{OUT}/mask_{v}.png').getchannel('A').load()
    W, H = base.size; leak = 0
    g = Image.new('RGBA', (W // S, H // S)); gp = g.load(); mixed = 0
    for by in range(H // S):
        for bx in range(W // S):
            px = [(bx*S+i, by*S+j) for j in range(S) for i in range(S)]
            leak += sum(1 for p in px if not mp[p] and op[p][:3] != bp[p][:3])
            inm = [p for p in px if mp[p] and max(abs(a-b) for a, b in zip(op[p][:3], BG)) > 12]
            changed = [p for p in inm if op[p][:3] != bp[p][:3]]
            if len(set(op[p][:3] for p in px)) > 1: mixed += 1
            # hat block: mostly in-mask, non-backdrop, and the AI touched it
            if len(inm) >= 8 and changed:
                gp[bx, by] = Counter(op[p][:3] for p in inm).most_common(1)[0][0] + (255,)
    b = g.getbbox()
    return g, {'hat_game_px': [b[2]-b[0], b[3]-b[1]] if b else None,
               'changed_outside_mask': leak, 'mixed_4x4_blocks': mixed}

def sheet():
    cap = json.load(open(f'{OUT}/capture.json'))['capture_dir']
    mannequin = Image.open(f'{cap}/front_nohat_policy.png').convert('RGBA')
    vanilla = Image.open(f'{OUT}/vanilla_worn.png').convert('RGBA')
    box, k = (84, 48, 172, 136), 3; tw, th = (box[2]-box[0])*k, (box[3]-box[1])*k
    rows, report = [], {}
    for v in VARIANTS:
        for n in HATS:
            g, rep = cutout(v, n); report[f'{v}_{n}'] = rep
            g.save(f'{OUT}/hat_{v}_{n}_1x.png')
            worn = mannequin.copy(); worn.alpha_composite(g.resize(worn.size, Image.NEAREST))
            rows.append((f'{v} / {n}  {rep["hat_game_px"]} game px', flat(worn)))
    json.dump(report, open(f'{OUT}/report.json', 'w'), indent=1); print(json.dumps(report))
    # grid: vanilla reference then 3 hats per variant row
    cols = 4; sh = Image.new('RGBA', (cols*(tw+10)+10, 2*(th+28)+10), (40, 40, 48, 255)); d = ImageDraw.Draw(sh)
    for r, v in enumerate(VARIANTS):
        y = 10 + r*(th+28) + 16
        cells = [('VANILLA bucket (game)', vanilla)] + [x for x in rows if x[0].startswith(v)]
        for c, (label, im) in enumerate(cells):
            x = 10 + c*(tw+10); d.text((x, y-14), label, fill='white')
            sh.paste(im.crop(box).resize((tw, th), Image.NEAREST), (x, y))
    sh.save(f'{OUT}/V3_CONTACT.png')

if __name__ == '__main__':
    {'prep': lambda: prep(sys.argv[2]), 'run': run, 'sheet': sheet}[sys.argv[1]]()
