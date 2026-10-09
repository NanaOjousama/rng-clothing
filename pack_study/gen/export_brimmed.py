"""Export crown x brim combinations as a Fashion Sense pack (baked colour).
Combinations involving plurffle's ribbon sun hat are skipped: its ribbon tails
straddle the junction and leave fragments (known issue)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import png
from combine_brimmed import combine, VIEWS
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = ('sun_hat_ribbon',)

def main():
    data = json.load(open(os.path.join(HERE, 'data', 'brimmed_parts.json')))['hats']
    combos = [c for c in json.load(open(os.path.join(HERE, 'data', 'brimmed_combos.json')))
              if not any(s in c['crown'] or s in c['brim'] for s in SKIP)]
    pack = os.path.join(HERE, 'out', 'gen', '[FS] PackStudy Brimmed')
    os.makedirs(pack, exist_ok=True)
    json.dump({'Name': 'PackStudy Brimmed', 'Author': 'pack_study generator', 'Version': '0.1.0',
               'Description': 'Crown x brim combinations from source straw hats', 'UniqueID': 'PackStudy.Brimmed',
               'UpdateKeys': [], 'ContentPackFor': {'UniqueID': 'PeacefulEnd.FashionSense'}},
              open(os.path.join(pack, 'manifest.json'), 'w'), indent=2)
    log = []
    for k, c in enumerate(combos):
        a, b, t = data[c['crown']], data[c['brim']], data[c['style']]
        w, h = b['frame']
        res = combine(a, b, t, b['frame'])
        rows = []
        for v in VIEWS:
            for y in range(h):
                rows.append([tuple(res[v].get((x, y), (0, 0, 0, 0))) for x in range(w)])
        name = f'PSB_{k:02d}'
        d = os.path.join(pack, 'Hats', name); os.makedirs(d, exist_ok=True)
        png.write(os.path.join(d, 'hat.png'), w, 4 * h, rows)
        model = {'Name': name}
        for i, v in enumerate(VIEWS):
            hp = b['head'].get(v, [0, 0])
            model[v.capitalize() + 'Hat'] = {'DisableGrayscale': True, 'StartingPosition': {'X': 0, 'Y': i * h},
                                             'HeadPosition': {'X': int(hp[0]), 'Y': int(hp[1])}, 'HatSize': {'Width': w, 'Length': h}}
        json.dump(model, open(os.path.join(d, 'hat.json'), 'w'), indent=2)
        log.append({'name': name, **c})
    json.dump(log, open(os.path.join(pack, 'combos_log.json'), 'w'), indent=1)
    print(len(log), 'hats ->', pack)

main()
