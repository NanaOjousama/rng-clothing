# Hybrid V3 Baseline Freeze

Recorded for Hybrid Garment Compiler V3 Phase 1. This is a documentation freeze, not a renderer promotion.

## Active route

- Entry point: `tools/generate_autonomous_generator_recovery.py`
- Concept engine: `generator/autonomous_recovery/concept_engine.py`
  - `FAMILIES`
  - `concept_for`
  - `semantic_errors`
  - `structural_difference`
- Adapter: `generator/autonomous_recovery/adapter.py`
  - `_carrier`
  - `_construct`
  - `render_autonomous_concept`

Current recovery flow:

```text
autonomous design concept
-> select existing V5 carrier
-> render_fs_hd_v2
-> render_fs_v3_surface
-> render_fs_v4
-> render_fs_v5b
-> render_fs_v5d when required
-> reset named surface to proven HD planes
-> article-specific construction adapter
-> polish_upper_frames
-> soften_shared_rear_neck
-> semantic palette/material adapter
-> Farmer preview / Fashion Sense export
```

The structure-only `reference_grammar.render_controlled_garment` route and premium-cardigan experimental profiles are not part of this active route.

## Frozen backend and runtime contracts

- HD base: `generator/renderers/fashionsense/hd_garment_v2.py::render_fs_hd_v2`
- Surface: `generator/renderers/fashionsense/surface_v3.py::render_fs_v3_surface`
- Article translation: `generator/renderers/fashionsense/article_v4.py::render_fs_v4`
- Upper construction: `generator/renderers/fashionsense/upper_v5b.py::render_fs_v5b`
- Extended upper construction: `generator/renderers/fashionsense/upper_v5d.py::render_fs_v5d`
- Shared polish: `generator/renderers/fashionsense/art_polish_v5e.py::polish_upper_frames`
- Shared rear neck: `generator/renderers/fashionsense/art_polish_v5e.py::soften_shared_rear_neck`
- Fashion Sense target: 7.5.0
- Shirt contract: 16×16 logical directional frames, 16×64 atlas, Scale 2, `BodyPosition (0,32)`, binary alpha
- Sleeve contract: `generator/data/fashionsense/runtime_sleeve_contracts.json::NATIVE_ANIMATED_SLEEVES_V1`
- Native sleeve behavior: `HideSleeves=false`, three `SleeveColors`, `SleevesId=None`
- Rejected behavior: custom 32×64 Scale-2 Sleeves atlas with disabled native offset

Baseline SHA-256 values:

| Frozen file | SHA-256 |
|---|---|
| `hd_garment_v2.py` | `b130953f8f2acfc2fadaa52c11bdf6eb9ac06e312e135274515b3cb1e16f0f4f` |
| `surface_v3.py` | `05d420c3a7366c7e53e46580bff9466aa83f7b464161ef18e52c1c81f8d50e23` |
| `article_v4.py` | `e1cfcb53da27f6a28d54b9b19c9f250421172a112a5e5fff1ece8614c0e42856` |
| `upper_v5b.py` | `d94901c0b7475ccb3414b8b079af7a203a8ba9b74cb3c4e1bbbe0a618dd1c082` |
| `upper_v5d.py` | `9d4a584c4c834c7bc6b1730dfa5f3a71b6872a847921a69f79b0034daf434176` |
| `art_polish_v5e.py` | `ca2695514d7b7baeb53a5c80c7794a6789b6f72b66ea16282871c98ca70f1c80` |
| `runtime_sleeve_contracts.json` | `a3903a0e1df5a6951a41eb7bc3232261275cb3a9f3780b74120e5c78f3219ffa` |
| `rarity_renderer_architecture.json` | `7fa30f76671920eabfb80bc4541c9998f25900b60a2dab805f36db8c2d928187` |

## Feature flag freeze

`HYBRID_GARMENT_COMPILER_V3_ENABLED` defaults to `false`. Phase 1 tools may exercise the isolated recipe-only package explicitly, but the legacy/current autonomous entry point does not import or partially consume V3 anatomy. Production and recovery behavior therefore remains unchanged while the flag is false.

## Phase 1 boundary

V3 Phase 1 may build canonical semantic garment models, validate them, project Front/Right/Back/Left, and emit semantic-flat diagnostics. It may not call the frozen renderer route, export Fashion Sense appearances, modify runtime contracts, or replace the current recovery path.
