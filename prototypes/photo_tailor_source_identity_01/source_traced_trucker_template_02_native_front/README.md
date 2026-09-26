# Source-traced trucker template — native-pixel revision

This revision corrects the earlier 20→16 front downscale. Every supplied view
now remains at native pixel resolution: front is the original 20×20 image,
centered at `(3, 3)` on the 26×26 canvas; right and back are their original
26×26 images; left is an exact horizontal mirror of right. No source pixel is
resampled, removed, redrawn, or repositioned relative to its own view.

The neutral template only changes RGB hue/saturation in place; alpha and all
construction coordinates remain exact. Component masks are intentionally not
invented until reviewed against this frozen source trace.

The explicit component masks in `component_masks_01/` were subsequently
reviewed and user-approved on 2026-09-26. They are bound to this trace's decoded
pixel SHA-256 and are the only component authority for isolated styling proofs.
