"""Collect every witch hat from the REFERENCE packs (read-only) -> out/refs.json + out/ref_fronts_x6.png.
Packs: witch_reference_packs_01 (Hats and Horns / Luny / Kailey, Nexus), witch_reference_packs_02 (492815, Naver),
wildwood_reference_01 (mushlune Wildwood), bloom_reference_01 (mushlune Bloom, added 2026-10-14).  Views cropped from each hat.json's StartingPosition + HatSize.
Analysis only (.venv PIL)."""
import json, os, re, sys
from PIL import Image, ImageDraw
EXP = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACKS = {'HnH': 'witch_reference_packs_01/raw/Hats and Horns', 'Luny': "witch_reference_packs_01/raw/Luny's Witch Hats for FS",
         'Kailey': 'witch_reference_packs_01/raw/Witch Hats', 'Naver': 'witch_reference_packs_02/raw',
         'Wildwood': 'wildwood_reference_01/raw', 'Bloom': 'bloom_reference_01/raw'}


def load(p):
    t = open(p, encoding='utf-8-sig').read(); t = re.sub(r',\s*([}\]])', r'\1', re.sub(r'//[^\n]*', '', t))
    return json.loads(t)


def main():
    out = []
    for pk, rel in PACKS.items():
        for dp, _, fs in sorted(os.walk(os.path.join(EXP, rel))):
            if 'hat.json' not in fs: continue
            j = load(os.path.join(dp, 'hat.json')); name = j.get('Name', os.path.basename(dp))
            if pk == 'HnH' and 'witch' not in name.lower(): continue
            if pk == 'Bloom' and 'crown' in name.lower(): continue      # Fall/Spring Crown: flower crowns, not witch hats
            img = Image.open(os.path.join(dp, 'hat.png')).convert('RGBA'); views = {}
            for k, v in (('FrontHat', 'F'), ('RightHat', 'R'), ('LeftHat', 'L'), ('BackHat', 'B')):
                if k not in j: continue
                sp, sz = j[k]['StartingPosition'], j[k]['HatSize']
                views[v] = (sp['X'], sp['Y'], sz['Width'], sz['Length'], j[k].get('HeadPosition', {'X': 0, 'Y': 0}))
            out.append({'pack': pk, 'name': name, 'dir': os.path.relpath(dp, EXP), 'views': views})
    json.dump(out, open('out/refs.json', 'w'), indent=1, ensure_ascii=False)
    S, T = 4, 34; cols = 2
    sheet = Image.new('RGBA', (cols * (230 + 2 * T * S + 20), (len(out) + 1) // cols * (T * S + 8) + 8), (30, 32, 40, 255))
    d = ImageDraw.Draw(sheet)
    for i, h in enumerate(out):
        x0 = (i % cols) * (230 + 2 * T * S + 20); y0 = 8 + (i // cols) * (T * S + 8)
        d.text((x0 + 4, y0 + 4), f"{i:02d} {h['pack']}\n{h['name'][:30]}", fill=(230, 230, 230))
        img = Image.open(os.path.join(EXP, h['dir'], 'hat.png')).convert('RGBA')
        for k, v in enumerate('FR'):
            if v not in h['views']: continue
            x, y, w, l, _ = h['views'][v]; tile = Image.new('RGBA', (T, T), (122, 150, 100, 255))
            tile.alpha_composite(img.crop((x, y, x + w, y + l)), ((T - w) // 2, T - l - 2))
            sheet.paste(tile.resize((T * S, T * S), Image.NEAREST), (x0 + 230 + k * (T * S + 4), y0))
    sheet.save('out/ref_fronts_x6.png'); print(len(out), 'witch hats', sheet.size)


if __name__ == '__main__':
    main()
