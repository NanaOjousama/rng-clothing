"""Canonical physical and projection validation for Hybrid V3 Phase 1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .data import V3DataRepository
from .projector import DIRECTIONS


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


class PhysicalValidator:
    def __init__(self, repository: V3DataRepository | None = None):
        self.repository = repository or V3DataRepository()

    def validate(self, canonical: dict[str, Any]) -> dict[str, Any]:
        issues: list[ValidationIssue] = []
        repo = self.repository
        family = canonical.get("identity", {}).get("family")
        if family not in repo.architectures:
            issues.append(ValidationIssue("UNKNOWN_FAMILY", "identity.family", str(family)))
            return self._result(issues)

        architecture = repo.resolve_architecture(family)
        family_rule = repo.documents["compatibility"]["familyRules"][family]
        components = canonical.get("components", [])
        by_id: dict[str, dict[str, Any]] = {}
        for index, component in enumerate(components):
            instance = component.get("instanceId")
            if instance in by_id:
                issues.append(ValidationIssue("DUPLICATE_INSTANCE", f"components[{index}]", str(instance)))
            by_id[instance] = component

        self._validate_parent_graph(by_id, issues)
        present_types = {component.get("componentType") for component in components}
        for required in family_rule["requiredTypes"]:
            if required not in present_types:
                issues.append(ValidationIssue("MISSING_REQUIRED_TYPE", "components", required))
        for forbidden in family_rule["forbiddenTypes"]:
            if forbidden in present_types:
                issues.append(ValidationIssue("FORBIDDEN_COMPONENT_TYPE", "components", forbidden))

        mandatory = set(architecture["mandatoryIdentitySlots"])
        missing_slots = mandatory - set(by_id)
        for slot in sorted(missing_slots):
            issues.append(ValidationIssue("MANDATORY_IDENTITY_LOSS", "components", slot))

        for index, component in enumerate(components):
            path = f"components[{index}]"
            definition_id = component.get("definitionId")
            if definition_id not in repo.components:
                issues.append(ValidationIssue("UNKNOWN_COMPONENT", path, str(definition_id)))
                continue
            definition = repo.components[definition_id]
            if component.get("componentType") != definition["componentType"]:
                issues.append(ValidationIssue("COMPONENT_TYPE_MISMATCH", path, definition_id))
            if family not in definition["compatibleFamilies"]:
                issues.append(ValidationIssue("COMPONENT_OUTSIDE_ALLOWED_FAMILY", path, definition_id))
            if component.get("attachmentRegion") != definition["parentAttachmentRegion"]:
                issues.append(ValidationIssue("ATTACHMENT_REGION_MISMATCH", f"{path}.attachmentRegion", str(component.get("attachmentRegion"))))
            material = canonical.get("material", {}).get("id")
            if definition.get("compatibleMaterials") and material not in definition["compatibleMaterials"]:
                issues.append(ValidationIssue("COMPONENT_MATERIAL_INCOMPATIBLE", path, f"{definition_id}/{material}"))
            parent_id = component.get("parent")
            if definition["componentType"] == "BODY":
                if parent_id is not None:
                    issues.append(ValidationIssue("ROOT_HAS_PARENT", path, str(parent_id)))
            elif parent_id not in by_id:
                issues.append(ValidationIssue("UNATTACHED_COMPONENT", path, str(parent_id)))
            else:
                parent_def = repo.components.get(by_id[parent_id].get("definitionId"), {})
                provided = parent_def.get("providesAttachmentRegions", [])
                region = component.get("attachmentRegion")
                if provided and region not in provided:
                    issues.append(ValidationIssue("INVALID_PARENT_ATTACHMENT", path, f"{parent_id} does not provide {region}"))
            for key, value in component.get("parameters", {}).items():
                allowed = definition.get("parameterRanges", {}).get(key)
                if allowed is not None and value not in allowed:
                    issues.append(ValidationIssue("PARAMETER_OUT_OF_RANGE", f"{path}.parameters.{key}", str(value)))
            policy = component.get("directionalVisibilityPolicy", {})
            for direction in DIRECTIONS:
                expected = definition["directionalVisibility"][direction]
                actual = policy.get(direction)
                if actual != expected:
                    issues.append(ValidationIssue("ILLEGAL_VISIBILITY_OVERRIDE", f"{path}.directionalVisibilityPolicy.{direction}", f"{actual} != {expected}"))
            if "WRAP" in definition["continuityBehavior"] and not component.get("continuityGroup"):
                issues.append(ValidationIssue("MISSING_WRAP_CONTINUITY", path, definition_id))

        material_policy = repo.material_families[family]
        material = canonical.get("material", {}).get("id")
        if material not in material_policy["allowed"] or material in material_policy.get("forbidden", []):
            issues.append(ValidationIssue("MATERIAL_INCOMPATIBLE", "material.id", str(material)))

        resolved_fit = canonical.get("fit", {}).get("resolvedProportions", {})
        for key, allowed in architecture["fitRanges"].items():
            value = resolved_fit.get(key)
            if value not in allowed:
                issues.append(ValidationIssue("FIT_OUT_OF_RANGE", f"fit.resolvedProportions.{key}", str(value)))

        self._validate_relationships(family, by_id, canonical, issues)
        envelope = canonical.get("runtimeEnvelope", {})
        if not envelope.get("safeUpperBodyOnly", False) or envelope.get("legOverlapAllowed", True):
            issues.append(ValidationIssue("RUNTIME_ENVELOPE_VIOLATION", "runtimeEnvelope", "unsafe lower geometry"))
        if envelope.get("customSleevesAllowed", True):
            issues.append(ValidationIssue("CUSTOM_SLEEVES_FORBIDDEN", "runtimeEnvelope.customSleevesAllowed", "must be false"))
        return self._result(issues)

    def validate_projections(self, canonical: dict[str, Any], projections: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        issues: list[ValidationIssue] = []
        expected_ids = {component["instanceId"] for component in canonical["components"]}
        for direction in DIRECTIONS:
            items = projections.get(direction, [])
            actual_ids = {item.get("componentInstance") for item in items}
            if actual_ids != expected_ids:
                issues.append(ValidationIssue("PROJECTION_COMPONENT_DRIFT", direction, f"{sorted(actual_ids)} != {sorted(expected_ids)}"))
            for item in items:
                component = next(c for c in canonical["components"] if c["instanceId"] == item["componentInstance"])
                expected = component["directionalVisibilityPolicy"][direction]
                if item.get("visibility") != expected:
                    issues.append(ValidationIssue("PROJECTION_VISIBILITY_DRIFT", f"{direction}.{item['componentInstance']}", str(item.get("visibility"))))
        return self._result(issues)

    def _validate_parent_graph(self, by_id: dict[str, dict[str, Any]], issues: list[ValidationIssue]) -> None:
        for start in by_id:
            seen: set[str] = set()
            current: str | None = start
            while current is not None and current in by_id:
                if current in seen:
                    issues.append(ValidationIssue("COMPONENT_GRAPH_CYCLE", f"components.{start}", current))
                    break
                seen.add(current)
                current = by_id[current].get("parent")

    def _validate_relationships(self, family: str, by_id: dict[str, dict[str, Any]], canonical: dict[str, Any], issues: list[ValidationIssue]) -> None:
        types = {item["componentType"] for item in by_id.values()}
        rear = canonical.get("rearStructure", {})
        if "PLACKET" in types and "OPENING" not in types:
            issues.append(ValidationIssue("PLACKET_WITHOUT_OPENING", "components", family))
        if "LAPEL" in types and not {"COLLAR", "OPENING"}.issubset(types):
            issues.append(ValidationIssue("LAPEL_WITHOUT_COLLAR_OPENING", "components", family))
        if "ARMHOLE" in types and "SLEEVE" in types:
            issues.append(ValidationIssue("SLEEVE_ARMHOLE_CONTRADICTION", "components", family))
        if family == "POLO_SHIRT":
            placket = by_id.get("placket")
            if placket and (placket["parameters"].get("length") != "short" or placket["parameters"].get("end") != "upper_chest"):
                issues.append(ValidationIssue("POLO_PLACKET_NOT_SHORT", "components.placket", str(placket["parameters"])))
            if rear.get("rearOpening") is not False:
                issues.append(ValidationIssue("POLO_REAR_OPENING_FORBIDDEN", "rearStructure.rearOpening", str(rear.get("rearOpening"))))
        if family == "SWEATER_VEST" and ("SLEEVE" in types or "ARMHOLE" not in types):
            issues.append(ValidationIssue("SWEATER_VEST_ARMHOLE_INVALID", "components", "vest requires armhole and forbids sleeve"))
        if family == "CARDIGAN" and "LAPEL" in types:
            issues.append(ValidationIssue("CARDIGAN_HARD_LAPEL", "components", "lapel forbidden"))
        if family == "BLAZER" and "LAPEL" not in types:
            issues.append(ValidationIssue("BLAZER_LAPEL_MISSING", "components", "lapel required"))
        if family == "SAILOR_TOP":
            rear_component = by_id.get("rear")
            if not rear_component or rear_component.get("definitionId") != "REAR_PANEL_SAILOR_SQUARE":
                issues.append(ValidationIssue("SAILOR_REAR_PANEL_MISSING", "components.rear", "mandatory sailor rear panel"))
        if rear.get("rearOpening") is True:
            issues.append(ValidationIssue("IMPOSSIBLE_REAR_STRUCTURE", "rearStructure.rearOpening", family))

    @staticmethod
    def _result(issues: list[ValidationIssue]) -> dict[str, Any]:
        return {"status": "PASS" if not issues else "FAIL", "issues": [issue.as_dict() for issue in issues]}
