# Private Photo Tailor Integration Lab — State

Built 2026-09-24 as a disposable private prototype. Production generator remains untouched.

Implemented/tested:
- four-view normalized Stardew projection;
- source-silhouette construction drafting;
- occupancy + semantic region masks;
- base field vs projection overlay layers;
- facing scopes (`FrontOnly`, `FrontSides`, `BackOnly`, `FrontBack`, `AllFacings`);
- normalized motif coordinates;
- normalized semantic pattern fields;
- color bands and independent region palettes;
- preservation of source shading topology;
- texture/pattern cleanup against outline and isolated fragments;
- coherent directional detail propagation.

Controls: eight copied human-approved source-respecting hats. No live production imports.

Proof batch: `experiments/photo_tailor_private_lab_01/`.
Primary sheet: `PHOTO_TAILOR_PRIVATE_LAB_CONTACT.png`.
Debug sheets: `PHOTO_TAILOR_PRIVATE_LAB_BASE_OVERLAY.png`, `PHOTO_TAILOR_PRIVATE_LAB_MASKS.png`.

Validation PASS:
- no production generator/render imports;
- source alpha geometry preserved across all 32 output views;
- base/overlay separation has no leakage;
- scoped detail behavior verified;
- pattern cleanup retains meaningful evidence;
- all 13 requested systems covered.
