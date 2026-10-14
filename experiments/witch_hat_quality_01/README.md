# witch_hat_quality_01: why the AI hats looked muddy, and a native-grid witch-hat forge

AI-ORIGINAL lane (CLAUDE.md §2b). Started 2026-10-11. Scope (user): witch hats only; the old
AI witch sprites are a failed baseline, not something to polish. The **vanilla Witch Hat is the
CONTROL** for structure, silhouette and readability, never a design to copy or recolour.

## 1. Diagnosis (measured: `tools/benchmark.py` -> `out/benchmark.json`, `out/benchmark_sheet.png`)

Benchmarks: vanilla Witch Hat, Emily's Magic Hat and Paper Hat; lovisity Mage and Magician
hats; Seyph pointed elf cap. These are measured and shown only.

| | benchmarks | old AI witch hats |
|---|---|---|
| form | chunky volumes; brim 2-3+ rows showing its top | 1-3 px stalk on a 1-row line |
| light | consistent form shading (lit side, shadow side, brim top vs underside) | k-means patches; two lit from below |
| ramps | 3-9 steps per material, often hue-shifted | 1-2 colour families |
| speckle | 0.08-0.44 | 0.05-0.12 (not the problem) |

**Cause:** shrinking an illustration to 16 px collapses tapering forms and throws away
deliberate shading. Better downscaling can't fix that. The sprite has to be **built on the
native grid**.

## 2. Control structure (vanilla Witch Hat, measured per row, pixels not copied)

- The crown is a narrow column, 5-6 px wide, with a blunt tip that leans 3-4 px.
- The brim is a deep oval, 16 px wide by 7 rows: most of the sprite is brim seen from above.
- The tip leans to the wearer's side and backward. It shows in all 4 views at full height:
  front right, back left, both side views toward the back of the head.

## 3. The forge (`tools/forge.py`, pure Python)

A design (parameters) is ray-cast once per native pixel centre, with no supersampling and no smoothing:
- **brim:** an elliptic slab with droop, curl, wavy edge and an optional rim-trim material
- **crown:** a tube swept along a bending axis (lean + crook), blunt tip
- **band:** raised above the brim's front edge, so trims read from the front
- **decals:** buckle, charms (star / moon / dot / patch) and a tip pom-pom, placed in 3D, so they
  only show from the side they face
- **camera:** orthographic, 36° elevation (deep brim oval, as in the control)
- **light:** fixed in camera space (top-left, every view)
- **colour:** hue-shifted OKLCh ramps (cool shadows, warm muted lights); the brim is kept in the
  crown's value range
- **outlines:** coloured (the darkest step of each material); the lit edge uses selective outline;
  inner contours where parts overlap; one highlight pixel
- **views:** all 4 come from one model. Each view keeps the tip's sideways lean and drops its
  toward/away part, the control's convention, so the hook never foreshortens away.

Iterations v0-v8 are in `out/forge_v*/`, each with a `vs_control.png`.

## 4. AI as the designer (`tools/gen_witch_briefs.py`, `tools/read_brief.py`; laptop)

SDXL base 1.0 (no LoRA, no training), 8 witch concepts x 2 seeds, round-4 guidance (generic
tinted cone blank). Renders: `C:\Users\Chris\ai_original_test\witch\briefs_r1\` (`renders.png`).
The reader turns each render into forge parameters:
- crown / band / brim / rim / accent colours from region medians
- lean side and amount, and hook
- proportions
- accent blobs as buckle / charms, and a tip pom-pom
- the prompt's own words pick the charm shape and brim character

All 16 read and forged: `out/r1/` (first read), `out/r1b/` (narrower crowns, raised band).

Reader errors seen (to fix next):
- missed frost_lilac s101's pom-pom
- invented a white pom-pom on ember_black s202 (a tip highlight)
- frost_lilac s202 squashed by an over-read lean
- crown width over-measured (band oval included), corrected by x0.82

## 5. Result: `out/WITCH_COMPARISON_round1.png`

Rows: CONTROL, then the best PREVIOUS AI hat, then six new picks (midnight stars, moss + orange
buckle, plum + gold buckle, pumpkin, storm teal, ember black). Columns: 4 views x6, the same
at game scale x4 on grass, and true size x1.

By eye at 1x and 4x, the new hats read as witch hats about as quickly as the control, in all
four views, and each is its own design (colour, band, buckle, charm, lean). The previous AI
hats read as flat sticks.

## Not yet proven / next

- worn capture (nothing installed: the user reviews the sheet first)
- the designs are still fairly plain: small charms; no ribbons, bow tails, stitched patches,
  feathers or fabric folds yet
- reader errors above
- light pastels (rose, frost) look washed out; they need a darker ramp floor
- the forge is witch-specific by design; other families would need their own geometry, or
  a LoRA (`experiments/lora_sdxl_research/PROPOSAL_phase1.md`, awaiting approval)
