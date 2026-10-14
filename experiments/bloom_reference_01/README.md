# bloom_reference_01 — FS Bloom Collection (hats only), reference pack

- Source: `good hats/FS Bloom Collection.zip` (user-supplied), author **mushlune**, UniqueID `mushlune.lunebloom`.
- Extracted 2026-10-14: the manifest and the **Hats** folder only (no shirts/pants), into `raw/` (git-ignored,
  read-only; personal use).
- Contents: 8 low-sweeping witch hats on one silhouette body (the same maker's body as Wildwood, front IoU
  0.80-0.86 to Wildwood), plus Fall Crown and Spring Crown (flower crowns, treated as general hats).
- Used by: `witch_silhouette_matrix_01/tools/collect.py` (groups G21-G27, crowns excluded) and the Phase 4
  dataset builder `lora_sdxl_research/tools/build_dataset_phase4.py`. The body cap of 6 dropped Hyacinth and
  Hydrangias from training.
- Nothing from this pack enters the generator or any player-facing pool.
