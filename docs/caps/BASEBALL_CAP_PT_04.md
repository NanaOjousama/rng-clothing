# Baseball Cap — Photo Tailor Reboot 04

Status: CANDIDATE_WORN_QC

Active normal-cap construction: Baseball Cap.

Authoritative fresh references:
- `cap reference/Screenshot_20260924_223136.png` — primary front and true back;
- `cap reference/Screenshot_20260924_223116.png` — primary right-facing side;
- `cap reference/Screenshot_20260924_223057.png` — secondary front/side proportion check;
- `cap reference/caprefimages.jpeg` and `capefernece.jpeg` — secondary construction checks.

Photo Tailor use:
- FashionSigLIP semantic analysis;
- normalized cap regions and facing logic;
- PT-style construction overlays;
- reference-derived occupancy rather than old cap-control geometry.

All authoritative views independently classify as hat -> cap -> standard.

Hard quarantine:
- no old Dad v1/v2 art;
- no old Trucker art;
- no old PT cap control;
- no Mario/reference-cap art;
- old single-vector reference is no longer active.

Projection rules:
- front/right use crown + band + brim regions;
- BackHat uses crown + rear strap only;
- true rear opening remains transparent negative space;
- BackHat has no brim semantic and no visor behind the player;
- left is the exact mirror of right;
- reference logos/motifs are ignored for the base construction.

Candidates:
- **PT5 Primary / Balanced** — primary worn-QC candidate.
- **PT6 Primary / Compact** — smaller comparison candidate.

Live QC pack:
`test-packs/fashionsense/RNG-Cap-Reboot-Baseball-PT-04/`

Installed:
`Mods/[FS] RNG Cap Reboot Baseball PT 04`

Human worn QC is authoritative. Do not promote into `HAT_RENDERER_V1` yet.
