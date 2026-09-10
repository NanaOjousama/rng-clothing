# Cheerful Pixels (CosmicSweetpea) — in-game pixel editor study

Studied for one question: **what does a working in-game pixel editor look like,
and which parts transfer to letting a player draw or tweak a garment motif?**

Method and its limit: the mod ships as a single 122KB `CheerfulPixels.dll` with
no source. This is a **metadata** read — types, fields, method signatures,
enum members — via `MetadataLoadContext`. Signatures and architecture are
therefore exact; anything about what happens *inside* a method is inference
from its signature and neighbours, and is marked as such. No IL bodies were
decompiled.

Scale: 40 types, 175 methods on the menu class alone. It is a real editor, not
a toy.

---

## 1. How it opens the editor

Three routes, all in `ModEntry`:

* **A configurable key** — `ModConfig.OpenKey` plus `BackupOpenKey`, handled in
  `OnButtonPressed`.
* **A HUD button** — `ModConfig.ShowHudButton`.
* **An in-world NPC** — this is the interesting one. `AuraRoseTexture`,
  `AuraRoseAnchorTile`, `GetAuraRoseWorldBounds`, `GetAuraRoseCollisionBounds`,
  `UpdateAuraRoseCollision`, `IsAuraRoseVisibleHere`. A character is drawn into
  the world on `OnRenderedWorld` with her own collision box, and walking into
  or interacting with her opens the studio.

Opening is deferred rather than immediate: `OpenRequested` / `OpenRequestedBy`
are set by the input handler, and `OnUpdateTicked` calls `OpenStudio(string)`.
**This is a pattern worth copying** — opening a menu from inside an input event
is where mods fight the input system; setting a flag and acting on the next tick
sidesteps it.

There is also `OnConsoleCommand` for dev access, and `OnReturnedToTitle` clears
state.

## 2. How it maps input to pixel cells

**`Point ScreenToCanvas(int x, int y)`** is the whole contract — one method,
screen pixel in, canvas cell out. Everything else is layered on top:

```
receiveLeftClick(x, y, playSound)
  -> ScreenToCanvas(x, y)
  -> ApplyBrushWithSymmetry(Point, Color?)
      -> ApplyBrushAt(Point, Color?)          // once per mirrored position
          -> BrushEngine.Apply(canvas, kind, point, ...)
              -> PaintCanvas.PaintPixel(x, y, color, flow)
```

The geometry it needs is held in fields and a family of `Get*` rectangle
methods — `GetCanvasSpace()`, `GetCanvasDrawBounds()`, `GetEditorArea()`,
plus `ZoomAdjustment`, `PreviewScale`, `GetEditorZoom()`,
`GetBestFittingPreviewScale()`. So the mapping is (inferred, from those names
and types) an offset-and-divide against the canvas draw rectangle at the
current zoom.

Layout is expressed as ~70 `Get<Thing>Button()` / `Get<Region>()` methods
returning `Rectangle`, computed on demand rather than stored. Hit-testing is
then `rect.Contains(x, y)` in `receiveLeftClick`. Verbose, but it means layout
and drawing cannot drift apart — both read the same rectangle.

**Controller input: there is none.** A search of the entire assembly for
`gamepad`, `Buttons`, `snapTo`, `applyMovementKey`, `currentlySnapped` returns
**zero** hits. The menu overrides only:

```
receiveLeftClick(int, int, bool)
receiveRightClick(int, int, bool)
receiveScrollWheelAction(int)
receiveKeyPress(Keys)
```

It is a **mouse-and-keyboard-only** editor. On a Steam Deck it would be driven
by the trackpad-as-mouse, not by the sticks or d-pad. This is the single
biggest thing we must NOT inherit.

## 3. How it stores and saves edits

Two separate mechanisms, cleanly split.

**Undo** — in-memory, snapshot-based:

```
PaintCanvas.SnapshotPacked() -> UInt32[]      // whole canvas, packed
PaintStudioMenu.CaptureUndo()
PaintStudioMenu.UndoHistory : List<...>
PaintStudioMenu.RedoHistory : List<...>
ModConfig.MaximumUndoSteps : int              // bounded
```

`CaptureUndo()` is called *before* a stroke, and the depth is capped by config.
Packing a `Color[]` to `UInt32[]` makes each snapshot 4 bytes per pixel with no
object overhead — cheap enough that whole-canvas snapshots beat tracking deltas.

**Project persistence** — `ProjectService.Save(PaintProjectData)` / `Load()`,
one project at a time (`HasProject`). `PaintProjectData` stores the pixels as
`UInt32[]` alongside the *whole editor session*: canvas size, surface kind,
preview position and scale, grid visibility, current brush, primary/secondary
colour, brush size / flow / opacity indices, gradient settings. Reopening
restores the editor exactly as it was left, not just the artwork.

**Export** — `PaintExportService` writes real PNGs:

```
ExportSmart(canvas, surface, mode, w, h)
ExportArt / ExportPresetPack / ExportFullPack / ExportPreview / ExportTileRepeat
SavePixels(canvas, folder, name, bool, w, h)
FindOpaqueBounds(Color[], w, h) -> Rectangle
CreateProjectFolder() / OpenFolder()
```

`ExportMode` is `Transparent | Trimmed | CleanPreview | PatternPreview |
FullPack`, and `FindOpaqueBounds` is what makes `Trimmed` possible — it finds
the artwork's real bounding box and crops to it. `OpenFolder()` opens the output
directory in the OS file manager, which is a nice touch for a mod whose output
is files.

## 4. How it previews art

Three layers:

* **The canvas itself** — `PaintCanvas` holds `Color[] Pixels`, a `Texture2D
  Texture`, and a `Dirty` flag, with `GetTexture(GraphicsDevice)` as the
  accessor. The pattern (inferred from the flag's presence) is: mutate the
  array freely, set `Dirty`, and upload once when the texture is next asked
  for — **not** a `SetData` per painted pixel. `Dispose()` releases it.
* **The editor view** — `GetEditorZoom()`, `ZoomAdjustment`,
  zoom +/- buttons, `GetFitButton()`, `DrawCanvasGrid()` and
  `DrawCheckerboard()` for transparency.
* **A readability check** — `ReadabilityScale { One, Two, Four }` and
  `PreviewScale` / `GetBestFittingPreviewScale()`, plus `ExportPreview`. The art
  is shown at 1x / 2x / 4x so the author can judge it at the size it will
  actually be seen.

That last one is the same discipline we have been applying by hand all session
("judge visually at normal gameplay scale, not by metrics") — they built it
into the tool as a first-class control.

## 5. Does it use `IClickableMenu`?

**Yes.** `CheerfulPixels.Menus.PaintStudioMenu : IClickableMenu`, and it
overrides the standard `receive*` handlers rather than patching input. It draws
its own chrome — `StudioRenderer` is a tiny helper of `Fill`, `Border`, `Card`,
`CenterText`, `Truncate` over flat `Color` fields (`Panel`, `Raised`, `Border`,
`AccentBright`, `Text`, `Muted`, `Quiet`) — so it reads as a flat modern editor
rather than a Stardew dialogue box.

That is a deliberate choice and the opposite of ours: our fitting screen is
meant to feel like part of the game, so it uses `drawDialogueBox` and the
game's own fonts. Their approach is right for a studio the player sits in for
an hour; ours is right for a quick adjustment at a sewing machine.

## 6. What can be adapted, conceptually

Ranked by how much they would buy us:

1. **`ScreenToCanvas` as the single mapping.** One function, one direction,
   everything else built on top. For us the inverse (`CellToScreen`) matters
   too, for drawing the mask overlay.
2. **Snapshot undo via packed pixels, bounded by config.** Our motif is at most
   16 cells — a snapshot is trivial, and it makes experimentation safe. Undo is
   the feature that turns "adjust" into "draw".
3. **Deferred menu opening** (`OpenRequested` flag consumed on the next tick)
   instead of opening from inside an input event. Directly applicable to the
   sewing-machine hook we already have.
4. **Dirty-flag texture upload.** One upload per frame regardless of how many
   pixels changed. Our current `ApplyMotif` rebuilds and re-uploads the whole
   atlas per nudge — fine for one keypress, wrong for freehand drawing.
5. **Readability preview at 1x / 2x / 4x** as a control, not a habit.
6. **Symmetry as a wrapper, not a mode.** `ApplyBrushWithSymmetry` → N ×
   `ApplyBrushAt` is a clean shape, and **vertical symmetry is exactly what a
   centred cap logo wants**. This is the single most valuable borrowed feature.
7. **`FindOpaqueBounds`** for trimming a drawn mark to its real extent — useful
   for re-centring a motif inside the mask after the player draws it.
8. **Restoring the whole editor session**, not just the art.
9. **Layout as `Get*()` rectangle methods** so drawing and hit-testing cannot
   disagree. Verbose but it prevents a real class of bug — one I have already
   hit once in the fitting menu.
10. **`ToolEngine.AddOutline(canvas, color)`** — an outline assistant. A drawn
    mark that fails our contrast rule against the visor could be rescued by an
    outline rather than rejected.

## 7. What must NOT be copied

**The blending brushes.** `Watercolor`, `SoftRound`, `Blend`, `Smudge`,
`DryBrush`, `Chalk`, `Lift`, and the whole `BrushEngine` blend stack
(`GetWatercolorPaintColor`, `GetThreeColorBlend`, `Blend`, `Average`, `LerpStraight`)
plus `flow` and `opacity` as continuous values. Every one of these **invents
colours between two existing ones**. Our caps carry a baked 6-colour palette and
`DisableGrayscale: true`; a blended pixel is precisely the "foreign colour" my
own Scale test used as a resampling detector. On a 20×20 sprite it reads as mud.
Painting must be **hard-edged, one palette colour per cell, opacity 1**.

**Free colour selection.** `DrawSvPicker` / `DrawHuePicker` /
`DrawAlphaPicker` and arbitrary primary/secondary/tertiary colours. Our motif
colour has to clear measured guardrails — contrast ≥60 against the crown, and
hue ≥60° **or** perceptual distance ≥30 from *both* the visor field and the
outline. A free HSV picker lets a player produce a mark that vanishes into the
visor, which is the exact failure the guardrails exist to prevent. The player
should choose from **pre-validated palette entries**, not a colour wheel.

**A resizable rectangular canvas.** `CanvasTemplate`, `Resize`,
`DefaultTileWidth/Height`. Our surface is not a rectangle — it is a
**16-cell irregular mask** (rows 5–7 of the crown), and it is fixed.

**The tiling toolset.** `SeamChecker`, `SeamMode`, `SeamRepairDirection`,
`CopyLeftEdgeToRight`, `OffsetHalf`, `ExportTileRepeat`, `PatternType`. Built
for repeating wallpaper and rugs. A cap logo does not tile.

**Mouse-only input.** Non-negotiable for us: Steam Deck is a stated
requirement, so a cell cursor must be drivable by d-pad and stick.

**Their visual style.** Flat panels and custom chrome suit a standalone studio;
our brief is that it must feel like part of Stardew.

**Exporting loose PNGs to a folder.** Their output is files for the player to
use elsewhere. Our edit has to become a live Fashion Sense texture and a saved
per-item override — the pipeline already exists and is stricter.

## 8. What I think is actually worth building

Their model is *free canvas, free colour, soft brushes*. Ours would be
**constrained canvas, validated colour, hard pixels** — the mask is the design
surface, not a limitation bolted onto a rectangle.

A "draw your own motif" feature that fits our workflow is much smaller than
their studio:

* the **16-cell safe mask** as the canvas, drawn zoomed with a grid, with
  out-of-mask cells visible but locked (so the player sees the crown they are
  drawing on, and why they cannot leave it)
* a **cell cursor** moved by d-pad/stick, paint on A, erase on X — the same
  input model as the fitting screen already uses
* colours from a **short pre-validated swatch row** derived from the cap's own
  palette, every entry already passing the visor/outline guardrails
* **vertical symmetry** as a toggle, borrowed wholesale
* **undo/redo** via packed snapshots
* **live preview on the farmer**, which we already have
* the existing exporter as the only way out — so a drawn motif is subject to the
  same rules as a generated one

Notably absent: brushes, blending, opacity, layers, canvas sizing, tiling, file
export. The constraint set does most of the design work.

One honest caveat: this is a substantially bigger feature than fitting, and the
fitting mod is not finished being verified yet. Worth doing after.
