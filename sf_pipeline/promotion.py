from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Set

from .model import PromotionStatus


_ALLOWED: Dict[PromotionStatus, Set[PromotionStatus]] = {
    PromotionStatus.GENERATED_UNREVIEWED: {
        PromotionStatus.CANDIDATE_FRONT_APPROVED,
        PromotionStatus.REWORK,
        PromotionStatus.REJECTED,
    },
    PromotionStatus.CANDIDATE_FRONT_APPROVED: {
        PromotionStatus.CANDIDATE_DIRECTIONAL,
        PromotionStatus.REWORK,
        PromotionStatus.REJECTED,
    },
    PromotionStatus.CANDIDATE_DIRECTIONAL: {
        PromotionStatus.QC_APPROVED,
        PromotionStatus.REWORK,
        PromotionStatus.REJECTED,
    },
    PromotionStatus.QC_APPROVED: {
        PromotionStatus.PRODUCTION_APPROVED,
        PromotionStatus.REWORK,
        PromotionStatus.REJECTED,
    },
    PromotionStatus.PRODUCTION_APPROVED: {
        PromotionStatus.REWORK,
        PromotionStatus.REJECTED,
    },
    PromotionStatus.REWORK: {
        PromotionStatus.GENERATED_UNREVIEWED,
        PromotionStatus.CANDIDATE_FRONT_APPROVED,
        PromotionStatus.REJECTED,
    },
    PromotionStatus.REJECTED: set(),
}


def can_transition(current: PromotionStatus, new: PromotionStatus) -> bool:
    return new in _ALLOWED[current]


def transition(current: PromotionStatus, new: PromotionStatus) -> PromotionStatus:
    if not can_transition(current, new):
        raise ValueError(f"Invalid promotion transition: {current.value} -> {new.value}")
    return new
