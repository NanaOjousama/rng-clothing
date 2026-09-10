"""V4 per-cell ownership and mutation policy.

This is deliberately independent of palette colors. It records *why* a logical
cell exists and which later stages may mutate it.  The goal is to prevent the
exact Hybrid V3 failure where a later polish pass silently rewrites component
identity.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class CellOwnership:
    component_owner: str
    system: str
    topology_role: str
    semantic_region: str
    shade_authority: str
    protection_level: str
    allowed_later_mutations: tuple[str, ...]
    originating_stage: str


class OwnershipLedgerV4:
    def __init__(self) -> None:
        self.cells: dict[str, dict[tuple[int, int], CellOwnership]] = {
            d: {} for d in ("front", "right", "back", "left")
        }
        self.conflicts: list[dict[str, Any]] = []
        self.rejected_mutations: list[dict[str, Any]] = []

    def claim(
        self,
        direction: str,
        cell: tuple[int, int],
        *,
        component_owner: str,
        system: str,
        topology_role: str = "COMPONENT_IDENTITY",
        semantic_region: str | None = None,
        shade_authority: str = "COMPONENT",
        protection_level: str = "STRUCTURAL",
        allowed_later_mutations: tuple[str, ...] = ("PALETTE_RESOLVE",),
        originating_stage: str = "V4_COMPONENT_COMPILER",
    ) -> None:
        incoming = CellOwnership(
            component_owner=component_owner,
            system=system,
            topology_role=topology_role,
            semantic_region=semantic_region or system,
            shade_authority=shade_authority,
            protection_level=protection_level,
            allowed_later_mutations=tuple(allowed_later_mutations),
            originating_stage=originating_stage,
        )
        existing = self.cells[direction].get(cell)
        # Deterministic precedence: a structural/locked component may claim a
        # cell previously owned only by the BODY form plane. That is an
        # intentional specialization, not a conflict. Equal-strength competing
        # component claims remain visible as conflicts.
        rank = {"SURFACE": 0, "FORM": 1, "STRUCTURAL": 2, "LOCKED": 3}
        if existing is not None and existing != incoming:
            if rank.get(incoming.protection_level, 0) >= rank.get(existing.protection_level, 0) and existing.protection_level == "FORM":
                self.cells[direction][cell] = incoming
                return
            conflict = {
                "direction": direction,
                "cell": list(cell),
                "existing": asdict(existing),
                "incoming": asdict(incoming),
                "resolution": "INCOMING_CLAIM_REJECTED_EXISTING_OWNER_PRESERVED",
            }
            self.conflicts.append(conflict)
            self.rejected_mutations.append({
                "direction": direction, "cell": list(cell), "stage": originating_stage,
                "reason": "ownership conflict: existing structural owner preserved",
                "owner": asdict(existing), "rejectedIncoming": asdict(incoming),
            })
            return
        self.cells[direction][cell] = incoming

    def may_mutate(self, direction: str, cell: tuple[int, int], stage: str) -> bool:
        owner = self.cells[direction].get(cell)
        return owner is None or stage in owner.allowed_later_mutations

    def reject(self, direction: str, cell: tuple[int, int], stage: str, *, reason: str) -> None:
        owner = self.cells[direction].get(cell)
        self.rejected_mutations.append({
            "direction": direction,
            "cell": list(cell),
            "stage": stage,
            "reason": reason,
            "owner": asdict(owner) if owner else None,
        })

    def protected_cells(self, direction: str) -> frozenset[tuple[int, int]]:
        return frozenset(
            cell for cell, owner in self.cells[direction].items()
            if owner.protection_level in {"STRUCTURAL", "LOCKED"}
        )

    def as_json(self) -> dict[str, Any]:
        return {
            "cells": {
                direction: [
                    {"cell": list(cell), **asdict(owner)}
                    for cell, owner in sorted(values.items(), key=lambda item: (item[0][1], item[0][0]))
                ]
                for direction, values in self.cells.items()
            },
            "conflicts": self.conflicts,
            "rejectedMutations": self.rejected_mutations,
        }
