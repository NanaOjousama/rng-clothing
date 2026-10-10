"""Real vanilla hats from the game's unpacked Content.  Analysis-only (PIL + numpy).

Authority: `Content (unpacked)/Characters/Farmer/hats.png` (20x80 cells, rows
front/right/left/back) + `Data/hats.json` (field 6 = sprite index when present).
"""
import json, os
import numpy as np
from PIL import Image

CONTENT = os.environ.get('SDV_CONTENT_UNPACKED',
                         '/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)')


def clean(a):
    """Zero RGB under alpha 0 so hidden colour never splits identical art."""
    a = a.copy()
    a[a[..., 3] == 0] = 0
    return a


def strip_from_vertical(img):
    """20x80 vertical cell (front,right,left,back) -> 80x20 corpus strip array (int16)."""
    a = np.asarray(img.convert('RGBA'), dtype=np.int16)
    return clean(np.concatenate([a[i * 20:(i + 1) * 20] for i in range(4)], axis=1))


def load_vanilla():
    """{sprite index: {'arr', 'id', 'name'}} for every non-empty cell of hats.png."""
    sheet = Image.open(os.path.join(CONTENT, 'Characters', 'Farmer', 'hats.png')).convert('RGBA')
    data = json.load(open(os.path.join(CONTENT, 'Data', 'hats.json'), encoding='utf-8'))
    names = {}
    for k, v in data.items():
        f = v.split('/')
        idx = int(f[6]) if len(f) > 6 and f[6].strip() else int(k)
        names[idx] = {'id': k, 'name': f[0]}
    cols = sheet.width // 20
    out = {}
    for idx in range(cols * (sheet.height // 80)):
        x, y = idx % cols * 20, idx // cols * 80
        a = strip_from_vertical(sheet.crop((x, y, x + 20, y + 80)))
        if a[..., 3].any():
            out[idx] = {'arr': a, **names.get(idx, {'id': None, 'name': f'hats_{idx}'})}
    return out
