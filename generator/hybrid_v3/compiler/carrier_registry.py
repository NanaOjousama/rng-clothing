"""Strict family-to-capability carrier selection for Hybrid V3."""

from __future__ import annotations

import copy
from typing import Any

from generator.renderers.fashionsense.upper_v5b import render_fs_v5b
from generator.v5b.engine import generate_v5b_benchmark
from generator.hybrid_v3.data import V3DataRepository


class UnsupportedCarrierError(ValueError):
    pass


class CarrierRegistry:
    def __init__(self, repository: V3DataRepository | None = None):
        self.repository = repository or V3DataRepository()

    def select(self, canonical: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], Any]:
        family = canonical["identity"]["family"]
        matches = [item for item in self.repository.carriers.values() if family in item["families"]]
        if len(matches) != 1:
            raise UnsupportedCarrierError(f"{family}: expected one carrier, found {len(matches)}")
        capability = matches[0]
        component_types = {item["componentType"] for item in canonical["components"]}
        unsupported = component_types - set(capability["supportedComponents"])
        if unsupported:
            raise UnsupportedCarrierError(f"{family}: carrier {capability['id']} lacks {sorted(unsupported)}")
        recipes = generate_v5b_benchmark()["recipes"]
        recipe = copy.deepcopy(recipes[capability["benchmarkRecipeIndex"]])
        recipe["id"] = f"hybrid-v3-phase2-{family.lower()}"
        raw = render_fs_v5b(recipe)
        return capability, recipe, raw
