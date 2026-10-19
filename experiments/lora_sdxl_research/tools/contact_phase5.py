"""Phase-5 eye-review contact sheets (analysis tool: venv PIL, `source tools/env.sh`).
Reads dataset/phase5_v1_review/candidates.json (build_dataset_phase5.py --review) and draws, per family, every
candidate's FRONT | RIGHT | BACK view at x4 nearest-neighbour on a mid grey, numbered; the index file maps numbers to
colourways, names, the family source and flags.  The sheets are what the family table is verified on (CLAUDE.md 3).
usage: python3 contact_phase5.py [--family NAME] [--only-flagged]"""
import collections, json, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_dataset_phase5 as P5
REV = P5.OUT + '_review'
Z, FW, COLS, ROWS = 4, 24, 6, 6
CW, CH = 3 * FW * Z + 16, FW * Z + 18


def main():
    rows = json.load(open(os.path.join(REV, 'candidates.json')))
    fam_only = sys.argv[sys.argv.index('--family') + 1] if '--family' in sys.argv else None
    groups = collections.defaultdict(list)
    for r in rows:
        if '--only-flagged' in sys.argv and not r['flags']: continue
        groups[r['family'] or 'NONE'].append(r)
    idx = []
    for fam, rs in sorted(groups.items()):
        if fam_only and fam != fam_only: continue
        for s in range(0, len(rs), COLS * ROWS):
            chunk = rs[s:s + COLS * ROWS]; im = Image.new('RGB', (COLS * CW, ROWS * CH + 20), (96, 96, 96)); d = ImageDraw.Draw(im)
            d.text((4, 4), f'{fam}  {s + 1}-{s + len(chunk)} / {len(rs)}', fill=(255, 255, 255))
            for i, r in enumerate(chunk):
                ox, oy = (i % COLS) * CW, 20 + (i // COLS) * CH
                for vi, v in enumerate(('front', 'right', 'back')):
                    for x, y, *p in r['views'][v]:
                        d.rectangle([ox + vi * FW * Z + x * Z, oy + y * Z, ox + vi * FW * Z + x * Z + Z - 1, oy + y * Z + Z - 1], fill=tuple(p))
                n = s + i + 1; tag = '!' if r['flags'] else ''
                d.text((ox + 2, oy + FW * Z + 2), f'{n}{tag} {r["rel"][:30]}', fill=(255, 255, 0) if r['flags'] else (230, 230, 230))
                idx.append(f'{fam}\t{n}\t{r["rel"]}\t{r["key"]}\t{r["names"]}\t{r["why"]}\tbrim={r["brim"]}\t{r["flags"]}')
            fn = f'{fam.replace(" ", "_")}_{s // (COLS * ROWS) + 1}.png'; im.save(os.path.join(REV, fn))
            print(fn, len(chunk))
    open(os.path.join(REV, 'index.tsv'), 'w').write('\n'.join(idx) + '\n')


if __name__ == '__main__':
    main()
