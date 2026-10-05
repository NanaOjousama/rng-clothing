"""SpriteFusion has no mask: run `edit` on the 1x mannequin, then align the output
back onto the mannequin (integer scale + offset, scored on pixels OUTSIDE the
hat mask) and keep only the in-mask pixels. Same mannequin/masks as v3.

  python3 sf_hat.py run <name> "<colour text>" [exact|loose]
"""
import json, sys, os
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from sf_pipeline.client import SpriteFusionClient, data_url
HERE = Path(__file__).parent; OUT = HERE / 'spritefusion'
CAP = json.load(open(HERE / 'v3/capture.json'))['capture_dir']

def mannequin_1x():
    p = OUT / 'mannequin_1x.png'
    if not p.exists():
        Image.open(HERE / CAP / 'front_nohat_policy.png').convert('RGBA').resize((64, 64), Image.NEAREST).save(p)
    return p

def align(out, man, mask):
    """best (scale, dx, dy): output pixel grid -> mannequin 1x grid."""
    best = None
    for s in (1, 2, 3, 4):
        o = out.resize((max(1, out.width // s), max(1, out.height // s)), Image.NEAREST) if s > 1 else out
        op, mp, kp = o.load(), man.load(), mask.load()
        for dy in range(-o.height, 64):
            for dx in range(-o.width, 64):
                hit = miss = 0
                for y in range(o.height):
                    yy = y + dy
                    if not 0 <= yy < 64: continue
                    for x in range(o.width):
                        xx = x + dx
                        if not 0 <= xx < 64 or kp[xx, yy]: continue
                        a, b = op[x, y], mp[xx, yy]
                        if a[3] == 0 and b[3] == 0: continue
                        if a[3] and b[3] and max(abs(i - j) for i, j in zip(a[:3], b[:3])) < 24: hit += 1
                        else: miss += 1
                score = hit - miss
                if best is None or score > best[0]: best = (score, s, dx, dy, hit, miss)
    return best

def run(name, colour, variant='exact'):
    OUT.mkdir(exist_ok=True)
    key = Path(os.path.expanduser('~/.config/spritefusion.key')).read_text()
    client = SpriteFusionClient(key)
    prompt = (f"Put a simple bucket hat on this farmer's head: {colour}, stardew valley style, dark outline. "
              "The hat is small, the same size as a vanilla Stardew Valley bucket hat, sitting on top of the hair "
              "and ending at the eyebrows. Keep the farmer, pose, face, hair below the hat, clothes, colours "
              "and canvas position exactly unchanged.")
    body = {'operation': 'edit', 'prompt': prompt, 'inputs': [{'data_url': data_url(mannequin_1x())}]}
    d = OUT / f'{variant}_{name}'; d.mkdir(exist_ok=True)
    events = client.generate(body); (d / 'events.json').write_text(json.dumps(events, indent=1))
    (d / 'request.json').write_text(json.dumps({**body, 'inputs': ['mannequin_1x.png']}, indent=1))
    man = Image.open(mannequin_1x()).convert('RGBA')
    mask = Image.open(HERE / f'pixellab/mask_{variant}_1x.png').convert('L')
    results = []
    for i, e in enumerate([e for e in events if e.get('type') == 'output' and e['asset'].get('width', 0) <= 64]):  # skip the 6x preview
        p = d / f'output_{i:02d}.png'; client.download(e['asset']['assetUrl'], p)
        out = Image.open(p).convert('RGBA')
        score, s, dx, dy, hit, miss = align(out, man, mask)
        o = out.resize((out.width // s, out.height // s), Image.NEAREST) if s > 1 else out
        placed = Image.new('RGBA', (64, 64)); placed.paste(o, (dx, dy))
        hat = Image.new('RGBA', (64, 64)); hat.paste(placed, (0, 0), mask)
        hat.save(d / f'hat_{i:02d}_1x.png')
        results.append({'output': p.name, 'size': out.size, 'scale': s, 'offset': [dx, dy],
                        'outside_mask_match': hit, 'outside_mask_mismatch': miss})
    credits = [e.get('credits') for e in events if e.get('credits')]
    (d / 'align.json').write_text(json.dumps({'results': results, 'credits': credits}, indent=1))
    print(name, variant, json.dumps(results), credits[-1] if credits else '')

if __name__ == '__main__':
    run(*sys.argv[2:])
