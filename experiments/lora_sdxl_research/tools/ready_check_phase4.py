"""Phase-4 readiness check (NO training, NO GPU, no torch import).  Static checks only:
configs parse and point at existing inputs; outputs not yet present (no overwrite); trainer/eval scripts compile and
their helper modules exist; baseline weights and baseline-dataset manifests exist with the fields the evals read;
review finalizer present.  usage: python ready_check_phase4.py"""
import json, os, py_compile, shutil
import toml   # the parser sd-scripts itself uses for these configs
class tomllib:
    @staticmethod
    def load(f): return toml.loads(f.read().decode('utf-8'))
R = r'C:\Users\Chris\sdxl_lora_research'; LAB = r'C:\Users\Chris\stardew-lora-lab'; SD = os.path.join(LAB, 'sd-scripts')
res = []
def chk(name, ok, info=''): res.append((ok, name, info)); print(('OK   ' if ok else 'FAIL ') + name + (f'  [{info}]' if info else ''))
for kind, n1, n2 in (('4view', 478, 43), ('front', 490, 43)):
    tr = tomllib.load(open(os.path.join(R, 'configs', f'phase4_{kind}_train.toml'), 'rb'))
    ds = tomllib.load(open(tr['dataset_config'], 'rb'))
    chk(f'{kind}: base model exists', os.path.exists(tr['pretrained_model_name_or_path']))
    chk(f'{kind}: output dir not yet trained (no overwrite)', not any(f.endswith('.safetensors') for f in os.listdir(tr['output_dir'])) if os.path.isdir(tr['output_dir']) else True, tr['output_dir'])
    subs = ds['datasets'][0]['subsets']
    for s, want in zip(subs, (n1, n2)):
        got = len([f for f in os.listdir(s['image_dir']) if f.endswith('.png')]) if os.path.isdir(s['image_dir']) else -1
        txt = len([f for f in os.listdir(s['image_dir']) if f.endswith('.txt')]) if os.path.isdir(s['image_dir']) else -1
        chk(f"{kind}: {os.path.basename(s['image_dir'])} images/captions (repeats {s['num_repeats']})", got == want and txt == want, f'{got}/{txt}, want {want}')
    steps = sum(len([f for f in os.listdir(s['image_dir']) if f.endswith('.png')]) * s['num_repeats'] for s in subs) * tr['max_train_epochs']
    chk(f'{kind}: total steps', True, str(steps))
for p in (os.path.join(SD, 'sdxl_train_network.py'), os.path.join(SD, 'networks', 'lora.py'), os.path.join(R, 'tools', 'sdxl_train_cleanfront.py'),
          os.path.join(R, 'runs', 'phase3_cleanfront_resume', 'sdvhat_phase3_cleanfront.safetensors'),
          os.path.join(R, 'runs', 'phase1_front_512', 'sdvhat_phase1_front_512.safetensors'),
          os.path.join(R, 'dataset', 'phase4_eval_jobs.json'), os.path.join(R, 'tools', 'complete_lora_review.ps1'),
          os.path.join(R, 'tools', 'publish_lora_reviews.ps1')):
    chk('exists ' + p.replace(R, 'R').replace(LAB, 'LAB'), os.path.exists(p))
for t in ('eval_phase4', 'eval_front_phase4', 'eval_variety_phase4', 'build_phase4_laptop', 'eval_phase3', 'decode_v2', 'demo_condition', 'sdxl_train_cleanfront'):
    try: py_compile.compile(os.path.join(R, 'tools', t + '.py'), doraise=True, cfile=os.path.join(os.environ.get('TEMP', R), t + '.pyc')); chk(f'compiles tools/{t}.py', True)
    except Exception as e: chk(f'compiles tools/{t}.py', False, str(e)[:120])
J = json.load(open(os.path.join(R, 'dataset', 'phase4_eval_jobs.json')))
chk('eval jobs: witch_test fronts / front prompts', len(J['witch_test']) == 6 and len(J['front_prompts']) == 18, f"{len(J['witch_test'])}/{len(J['front_prompts'])}")
for ds, keys in (('phase1_front_512', ('block', 'offset', 'background', 'canvas', 'trigger', 'items')), ('phase3_4view_512', ('items',))):
    p = os.path.join(R, 'dataset', ds, 'manifest.json')
    if not os.path.exists(p): chk(f'{ds} manifest', False, 'missing'); continue
    M = json.load(open(p)); miss = [k for k in keys if k not in M]
    chk(f'{ds} manifest fields the evals read', not miss, 'missing ' + ','.join(miss) if miss else f"{len(M['items'])} items")
    if ds == 'phase1_front_512' and not miss:
        tr = [it for it in M['items'] if it.get('split') == 'train' and not it.get('augmented')]
        sub = lambda it: os.path.join(R, 'dataset', ds, 'train', ('2_' if it.get('subset') == 'witch' else '1_') + M['trigger'], it['file'] + '.png')
        lost = [it['file'] for it in tr if not os.path.exists(sub(it))]
        chk('phase1 train images where eval_front_phase4 looks', tr and not lost, f'{len(tr)} train, {len(lost)} not found' + (f' e.g. {lost[0]}' if lost else ''))
free = shutil.disk_usage(R).free / 2**30; chk('free disk (GiB)', free > 20, f'{free:.0f}')
print('\nREADY' if all(r[0] for r in res) else f"\nNOT READY: {sum(not r[0] for r in res)} failing")
