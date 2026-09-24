# Prototype observations

What the proof demonstrates:
- Region-aware recoloring can preserve approved source geometry while changing the design language substantially.
- Normalized pattern coordinates make stripes/plaid/dots continue coherently instead of being independently guessed per direction.
- Base/overlay separation is useful for keeping construction shading stable while allowing motifs, seams, pins, and other scoped details.
- Facing scopes are materially useful: front-only badges/seams do not leak to side/back views, while all-facing details propagate predictably.
- Occupancy/region masks make the renderer inspectable; failures can be traced to construction regions rather than arbitrary pixels.
- Reusing the source luminance topology gives the generated colors a more Stardew-like shaded shape than flat recoloring.

Known prototype weaknesses:
- Region drafting is still based on simple family-specific normalized bands, not a full learned/author-authored semantic segmentation.
- Side-view motif projection can intentionally move toward the visible front/back edge and may still need family-specific anchors.
- Pattern frequency is generic; production quality would need family/material-specific frequency contracts.
- This is evidence for the architecture, not permission-safe production code.

Decision point: judge the contact sheet first. If the visual improvement is worthwhile, reimplement the winning concepts cleanly in our own production architecture after permission/licensing is settled.
