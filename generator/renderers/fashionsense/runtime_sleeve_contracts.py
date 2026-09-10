"""Known-good Fashion Sense sleeve contracts derived from live runtime evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "generator" / "data" / "fashionsense" / "runtime_sleeve_contracts.json"


def load_runtime_sleeve_contracts() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def validate_native_animated_sleeves(pack: Path, shirt: dict[str, Any], preset: dict[str, Any]) -> tuple[str, ...]:
    """Reject the detached custom-atlas contract and require native arm attachment.

    This check is reusable by every future Rare+ pack exporter. A future custom
    Sleeves backend needs new live runtime evidence and a new named contract;
    it may not silently reuse the rejected V5B assumptions.
    """
    errors: list[str] = []
    contract = load_runtime_sleeve_contracts()["contracts"]["NATIVE_ANIMATED_SLEEVES_V1"]
    if (pack / "Sleeves").exists(): errors.append("custom Sleeves directory violates NATIVE_ANIMATED_SLEEVES_V1")
    if preset.get("SleevesId") != contract["preset"]["SleevesId"]: errors.append("preset must use SleevesId None")
    for key in ("FrontShirt", "RightShirt", "LeftShirt", "BackShirt"):
        model = shirt.get(key, {})
        if model.get("HideSleeves") is not False: errors.append(f"{key} must preserve native sleeves")
        if len(model.get("SleeveColors", [])) != contract["shirt"]["SleeveColorsCount"]: errors.append(f"{key} needs exactly three SleeveColors")
        if model.get("Scale") != contract["shirt"]["Scale"]: errors.append(f"{key} wrong Scale")
        if model.get("BodyPosition") != contract["shirt"]["BodyPosition"]: errors.append(f"{key} wrong BodyPosition")
        if "DisableNativeOffset" in model and model["DisableNativeOffset"]: errors.append(f"{key} may not disable native feature offsets")
    return tuple(errors)
