# bear_hood_structural_01 — review summary (2026-10-16)

**AI-ORIGINAL (CLAUDE.md §2b). Nothing approved, installed, retrained or downloaded. The frozen generator is untouched.**

**Question:** can structural guidance, instead of prompt or seed changes, give p4e10 a complete bear hood with round bear ears, an open face hole, proper flaps and visible tassels?

## Setup

- **Structure:** a 24×24 template.
  - Face ring and flaps: plurffle **Hood** family base (front, unchanged).
  - Added by rule: round bear ears and cord-and-bead tassels.
  - Palette: browns taken from your circled bear.
- **Model:** p4e10 at LoRA 1.0, **img2img** from that template. DPM++ 2M, 28 steps, CFG 8.5.
- **Prompt:** the T2 `construction` bear prompt, **verbatim**. The init image is the only change.
- **Renders:** strengths 0.45 / 0.60 / 0.75 × seeds 7, 8, 9, 11 = 12 renders, 202 s on the RTX 3060.
- **Why 24×24:** it is p4e10's trained frame. One cell = one Fashion Sense hat pixel at Scale 4. The frame is the vanilla 20×20 hat cell plus 2 px on each side and 4 px of headroom.
  - Export: `HatSize 24×24`, `HeadPosition {2, 4}`. No resampling anywhere.

## Sheets

| file | what |
|---|---|
| `bear_hood_hat_x1 / x4 / x10` | references row, then per seed: same prompt with **no template** (T2) → 0.45 → 0.60 → 0.75 |
| `bear_hood_worn_x1 / x4` | the same layout, composited on the vanilla farmer (front, frame 0) |
| `bear_hood_picks_*` | head-to-head: template, your circled bear, ear-flap c08 s11, then the 4 picks |

x4 is the default Stardew zoom (one hat pixel = 4 screen pixels). x1 is the raw file.

## Rubric — by eye at x4 worn (tassels checked on the exact rows 22–23)

| render | bear ears | open face | flaps | tassels | notes |
|---|---|---|---|---|---|
| template (input) | ✓ | ✓ | ✓ | ✓ bead | flat, 7 colours |
| circled bear (T1 base s9) | ~ dark, no inner ear | ✓ | ✗ short | ✗ | sits high; reads as ears on a cap |
| ear-flap c08 s11 | ~ small | ✓ | ✓ | ✗ | chin strap instead |
| no template (T2 s7 / s8) | ✓ | **✗ face covered** | — | ✗ | mask-like |
| **0.45 s7 / s8 / s9 / s11** | ✓ | ✓ | ✓ | ✓ 1-px bead | template kept almost exactly (IoU 0.98–1.00); darker shading |
| **0.60 s7** | ✓ | ✓ | ✓ | **✓✓ checkered pompoms** | **most complete** |
| 0.60 s8 / s9 | ✓ | ✓ | ✓ | ~ bead broken | s8 adds a brow nose |
| 0.60 s11 | ✓ | ✓ | ✓ | ~ faint | **brow eyes and nose: most bear character** |
| 0.75 s7 / s8 | ✓ | ✓ | ✓ | ✗ | s8 swaps tassels for a chin strap |
| 0.75 s9 | ✓ | ✓ | ✓ | ~ | furriest, 8 colours |
| 0.75 s11 | ✓ | ✓ | ✓ | ✗ | **defect:** magenta background bar across the chin |

**5 of 12 pass all four requirements** (all four 0.45 renders and 0.60 s7). 0 of 3 comparison bears pass.

## Verdict

- **Structural guidance works.** All 12 template-guided renders keep the round ears, the open face and both flaps. The same prompt with no template covers the face (seeds 7 and 8). Prompts and seeds never produced this structure on their own.
- **Best complete bear hood: `i2i_st060__s7`.** Best character: `i2i_st060__s11` (brow face; its tassels need fixing).
  - Both are visibly better than your circled bear and the c08 ear-flap bear on all four features.
- **Strength trade-off:**
  - **0.45** copies the template and adds little.
  - **0.60** is where real design appears (brow face, pompoms), and where 1-px features start to break.
  - **0.75** rewrites the small features: tassels are lost, a chin strap appears, the background leaks.
- **Honest limits:**
  - The template does most of the structural work. The AI's added value is detail: brow face, pompoms, fur shading.
  - The AI also takes the palette from 7 colours to 12–21 (near-duplicate shades). A palette snap is needed before any pack.
  - Tassels are capped by the 24×24 frame: there are only 2 rows below the flaps.
  - The worn view is a composite, not a QC Bridge capture. The game was not running.

## Next (not done)

1. Palette-snap the two picks to the template's 7-colour ramp, and review them again.
2. Make a worn capture through the QC Bridge (needs the game running and a test pack).
3. Right / left / back views, from the Hood base's own four directions.
4. Optional: the T2I-Adapter arm, only with approval, if 0.60's broken tassels need a structure lock.
