# Trucker front-view AI geometry references

Purpose: provide Claude's `prototypes/construction_printer/` with readable **front-view visor geometry evidence**. The existing side views were not the problem and should not be replaced from this experiment.

This is reference material only. Do not copy these colors or styling into production art. The approved trucker family master remains pixel/construction authority.

## PixelLab

`pixellab/PIXELLAB_TRUCKER_FRONT_BATCH_X10.png`

Generated at 32x32 using PixelLab Pro Flash with four prompts deliberately varying front visor geometry. Useful references:

- `PL02`: compact/short visor, clean inset lower edge.
- `PL03`: medium visor, clear shallow arc and tapered ends.
- `PL04`: broad visor, strongest stepped curvature.

## Retro Diffusion

`retro_diffusion/RETRO_DIFFUSION_TRUCKER_FRONT_BATCH_X10.png`

Generated at 32x32 with `rd_mini__fast_low_res`. Total RD generation cost recorded by the tool: US$0.068 for four images.

Useful references:

- `RD01`: very explicit crown-to-visor boundary and compact rounded visor.
- `RD04`: broad stepped visor, useful alternate shape evidence.

## Sprite Fusion

A front-focused request is ready at `spritefusion/request.json`, but the API returned HTTP 402 Payment Required before producing any output. `spritefusion/status.json` records the block. No unrelated or recycled Sprite Fusion image was substituted.

## Recommended Claude sheet

`CLAUDE_FRONT_VISOR_SHORTLIST_X8.png` contains PL02 / PL03 / PL04 / RD01 / RD04. Use these only to improve the **front visor profile**: width, taper, lower-edge curvature, and crown-to-visor join. Keep the approved side/back geometry unchanged unless separately requested.
