"""Unified production source router.

Routes source selection before rendering so provenance boundaries remain strict.
"""
from __future__ import annotations
from generator.content_source_policy import allowed_sources,normalize_mode
from generator.vanilla_source_production import promoted as vanilla_promoted,render as render_vanilla
from generator.source_respecting_hat_production import load_goldens,roll_and_render as render_mod_author_hat

def pools(mode:str='Everything')->dict:
    allow=set(allowed_sources(mode)); out={'mode':normalize_mode(mode),'allowedSources':sorted(allow),'hat':[],'shirt':[]}
    if 'VANILLA' in allow:
        out['hat'] += [{'provenance':'VANILLA','kind':'hat','sourceIndex':i} for i in vanilla_promoted('hat')]
        out['shirt'] += [{'provenance':'VANILLA','kind':'shirt','sourceIndex':i} for i in vanilla_promoted('shirt')]
    if 'MOD_AUTHOR' in allow:
        out['hat'] += [{'provenance':'MOD_AUTHOR','kind':'hat','family':f} for f in sorted(load_goldens()['families'])]
    # CONSTRUCTION_PRINTER is deliberately represented as an allowed source class
    # but has no production-promoted entries yet. Prototype content cannot leak in.
    return out

def render(entry:dict, *, palette='COASTAL_SEAFOAM_CORAL', rarity='common', presentation='mixed')->dict:
    provenance=entry['provenance']
    if provenance=='VANILLA': return render_vanilla(entry['kind'],entry['sourceIndex'],palette)
    if provenance=='MOD_AUTHOR' and entry['kind']=='hat':
        result=render_mod_author_hat(entry['family'],rarity,presentation)
        result['provenance']='MOD_AUTHOR'; return result
    raise ValueError(f'unsupported production entry {entry}')
