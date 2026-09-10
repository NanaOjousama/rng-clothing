# Sweater Vest Side Top-Edge Artifact Micro-Fix — Pass 2

Status: **PASS STATIC / RUNTIME NOT TESTED**.

## Cause

The artifact is an **inherited source-carrier alpha error**. Pass 1 removed the unsupported row-zero collar/shoulder spill, but its predicate inspected only row zero. It could not see the separate left upper-right component `[(14,1),(15,1),(15,2)]`. The right frame contained the exact mirrored island `[(0,1),(0,2),(1,1)]`, so it received the same bounded correction. The pixels predate construction/polish; frame mapping, preview translation, and export did not create them.

## Repair

`generator.autonomous_recovery.adapter._clean_vest_side_top_overhang` retains the Pass 1 row-zero cleanup, then runs four-neighbor connected-component analysis on each vest side frame and removes every component except the main garment component. Pass 2 removes left `[(14,1),(15,1),(15,2)]` and mirrored right `[(0,1),(0,2),(1,1)]`. Side component counts change from 2 to 1. Supported neck/shoulder/body cells remain. Front, back, palette, native sleeves, atlas order, Scale 2, BodyPosition `(0,32)`, and all other garments are unchanged.

- Corrected pack: `/run/media/deck/USD00/RNG_clothing/test-packs/fashionsense/RNG-Clothing-Autonomous-Recovery`
- Corrected 16x16 left frame: `/run/media/deck/USD00/RNG_clothing/output/fashionsense/autonomous-generator-recovery/pollenridge-sweater-vest-left-corrected.png`
- Before/after crop: `/run/media/deck/USD00/RNG_clothing/output/comparisons/AUTONOMOUS_RECOVERY_SWEATER_VEST_SIDE_TOP_FIX.png`
- Validation: `/run/media/deck/USD00/RNG_clothing/output/fashionsense/autonomous-generator-recovery/sweater-vest-side-top-fix-validation.json`
