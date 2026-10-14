# RNG Clothing

Private development repository for a Stardew Valley clothing-generation project.

## Goals
- Generate usable, consistent clothing sprites across four character views.
- Maintain construction templates and validation for pixel-art clothing.
- Experiment with native-resolution LoRA training and compare results.
- Support configurable clothing packs and future gameplay integration.

## Planned layout
- `generator/` — clothing generation and processing code
- `construction/` — template definitions and alignment/validation utilities
- `training/` — training scripts, configs, manifests, and reproducible workflows
- `evaluation/` — comparison tools, reports and small textual results
- `tests/` — automated regression and variety tests
- `docs/` — project plans and implementation notes

These folders are populated as reviewed source files are migrated. Avoid copying an entire training workspace into this repository.

## Data handling
Keep raw datasets, reference images/packs, downloaded assets, model checkpoints, virtual environments, generated sprites, and caches **local**. Commit only reviewed source code, non-sensitive configs, small manifests, tests, and intentional reports. Check licenses before redistributing third-party assets. A private repository is not a substitute for secrets management.

## Current state
Repository scaffold only. Existing local workspaces are not automatically linked or modified.
