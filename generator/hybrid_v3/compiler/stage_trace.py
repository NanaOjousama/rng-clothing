"""Auditable Phase 2 stage traces and frozen-backend verification."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FROZEN = {
    "generator/renderers/fashionsense/hd_garment_v2.py": "b130953f8f2acfc2fadaa52c11bdf6eb9ac06e312e135274515b3cb1e16f0f4f",
    "generator/renderers/fashionsense/surface_v3.py": "05d420c3a7366c7e53e46580bff9466aa83f7b464161ef18e52c1c81f8d50e23",
    "generator/renderers/fashionsense/article_v4.py": "e1cfcb53da27f6a28d54b9b19c9f250421172a112a5e5fff1ece8614c0e42856",
    "generator/renderers/fashionsense/upper_v5b.py": "d94901c0b7475ccb3414b8b079af7a203a8ba9b74cb3c4e1bbbe0a618dd1c082",
    "generator/renderers/fashionsense/upper_v5d.py": "9d4a584c4c834c7bc6b1730dfa5f3a71b6872a847921a69f79b0034daf434176",
    "generator/renderers/fashionsense/art_polish_v5e.py": "ca2695514d7b7baeb53a5c80c7794a6789b6f72b66ea16282871c98ca70f1c80",
    "generator/data/fashionsense/runtime_sleeve_contracts.json": "a3903a0e1df5a6951a41eb7bc3232261275cb3a9f3780b74120e5c78f3219ffa",
    "generator/data/rarity_renderer_architecture.json": "7fa30f76671920eabfb80bc4541c9998f25900b60a2dab805f36db8c2d928187",
}


def verify_frozen_backend() -> dict:
    files = []
    for relative, expected in FROZEN.items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        files.append({"path": relative, "expected": expected, "actual": actual, "status": "PASS" if actual == expected else "FAIL"})
    return {"status": "PASS" if all(item["status"] == "PASS" for item in files) else "FAIL", "files": files}


def phase2_trace(carrier_id: str) -> list[str]:
    return [
        "validated_v3_canonical_model", "validated_directional_projections",
        "select_strict_carrier_capability:" + carrier_id,
        "render_fs_hd_v2", "render_fs_v3_surface", "render_fs_v4", "render_fs_v5b",
        "reset_named_surface_to_proven_hd_planes", "compile_v3_component_graph",
        "validate_semantic_pixel_regions", "polish_upper_frames", "soften_shared_rear_neck",
        "semantic_material_palette_adapter", "sprite_integrity_validation", "farmer_composite_gate",
    ]
