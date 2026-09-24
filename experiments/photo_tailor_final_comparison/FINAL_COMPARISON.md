# Final Photo Tailor Prototype Comparison

## Apples-to-apples 20-reference benchmark
- **A — Golden/current:** 8.73
- **B — Full PT Lab 02:** 9.18 (+0.45 vs A)
- **C — Hybrid Lab 03:** 9.29 (+0.48 vs A; +0.11 vs B)

Lab 03 has the strongest proxy overall. It keeps source pixels authoritative and uses PT only for bounded pattern, region-palette/color-band, motif/facing-scope, overlay and occupancy-cleanup deltas.

## Three-lab history
- **Lab 01:** 8-design capability proof. Not the same 20-reference set, so no fake numeric comparison.
- **Lab 02:** full reference-driven PT compiler; stronger semantics but small cleanliness losses.
- **Lab 03:** hybrid; retains PT gains while recovering most cleanliness losses.

Human review of FINAL_A_B_C_20_REFERENCE_CONTACT.png remains the final art-quality decision.
