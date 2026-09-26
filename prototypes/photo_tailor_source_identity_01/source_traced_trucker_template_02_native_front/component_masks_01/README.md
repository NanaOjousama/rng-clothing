# Trucker 26×26 explicit component-mask approval proof

These masks were manually traced against the accepted aligned-source pixels.
They are not inferred from brightness, rows, or color membership.

Recolorable component interiors:

- `front_panel`
- `rear_mesh` (including the mesh visible at both sides of the front view)
- `brim`
- `top_button`
- `back_closure`

The transparent back opening is recorded as protected negative space. Every
occupied pixel outside a component interior is automatically protected as
construction: outlines, seams, borders, and rough/cut-off source remnants.

The left masks are stored explicitly and verified as exact mirrors of the right
masks. The mask document is bound to the accepted decoded-pixel SHA-256.

Status: user-approved on 2026-09-26 as the reviewed trucker component masks.
They are authorized for isolated source-preserving proofs, but are not connected
to production.
