# Hat Type Gap Audit

**Renderer:** HAT_RENDERER_V1 is frozen. **Catalog:** open for expansion.

## Snapshot

- Current production families: **20**.
- Hat-slot source appearances audited: **116**.
- Source appearances already represented by production family contracts/states: **70**.
- Source appearances not represented by production contracts: **46**.

## Current cap reboot

- **Scope:** Baseball Cap + Dad Cap + Trucker Cap.
- **Snapback:** deferred/not required unless future worn-scale testing proves it meaningfully distinct.
- **Mario/reference cap:** excluded; separate easter-egg project later.
- **Clean-room rule:** old Dad/Trucker experiment art remains visually quarantined during new construction.

- **Baseball cap** — PHOTO_TAILOR_REBOOT_IN_PROGRESS — PT5/PT6 worn QC from fresh cap-reference folder; old rectangle clean-room pass is superseded.
- **Dad cap** — CLEANROOM_REBOOT_PLANNED — Fresh construction after Baseball; old Dad experiments remain visually quarantined until new master approval.
- **Snapback cap** — DEFERRED_NOT_REQUIRED — Do not include in current cap reboot; revisit only if it proves meaningfully distinct from Baseball at worn scale.
- **Trucker cap** — CLEANROOM_REBOOT_PLANNED — Fresh construction after Baseball/Dad; old Trucker experiment art remains visually quarantined until new master approval.

## Highest-value production gaps already present in the repo/source corpus

- **Cowboy hat** — SOURCE_PRESENT_UNPROMOTED — Promote as its own construction family.
- **Slouch beanie** — EXPERIMENT_PRESENT — Promote as a distinct beanie construction rather than a material variant.
- **Party hat** — SOURCE_PRESENT_UNPROMOTED — Review and promote if worn identity passes.
- **Paperboy / newsboy cap** — SOURCE_PRESENT_BUT_REJECTED — Do not promote rejected source; replace/re-author a readable construction.
- **Veil family** — SOURCE_PRESENT_HEAD_ACCESSORY — Decide whether this belongs in hat catalog or accessory catalog before promotion.
- **Tiara family** — SOURCE_PRESENT_HEAD_ACCESSORY — Treat as head-accessory construction family if included in hats.
- **Goggles-on-head** — SOURCE_PRESENT_HEAD_ACCESSORY — Optional head-accessory family.
- **Flower crown** — SOURCE_PRESENT_HEAD_ACCESSORY — Optional alternate crown/garland construction.

## Deferred easter-egg/reference content

- **Mario-style reference cap** — DEFERRED_EASTER_EGG — Separate easter-egg/reference project; excluded from the normal cap reboot.

## Reference-only / genuinely new construction gaps

- **Witch / wizard pointy hat** — REFERENCE_ONLY — Needs new approved construction before production.
- **Jester hat** — REFERENCE_ONLY — Needs new approved construction.
- **Sombrero** — REFERENCE_ONLY — Needs new approved construction.
- **Prospector / miner hat** — REFERENCE_ONLY — Needs new approved construction.
- **Helmet family** — REFERENCE_ONLY — Separate armor/headgear family; not a normal soft-hat variant.
- **Visor** — REFERENCE_ONLY — Needs new approved construction.
- **Deerstalker / detective cap** — REFERENCE_ONLY — Needs new approved construction.
- **Sailor cap** — REFERENCE_ONLY — Needs source/construction review before production.
- **Top hat** — REFERENCE_OR_STYLE_PROFILE_ONLY — No production/source-catalog construction; author or promote a reference-backed construction.
- **Fedora** — POLICY_REFERENCE_ONLY — No production/source-catalog construction; needs approved construction.
- **Bucket hat** — NOT_FOUND_IN_CURRENT_CORPUS — New construction required.
- **Chef hat** — NOT_FOUND_IN_CURRENT_CORPUS — New construction required.

## Uncovered source-catalog items by classification

- **CONSTRUCTION_BASE**: 2
- **CONSTRUCTION_CANDIDATE**: 8
- **HEAD_ACCESSORY**: 33
- **MASK_FACE_HEADWEAR**: 1
- **REJECTED_CONSTRUCTION**: 1
- **RENDER_MATERIAL_VARIANT**: 1

## Old material disposition

### KEEP_ACTIVE

- generator/source_respecting_hat_production.py
- generator/hat_hybrid_enhancements.py
- generator/data/source_respecting_hat_goldens.json
- generator/data/source_parts/hat_source_parts.json
- generator/data/hat_hybrid_production_policy.json
- generator/data/hat_renderer_contract.json

### KEEP_REFERENCE_OR_PROMOTION_INPUT

- source_catalog/HAT_WORKING_CATALOG.json
- source_catalog/HAT_WORKING_CATALOG.md
- experiments/slouch_beanie_compare
- prototypes/mario_hat
- experiments/mario_hat
- experiments/source_respecting_hat_pilot_01
- experiments/source_respecting_hat_batch_a_01
- experiments/source_respecting_hat_remaining_01

### QUARANTINED_CAP_HISTORY

- experiments/dad_cap/
- experiments/dad_cap_v2/
- experiments/trucker_cap/

### ARCHIVE_CANDIDATE_AFTER_CURRENT_FREEZE

- experiments/hat_production_batch_01
- experiments/hat_production_batch_09
- experiments/source_fidelity
- experiments/cap_ai

### DELETE_CANDIDATE_AFTER_VERIFICATION

- temporary enlarged previews / caches that are reproducible

## Important findings

- **Cowboy Hat already exists in the primary source corpus** and is REVIEW_NEEDED; it does not need a brand-new silhouette unless live review rejects it.
- **Baseball Cap (Cap 2) and Snapback are already LIVE_APPROVED source constructions**, but were never promoted into the current 20-family production catalog.
- Dad Cap, Trucker Cap, Slouch Beanie, and the Mario-style cap all have existing repo work that should be reviewed/promoted instead of recreated blindly.
- The old Paperboy Hat failed live identity/readability; keep that failure as evidence, but do not promote the rejected construction.
- Do not delete old source/prototype material before the corresponding missing family is promoted or explicitly rejected.
