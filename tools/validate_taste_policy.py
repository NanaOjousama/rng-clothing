#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from generator.taste_policy import evaluate_recipe, evaluate_registered_recipe, load_registry

REG=ROOT/'generator/data/taste_policy_registry.json'
SLOUCH=ROOT/'generator/data/headwear/slouch_beanie_roll_matrix.json'


def synthetic_policy():
    return {
      "rarityRules":{
        "common":{"forced":{"motif":"none"}},
        "uncommon":{"forced":{"motif":"none"}},
        "rare":{},
        "epic":{},
        "minimumRarityByFeature":{"motif_non_none":"rare"}
      },
      "tastePolicy":{
        "complexityBudgets":{
          "common":{"min":0,"max":1,"maxVisualChannels":1,"maxSecondary":0,"maxAccents":1},
          "uncommon":{"min":1,"max":2,"maxVisualChannels":2,"maxSecondary":1,"maxAccents":1},
          "rare":{"min":2,"max":4,"maxVisualChannels":3,"maxSecondary":1,"maxAccents":2},
          "epic":{"min":3,"max":5,"maxVisualChannels":3,"maxSecondary":2,"maxAccents":2}
        },
        "channels":{"PATTERN":["pattern"],"GRAPHIC":["motif"],"ATTACHMENT":["attachment"]},
        "featureCosts":{
          "pattern":{"solid":0,"stripe":1,"busy":2},
          "motif":{"none":0,"*":2},
          "attachment":{"none":0,"pom":1}
        },
        "impact":{"high":["pattern.busy"],"mediumPrefixes":["motif."],"medium":["pattern.stripe"]},
        "dominantPriority":["GRAPHIC","PATTERN","ATTACHMENT"],
        "strongConflictRules":[
          {"id":"busy_vs_motif","when":{"pattern":"busy"},"disallow":{"motif":["star"]}}
        ],
        "roleRules":{"BASE":"","PRIMARY":"","SECONDARY":"","ACCENT":"","rule":""}
      }
    }
def main():
    registry=load_registry(ROOT)
    assert registry["engine"]=="generator/taste_policy.py"
    assert registry["unregisteredActiveTemplateFamilyAction"]=="REJECT"
    templates=json.loads((ROOT/registry["templateRegistry"]).read_text())
    active_families=set()
    for entry in templates["templates"].values():
        if entry.get("status") in {"QC_READY","ACTIVE","PRODUCTION"}:
            active_families.add(entry["family"])
    registered=set()
    for name,entry in registry["families"].items():
        if entry.get("status")=="ACTIVE":
            registered.add(name)
    assert not (active_families-registered)
    assert "slouch_beanie" in registered

    # Generic engine proof: no slouch-specific field names required.
    generic=synthetic_policy()
    assert evaluate_recipe(
        {"pattern":"solid","motif":"none","attachment":"none"},
        "common", generic
    ).valid
    assert evaluate_recipe(
        {"pattern":"stripe","motif":"none","attachment":"none"},
        "uncommon", generic
    ).valid
    bad_motif=evaluate_recipe(
        {"pattern":"stripe","motif":"star","attachment":"none"},
        "uncommon", generic
    )
    assert not bad_motif.valid
    assert any("rarity" in e for e in bad_motif.errors)
    busy=evaluate_recipe(
        {"pattern":"busy","motif":"star","attachment":"none"},
        "rare", generic
    )
    assert not busy.valid
    assert "conflict:busy_vs_motif" in busy.errors

    slouch=json.loads(SLOUCH.read_text())
    # Common: clean, subtle, valid.
    common={
      "slouchDepth":"medium","bandType":"standard_cuff","drapeDirection":"back_center",
      "crownShape":"rounded","openingFit":"normal","knitStructure":"fine_rib",
      "pattern":"solid","trimAccent":"none","microAccent":"none","motif":"none",
      "carrierStyle":"none","decorationStyle":"none","motifPlacement":"none",
      "attachment":"none","hardwareAccent":"none"
    }
    rc=evaluate_recipe(common,"common",slouch)
    assert rc.valid, rc.errors

    # Uncommon stripe = valid, but motif is not.
    uncommon={**common,"pattern":"single_stripe"}
    ru=evaluate_recipe(uncommon,"uncommon",slouch)
    assert ru.valid, ru.errors
    uncommon_bad={**uncommon,"motif":"snowflake","decorationStyle":"direct_stitch","motifPlacement":"cuff_front_center"}
    assert not evaluate_recipe(uncommon_bad,"uncommon",slouch).valid

    incomplete_patch={
      **common,
      "pattern":"single_stripe",
      "carrierStyle":"patch_square",
      "motifPlacement":"none",
    }
    incomplete=evaluate_recipe(incomplete_patch,"rare",slouch)
    assert not incomplete.valid
    assert any(e.startswith("semantic:carrier_needs_placement") for e in incomplete.errors)
    rare={
      **common,
      "knitStructure":"cable",
      "motif":"leaf",
      "decorationStyle":"direct_stitch",
      "motifPlacement":"cuff_front_center",
    }
    rr=evaluate_recipe(rare,"rare",slouch)
    assert rr.valid, rr.errors
    assert rr.primary is not None

    # Chaotic Epic: multiple competing strong systems must be rejected.
    chaotic={
      **common,
      "slouchDepth":"extra",
      "knitStructure":"cable",
      "pattern":"plaid_woven",
      "trimAccent":"double_trim_lines",
      "microAccent":"side_bow_small",
      "motif":"flower_cluster_small",
      "carrierStyle":"patch_rect",
      "decorationStyle":"woven_patch",
      "motifPlacement":"cuff_front_center",
      "attachment":"pom_large",
      "hardwareAccent":"button_accent",
    }
    re=evaluate_recipe(chaotic,"epic",slouch)
    assert not re.valid
    assert re.complexity > re.budget_max or any(e.startswith("conflict:") for e in re.errors)

    print("PASS generator-wide taste policy")
    print("generic engine: PASS")
    print("slouch integration: PASS")
    print("common",rc.complexity,rc.primary,rc.active_channels)
    print("uncommon",ru.complexity,ru.primary,ru.active_channels)
    print("rare",rr.complexity,rr.primary,rr.active_channels)
    print("chaotic epic rejected:",", ".join(re.errors))


if __name__=="__main__":
    main()
