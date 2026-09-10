# Fashion Sense capability audit for V5

**Date:** 2026-09-05. **Source:** `FASHION SENSE/FashionSense-stable/FashionSense/`
(FS 7.5.0). Content packs used only as secondary evidence.
**Scope:** read-only audit. No V5 code changed. Sailor remains frozen.

## Verified mechanics

| question | answer | evidence |
|---|---|---|
| How is a custom frame selected? | `new Rectangle(StartingPosition.X, StartingPosition.Y, ShirtSize.Width, ShirtSize.Length)` | `DrawManager.GetSourceRectangle` L1180-1193 |
| Is 8×8 required? | **No.** Convention only. | Corpus: 1140×`8x8`, 132×`58x80`, 32×`16x16`, plus `8x7`, `10x11`, `10x12`, `16x14`, `10x8` |
| What does ShirtSize control? | Only the source rect W/H. Nothing else. | `AppearanceHelpers.GetModelSize` L1204 |
| How is scaling done? | `model.Scale * DrawTool.Scale`, `Scale` defaults to `4f` — identical to the vanilla path's hardcoded `4f`. | `DrawManager` L623; `AppearanceModel.Scale` L34 |
| What is BodyPosition? | The sprite **origin offset**: `DrawTool.Origin + new Vector2(positionOffset.X, positionOffset.Y)`. Animation `Offset` is added to it per frame. | `DrawManager.GetPositionOffset` L1140-1176 |
| Can it vary by direction? | **Yes** — each of the 4 directional models is a separate `ShirtModel`. | `ShirtContentPack.GetShirtFromFacingDirection` |
| Can frame envelopes differ per direction? | **Yes**, officially. `MageRobe` front is `16x14` @ `BodyPosition {3,2}`; its other three are `8x8` @ `{0,0}`. | `Examples/[FS] Example Pack/Shirts/MageRobe/shirt.json` |
| Draw offsets | `GetFeatureOffset` gives per-direction shirt offsets; `DisableNativeOffset: true` zeroes them for full manual control. | `AppearanceHelpers` L1066-1090 |
| Arm interaction | **Sleeves draw at `DrawTool.Position + who.armOffset`. Shirts never receive `armOffset`.** | `DrawManager.DrawSleevesCustom` L668 vs shirt draw L623 |
| Sleeve colour control | `SleeveColors[0..2]` overwrite farmer palette indices 256/257/258. Recolour only — cannot change sleeve geometry. | `DrawPatch` L216-218 |
| Clipping / stencil masks? | **No.** All masks are colour-keyed recolour: `IsMaskedColor` does exact RGB equality, builds a separate texture per mask layer, draws each tinted. | `AppearanceModel.IsMaskedColor`; `DrawManager.DrawColorMask` L985-996 |
| Layer control | `DrawOrderOverride {Preposition, AppearanceType}` per model *and* per animation frame; `Sleeves.DrawBeforeShirt`, `Accessory.DrawAfterSleeves/DrawAfterPlayer/DrawBehindHead`. | `Generic/DrawOrder.cs`; `LayerManager` L392-396 |
| Animation for shirts | Yes: `UniformAnimation`/`IdleAnimation`/`MovementAnimation`, frames advance along X, ~45 condition types, random durations, `SubFrames`. | `AnimationModel.cs`; `Condition.cs`; `Shirts/Blinky/shirt.json` |
| Independent garment pieces | Accessories, `MAX_ACCESSORY_LIMIT = 100`, each independently sized/positioned/animated/layered. | `AccessoryManager` L16 |

## A. Confirmed useful capabilities

### A1. Per-direction frame envelope (oversized front/side frames)
FS reads W/H per direction. A garment can give its front a 16×14 frame with a
compensating `BodyPosition` while the other views stay 8×8. Officially
demonstrated by `MageRobe`.

* **V5 uses it?** No — all four frames are hardcoded 8×8 / `BodyPosition {0,0}`.
* **Solves:** collars, lapels, shoulder mass and hanging flaps that currently
  must be squeezed into the torso box; gives the side view its own envelope.
* **Improvement:** moderate-to-high for *future* families (coats, dresses,
  robes). Low for Sailor, which is frozen.
* **Complexity:** medium. Projection currently assumes one envelope for all
  views; `required_coverage`, continuity and the atlas writer all key off 8×8.
* **Risk:** low — supported since early FS, used by the official example pack.
* **Fits V5?** Yes in principle: `Envelope` is already a first-class concept.
* **Recommendation: TEST** (prototype on a new family, not Sailor).

### A2. Sleeves as a separate appearance type
`SleevesModel` is a full appearance with its own 4 directions, `SleevesSize`
(default pack: **16×32**), ~200 frames mapped to farmer animation frames, and
it draws at `who.armOffset`.

* **V5 uses it?** No. V5 only sets `SleeveColors` (correctly).
* **Solves:** genuinely garment-shaped arms. This is the *only* mechanism that
  can put art on a moving arm — our repeated "strap on the arm", "sleeve
  detached", "bars through the elbows" reports were structurally unfixable in
  the shirt frame, which is why removing art from the outer columns was right.
* **Improvement:** high ceiling, but only for garments that need real sleeves.
* **Complexity:** **high** — ~200 animation-frame mappings, and it is a
  *separate equipment slot*: a shirt cannot force sleeves, so a generated
  garment would need a paired Sleeves appearance plus an outfit to bind them.
* **Risk:** medium — conflicts with whatever sleeves the player has equipped.
* **Recommendation: IGNORE for now.** Revisit only if a family genuinely needs
  arm geometry. `SleeveColors` already covers colour integration.

## B. Interesting, probably not worth it

* **`Scale` < 4 for higher density.** `Scale: 2.0` + `16x16` = same on-screen
  footprint at double resolution. Real and shipping — including our own
  `RNG-Clothing-Hoodie-Layer-Correction` (32 frames) and `[FS]HD clothes`
  (`58x80` @ `2.9`, 132 frames). **But** it makes garment pixels half the size
  of the Farmer's, which reads as mixed-resolution. Also shifts the offset
  maths (`16f * scale`, `heightOffset * scale`), needing `BodyPosition`
  compensation. **TEST at most**, and only as a deliberate art-direction change.
* **`ColorMaskLayers`.** Named, user-recolourable layers; the dominant corpus
  convention (1050 frames). V5 sets `DisableGrayscale: true`, which disables
  masks entirely (`HasColorMask()` returns false). That is the *correct* choice
  for us — V5's Color Architecture resolves exact colours, and handing recolour
  to the player would undo the identity-separation guarantees the QC enforces.
  **IGNORE**, deliberately.
* **Animation.** Rich and cheap to declare, but V5's remaining problems are
  static-composition problems. Animating them would add motion to a garment
  that does not yet read correctly still. **IGNORE now**, plausible later for
  Legendary-tier garments.
* **Accessories as garment pieces.** Up to 100 independently layered sprites
  with `DrawAfterSleeves`. Powerful, but consumes slots the player owns and
  sits outside the shirt abstraction. **IGNORE.**
* **`Flipped`.** Mirrors a frame; `MageRobe` reuses one side frame for both.
  V5 already renders both sides deterministically, so this saves nothing.
* `DrawOrderOverride`, `AppearanceSyncing`, `SkinToneMasks`, `IsPrismatic`,
  `HidePlayerBase`, `DisableNativeOffset` — all real, none address a current
  failure mode. **IGNORE.**

## C. Assumptions we had wrong

1. **"8×8 is the Fashion Sense shirt format."** It is a *convention*.
   `ShirtSize` is free-form; the corpus contains six other sizes and the
   official example pack ships a 16×14 front.
2. **"ShirtSize/BodyPosition are per-garment."** They are **per-direction**.
   V5 emits four identical blocks; `MageRobe` proves they can differ.
3. **"Scale must be omitted/4."** `Scale` is a real authoring lever, used by
   shipping packs — including earlier work in this very project.
4. **"The shirt frame can express sleeve/arm behaviour."** It cannot. Only
   `Sleeves` receives `who.armOffset`. Everything the shirt draws in its outer
   columns is static while the arm moves underneath it.

## D. Things Fashion Sense does not support

* **No geometric clipping, alpha stencils, or partial masks.** Every mask is
  exact-RGB colour replacement. There is no way to have the framework cut a
  garment against the body silhouette.
* **No occlusion against the Farmer body.** Draw order is the only tool.
* **No automatic outlining, AA, or silhouette treatment.**
* **No deformation/skeletal support.** The side view is an independent sprite;
  nothing interpolates between directions.
* **No sub-frame masking of the shirt by the arm.** Our neck holes, armpit
  gaps and boxy bands were **not** framework limitations — every one was
  authored art, and each was fixed in authored art.

## Ranked opportunities

1. **Per-direction frame envelopes (A1)** — the only finding that materially
   expands what V5 can express. *Prototype later, on a new family.*
2. **Scale/resolution change (B)** — real, proven, but an art-direction
   decision with a mixed-resolution cost. *Prototype only if deliberately
   chosen.*
3. **Sleeves appearance (A2)** — high ceiling, high cost, needs a slot we do
   not own. *Ignore until a family requires arm geometry.*
4. Everything else — *ignore*.

## Conclusion

**We are using Fashion Sense correctly.** `ShirtSize`, `StartingPosition`,
`DisableGrayscale`, `SleeveColors`, `HideSleeves` and the omission of `Scale`
are all right for what V5 produces, and the pack format matches the shipping
reference exactly.

The one genuine misconception is that the 8×8 envelope is imposed by the
framework. It is not — it is ours, and per-direction envelopes are officially
supported. That is worth prototyping for future families.

But it would not have prevented a single reported in-game failure. The armpit
pixel, the edge-to-edge bands, the flat flap, the boxy neckline and the
protruding side profile were all authored-geometry defects, and a larger canvas
would only have given them more room. **The remaining limits are our authored
art and construction, not Fashion Sense.**
