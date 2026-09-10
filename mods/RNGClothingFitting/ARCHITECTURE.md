# Fitting mod architecture

Patterns adapted from Cheerful Pixels (see
`references/cheerful-pixels/STUDY.md`), reshaped for a masked garment workflow
rather than a free canvas.

## Files

| file | role |
|---|---|
| `ModEntry.cs` | SMAPI events, sewing-machine hook, **deferred menu opening**, session store |
| `FittingGeometry.cs` | **every rectangle**, and the **only** screen↔cell mapping |
| `FittingMenu.cs` | the screen: vanilla chrome, controller-snapped focus, readability strip, mask grid |
| `FittingData.cs` | `CapSidecar`, `Fit`, `FitRules` — movement legality |
| `FitHistory.cs` | `FitSnapshot` + bounded undo/redo |
| `Symmetry.cs` | reusable mirroring wrapper (implemented, not yet consumed) |
| `FittingSession.cs` | per-item **view** state + `SessionStore` |
| `FashionSenseBridge.cs` | FS reflection, **dirty-flag** texture updates, shared frame composer |
| `CapCatalog.cs` | sidecar discovery by item id |
| `FitStore.cs` | per-save persistence of fits |
| `../RNGClothingFitting.Tests/` | 120 headless checks over the pure logic |

## The load-bearing decisions

**Deferred opening.** `OnButtonPressed` only sets `openRequested`;
`OnUpdateTicked` opens the menu a tick later and **re-checks everything**,
because the menu or the worn hat can change in that tick. Swapping
`Game1.activeClickableMenu` from inside an input event leaves the old menu
mid-dispatch.

**One geometry source.** Drawing and hit-testing both read `FittingGeometry`.
This is not hypothetical: an earlier version placed the "Adjust Fit" button by
one expression and hit-tested it by another, and they disagreed off-screen.
Rectangles are computed on demand, never cached, so a UI-scale change cannot
leave a stale bound behind.

**One coordinate mapping.** `ScreenToCell` / `CellToScreen` are exact inverses,
and the tests assert that **every pixel of every cell** maps back to its own
cell at 1x, 2x and 4x — not just the corners.

**Snapshot undo, captured before the change.** That is what makes one Undo land
on the state the player last saw rather than one step short of it. A capture
that would record no change is discarded, so a blocked nudge never costs an
undo step. Depth is capped at 24.

**Dirty-flag textures.** `MarkMotifDirty` is cheap and idempotent; `FlushMotif`
runs at most once per frame from `update()`, and skips entirely when the design
has not moved from what is already on screen. Hat position needs none of this —
`HeadPosition` is a property FS reads while drawing, so assigning it is free.

**One frame composer.** `ComposeFrontFrame` is used by *both* the on-screen mask
grid and the texture handed to Fashion Sense, so the preview cannot disagree
with the result. The grid draws each source pixel as one filled square, so it
is nearest-neighbour by construction and no filtering can creep in.

**Controller-complete, not controller-only.** Every action is a real
`ClickableComponent` with neighbour links, so the game's own snappy-menu
navigation walks the whole screen with the d-pad and A. The left stick
additionally nudges and the shoulder buttons switch target, but nothing is
reachable *only* that way — and nothing is mouse-only either.

## Adapted from Cheerful Pixels

| pattern | how ours differs |
|---|---|
| deferred open via a request flag | same shape; re-validates on the tick |
| layout as `Get*` rectangles | same; ours is one class, not ~70 methods on the menu |
| single `ScreenToCanvas` | ours adds the exact inverse, and tests it per-pixel |
| packed snapshot undo, bounded by config | same; ours also drops no-op captures |
| dirty-flag texture upload | same; ours also skips when nothing moved |
| 1x/2x/4x readability | same, but the worn farmer stays on screen as the authority |
| symmetry as a wrapper | vertical only; **the mask overrides the mirror** |
| session restore | ours restores view state only, never the garment |

## Deliberately excluded

**All blending.** Watercolour, soft round, smudge, drybrush, chalk, lift, and
continuous flow/opacity. Every one invents colours between two existing ones.
Our caps carry a baked 6-colour palette with `DisableGrayscale: true`, and a
blended pixel is exactly the "foreign colour" the Scale test used as a
resampling detector. Painting must stay hard-edged, one palette colour per cell.

**Free colour selection.** No HSV/hue/alpha pickers. Motif colour must clear
measured guardrails (contrast ≥60 vs crown; hue ≥60° **or** perceptual distance
≥30 from *both* visor field and outline). A colour wheel lets a player make a
mark that vanishes into the visor.

**Resizable rectangular canvas.** Our surface is a fixed 16-cell irregular mask.

**Tiling tools.** Seam checking, edge copying, half-offset, pattern types. A cap
logo does not tile.

**Loose PNG export.** Our edit becomes a live FS texture plus a per-item
override. The pack on disk is never rewritten.

**Custom studio chrome.** `drawDialogueBox` and vanilla fonts throughout.

**Mouse-only input.** Cheerful Pixels has zero controller support; a search of
its assembly for `gamepad`, `Buttons`, `snapTo`, `applyMovementKey`,
`currentlySnapped` returns nothing.

## Ready for the masked editor

In place and proven: the grid surface with out-of-mask cells visible but dimmed,
the per-pixel coordinate mapping, the symmetry wrapper, undo with a
`PaintedCells` slot that already round-trips, cursor and swatch fields in
session state, and the dirty-flag upload path.

Still needed: a paint/erase mode on the grid, a validated swatch row derived
from the cap's palette, extending `FitRules` to per-cell edits, and persisting
painted cells in `FitStore`.

## Scale

**Not exposed.** Measured 2026-09-09: at 3.8 and 4.2 (the 0.95/1.05 multipliers
of the 4.0 default) roughly a third of pixel runs come out an irregular width,
against 0.0% at 4.0 and at a clean 2x. `FitSnapshot.ScaleIndex` exists and is
inert. See `authored/measurements/fs_scale.md`.
