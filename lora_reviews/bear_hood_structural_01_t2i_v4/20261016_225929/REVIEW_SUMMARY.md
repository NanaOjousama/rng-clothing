# bear_hood_structural_01 — T2I V4: early-step-only adapter + palette-cleaned baseline (2026-10-16)

**AI-ORIGINAL (CLAUDE.md §2b). Inference only.**
- No training, no downloads, no production changes. The frozen generator is untouched.
- Earlier runs were read only.
- The harness edit is backward-compatible: **factor-1.0 control = V2, bit-for-bit, 4/4.**

## Question

Apply T2I-Adapter guidance (full V2 grid map) **only during the first 30 / 40 / 50 % of denoising**:
- img2img strength 0.75, from the **original template**. Its inner-ear and bead cells were verified pale `c68a4e`, and the init sha256 is unchanged.
- adapter scale 0.4, p4e10 LoRA 1.0.

Can the structure be locked early while the init's pale inner ears and tassel beads return late?

## Setup

16 renders, 200 s, seeds 7 / 8 / 9 / 11. Constant: T2 construction prompt verbatim, negative prompt, DPM++ 2M, 28 steps, CFG 8.5.

- img2img 0.75 runs **21** steps. The adapter was applied to the first **6 / 8 / 10 / 21** of them (factor 0.3 / 0.4 / 0.5 / 1.0). Steps applied and UNet calls are recorded per render.
- The factor works like the official pipeline's `adapter_conditioning_factor`, counted over the steps img2img actually runs.
- **Palette-clean of A i0.60 s7:**
  - its colours are merged by OKLab closeness down to **8**;
  - each group is represented by its most-used *existing* colour (no new colours);
  - **cells, silhouette and alpha mask are unchanged** (asserted);
  - result: 148 raw RGB values, i.e. 17 distinct colours, become 8.

## Per-feature evaluation (`v4_feature_eval.txt`; badge SFELCB; advisory, the eye decides)

Pass rules:
- **S**ilhouette: hood IoU ≥ 0.95.
- **F**ace opening: empty.
- **E**ars: pale inner ear, probe ≥ +40.
- f**L**aps: ≥ 90% present.
- **C**ords: present.
- **B**eads: present and ≥ +30 lighter than the hood.

| render | S | F | E (inner ear) | L | C | B (bead Δ) | colours | passed |
|---|---|---|---|---|---|---|---|---|
| TEMPLATE (input) | ✓ | ✓ | ✓ +112 | ✓ | ✓ | ✓ +101 | 7 | 6/6 |
| **A i0.60 s7** (current best) | ✓ | ✓ | **✓ +117** | ✓ | ✓ | **✓ +120** | 17 | **6/6** |
| **A i0.60 s7 PALETTE-CLEAN 8** | ✓ | ✓ | **✓ +119** | ✓ | ✓ | **✓ +132** | **8** | **6/6** |
| V4 factor 0.3 (6/21 steps), best = s7 | ✓ | ✓ | ✗ +8 | ✓ | ✓ | **✓ +66/+72** | 17 | 5/6 |
| V4 factor 0.3, s8 / s9 / s11 | ✓ | ✓ | ✗ −3…+11 | ✓ | ✓ | ✗ | 11–15 | 4/6 |
| V4 factor 0.4 (8/21), all seeds | ✓ | ✓ | ✗ 0…+7 | ✓ | ✓ | ✗ (s7 +12) | 13–18 | 4/6 |
| V4 factor 0.5 (10/21), all seeds | ✓ | ✓ | ✗ −1…+5 | ✓ | ✓ | ✗ | 10–13 | 4/6 |
| V4 factor 1.0 = V2 control | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ dark | 13–22 | 4/6 |
| best V2 combined (by rule: i0.75 a0.8 s8) | ✓ | ✓ | ✗ −19 | ✓ | ✓ | ✗ −38 | 10 | 4/6 |
| best V3 combined (by rule: i0.75 a0.4 s11) | ✓ | ✓ | ✓ +85 | ✓ | ✗ | ✗ | 13 | 4/6 |

"Best combined" was chosen by rule: most features passed, then fewest colours.

## Findings

**Tassel beads:**
- Earlier guidance-stop lets more of the init's colour back.
- Seed 7 bead brightness: −27 (full) → −5 (0.5) → +12 (0.4) → **+69 (0.3)**.
- Light beads survive in **1 of 12** early-stop renders (factor 0.3, s7, light grey/white), with all cords kept.

**Pale inner ears:**
- They survive in **0 of 12**. Even 6 guided steps darken them for good.
- The early steps set the coarse colour layout, and the unguided late steps never brighten those cells back.

**Structure:**
- Silhouette, face opening, both flaps and cords hold in **12/12** at every factor.
- The lock is strong even at 6 steps.
- Img2img 0.75 *without* an adapter keeps only 4 of 8 tassel cells (A i0.75).

**Design:**
- Factor 0.3 s7 adds a brighter orange colourway and a brow nose.
- It is the best adapter render of the study (5/6), but its ears lack the pale inner ear.

**Palette clean:** it achieves what the adapter was meant to add (a clean, controlled palette) without losing anything.
- 17 → 8 colours.
- All 6 features kept.
- Silhouette and mask identical; visually the same hood, with crisper shading.

## Verdict

1. **Best complete bear hood: `A i0.60 s7 PALETTE-CLEAN 8`.** It is the current best (A i0.60 s7) with a controlled 8-colour palette, and every required feature intact.
2. **The adapter is still not preferred.** Early-stop is the closest it has come (5/6, light beads on one seed), but no T2I render has kept the pale inner ears together with tassel beads.
3. **Across V1–V4 the conclusion is consistent.** A binary outline map locks structure, but it controls colour too early to carry two-tone details. For this design, the structural template plus img2img plus a native-grid palette clean is the best pipeline.

## Next (not run)

- Palette-clean the other three A seeds.
- Run worn QC of the A palette-clean hood through the QC Bridge (game restart + test pack).
- Then the four directions from the plurffle Hood base.

**Nothing here is approved.**
