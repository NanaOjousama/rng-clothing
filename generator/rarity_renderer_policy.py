"""Renderer-capability routing for the Common/Uncommon/Rare architecture.

This module selects a backend class from semantic rarity. It deliberately does
not render pixels or add renderer-specific fields to garment recipes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "generator" / "data" / "rarity_renderer_architecture.json"


@dataclass(frozen=True)
class RendererRoute:
    rarity: str
    renderer_class: str
    backend: str
    maximum_layers: int | None
    allowed_components: tuple[str, ...]
    supports_state_behavior: bool


@dataclass(frozen=True)
class RouteValidation:
    valid: bool
    errors: tuple[str, ...]


def load_rarity_renderer_policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def select_renderer_route(rarity: str, policy: dict | None = None) -> RendererRoute:
    policy = policy or load_rarity_renderer_policy()
    if rarity not in policy["routes"]:
        raise ValueError(f"unsupported active rarity {rarity!r}")
    raw = policy["routes"][rarity]
    return RendererRoute(
        rarity=rarity,
        renderer_class=raw["rendererClass"],
        backend=raw["backend"],
        maximum_layers=raw.get("maximumGeneratedAppearanceLayers"),
        allowed_components=tuple(raw.get("allowedGeneratedComponents", ())),
        supports_state_behavior=bool(raw["supportsStateBehavior"]),
    )


def validate_renderer_assembly(
    rarity: str,
    components: Iterable[str] = (),
    *,
    preset: bool = False,
    state_behavior: bool = False,
    policy: dict | None = None,
) -> RouteValidation:
    """Validate renderer-layer intent without inspecting pixel coordinates."""

    policy = policy or load_rarity_renderer_policy()
    route = select_renderer_route(rarity, policy)
    raw = policy["routes"][rarity]
    selected = tuple(dict.fromkeys(components))
    errors: list[str] = []

    if route.backend == "vanilla" and selected:
        errors.append("Common vanilla route cannot declare Fashion Sense appearance components")
    unknown = sorted(set(selected) - set(route.allowed_components))
    if unknown:
        errors.append(f"{rarity} route does not allow generated components {unknown}")
    if route.maximum_layers is not None and len(selected) > route.maximum_layers:
        errors.append(f"{rarity} route allows at most {route.maximum_layers} generated appearance layer(s)")
    minimum = raw.get("minimumGeneratedAppearanceLayers", 0)
    if len(selected) < minimum:
        errors.append(f"{rarity} route requires at least {minimum} generated appearance layer(s)")
    if state_behavior and not route.supports_state_behavior:
        errors.append(f"{rarity} route does not allow conditional/stateful appearance behavior")
    if raw.get("presetRequiredWhenLayerCountExceedsOne") and len(selected) > 1 and not preset:
        errors.append("coordinated RarePlus appearances require one generated preset")
    if preset and len(selected) <= 1 and rarity != "Rare":
        errors.append(f"{rarity} simple route must not require a coordinated preset")

    return RouteValidation(not errors, tuple(errors))

