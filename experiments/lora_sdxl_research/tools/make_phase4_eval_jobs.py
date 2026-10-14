"""Phase-4 evaluation inputs (Deck, pure Python) -> dataset/phase4_eval_jobs.json (small; copied to the laptop).

FOUR-VIEW (in-context, front given):
  witch_test  the 6 AI-ORIGINAL silhouette-test fronts of witch_front_candidates_01 (S1 T1 W1 W2 P1 P2), the same
              inputs as runs/witch_fronts_e10_01 -> direct e10 comparison.  EVAL INPUTS ONLY, never training data.
              Native: 20-wide at window (+2, +4), W1/W2 22-wide at (+1, +4) (fit natively now; e10 saw 20-wide crops).
  holdout     every phase-4 holdout sheet (26 library = the phase-3 holdout, + 3 witch references), read on the laptop.
FRONT (text -> front): the same prompts for the phase-1 front LoRA and the phase-4 front LoRA, 4 families x 3
  decorations, plus 6 general-hat prompts (regression check for the existing general data).
usage: python3 -I make_phase4_eval_jobs.py"""
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); EXP = os.path.dirname(HERE)
PAL = {'0': (24, 18, 36), '1': (46, 34, 72), '2': (70, 54, 104), '3': (98, 80, 140), '5': (214, 168, 70), '6': (150, 108, 44)}
FAM = {'S1': 'short witch hat', 'T1': 'tall floppy witch hat', 'W1': 'low sweeping witch hat', 'W2': 'low sweeping witch hat',
       'P1': 'classic pointed witch hat', 'P2': 'classic pointed witch hat'}
COL = 'black, dark purple, purple'                     # the test fronts' three most common colours (same for all six)
FRONT_PROMPTS = {
    'short': ['short witch hat, band', 'short witch hat, flowers', 'short witch hat, ribbon band'],
    'tall_floppy': ['tall floppy witch hat, band', 'tall floppy witch hat, flower crown', 'tall floppy witch hat, single flower'],
    'classic': ['classic pointed witch hat, band', 'classic pointed witch hat, veil', 'classic pointed witch hat, moss'],
    'low_sweeping': ['low sweeping witch hat, bow', 'low sweeping witch hat, flowers', 'low sweeping witch hat, moon and stars'],
    'general': ['cap', 'knit beanie', 'flower hat', 'cowboy hat, wide brim', 'animal hat, cat ears', 'crown'],
}
FRONT_COLOURS = ['dark purple, purple, yellow', 'dark green, green, pink', 'dark blue, blue, white']


def main():
    m = json.load(open(os.path.join(EXP, 'witch_front_candidates_01', 'out', 'fronts.json'))); jobs = []
    for k in ('S1', 'T1', 'W1', 'W2', 'P1', 'P2'):
        g = m[k]['grid']; w = len(g[0]); ox = (24 - w) // 2
        cells = [[None] * 24 for _ in range(24)]
        for y, row in enumerate(g):
            for x, ch in enumerate(row):
                if ch != '.': cells[y + 4][x + ox] = list(PAL[ch])
        f20 = None
        if w == 20: f20 = [[cells[y + 4][x + 2] for x in range(20)] for y in range(20)]
        else:                                                                 # e10's own 20-wide copy (palette-index rows)
            rows = json.load(open(os.path.join(EXP, 'witch_front_candidates_01', 'out', 'e10_fronts_20.json')))[k]
            f20 = [[list(PAL[ch]) if ch != '.' else None for ch in r] for r in rows]
        jobs.append({'id': f'witch_test__{k}', 'family': FAM[k], 'name': m[k]['name'], 'front24': cells, 'front20': f20,
                     'caption_tail': f'{FAM[k]}, band, {COL}', 'tag': 'AI-ORIGINAL eval input (witch_front_candidates_01)'})
    fp = []
    for fam, ps in FRONT_PROMPTS.items():
        for i, p in enumerate(ps): fp.append({'id': f'{fam}_{i}', 'family': fam, 'words': p, 'colours': FRONT_COLOURS[i % 3]})
    json.dump({'witch_test': jobs, 'front_prompts': fp, 'seeds': [7, 8, 9], 'note': 'front20 = the 20x20 input e10 saw '
               '(W1/W2: witch_front_candidates_01/out/e10_fronts_20.json, columns dropped)'},
              open(os.path.join(HERE, 'dataset', 'phase4_eval_jobs.json'), 'w'))
    print(len(jobs), 'witch test fronts,', len(fp), 'front prompts')


if __name__ == '__main__':
    main()
