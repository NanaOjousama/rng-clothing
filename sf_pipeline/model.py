from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class PromotionStatus(str, Enum):
    GENERATED_UNREVIEWED = "GENERATED_UNREVIEWED"
    CANDIDATE_FRONT_APPROVED = "CANDIDATE_FRONT_APPROVED"
    CANDIDATE_DIRECTIONAL = "CANDIDATE_DIRECTIONAL"
    QC_APPROVED = "QC_APPROVED"
    PRODUCTION_APPROVED = "PRODUCTION_APPROVED"
    REWORK = "REWORK"
    REJECTED = "REJECTED"


class DirectionMethod(str, Enum):
    LEGACY_DIRECTION_SET = "legacy-direction-set"
    EDIT_CARDINAL = "edit-cardinal"


class ReferenceRole(str, Enum):
    CONSTRUCTION = "construction"
    MATERIAL = "material"
    PATTERN = "pattern"
    MOTIF = "motif"
    TRIM = "trim"
    PALETTE_VALUE = "palette_value"
    OVERALL_STYLE = "overall_style"


@dataclass
class ReferenceInput:
    role: ReferenceRole
    local_path: str
    asset_id: str = ""
    note: str = ""


@dataclass
class CandidateOutput:
    index: int
    asset_id: str
    local_path: str
    width: int
    height: int
    request_id: str = ""
    human_review: str = "PENDING"
    human_note: str = ""


@dataclass
class CandidateManifest:
    id: str
    operation: str
    requested_size: int
    prompt: str
    references: List[ReferenceInput] = field(default_factory=list)
    outputs: List[CandidateOutput] = field(default_factory=list)
    status: PromotionStatus = PromotionStatus.GENERATED_UNREVIEWED
    source_family: str = ""
    construction_template: str = ""


@dataclass
class DirectionAsset:
    direction: str
    asset_id: str
    local_path: str
    width: int
    height: int
    human_review: str = "PENDING"
    human_note: str = ""


@dataclass
class DirectionSetManifest:
    id: str
    source_candidate_id: str
    source_asset_id: str
    requested_size: int
    directions: Dict[str, DirectionAsset] = field(default_factory=dict)
    status: PromotionStatus = PromotionStatus.CANDIDATE_DIRECTIONAL
    consistency_classes: Dict[str, str] = field(default_factory=dict)
    qc_notes: List[str] = field(default_factory=list)
    method: DirectionMethod = DirectionMethod.LEGACY_DIRECTION_SET
    garment_category: str = ""

    @property
    def cardinal(self) -> Dict[str, Optional[DirectionAsset]]:
        if self.method == DirectionMethod.EDIT_CARDINAL:
            return {
                "front": self.directions.get("front"),
                "right": self.directions.get("right"),
                "back": self.directions.get("back"),
                "left": self.directions.get("left"),
            }
        return {
            "front": self.directions.get("S"),
            "right": self.directions.get("E"),
            "back": self.directions.get("N"),
            "left": self.directions.get("W"),
        }
