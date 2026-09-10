# Controlled Grammar Back-Neck Micro-Fix

Status: **PASS_STATIC_RUNTIME_NOT_TESTED**. Runtime remains **NOT TESTED**.

## Shared correction

The shared `generator/renderers/fashionsense/art_polish_v5e.py::soften_shared_rear_neck` shade-mask pass now removes the unprotected lower point of the inherited rear-opening crease after `polish_upper_frames`. It replaces those cells with adjacent existing fabric shade roles, so upper-left lighting and material ramps remain intact.

Only rear-view `DEEP_CREASE` / `STRUCTURAL_EDGE` cells in the shallow neck window are eligible. Garment-authored cardigan collar and work-jacket yoke signal cells are protected. Alpha, runtime fields, palettes, grammars, native sleeves, front, right, and left art are unchanged.

| Grammar | Back shade cells changed | Old point depth row | Front/right/left identical | Alpha identical |
|---|---:|---:|---|---|
| `FITTED_TEE` | 0 | 0 | TRUE | TRUE |
| `OPEN_CARDIGAN` | 8 | 5 | TRUE | TRUE |
| `WORK_JACKET` | 4 | 5 | TRUE | TRUE |

The fitted tee already had a shallow rear neckline after its closed-opening translation, so the shared pass correctly made no destructive change to it. It was nevertheless regenerated through the same corrected route. The cardigan and work jacket lost only the deep stamped-on point beneath their distinct rear collar/yoke construction.

## Outputs

- Before/after back views: `/run/media/deck/USD00/RNG_clothing/output/comparisons/CONTROLLED_GRAMMAR_BACK_NECK_BEFORE_AFTER.png`
- Regenerated directions: `/run/media/deck/USD00/RNG_clothing/output/comparisons/CONTROLLED_GRAMMAR_HD_ADAPTER_DIRECTIONS.png`
- Regenerated Farmer composites: `/run/media/deck/USD00/RNG_clothing/output/comparisons/CONTROLLED_GRAMMAR_HD_ADAPTER_FARMER_DIRECTIONS.png`
- Micro-fix validation: `/run/media/deck/USD00/RNG_clothing/output/fashionsense/controlled-grammar-hd-adapter-repair/back-neck-micro-fix-validation.json`
- Experimental test pack: `/run/media/deck/USD00/RNG_clothing/test-packs/fashionsense/RNG-Clothing-Controlled-Grammar-HD-Adapter-Repair`

Stop state: shared rear-neck micro-fix only; no additional garments or design changes.
