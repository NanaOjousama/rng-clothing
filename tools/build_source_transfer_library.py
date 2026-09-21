#!/usr/bin/env python3
"""Derive the source-backed template-transfer inventory from proven source families.

This never edits third-party source. It adds a second classification layer over
families.json: what a deconstructed thing may donate to a new construction
template, and under which semantic-zone contract.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / 'source_catalog/catalog.json'
FAM = ROOT / 'source_catalog/families.json'
OUT = ROOT / 'source_catalog/SOURCE_TRANSFER_LIBRARY.json'
OUT_MD = ROOT / 'source_catalog/SOURCE_TRANSFER_LIBRARY.md'

MOTIF = re.compile(r'leaf|flower|daisy|heart|star|moon|mushroom|tiara|garland|crest|rune', re.I)
ATTACH = re.compile(r'bow|ribbon|cat|ear|wing|pom|feather|veil', re.I)
HARDWARE = re.compile(r'chain|bell|button|buckle|stud|pin|clip', re.I)
PATTERN = re.compile(r'dot|stripe|plaid|check|rib|cable|waffle|jacquard|heather|messy', re.I)


def reusable_kind(name: str) -> tuple[str, str]:
    if HARDWARE.search(name): return 'HARDWARE', 'attachment_edge'
    if ATTACH.search(name): return 'ATTACHMENT', 'attachment_edge'
    if MOTIF.search(name): return 'MOTIF', 'surface'
    if PATTERN.search(name): return 'MATERIAL_PATTERN', 'surface'
    return 'REUSABLE_COMPONENT', 'surface'


def main():
    cat = json.loads(CAT.read_text())
    fams = json.loads(FAM.read_text())['families']
    appearances = {(a['pack'], a['category'], a['name']): a for a in cat['appearances']}
    families, parts = [], []
    for f in fams:
        identity = {'pack': f['pack'], 'category': f['category'], 'family': f['family'], 'base': f['base']}
        base_app = appearances.get((f['pack'], f['category'], f['base']), {})
        frame_evidence = (base_app.get('analysis') or {}).get('frames') or {}
        style = {
            'id': f"{f['pack']}::{f['category']}::{f['family']}",
            'partKind': 'STYLE_PROFILE', 'transferScope': 'STYLE_DONOR',
            'sourceBaseIdentity': identity,
            'category': f['category'], 'family': f['family'], 'pack': f['pack'], 'author': f.get('author'),
            'vocabulary': f.get('vocabulary', []), 'roles': f.get('roles', {}),
            'tone': f.get('tone', {}), 'credit': f.get('credit', {}),
            'paletteEvidence': {k: v.get('palette', []) for k,v in frame_evidence.items()},
            'recolourable': (base_app.get('analysis') or {}).get('recolourable'),
            'declaredMasks': (base_app.get('analysis') or {}).get('declared_masks', []),
            'safeTransfer': ['tone rhythm', 'value-role ordering', 'palette relationship'],
            'neverTransfer': ['base silhouette', 'source coordinates as target geometry']
        }
        families.append({
            'identity': identity, 'category': f['category'], 'baseCells': f.get('base_cells'),
            'directions': f.get('directions', []), 'styleProfile': style,
            'reconstructionExact': f.get('all_exact', False),
            'variantCount': len(f.get('variants', [])),
        })
        parts.append(dict(style, name=f"{f['family']} style profile", sourceClass='FAMILY'))
        for v in f.get('variants', []):
            cls = v.get('class')
            row = {
                'name': v['variant'], 'family': f['family'], 'category': f['category'],
                'pack': f['pack'], 'author': f.get('author'), 'sourceClass': cls,
                'sourceBaseIdentity': identity, 'exactReconstruction': v.get('exact'),
                'added': v.get('added'), 'changed': v.get('changed'), 'removed': v.get('removed'),
                'reason': v.get('reason'),
            }
            if cls == 'REUSABLE':
                kind, zone = reusable_kind(v['variant'])
                row.update(partKind=kind, transferScope='FAMILY_REUSABLE', requiresZone=zone,
                           safeTransfer=['only through declared target zone/anchor', 'preserve target locked alpha'],
                           neverTransfer=['blind source coordinates', 'target silhouette removal'])
            elif cls == 'BASE-SPECIFIC':
                row.update(partKind='BASE_SPECIFIC', transferScope='SAME_BASE_ONLY', requiresZone=None,
                           safeTransfer=['only when target source identity exactly matches original base'],
                           neverTransfer=['cross-template reuse'])
            else:
                row.update(partKind='ALTERNATE_CONSTRUCTION', transferScope='ALTERNATE_CONSTRUCTION', requiresZone=None,
                           safeTransfer=['promote/review as its own construction template'],
                           neverTransfer=['overlay/composition onto another construction'])
            parts.append(row)

    sb = []
    for p in sorted((ROOT/'authored/source_backed').glob('*/source_backed.json')):
        m = json.loads(p.read_text())
        sb.append({'id': m['name'], 'family': m['family'], 'shapeVariant': m['shape_variant'],
                   'classification': m.get('classification'), 'frameSize': m['source']['frame_size'],
                   'source': m['source'], 'zones': sorted({z for vv in m.get('zones', {}).values() for z in vv}),
                   'role': 'EXISTING_SOURCE_BACKED_TEMPLATE'})

    doc = {
        'schema': 'source-transfer-library/v1',
        'sourceAppearanceCount': len(cat['appearances']), 'sourceFamilyCount': len(families),
        'policy': {
            'construction': 'target template owns geometry; source donors never silently rewrite it',
            'style': 'family tone/value vocabulary may donate style relationships without donating silhouette',
            'parts': 'only FAMILY_REUSABLE parts with a satisfied target semantic zone are cross-template candidates',
            'baseSpecific': 'same-source-base only',
            'alternateConstruction': 'promote to a separate template; never overlay',
            'roundTrip': 'neutral template/source fidelity is mandatory before variation',
        },
        'reusablePartCategories': {
            'STYLE_PROFILE': 'family-authored value/tone relationship',
            'MATERIAL_PATTERN': 'surface treatment that requires a target surface zone',
            'MOTIF': 'small decoration seated inside a declared surface zone',
            'ATTACHMENT': 'geometry added at an explicitly declared attachment edge',
            'HARDWARE': 'small rigid accent attached at an explicitly declared edge/zone',
            'REUSABLE_COMPONENT': 'proven family-reusable delta not yet semantically specialized',
            'BASE_SPECIFIC': 'exactly one authored base only',
            'ALTERNATE_CONSTRUCTION': 'different geometry; candidate template, never a composable part',
        },
        'families': families, 'parts': parts, 'existingSourceBackedTemplates': sb,
        'counts': {'partKinds': dict(Counter(p['partKind'] for p in parts)),
                   'transferScopes': dict(Counter(p['transferScope'] for p in parts))}
    }
    OUT.write_text(json.dumps(doc, indent=2)+'\n')

    lines=['# Source Transfer Library','',
           'Derived from `catalog.json` + exact-reconstruction `families.json`. Third-party source is read-only.','',
           f"- appearances: **{doc['sourceAppearanceCount']}**", f"- deconstructed families: **{doc['sourceFamilyCount']}**",'']
    lines += ['## Transfer policy',''] + [f"- **{k}** — {v}" for k,v in doc['policy'].items()]
    lines += ['','## Part kinds',''] + [f"- **{k}**: {v}" for k,v in doc['reusablePartCategories'].items()]
    lines += ['','## Counts','']
    for k,v in sorted(doc['counts']['partKinds'].items()): lines.append(f'- {k}: **{v}**')
    lines += ['','## Proven cross-template candidates','']
    for p in parts:
        if p['transferScope']=='FAMILY_REUSABLE':
            lines.append(f"- **{p['name']}** — {p['partKind']} — {p['pack']} / {p['family']} — requires `{p['requiresZone']}`")
    OUT_MD.write_text('\n'.join(lines)+'\n')
    print('PASS source transfer library')
    print('appearances',len(cat['appearances']),'families',len(families))
    print('part kinds',doc['counts']['partKinds'])
    print('scopes',doc['counts']['transferScopes'])

if __name__=='__main__': main()
