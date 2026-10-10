"""Replay generate.py runs with provenance capture.  Pure Python.
usage: qc_replay.py <gen_dir> <out_dir> <records.json> <n> <seed>[,<seed>...] [name ...]
  gen_dir: a pack_study/gen directory -- the current one, or an archived copy of the
  commit that built a QC pack (git archive <commit> pack_study | tar -x), so hats
  already judged in game are reproduced by the code that made them.
  Writes records (gen/provenance.py) for the named hats, or all hats if none named."""
import importlib, json, os, sys


def main():
    gen_dir, out, dest, n, seeds = sys.argv[1:6]
    want = set(sys.argv[6:])
    sys.path.insert(0, os.path.abspath(gen_dir))
    gen = importlib.import_module('generate')
    prov = importlib.import_module('provenance') if os.path.exists(os.path.join(gen_dir, 'provenance.py')) else None
    if prov is None:                                # archived commit predates provenance.py: use ours
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        import provenance as prov
    rec = prov.record(gen)
    keep = []
    for seed in seeds.split(','):
        sys.argv = ['generate.py', out, n, seed]
        gen.main()
        for row in json.load(open(os.path.join(out, f'roll_log_s{seed}.json'))):
            if not want or row['name'] in want:
                r = prov.finish(gen, rec, row); r['row'] = row; r['seed'] = int(seed); keep.append(r)
        rec.clear()
    json.dump(keep, open(dest, 'w'))
    print(len(keep), 'records ->', dest)


if __name__ == '__main__':
    main()
