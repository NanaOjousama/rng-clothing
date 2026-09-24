# PRIVATE / DISPOSABLE ONLY

This prototype is not a production dependency or release asset.

Isolation:
- No imports from `generator`, `v5`, or mod runtime code.
- Hat and shirt controls are copied snapshots.
- Reference images are copied into this prototype.
- Photo Tailor decompile excerpts are isolated under `vendor/photo_tailor_decompiled/`.
- FashionSigLIP model + labels are isolated under `vendor/photo_tailor_models/`; the large ONNX file is local-only and ignored by git.
- Generated proof is isolated under `experiments/photo_tailor_private_lab_02/`.

Removal if permission is denied:
1. Delete `prototypes/photo_tailor_private_lab_02/`.
2. Delete `experiments/photo_tailor_private_lab_02/`.
3. No production code needs repair because nothing imports this lab.
