# V4 Art Grammar — Pass 1

## What changed

- Added an experimental `PixelGrammarCompilerV4` proof path.
- Demoted the legacy V5E polish to a body-optics pass that runs **before** V4 component identity.
- Added `normalize_body_form()` to rebuild calm, readable fabric planes while preserving carrier alpha geometry.
- Removed the Coastal-Polo-specific cleanup branch from the folded polo collar compiler.
- Replaced it with one general directional polo collar grammar:
  - original readable front treatment preserved;
  - shallow subordinate rear fold;
  - compact attached side wedges.
- Component identity now runs after the global optical polish so collars/plackets/armholes are not subsequently recolored by that global pass.
- Rear-neck cleanup remains after components but protects all compiler-owned rear component cells.

## Why

The Phase 2 failure audit proved that the old pipeline had conflicting ownership:
component changes could be made and then partially overwritten by `polish_upper_frames`.
It also proved that side-body darkness was inherited strongly enough to remain visually unchanged after micro-fixes.

Pass 1 makes ownership explicit:

`carrier alpha -> legacy body optics -> V4 body form -> component identity -> protected rear-neck cleanup -> palette`

## Proof status

The fixed-seed T-shirt, polo, and sweater vest all pass current structural validation.
Human visual QC remains authoritative.

This is not declared production-ready. Pass 1 is intended to prove that a code-level ownership correction can create a materially different, cleaner render rather than another nearly-identical micro-fix.
