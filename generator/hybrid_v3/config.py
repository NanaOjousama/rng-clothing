"""Feature-gate contract for Hybrid Garment Compiler V3."""

from __future__ import annotations

import os

FEATURE_FLAG_NAME = "HYBRID_GARMENT_COMPILER_V3_ENABLED"
HYBRID_GARMENT_COMPILER_V3_ENABLED = False


def is_enabled(environment: dict[str, str] | None = None) -> bool:
    """Return the explicit production integration state; default is false."""

    source = os.environ if environment is None else environment
    raw = source.get(FEATURE_FLAG_NAME)
    if raw is None:
        return HYBRID_GARMENT_COMPILER_V3_ENABLED
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def assert_no_partial_mix(*, legacy_anatomy: bool, v3_anatomy: bool) -> None:
    if legacy_anatomy and v3_anatomy:
        raise RuntimeError("V3 and legacy anatomy may not be mixed in one garment")
