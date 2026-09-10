"""Versioned V3 data loading with deterministic content digests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "specs/hybrid_garment_compiler/v3"

FILES = {
    "manifest": "manifest.json",
    "canonicalSchema": "canonical_garment_model.schema.json",
    "recipeSchema": "generated_recipe.schema.json",
    "architectures": "architecture_definitions.json",
    "components": "component_definitions.json",
    "compatibility": "component_compatibility.json",
    "designIntents": "design_intents.json",
    "fitProfiles": "fit_profiles.json",
    "materials": "family_material_compatibility.json",
    "projection": "projection_contract.json",
    "carriers": "carrier_capabilities.json",
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class V3DataRepository:
    def __init__(self, root: Path = DATA_ROOT):
        self.root = root
        self.documents = {key: _load(root / name) for key, name in FILES.items()}
        self.digests = {key: file_digest(root / name) for key, name in FILES.items()}
        self.architectures = {item["id"]: item for item in self.documents["architectures"]["architectures"]}
        self.components = {item["id"]: item for item in self.documents["components"]["components"]}
        self.intents = {item["id"]: item for item in self.documents["designIntents"]["intents"]}
        self.fit_profiles = {item["id"]: item for item in self.documents["fitProfiles"]["profiles"]}
        self.material_families = self.documents["materials"]["families"]
        self.carriers = {item["id"]: item for item in self.documents["carriers"]["carriers"]}

    def resolve_architecture(self, family: str, stack: tuple[str, ...] = ()) -> dict[str, Any]:
        if family in stack:
            raise ValueError(f"architecture inheritance cycle: {' -> '.join((*stack, family))}")
        architecture = self.architectures[family]
        parent = architecture.get("inherits")
        slots: dict[str, Any] = {}
        chain: list[str] = []
        if parent:
            resolved = self.resolve_architecture(parent, (*stack, family))
            slots.update({slot["slot"]: dict(slot) for slot in resolved["componentSlots"]})
            chain.extend(resolved["inheritanceChain"])
        for removed in architecture.get("removeSlots", []):
            slots.pop(removed, None)
        for slot in architecture.get("componentSlots", []):
            slots[slot["slot"]] = dict(slot)
        return {
            **architecture,
            "componentSlots": list(slots.values()),
            "inheritanceChain": [*chain, family],
        }
