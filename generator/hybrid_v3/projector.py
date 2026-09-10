"""Deterministic directional projection from one canonical garment graph."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .data import V3DataRepository

DIRECTIONS = ("front", "right", "back", "left")


class DirectionalProjector:
    def __init__(self, repository: V3DataRepository | None = None):
        self.repository = repository or V3DataRepository()

    def project(self, canonical: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        projections: dict[str, list[dict[str, Any]]] = {direction: [] for direction in DIRECTIONS}
        for component in canonical["components"]:
            policy = component["directionalVisibilityPolicy"]
            for direction in DIRECTIONS:
                projections[direction].append(
                    {
                        "componentInstance": component["instanceId"],
                        "definitionId": component["definitionId"],
                        "componentType": component["componentType"],
                        "parent": component["parent"],
                        "attachmentRegion": component["attachmentRegion"],
                        "visibility": policy[direction],
                        "continuityGroup": component.get("continuityGroup"),
                        "pixelPriority": component["pixelPriority"],
                        "silhouetteImpact": component["silhouetteImpact"],
                        "parameters": deepcopy(component["parameters"]),
                    }
                )
        return projections
