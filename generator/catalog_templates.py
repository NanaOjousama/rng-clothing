"""Registry API for source-catalog construction templates and family taste policies."""
from __future__ import annotations
import json
from pathlib import Path
from generator.taste_policy import evaluate_recipe
from v5.source.template_transfer import load_contract, verify_contract, decision

ROOT=Path(__file__).resolve().parents[1]
TEMPLATES=ROOT/'generator/data/templates/index.json'
TASTE=ROOT/'generator/data/taste_policy_registry.json'
TRANSFER=ROOT/'source_catalog/SOURCE_TRANSFER_LIBRARY.json'


def template_registry():
    return json.loads(TEMPLATES.read_text())


def taste_registry():
    return json.loads(TASTE.read_text())


def list_families(*, include_manual=True):
    t=template_registry()['templates']
    rows=[]
    for tid,entry in sorted(t.items()):
        if not include_manual and entry.get('origin')!='catalog-promoter':
            continue
        rows.append({'template':tid,**entry})
    return rows


def load_family(family):
    treg=taste_registry()['families']
    if family not in treg or treg[family].get('status')!='ACTIVE':
        raise KeyError(f'unregistered family {family!r}')
    p=ROOT/treg[family]['policyFile']
    return json.loads(p.read_text())


def load_template_for_family(family):
    policy=load_family(family)
    tid=policy['template']
    entry=template_registry()['templates'][tid]
    contract=load_contract(ROOT/entry['contract'])
    verify_contract(contract)
    return contract


def evaluate_family_recipe(family,rarity,recipe):
    return evaluate_recipe(recipe,rarity,load_family(family))


def transfer_library():
    return json.loads(TRANSFER.read_text())


def source_family_entry(family):
    contract=load_template_for_family(family)
    ident=contract.source_identity
    for entry in transfer_library()['families']:
        if entry.get('identity')==ident:
            return entry
    return None


def compatible_donors(family, *, kinds=None):
    contract=load_template_for_family(family)
    allowed=[]; denied=[]
    kindset=set(kinds) if kinds else None
    for part in transfer_library()['parts']:
        if kindset and part.get('partKind') not in kindset:
            continue
        verdict=decision(part,contract)
        item={'part':part,'decision':verdict}
        (allowed if verdict['decision']=='ALLOW' else denied).append(item)
    return {'family':family,'template':contract.id,'allowed':allowed,'denied':denied}
