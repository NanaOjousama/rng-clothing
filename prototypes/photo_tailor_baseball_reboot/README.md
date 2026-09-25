# Photo Tailor Baseball Reboot Prototype

Private fresh-construction prototype for the normal Baseball Cap family.

Authoritative references are read directly from `cap reference/`:
- primary front + true back: `Screenshot_20260924_223136.png`;
- primary right-facing side: `Screenshot_20260924_223116.png`;
- secondary front/side checks: `Screenshot_20260924_223057.png`;
- `caprefimages.jpeg` / `capefernece.jpeg` are additional construction references.

Active implementation:
`run_pt_baseball_v4.py`

Photo Tailor use:
- FashionSigLIP semantic analysis;
- normalized cap region semantics;
- facing-scoped construction overlays;
- reference-derived occupancy;
- Stardew hard-value cleanup.

Hard quarantine:
- no reads from `experiments/dad_cap/`;
- no reads from `experiments/dad_cap_v2/`;
- no reads from `experiments/trucker_cap/`;
- no old Photo Tailor cap control;
- no Mario/reference-cap art.

BackHat rule:
- use only true rear crown/opening/strap reference;
- never project the front visor behind the player;
- BackHat has no brim semantic.

Status: PT5/PT6 are candidate worn-QC only. Human review is authoritative.
