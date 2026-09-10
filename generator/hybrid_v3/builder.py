"""Build one deterministic, coordinate-free canonical garment model."""

from __future__ import annotations

import hashlib
import json
import random
from typing import Any

from .data import V3DataRepository
from .seeding import SeedBook


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _choose(values: list[Any], seed: int) -> Any:
    if not values:
        raise ValueError("cannot choose from an empty list")
    return values[random.Random(seed).randrange(len(values))]


def _bounded(preferred: Any, allowed: list[Any]) -> Any:
    if preferred in allowed:
        return preferred
    for fallback in ("regular", "normal", "medium", "low", "none", "fitted", "cropped", "relaxed", "broad", "narrow"):
        if fallback in allowed:
            return fallback
    return allowed[0]


class CanonicalGarmentBuilder:
    """Resolve architecture, intent, fit, components, and material into one graph."""

    def __init__(self, repository: V3DataRepository | None = None):
        self.repository = repository or V3DataRepository()

    def build(
        self,
        *,
        family: str,
        design_intent: str,
        fit_profile: str,
        root_seed: int,
        rarity_budget: str = "PHASE1_RECIPE_ONLY",
        material: str | None = None,
    ) -> dict[str, Any]:
        repo = self.repository
        if family not in repo.architectures:
            raise KeyError(f"unknown V3 family: {family}")
        if design_intent not in repo.intents:
            raise KeyError(f"unknown design intent: {design_intent}")
        if fit_profile not in repo.fit_profiles:
            raise KeyError(f"unknown fit profile: {fit_profile}")

        architecture = repo.resolve_architecture(family)
        intent = repo.intents[design_intent]
        fit = repo.fit_profiles[fit_profile]
        if family not in intent["families"]:
            raise ValueError(f"intent {design_intent} is not compatible with {family}")

        seeds = SeedBook(int(root_seed))
        seeds.for_stage("rarity", rarity_budget)
        seeds.for_stage("family", family)
        seeds.for_stage("architecture", family, architecture["version"])
        seeds.for_stage("design_intent", design_intent)
        seeds.for_stage("fit", fit_profile)

        ranges = architecture["fitRanges"]
        tendencies = fit["tendencies"]
        resolved_fit = {
            "shoulder": _bounded(tendencies["shoulder"], ranges["shoulder"]),
            "waistSuppression": _bounded(tendencies["waistSuppression"], ranges["waistSuppression"]),
            "bodyLength": _bounded(tendencies["bodyLength"], ranges["bodyLength"]),
            "volume": _bounded(tendencies["volume"], ranges["volume"]),
        }

        material_policy = repo.material_families[family]
        material_seed = seeds.for_stage("material", family)
        selected_material = material or intent.get("materialPreference") or material_policy.get("default")
        if selected_material is None:
            selected_material = _choose(material_policy["allowed"], material_seed)

        slot_by_name = {slot["slot"]: slot for slot in architecture["componentSlots"]}
        components: list[dict[str, Any]] = []
        preferences = intent.get("componentPreferences", {})
        optional_slots = set(intent.get("optionalSlots", []))
        parameter_tendencies = intent.get("parameterTendencies", {})

        for slot_name, slot in slot_by_name.items():
            if not slot.get("required", False) and slot_name not in optional_slots:
                continue
            selection_seed = seeds.for_stage("component_selection", family, slot_name)
            preferred_definition = preferences.get(slot_name)
            candidates = slot["candidates"]
            definition_id = preferred_definition if preferred_definition in candidates else _choose(candidates, selection_seed)
            definition = repo.components[definition_id]

            parameters: dict[str, Any] = {}
            for key, allowed in definition.get("parameterRanges", {}).items():
                parameter_seed = seeds.for_stage("component_parameter", slot_name, key)
                parameters[key] = _choose(allowed, parameter_seed)
            parameters.update(slot.get("parameters", {}))
            parameters.update(parameter_tendencies.get(slot_name, {}))
            if slot_name == "body":
                parameters.update(
                    {
                        "shoulder": resolved_fit["shoulder"],
                        "waistSuppression": resolved_fit["waistSuppression"],
                        "length": resolved_fit["bodyLength"],
                        "volume": resolved_fit["volume"],
                        "fit": "fitted" if resolved_fit["volume"] == "fitted" else "regular",
                    }
                )

            continuity = definition["continuityBehavior"]
            continuity_group = f"{family}:{slot_name}" if "WRAP" in continuity else None
            components.append(
                {
                    "instanceId": slot_name,
                    "definitionId": definition_id,
                    "componentType": definition["componentType"],
                    "parent": slot.get("parentSlot"),
                    "attachmentRegion": definition["parentAttachmentRegion"],
                    "parameters": parameters,
                    "directionalVisibilityPolicy": dict(definition["directionalVisibility"]),
                    "continuityBehavior": continuity,
                    "continuityGroup": continuity_group,
                    "pixelPriority": definition["pixelPriority"],
                    "silhouetteImpact": definition["silhouetteImpact"],
                    "mandatory": bool(slot.get("required", False)),
                }
            )

        relations = []
        for component in components:
            if component["parent"] is not None:
                relations.append(
                    {
                        "type": "ATTACHED_TO",
                        "from": component["instanceId"],
                        "to": component["parent"],
                        "region": component["attachmentRegion"],
                    }
                )
            if component["continuityGroup"]:
                relations.append(
                    {
                        "type": "WRAPS_WITH",
                        "from": component["instanceId"],
                        "group": component["continuityGroup"],
                    }
                )

        architecture_record = {
            "id": family,
            "version": architecture["version"],
            "digest": _digest(architecture),
            "inheritanceChain": architecture["inheritanceChain"],
            "mandatoryIdentitySlots": architecture["mandatoryIdentitySlots"],
        }
        data_digests = {
            key: value
            for key, value in repo.digests.items()
            if key not in {"canonicalSchema", "recipeSchema"}
        }
        provenance = seeds.provenance()
        provenance.update(
            {
                "generator": "generator.hybrid_v3.builder.CanonicalGarmentBuilder",
                "generatorVersion": "1.0.0-phase1",
                "dataDigests": data_digests,
                "rendererInvoked": False,
            }
        )

        return {
            "schemaVersion": "3.0.0",
            "identity": {
                "id": f"V3-{family}-{design_intent}-{fit_profile}-{root_seed}",
                "family": family,
            },
            "rarityBudget": {"id": rarity_budget, "mode": "INTERFACE_ONLY_NO_BALANCE_CHANGE"},
            "architecture": architecture_record,
            "designIntent": {
                "id": design_intent,
                "version": intent["version"],
                "dominant": intent["dominant"],
                "supporting": intent["supporting"],
                "avoid": intent.get("avoid", []),
            },
            "fit": {
                "profile": fit_profile,
                "version": fit["version"],
                "resolvedProportions": resolved_fit,
            },
            "material": {
                "id": selected_material,
                "behaviorSource": "specs/palettes/material_color_behavior.json",
                "temporaryMapping": material_policy.get("temporaryMapping"),
            },
            "components": components,
            "relations": relations,
            "rearStructure": dict(architecture["rearStructure"]),
            "surfaceIntent": dict(intent["surfaceIntent"]),
            "runtimeEnvelope": dict(architecture["runtimeEnvelope"]),
            "provenance": provenance,
        }
