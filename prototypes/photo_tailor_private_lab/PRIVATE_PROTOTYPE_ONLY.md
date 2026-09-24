# PRIVATE / DISPOSABLE PHOTO TAILOR LAB

This tree is a private experiment only. It is not a production generator module, runtime dependency, release asset, or shipping package.

Isolation rules:
- No production `generator` or `v5` imports.
- Approved hats are copied into `control_assets/`; prototype rendering never mutates their source files.
- Photo Tailor decompile excerpts used for study/adaptation are copied under `vendor/photo_tailor_decompiled/`.
- Runtime dependencies live outside the repo in `/home/deck/.cache/photo_tailor_private_lab_venv`.
- Generated proof is isolated under `experiments/photo_tailor_private_lab_01/`.

Removal if permission is denied later:
1. Delete `prototypes/photo_tailor_private_lab/`.
2. Delete `experiments/photo_tailor_private_lab_01/`.
3. Delete `/home/deck/.cache/photo_tailor_private_lab_venv`.
No production generator file depends on any of these paths.
