import json, os, pathlib

ROOT = '/workspace/phase5/dataset/phase5_v1'
SRC = os.path.join(ROOT, 'train', '1_sdvhat')
SPLIT = os.path.join(ROOT, 'train_split')
MAN = json.load(open(os.path.join(ROOT, 'manifest.json')))

for lay in ('front', 'fourview'):
    d = os.path.join(SPLIT, lay)
    os.makedirs(d, exist_ok=True)

lists = {'front': [], 'fourview': []}
for item in MAN['items']:
    if item['split'] != 'train':
        continue
    lay = item['layout']
    stem = item['file']
    for ext in ('.png', '.txt'):
        src = os.path.join(SRC, stem + ext)
        dst = os.path.join(SPLIT, lay, stem + ext)
        if not os.path.exists(dst):
            os.symlink(src, dst)
    lists[lay].append(stem)

for lay, files in lists.items():
    out = os.path.join(SPLIT, f'{lay}_manifest.txt')
    with open(out, 'w') as f:
        f.write('\n'.join(sorted(files)) + '\n')
    n_png = len([x for x in os.listdir(os.path.join(SPLIT, lay)) if x.endswith('.png')])
    print(lay, 'stems:', len(files), 'png symlinks on disk:', n_png)

print('done, split dirs at', SPLIT)
