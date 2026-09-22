from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List

from .model import ReferenceInput, ReferenceRole


PREFERRED_MIN_REFERENCES = 4
PREFERRED_MAX_REFERENCES = 8
API_MAX_REFERENCES = 20


def validate_reference_bundle(refs: Iterable[ReferenceInput]) -> List[str]:
    refs = list(refs)
    issues: List[str] = []
    if not refs:
        issues.append("no_references")
    if len(refs) > API_MAX_REFERENCES:
        issues.append("too_many_references")
    if not any(r.role == ReferenceRole.CONSTRUCTION for r in refs):
        issues.append("missing_construction_reference")
    if len(refs) < PREFERRED_MIN_REFERENCES:
        issues.append("below_preferred_reference_count")
    if len(refs) > PREFERRED_MAX_REFERENCES:
        issues.append("above_preferred_reference_count")
    return issues


def build_style_reference_request(prompt: str, refs: Iterable[ReferenceInput],
                                  size: int = 16) -> dict:
    refs = list(refs)
    blocking = [x for x in validate_reference_bundle(refs)
                if x in {"no_references", "too_many_references",
                         "missing_construction_reference"}]
    if blocking:
        raise ValueError("Invalid reference bundle: " + ", ".join(blocking))
    if size not in (16, 32, 64):
        raise ValueError("Sprite Fusion size must be 16, 32, or 64.")

    return {
        "operation": "style-reference",
        "size": size,
        "prompt": prompt,
        "referenceRoles": [
            {
                "role": r.role.value,
                "localPath": r.local_path,
                "assetId": r.asset_id,
                "note": r.note,
            }
            for r in refs
        ],
    }
