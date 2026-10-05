# bucket_ai_inpaint_01 — AI hat inpainted onto the real farmer, cut out by diff

## Status (2026-10-05)

ACCEPTED (committed): policy-hair mannequin capture, true-hat masks, three-tool
inpaint runs (`v3/`, `pixellab/`, `spritefusion/`), merged core cut (`merged.py`),
vanilla-structured outline repair (`outline.py`, `outline_preview.py`) and its
outputs `outlined_*_1x.png` (8 hats) + `OUTLINED_ALL9.png`.

EXPERIMENTAL / REJECTED (local only, not committed):
- `REJECTED_decoration_round/` — decoration round failed; see its README.
- `*_spritefusion_gingham_*` — SF placed the hat higher and redrew the hair inside
  the core; dropped.
- `v1_toobig/`, `v2_wronghair/`, `prep.py`, `run.py`, `extract.py` — superseded
  rounds (mask too big; wrong hair, 38 instead of policy 30).

None of these hats are approved source art or loaded in game yet; every "worn" image
is a composite onto the real policy-hair mannequin capture.

Rules-waived test (user-approved). Base = QC bridge `front_nohat` capture,
session 20261004-220717/ai_bucket_base. [WRONG, corrected in v3: the claim that
hairstyle 38 is unaffected because it has no HairData CoveredIndex ignores vanilla
Farmer.getHair(), which maps 38 -> 30 under DrawObscuredHair.] Retro Diffusion `inpainting` edit tool via
REST (`X-RD-Token`), $0.18/run.

- `prep.py` base + mask. RD reads the mask from ALPHA (opaque white = regenerate,
  transparent = keep); an opaque RGB mask regenerates the whole image
  (`out_olive_IGNOREDMASK.png`).
- `run.py <name> <seed> <prompt>` one inpaint.
- `extract.py` diff vs base -> hat, 4x4 majority snap -> 1x, contact sheet, `report.json`.

Result: 0 px changed outside mask (clean diff). Output is NOT on the 4x grid
(140-233 mixed blocks); hats came out 22-24 x 14-16 game px, wider than the 20x20
FS hat frame (vanilla bucket ~14 x 13). Pixels the AI drew in the same colour as
the hair underneath are missed by the diff (holes in pink/denim).

## v2 — vanilla-sized mask (v1 results moved to `v1_toobig/`)

Mask = vanilla Bucket Hat footprint +1 game px, cut at the brow line (16x10 game
px). Hats now 15-16 x 10 game px, same scale as vanilla (`VS_VANILLA_BUCKET.png`).
Extraction changed to "inside mask and not backdrop" plus majority-of-hat block
snap; a pure diff dropped hat pixels that matched the hair colour.
Remaining gap vs vanilla: AI hats are dome/bell shaped with no flared flat brim.
Denim reads closest; olive came out camo-noisy.

## v3 — correct mannequin (v2 moved to `v2_wronghair/`)

Vanilla `BucketHat` is `showRealHair=false` -> `DrawObscuredHair`. Vanilla
`Farmer.getHair()` (decompiled, 1.6.15) maps hairstyle 38 -> 30 under it; HairData
CoveredIndex is NOT the whole story. QC bridge now writes `{dir}_nohat_policy.png`
(hat removed, policy hairstyle kept) + `hair_real`/`hair_policy` in render_state.
True hat = worn vs nohat_policy (old `hatonly` also counted the hair swap):
vanilla Bucket Hat front = 14x9 game px, 94 px.
Capture: qc_bridge/captures/20261004-231349/ai_bucket_mannequin. Script: `v3.py`.
exact mask = true vanilla hat (14x9); loose = +1 game px (16x11) + flat-brim prompt.
Sheet: `v3/V3_CONTACT.png`. One parallel call 500'd after being charged (exact/pink
rerun) -> run calls sequentially.

## v4 — PixelLab + SpriteFusion, merged core/allowance cut

New hats (mustard corduroy, red gingham, green + mushroom patch), same mannequin and masks.
- PixelLab `inpaint_image_pro_flash` at native 64x64 (1 px = 1 game px, no snapping),
  5 generations each, mask = binary RGB. Jobs in `pixellab/jobs.json`.
- SpriteFusion has no mask: `sf_hat.py` runs `edit` on the 1x mannequin (no `size`
  field allowed for edits), aligns the trimmed output back (scale+offset scored outside
  the mask), skips the 6x preview. 15 credits each. SF redraws the face/hair too.
- `merged.py`: core = true vanilla footprint (shape fixed, every px is hat);
  allowance = +1 px ring, decoration only. First "rare colour" rule kept outline and
  brim spill (18-40 px) -> tightened to drop colours near core-common, core-edge
  (outline) or mannequin colours. Result: 0 decoration px kept on all 9 -- none of
  these generations put decoration in the ring; they used it for brim/outline, so the
  cores lose their side outline. Sheet: `MERGED_CORE_ALLOWANCE_3TOOLS.png`.

## v5 — vanilla-structured outline repair + decoration round

`outline.py`: vanilla Bucket Hat front gives outline STRUCTURE only (34 px, darkest
ramp step = external contour, 1 px, continuous; interior shading untouched). Colour
is each hat's own nearby body colour, darkened per the vanilla hats.png corpus (110
front frames: edge/interior luminance 0.38 dark / 0.37 mid / 0.35 bright, ~0.30
yellows; bright coloured bodies hue-shift ~-23 deg), capped at HLS L<=0.30, S<=0.65
(a lum-matched saturated red stayed vivid on RD pink). <=2 outline colours per hat;
AI pixels already that dark are kept. Bucket Hat's own 0.45 ratio was too light for
colour (first mustard preview). Inputs `merged_*` untouched -> `outlined_*`.
Sheets: `OUTLINE_PREVIEW_mustard.png`, `OUTLINED_ALL9.png`. SF gingham is bad input
(SF hat higher + redrawn hair inside the core) -- drop it.

`REJECTED_decoration_round/deco.py`: outlined hat frozen, RD inpaints only the 1 px allowance ring, decoration
filter after. FAILED: the AI used the ring to thicken the outline (31-38 ring px
changed), only 2-3 px survived the filter and they are stray face-tone/grey noise,
not decorations. A 1 px ring is too thin to hold a decoration.
`REJECTED_decoration_round/DECORATION_ROUND.png`.
