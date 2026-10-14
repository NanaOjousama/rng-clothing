# RNG Clothing workspace map

Last audited: **2026-10-14**. This file is a directory guide, not a migration of the generator architecture.

## First place to look

| Need | Location | Status |
| --- | --- | --- |
| What the project is | `README.md` | Overview |
| Instructions for Claude / Codex | `CLAUDE.md`, `AGENTS.md` | Keep at root; active |
| Current milestone, decisions, and blockers | `CURRENT_STATE.md`, `PROJECT_MEMORY.md` | Keep at root; active |
| Actual garment generator | `generator/` | Active code; do not move casually |
| Validated source-derived assets / construction | `authored/` | Active; paths are used by scripts |
| In-game testing and clothing mods | `mods/`, `qc_bridge/`, `test-helpers/` | Active; live paths may be relied on |
| Commands and validators | `tools/`, `tests/` | Active; many hard-coded imports/paths |
| Current and past experiments | [`experiments/INDEX.md`](../experiments/INDEX.md) | 180 experiment folders grouped by topic; preserves original paths |
| Construction studies and earlier prototypes | `prototypes/`, `v5/`, `rngc/` | Do not assume abandoned |
| Pack source studies and extracted hats | `pack_study/` | Active design research |
| Specifications and documentation | `specs/`, `docs/`, `reports/` | Text and indexed results |
| Historical backup / old attempts | `archive/` | Keep for recovery; no automatic deletion |
| Third-party clothing reference libraries | `references/`, `good hats/`, `cap reference/`, `personal_sources/`, `Beret/`, `generator content/` | Local, mostly Git-ignored; not to be published |
| Installed upstream Photo Tailor and decompilation | `PhotoTailor/` | External local tool, Git-ignored |
| Python runtime / model or integration toolchains | `.venv/`, `prototypes/ai_template_pipeline/.venv/`, `tools/vendor/`, `tools/toolchains/` | Large but needed locally; Git-ignored |

## Witch-hat / LoRA research

- Plans, generation/evaluation code, and validation status: `experiments/lora_sdxl_research/`.
- Front-design studies: `experiments/witch_front_design_01/`.
- LoRA GPU training itself runs **on the Windows laptop**, not in this Steam Deck repo.
- Training is **not approved to start** as of this organization pass.
- When evaluations are authorized and finish later, the laptop's completion hook uploads **review images only** to private `hewyinw/tfwr`, **separate branch `lora-reviews`**. Do not confuse that review branch with this RNG Clothing Git repository.

## Root clutter: what was sorted on 2026-10-14

23 loose images from the project root were moved, **without deleting or modifying image content**, to:

- `archive/loose_root_assets_2026-10-14/screenshots/` — 17 older screenshots
- `archive/loose_root_assets_2026-10-14/design_previews/` — six loose image previews arranged by study

Each original-to-new path, size, and SHA-256 hash is in `docs/ROOT_ASSET_RELOCATION_2026-10-14.tsv`. Restore any image by reversing that row's move.

These were selected only after a scan found no exact references to their filenames in the 2,489 Git-tracked text/code files inspected. This does not guarantee personal notes or past chat references never mentioned an old location.

## Awkward names that are deliberately NOT renamed

These names may look messy, but some are literal dependencies in scripts, manifests, or provenance:

- `New Folder/` — its direction sprites are referenced by a photo-tailor source-tracing experiment.
- `BUCKET HAT/` — referenced by QC/build scripts.
- `TRCUKER CONSTRUCKTION/` — includes locally referenced trucker screenshots and design studies.
- `beret_deesign/`, `beret_variant1/`, `reference batch/`, `slouch beanie motif/` — referenced by previous test inputs or source provenance.
- `apprved/` — check the approved-art routes before renaming.
- `good hats/` — personal third-party source-hat packs for witch-hat studies.
- `baseball-cap-vector-template-set-uniform-fashion-blank-hat-design-sport-clothing_1284-44135.avif` — referenced by baseball-cap generation scripts.
- `pixellab-CREATE-DIFFERENT-VARIANT-OF-ST-1789257040523.png` — referenced by an authored-family registry.

Rename one of these only as a separate refactor: find every consumer, update paths, run tests, and compare output hashes before and after.

## Organizing future files

1. Put new *third-party originals* under `references/` or the study's `raw/` folder (not the repo root); keep author/provenance notes. Avoid publishing raw packs to Git.
2. Put disposable images/metrics under `experiments/<study>/out/` or `output/`; curate only meaningful reproducibility artifacts for commits.
3. Keep actual source logic under `generator/`, validated assets under `authored/`, and integration mods under `mods/`. Do not migrate these casually.
4. Add short README/manifest notes to experiments so a review sheet is traceable to its model/checkpoint, seed, and source family.
5. Do not `git clean` blindly, delete worktrees, clear captures, or purge cached model/toolchain files without a specific recovery and dependency audit.

## What remains for a deeper cleanup

- Consolidate older legacy root folders **only after** updating their hard-coded consumers.
- Review local generated/failed experiments for archival **without deleting the only copies**.
- Consider separating local third-party assets from the Git workspace entirely once corpus manifests and all dependent paths are verified.
- Keep the current active `pack-study` branch and existing uncommitted work intact; no Git remote is attached to RNG Clothing.
