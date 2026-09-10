# Stardew Visual QC Bridge

Development-only SMAPI companion that exposes what Stardew **actually renders**,
so generated headwear can be measured against the real Fashion Sense draw rather
than against a reconstruction of it.

Not a general automation mod. It reads state, faces the player, equips hats, and
captures frames — all things a player can already do.

## Install / build

```
cd test-helpers/StardewVisualQCBridge
~/.dotnet/dotnet build -c Release
```

Built against **net6.0** (Stardew 1.6.15) with ModBuildConfig 4.4.0 from the local
NuGet cache — no network needed. `GamePath` is pinned in the `.csproj` for this
Steam Deck. The only compile reference beyond SMAPI is the `Newtonsoft.Json.dll`
SMAPI already loads, referenced with `<Private>false</Private>` so nothing extra
is copied. **No new runtime dependency.**

Installed to `Mods/StardewVisualQCBridge/`. `config.json`:

```json
{ "BridgePath": "/run/media/deck/USD00/RNG_clothing/qc_bridge",
  "PollIntervalTicks": 15, "Enabled": true }
```

`Enabled: false` makes the mod subscribe to nothing at all. Delete the folder for
a release build.

## Transport

A directory of JSON files, deliberately — inspectable, survives a crash, needs no
dependency, and works from Claude Code, a shell, or by hand.

```
qc_bridge/
  requests/    caller writes <id>.json, the mod claims it by deletion
  responses/   mod writes <id>.json (write-then-move, never half-read)
  captures/<session>/<label>/…
  latest_state.json
```

## Commands

`ping` · `list_hats` · `equip_hat` · `next_hat` · `previous_hat` · `clear_hat` ·
`set_direction` · `set_scene` · `get_render_state` · `capture_hat` ·
`capture_all_directions`

From the console: `qc list`, `qc equip <id>`, `qc dir front`, `qc capture_all`.
From here: `python3 tools/qc.py capture_all label=seed000`.

## What a capture contains

Per direction, two different things that must not be confused:

| file | what it is |
|---|---|
| `<dir>_screen.png` | the **actual backbuffer** — the authority |
| `<dir>_head.png` | head crop of the same backbuffer |
| `<dir>_worn.png` | the farmer through `FarmerRenderer.draw`, offscreen |
| `<dir>_nohat.png` | the same farmer, hat cleared |
| `<dir>_hatonly.png` | their difference — the hat's real drawn footprint |
| `render_state.json` | every value the renderer used |

The isolated pass is **not** a synthetic composite: it calls the same
`FarmerRenderer.draw` that Fashion Sense prefixes, so it goes through the whole
real pipeline. It exists because the backbuffer has a world behind it and alpha
is therefore meaningless for measurement. The screenshot stays the authority for
"does this look right"; the isolated pair is what makes seating, face intrusion
and hair relationship *measurable*.

The `nohat` difference is the key idea: an isolated 20×20 sprite cannot tell you
where a hat sits on a head. A pair of real renders can, because the head is in
both and the hat is in only one.

## The real hat draw path

From `DrawManager.DrawAppearance` and `AppearanceHelpers.GetFeatureOffset`
(Fashion Sense 7.5.0), read from source, not memory:

```
screenPos = Position + Origin + PositionOffset + featureOffset
origin    = Origin + (HeadPosition.X, HeadPosition.Y)
scale     = model.Scale * DrawTool.Scale        // model.Scale defaults to 4
source    = (StartingPosition.X, StartingPosition.Y, HatSize.Width, HatSize.Length)
flip      = model.Flipped                        // SpriteEffects

featureOffset.X = -8 + (flip ? -1 : 1) * featureXOffsetPerFrame[frame] * 4
featureOffset.Y = -16 + featureYOffsetPerFrame[frame] * 4 + 4 + heightOffset
   where flip = who.FarmerSprite.CurrentAnimationFrame.flip
```

Three things this settles that the old synthetic composite got wrong, or could
not have known:

1. **`HeadPosition` is added to the sprite ORIGIN, not the position.** Its screen
   effect is therefore `-HeadPosition * scale`, not `+HeadPosition` pixels. The
   validation pack README's formula is wrong; it is harmless only because we
   write `X = 0`.
2. **The offset is per animation FRAME**, via `featureXOffsetPerFrame` /
   `featureYOffsetPerFrame` — the head bob. The synthetic composite used one
   fixed offset for every frame, so it could not reproduce a walking farmer at
   all, and captures must be taken on a settled idle frame or they measure the
   wrong thing.
3. **Direction mapping is SDV facing order**, not sheet order:
   `0 up→BackHat, 1 right→RightHat, 2 down→FrontHat, 3 left→LeftHat`
   (`HatContentPack.GetHatFromFacingDirection`). Left is an authored frame *and*
   the animation frame reports `flip`, which negates the X feature offset but
   does **not** mirror the texture — `SpriteEffects` comes from `model.Flipped`
   only. Our pack is correct here; the risk of double-mirroring is real and now
   documented.

## Limitations, honestly

* Nothing has yet been captured from a running game — the bridge is built,
  installed and dry-tested only. Every number in Parts 5–8 waits on that.
* `GetBackBufferData` is used for the screenshot. If a driver refuses it the
  capture fails open and says so in the response rather than substituting
  anything.
* Zoom is **recorded, not set**: `Options.zoomLevel` is derived and read-only in
  1.6, and forcing base zoom mid-session desyncs the viewport. A QC run is
  comparable only if the player does not change zoom during it.
* The bridge does not patch Fashion Sense or the renderer. If the *final* draw
  arguments are ever needed rather than the recomputed ones, that would need a
  narrow QC-only Harmony postfix, which is deliberately not here yet.
