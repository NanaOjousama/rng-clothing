# RNG Clothing Fitting

Adjust how a generated cap sits on your head, at any sewing machine.

Standalone and player-facing. It is **not** part of the QC Bridge, which stays
dev-only, and it never uses the Fashion Sense Hand Mirror.

## How it behaves in game

Walk up to a **vanilla sewing machine** wearing one of our generated caps and an
*Adjust Fit* button appears beside the tailoring menu. Wearing anything else —
or nothing — the button never appears and the sewing machine is exactly vanilla.

| | keyboard | controller |
|---|---|---|
| open fitting | click the button | `LT` |
| move | arrows / WASD | d-pad or left stick |
| switch cap ↔ design | `Tab` | `LB` / `RB` |
| turn the preview | — | `Y` |
| reset | `R` | `X` |
| save | `Enter` | `A` |
| cancel | `Esc` | `B` |

Every action has an on-screen button too, so nothing is reachable by only one
input device.

## What it does not do

* **No Harmony patches.** It listens to SMAPI events and writes public
  properties on Fashion Sense's own loaded models.
* **No global input suppression.** The one `Suppress` call is for the single
  button press that opens the menu. The fitting screen is a real
  `IClickableMenu`, so the game routes input to it the way it does for any menu.
* **It never replaces the tailoring menu**, and never rewrites a generated
  pack on disk.

## Why one step is one pixel

Fashion Sense's `HeadPosition` is `int X, int Y`. Half-pixel offsets were
tested in game across nine models: `X ±0.5` and `Y ±0.5` all produced
byte-identical output to one another, and the hat **was not drawn at all** — a
fractional value fails to deserialise and Fashion Sense silently declines to
render while still listing the appearance. Integer offsets matched exactly,
each step moving 4 screen pixels crisply.

So the smallest renderer-safe increment is one sprite pixel, and that is what
the UI exposes.

`Scale` is a separate axis, and it was tested: **it failed, so there is no
scale control.** At the proposed 0.95 and 1.05 multipliers (3.8 and 4.2 against
the 4.0 default) roughly a third of all pixel runs come out an irregular width —
1, 2, 3, 5, 7 and 9 screen pixels mixed where every one should be 4 — while the
4.0 default and a clean 2x both measure 0.0% irregular. It also resizes some
facings and not others. Details in `authored/measurements/fs_scale.md`.

## The direction inversion

`HeadPosition` runs opposite to screen direction: `X+1` draws the hat 4px
**left**, `Y+1` draws it 4px **up**. The player never meets that. The mapping is
inverted in exactly one place — `Fit.HeadPosition` — and everything else, the UI
and the saved data included, is in plain screen directions where right and down
are positive.

## Defaults are never overwritten

A generated cap keeps its authored position in its own `hat.json`. A player's
adjustment is stored separately, per save file, and re-applied on load. That is
what lets **Reset** recover the generated default exactly, and what keeps
re-rolling the same seed reproducible.

`fitting.json`, written beside each cap by the generator, carries the authored
default per direction (assuming `{0,0}` would silently move the 63% of source
hats that rely on a non-zero value), the per-pixel safe mask, and the colour
each safe cell has with no design on it — moving a design means repainting what
it left behind, and only the generator knows what was underneath.

## Moving a design is blocked, not clipped

A design may only occupy cells in the approved per-pixel safe mask. A move that
would take any cell outside it is refused **whole** — never clipped, never
deformed, never partly moved, because half a mark is a different mark. The visor
and the rim are outside the mask, so they are untouched by construction rather
than by promise.

Room to move is currently tight, because the mask is 16 cells and the marks
nearly fill it:

| design | legal positions |
|---|---|
| `bar` | 8 |
| `angle_l` | 7 |
| `dot` | 6 |
| `chevron`, `twin_bars` | 3 |
| `zigzag` | 2 |
| `ring` | **1 — cannot move** |

Admitting row 8 into the mask would roughly double every one of these
(`ring` 1 → 6). That decision is still open.
