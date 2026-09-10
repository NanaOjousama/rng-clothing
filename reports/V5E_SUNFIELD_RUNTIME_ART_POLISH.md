# V5E Sunfield Pathfinder Runtime Art Polish

## Frozen runtime contract

Live front, right, and back testing confirmed that `NATIVE_ANIMATED_SLEEVES_V1` fixes the detached-arm regression. This contract is now frozen: the Fashion Sense Shirt retains `HideSleeves: false`, three `SleeveColors`, `Scale: 2`, and `BodyPosition: (0,32)`; the coordinated preset retains `SleevesId: None`; and no custom `Sleeves/` atlas may be exported.

The rejected 32x64 Scale-2 custom Sleeves atlas remains permanently guarded. This pass does not restore or reinterpret it.

## Art-only corrections

- Front lapels now use the jacket's dye ramp instead of bright undershirt color. The bounded olive/neutral inner layer remains the only strong central layer cue.
- Pocket flaps and bodies now read as constructed jacket fabric rather than two bright blocks. A small connected shadow termination gives each pocket depth.
- Shoulder-panel clusters now flow toward the lapels. The upper torso exterior uses a mid-dark fabric bridge where the native Farmer sleeve begins, avoiding a full dark vest-like cut line.
- The isolated bright pointed back V was replaced by a two-cell undershirt glimpse enclosed by a low shell-fabric collar and recess. The collar connects into the existing yoke.
- Side views retain a bounded inner opening, add a descending shoulder/shell break, and give the pocket a compact body beneath its flap.
- The darkest exterior contour remains concentrated at the neck recess, lower side shell, underarm termination, and hem corners. It is no longer uniformly applied through the native sleeve junction.

No alpha cells, anchors, scale, direction mapping, Fashion Sense fields, preset layers, or native sleeve colors were changed.

## Status

- Native arm attachment contract: **FROZEN_RUNTIME_PASS**
- Sunfield Pathfinder art: **ART RETEST REQUIRED**
- Left-direction runtime appearance: still requires the requested live visual review even though it inherits the same frozen native arm contract.
