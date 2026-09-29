"""Production content-source filtering for RNG Clothing."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'generator/data/content_source_policy.json'

def load_policy()->dict:
    return json.loads(POLICY.read_text())

def normalize_mode(mode:str|None)->str:
    p=load_policy(); mode=mode or p['defaultMode']
    if mode in p['modes']: return mode
    alias=p.get('aliases',{}).get(str(mode).lower())
    if alias: return alias
    raise ValueError(f'unknown content source mode {mode!r}')

def allowed_sources(mode:str|None)->tuple[str,...]:
    p=load_policy(); key=normalize_mode(mode)
    return tuple(p['modes'][key])

def source_allowed(mode:str|None,provenance:str)->bool:
    return provenance in allowed_sources(mode)
