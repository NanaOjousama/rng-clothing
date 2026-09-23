"""Generator-wide rarity/taste policy evaluator.

The engine is family-agnostic. Each garment family supplies its own
rarityRules + tastePolicy data, while all generator paths use this evaluator.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RARITY_RANK = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3}


@dataclass(frozen=True)
class TasteReport:
    valid: bool
    rarity: str
    complexity: int
    budget_min: int
    budget_max: int
    active_channels: tuple[str, ...]
    primary: str | None
    secondary: tuple[str, ...]
    accents: tuple[str, ...]
    errors: tuple[str, ...]


def _matches(recipe: dict[str, Any], cond: dict[str, Any]) -> bool:
    for axis, expected in cond.items():
        actual = recipe.get(axis)
        if isinstance(expected, list):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True


def _cost(policy: dict[str, Any], axis: str, value: Any) -> int:
    table = policy["featureCosts"].get(axis, {})
    if value in table:
        return int(table[value])
    if "*" in table and value not in (None, "none"):
        return int(table["*"])
    return 0


def _feature_id(axis: str, value: Any) -> str:
    return f"{axis}.{value}"


def _channel_map(policy: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for channel, axes in policy["channels"].items():
        for axis in axes:
            out[axis] = channel
    return out


def _impact(policy: dict[str, Any], fid: str) -> int:
    impact = policy["impact"]
    if fid in impact.get("high", []):
        return 3
    if fid in impact.get("medium", []):
        return 2
    if any(fid.startswith(prefix) for prefix in impact.get("mediumPrefixes", [])):
        return 2
    return 1
def _rarity_floor_errors(
    recipe: dict[str, Any], rarity: str, family_policy: dict[str, Any]
) -> list[str]:
    rules = family_policy["rarityRules"][rarity]
    floors = family_policy["rarityRules"].get("minimumRarityByFeature", {})
    errors: list[str] = []

    for axis, expected in rules.get("forced", {}).items():
        if recipe.get(axis) != expected:
            errors.append(f"rarity_forces:{axis}={expected}")

    field_axis = {
        "allowedPatterns": "pattern",
        "allowedTrimAccents": "trimAccent",
        "allowedKnitStructures": "knitStructure",
        "allowedBandTypes": "bandType",
        "allowedMicroAccents": "microAccent",
    }
    for field, axis in field_axis.items():
        allowed = rules.get(field)
        if allowed is not None and recipe.get(axis) not in allowed:
            errors.append(f"rarity_disallows:{axis}={recipe.get(axis)}")
    for axis, allowed in rules.get('allowedValues', {}).items():
        if recipe.get(axis) not in allowed:
            errors.append(f"rarity_disallows:{axis}={recipe.get(axis)}")

    rank = RARITY_RANK[rarity]
    motif_floor = floors.get("motif_non_none")
    if motif_floor and recipe.get("motif") not in (None, "none"):
        if rank < RARITY_RANK[motif_floor]:
            errors.append("rarity_floor:motif")
    carrier_floor = floors.get("carrierStyle_non_none")
    if carrier_floor and recipe.get("carrierStyle") not in (None, "none"):
        if rank < RARITY_RANK[carrier_floor]:
            errors.append("rarity_floor:carrierStyle")

    localized = floors.get("localized_microAccent")
    if isinstance(localized, list) and localized:
        local_floor, *values = localized
        if recipe.get("microAccent") in values and rank < RARITY_RANK[local_floor]:
            errors.append("rarity_floor:localized_microAccent")

    pattern = recipe.get("pattern")
    if pattern in floors and isinstance(floors[pattern], str):
        if rank < RARITY_RANK[floors[pattern]]:
            errors.append(f"rarity_floor:pattern.{pattern}")
    for rule in family_policy['rarityRules'].get('minimumRarityRules', []):
        axis=rule['axis']; value=recipe.get(axis); active=False
        if rule.get('nonNone'):
            active=value not in (None,'none')
        if 'values' in rule:
            active=value in rule['values']
        if active and rank < RARITY_RANK[rule['minimum']]:
            errors.append(f"rarity_floor:{axis}.{value}")

    distinctive = rules.get("distinctiveFeatureRule", {}).get("requireAny", {})
    if distinctive and not any(recipe.get(a) in values for a, values in distinctive.items()):
        errors.append("rarity_requires_distinctive_feature")
    return errors
def _conflict_errors(recipe: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for rule in policy.get("strongConflictRules", []):
        if not _matches(recipe, rule.get("when", {})):
            continue
        for axis, blocked in rule.get("disallow", {}).items():
            if recipe.get(axis) in blocked:
                errors.append(f"conflict:{rule['id']}")
                break
    return errors


def _semantic_errors(recipe: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for rule in policy.get("semanticRequirements", []):
        axis = rule["axis"]
        value = recipe.get(axis)
        active = False
        if rule.get("whenNonNone"):
            active = value not in (None, "none")
        if "whenValues" in rule:
            active = value in rule["whenValues"]
        if not active:
            continue
        for required in rule.get("requiresNonNone", []):
            if recipe.get(required) in (None, "none"):
                errors.append(f"semantic:{rule['id']}:{required}")
    return errors


def evaluate_recipe(
    recipe: dict[str, Any], rarity: str, family_policy: dict[str, Any]
) -> TasteReport:
    rarity = rarity.lower()
    if rarity not in RARITY_RANK:
        raise ValueError(f"unsupported rarity {rarity!r}")

    policy = family_policy["tastePolicy"]
    budget = policy["complexityBudgets"][rarity]
    errors = _rarity_floor_errors(recipe, rarity, family_policy)
    errors.extend(_conflict_errors(recipe, policy))
    errors.extend(_semantic_errors(recipe, policy))

    channel_for = _channel_map(policy)
    rows: list[tuple[str, str, int, int]] = []
    complexity = 0
    for axis in policy["featureCosts"]:
        value = recipe.get(axis)
        cost = _cost(policy, axis, value)
        complexity += cost
        if cost <= 0:
            continue
        fid = _feature_id(axis, value)
        rows.append((fid, channel_for.get(axis, "CONSTRUCTION"), cost, _impact(policy, fid)))

    if not (budget["min"] <= complexity <= budget["max"]):
        errors.append(f"complexity_budget:{complexity} not in {budget['min']}..{budget['max']}")

    active_channels = sorted({channel for _, channel, _, _ in rows if channel != "CONSTRUCTION"})
    if len(active_channels) > budget["maxVisualChannels"]:
        errors.append(f"visual_channels:{len(active_channels)}>{budget['maxVisualChannels']}")
    channel_priority = {
        name: i for i, name in enumerate(policy.get("dominantPriority", []))
    }
    role_rows = [row for row in rows if row[1] != "CONSTRUCTION"]
    ranked = sorted(
        role_rows,
        key=lambda row: (
            -row[3],
            channel_priority.get(row[1], 999),
            -row[2],
            row[0],
        ),
    )

    primary = ranked[0][0] if ranked else None
    secondary = tuple(row[0] for row in ranked[1:] if row[3] >= 2)
    accents = tuple(row[0] for row in ranked[1:] if row[3] == 1)

    if len(secondary) > budget["maxSecondary"]:
        errors.append(f"secondary_features:{len(secondary)}>{budget['maxSecondary']}")
    if len(accents) > budget["maxAccents"]:
        errors.append(f"accent_features:{len(accents)}>{budget['maxAccents']}")

    high_rows = [row for row in ranked if row[3] >= 3]
    if len(high_rows) > 1:
        high_channels = {row[1] for row in high_rows}
        if len(high_channels) > 1:
            errors.append("competing_dominant_features")

    for channel in active_channels:
        strong = [row for row in rows if row[1] == channel and row[3] >= 2]
        if len(strong) > 1 and channel != "GRAPHIC":
            errors.append(f"multiple_strong_features_in_channel:{channel}")

    return TasteReport(
        valid=not errors,
        rarity=rarity,
        complexity=complexity,
        budget_min=int(budget["min"]),
        budget_max=int(budget["max"]),
        active_channels=tuple(active_channels),
        primary=primary,
        secondary=secondary,
        accents=accents,
        errors=tuple(dict.fromkeys(errors)),
    )


def report_dict(report: TasteReport) -> dict[str, Any]:
    return {
        "valid": report.valid,
        "rarity": report.rarity,
        "complexity": report.complexity,
        "budget": [report.budget_min, report.budget_max],
        "activeChannels": list(report.active_channels),
        "primary": report.primary,
        "secondary": list(report.secondary),
        "accents": list(report.accents),
        "errors": list(report.errors),
    }


def load_registry(root_path):
    from pathlib import Path
    import json
    root = Path(root_path)
    return json.loads((root / 'generator/data/taste_policy_registry.json').read_text())


def load_registered_family_policy(root_path, family: str):
    from pathlib import Path
    import json
    root = Path(root_path)
    registry = load_registry(root)
    entry = registry.get('families', {}).get(family)
    if not entry or entry.get('status') != 'ACTIVE':
        raise ValueError(f'unregistered taste-policy family {family!r}')
    return json.loads((root / entry['policyFile']).read_text())


def evaluate_registered_recipe(root_path, family: str, recipe, rarity: str) -> TasteReport:
    return evaluate_recipe(recipe, rarity, load_registered_family_policy(root_path, family))
