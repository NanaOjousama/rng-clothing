# Photo Tailor Private Integration Lab

Purpose: test whether Photo Tailor's compiler ideas materially improve our Stardew clothing workflow before any production integration decision.

Adapted systems under test: canonical normalized projection, construction drafting, occupancy/region masks, base vs overlay fields, facing scopes, normalized motifs, semantic pattern coordinates, color bands, per-region palettes, source shading topology, cleanup of weak pattern fragments, and coherent Front/Right/Left/Back propagation.

Rendering/control side: eight copied approved source-respecting hats (`beret`, `beanie`, `straw_hat`, `boater_hat`, `mushroom_hat`, `sun_hat`, `tulip_hat`, `hood`). The copied silhouette is authoritative; the experiment is allowed to recolor/fill/detail only inside that occupancy.

Primary proof:
- `experiments/photo_tailor_private_lab_01/PHOTO_TAILOR_PRIVATE_LAB_CONTACT.png`
- `PHOTO_TAILOR_PRIVATE_LAB_BASE_OVERLAY.png`
- `PHOTO_TAILOR_PRIVATE_LAB_MASKS.png`
- each design folder contains four finals, base fields, overlays, occupancy masks, region maps, and `draft.json`.

The prototype is intentionally not release-ready. Its region drafting is generic and its purpose is to answer whether this architecture is useful enough to reimplement cleanly later.
