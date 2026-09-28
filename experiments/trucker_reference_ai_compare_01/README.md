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

The retry succeeded after credits became available. Sprite Fusion returned 12 native 32x32 front-view trucker references from the front-focused request in `spritefusion/request.json`. Batch: `spritefusion/SPRITE_FUSION_TRUCKER_FRONT_BATCH_X8.png`. The prompt explicitly keeps the visor subtle/tucked so front-view readability comes from taper, lower-edge curvature and the crown-to-visor join rather than exaggerated forward projection. `spritefusion/status.json` records the successful request and credit state.

## Recommended Claude sheet

`CLAUDE_FRONT_VISOR_SHORTLIST_X8.png` now includes PixelLab, Retro Diffusion and Sprite Fusion candidates chosen for a **subtle straight-on front-view visor**. Use these only to improve front visor width, taper, lower-edge curvature and crown-to-visor join. Do not force projection; too much visible visor depth raises the apparent camera angle. Keep the approved side/back geometry unchanged unless separately requested.

`TRUCKER_FRONT_THREE_TOOL_COMPARE_X7.png` is the representative three-tool comparison.
