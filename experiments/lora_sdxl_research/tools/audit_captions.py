"""Caption audit (Deck, pure Python, read-only).  2026-10-12: the bear (seyph c287) was captioned 'cowboy hat' and
the cat (seyph c288) 'bowler hat', and the phase-2 LoRA drew cowboy brims / bowler crowns on their side views.

Root cause found: build_dataset.clean_name maps a 'hats_N' name to VANILLA hat N's name, whoever the author is.
Packs that replace vanilla hat art (Seyph, ...) therefore get the replaced vanilla hat's name (hats_0 -> Cowboy Hat).

Every caption term is traced to its source and flagged:
  VANILLA_SLOT   name came from a hats_N slot of a non-ConcernedApe construction (replacement art, name unverified)
  BRIM_CONFLICT  a brimmed-hat word (cowboy/bowler/top hat/fedora/boater/sombrero/'wide|narrow brim'/straw/sun hat)
                 while the VERIFIED structure (pack_study/data/host_structure.json, reviewed by eye) says brim none
  FAMILY_SOURCE  family words come from host_families() (names + hand labels); listed for reference, not flagged
Nothing is changed: proposals are written for review.  Covers phase-1 (front) and phase-2 (4-view) manifests.
usage: python3 -I audit_captions.py  -> analysis/caption_audit.json + analysis/caption_audit.md"""
import collections, json, os, re, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import build_dataset as B

BRIM_WORDS = ['cowboy hat', 'bowler hat', 'top hat', 'fedora', 'boater', 'sombrero', 'wide brim', 'narrow brim',
              'straw hat', 'sun hat', 'ranger hat', 'panama']
MANIFESTS = {'phase1_front': 'dataset/phase1_front/manifest.json', 'phase2_4view_512': 'dataset/phase2_4view_512/manifest.json'}


def main():
    L = {c['id']: c for c in json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'library.json')))['constructions']}
    struct_ = json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'host_structure.json')))['hosts']
    labels = json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'host_labels.json')))['labels']
    vanilla = B.load_vanilla() if hasattr(B, 'load_vanilla') else {
        int(k): v.split('/')[0] for k, v in json.load(open(B.VANILLA)).items() if k.isdigit()}
    out = {'root_cause': __doc__.split('\n\n')[1].strip(), 'datasets': {}}; md = ['# Caption audit (2026-10-12)', '']
    for ds, rel in MANIFESTS.items():
        p = os.path.join(HERE, rel)
        if not os.path.exists(p): continue
        M = json.load(open(p)); seen = {}; flagged = []
        for it in M['items']:
            cid = it.get('construction') or it['file'].split('__w')[0]
            if cid in seen: seen[cid]['files'].append(it['file']); continue
            c = L.get(cid)
            if c is None: continue
            brim = struct_.get(cid, {}).get('brim'); cap = it['caption'].lower()
            slot = [(n, vanilla.get(int(re.fullmatch(r'hats_(\d+)', n).group(1)))) for n in c['names'] if re.fullmatch(r'hats_(\d+)', n)]
            flags = []
            if slot and c['author'] != 'ConcernedApe':
                flags.append({'flag': 'VANILLA_SLOT', 'detail': f"{slot[0][0]} -> '{slot[0][1]}' (author {c['author']})"})
            if brim == 'none':
                hit = [w for w in BRIM_WORDS if w in cap]
                if hit: flags.append({'flag': 'BRIM_CONFLICT', 'detail': f"{hit} but verified brim = none"})
            fams = sorted(B.SEM.host_families(c['names'], cid))
            rec = {'construction': cid, 'author': c['author'], 'names': c['names'][:3], 'split': it['split'],
                   'verified_brim': brim, 'families': fams, 'label_note': labels.get(cid, {}).get('note'),
                   'caption': it['caption'], 'flags': flags, 'files': [it['file']]}
            seen[cid] = rec
            if flags: flagged.append(rec)
        cnt = collections.Counter(f['flag'] for r in flagged for f in r['flags'])
        files = sum(len(r['files']) for r in flagged); total = len(M['items'])
        out['datasets'][ds] = {'constructions': len(seen), 'flagged_constructions': len(flagged), 'flag_counts': dict(cnt),
                               'files_affected': files, 'files_total': total, 'flagged': flagged}
        md += [f'## {ds}', '', f'{len(flagged)} of {len(seen)} constructions flagged ({files} of {total} images). '
               f'Counts: {dict(cnt)}', '', '| construction | split | flags | caption terms |', '|---|---|---|---|']
        for r in sorted(flagged, key=lambda r: (r['split'], r['construction'])):
            terms = ', '.join(r['caption'].split(', ')[6 if ds.startswith('phase2') else 2:][:4])
            md.append(f"| {r['construction']} | {r['split']} | {'; '.join(f['flag'] + ': ' + f['detail'] for f in r['flags'])} | {terms} |")
        md.append('')
    json.dump(out, open(os.path.join(HERE, 'analysis', 'caption_audit.json'), 'w'), indent=1)
    open(os.path.join(HERE, 'analysis', 'caption_audit.md'), 'w').write('\n'.join(md))
    for ds, d in out['datasets'].items():
        print(ds, d['flagged_constructions'], '/', d['constructions'], d['flag_counts'], f"{d['files_affected']}/{d['files_total']} images")


if __name__ == '__main__':
    main()
