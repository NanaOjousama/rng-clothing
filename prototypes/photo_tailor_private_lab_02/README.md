# Photo Tailor Private Lab 02 — End-to-End Challenge

Disposable private A/B prototype joining the earlier FashionSigLIP reference analyzer with the Photo Tailor-style semantic compiler. It does not import production generator/render modules.

## Batch
- 20 actual project reference images: 16 hats + 4 shirts.
- FashionSigLIP produces semantic blueprint candidates and reference palettes.
- A coarse Precise-Recognition-style construction hint selects a copied control family.
- Current baseline = untouched copied source-respecting/control construction.
- Enhanced = region masks + normalized patterns + region palettes/color bands + base/overlay + facing scopes + source shading topology.

## Review outputs
- `experiments/photo_tailor_private_lab_02/LAB02_ALL_20_CONTACT.png`
- `LAB02_HATS_16_CONTACT.png`
- `LAB02_SHIRTS_4_CONTACT.png`
- `LAB02_SCORECARD.png`
- Each sample folder has its original reference, blueprint, masks, baseline 4-view, enhanced 4-view, per-view outputs, comparison sheet, and JSON scores.

Automated scores are diagnostic proxies only; human art review remains authoritative.
