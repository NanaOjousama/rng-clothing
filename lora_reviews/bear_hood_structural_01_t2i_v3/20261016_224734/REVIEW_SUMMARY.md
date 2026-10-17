# bear_hood_structural_01 — T2I-Adapter V3 (minimal map): review summary (2026-10-16)

**AI-ORIGINAL (CLAUDE.md §2b). Inference only.**
- No training. No production settings changed. The frozen generator is untouched.
- Earlier runs were read only.
- No new downloads: this reuses the lineart SDXL adapter fetched earlier.

## Question

Does a **minimal** structure map work better? V3 marks only the outer hood silhouette and the face-hole edge.

**Explicit test:** removing inner-ear and tassel guidance should fix their colours (V2 drew them in outline colour). Does it fix them, or do those features simply disappear?

## Setup (16 renders, 221 s, seeds 7 / 8 / 9 / 11)

- **V3 map** (`cond_silhouette_512.png`, 74 cells): parts are background | hood.
  - Inner-ear cells count as hood, so they get no line.
  - Tassel rows 22–23 count as background, so they get no line either.
  - Built on the Deck. Rebuilt on the laptop and verified: **raw-pixel sha256 identical** (`dbab7921…`).
- **Held constant:** same template init, p4e10 LoRA 1.0, the T2 construction prompt verbatim, negative prompt, DPM++ 2M, 28 steps, CFG 8.5.
- Each render records **img2img strength** (`strength`) and **adapter conditioning scale** (`adapter_scale`) as separate fields.

| arm | img2img strength | adapter scale | comparator |
|---|---|---|---|
| V3 B (adapter only) | — | 0.4 | V2 B a0.4 (same cell) |
| V3 B (adapter only) | — | 0.5 | new |
| V3 C (img2img + adapter) | 0.75 | 0.4 | V2 C i0.75 a0.4 (same cell) |
| V3 C (img2img + adapter) | 0.90 | 0.4 | V2 C i0.90 a0.4 (same cell) |

**Baseline:** A, template img2img at strength 0.60, no adapter.

## Feature probe (`v3_feature_probe.txt`; advisory, the eye decides)

- **inner ear** = brightness of the template's inner-ear cells minus the rest of the ear; > 0 means a pale inner ear.
- **cords** = tassel cells present, out of 8.
- **bead** = whether the tassel bead cell exists, and its brightness.
- The template itself scores +112 / 8 / +101.

| arm | inner ear | cords /8 | bead | colours |
|---|---|---|---|---|
| **A img2img 0.60** | **+96 … +117 (4/4 pale)** | 4–12 | light on s7 | 13–21 |
| V2 B a0.4 (full map) | −17 … −4 (dark) | 2–6 | none | 15–20 |
| **V3 B a0.4** | −15 … −3 (0/4 pale) | **0–1** | none | 10–18 |
| **V3 B a0.5** | −14 … +14 (0/4 pale) | **0** | none | 10–15 |
| V2 C i0.75 a0.4 (full map) | −13 … +1 (dark) | 8 (s11: 3) | **dark** | 13–22 |
| **V3 C i0.75 a0.4** | +12 … +15; **s11 +85** (1/4 pale) | **0** | none | **7–13** |
| V2 C i0.90 a0.4 (full map) | −11 … −6 | 2–8 | mostly none | 16–18 |
| **V3 C i0.90 a0.4** | −17 … +5 | **0** | none | 9–15 |

## Answer to the explicit test

**Yes on colours, and yes the features disappear.**

**Colours improved:**
- No more black ears or orange "eye" dots.
- V3 C at 0.75 has lighter inner ears, and one seed (s11) has truly pale, correctly coloured bear ears.
- The palettes are the cleanest of the whole study (7–15 colours).

**The features disappeared:**
- **Tassels: 0 cord cells in 15 of 16 renders, 1 in the other.**
- That includes **C, where the template init still contains the tassels.** The adapter drew an outline where the map's flaps end and erased what lay beyond it.
- **The pale inner ear came back in only 1 of 16.**
- The adapter enforces exactly what is in the map and suppresses what is not, overriding the init image during the late steps.

**What V3 keeps:** hood silhouette ✓, clear face opening ✓, both flaps ✓, clean native grid ✓. Meaningful new design persists:
- B s7: a brow face panel;
- B s9: an orange face band with eyes and cheeks;
- C s11: white-eyed brow face with pale inner ears.

## Verdict vs the best img2img bear hood (A i0.60 s7)

**Keep img2img (A).** The adapter is preferred only if it improves the design *and* the construction. V3 does not:

| | A i0.60 s7 | best V3 (C i0.75 a0.4 s11) |
|---|---|---|
| silhouette, face opening, both flaps | ✓ | ✓ |
| correctly coloured bear ears | ✓ | ✓ (best ear colour; 1/16 seeds) |
| tassel cords + beads | **✓ pompoms** | **✗ (16/16 lost)** |
| new design detail | brow dots | **✓ brow face** |
| palette / grid | 17 colours, muddier | **13 colours, crisp** |

## What the three maps showed together

| map | result |
|---|---|
| V1 lines | the map is drawn literally |
| V2 full cells | structure kept, but marked details come out in outline colour |
| V3 minimal | colours freed, but unmarked details erased |

**A binary outline map cannot carry "this cell is a pale detail".**

## Next test (not run)

**adapter_conditioning_factor ≈ 0.3–0.5:** apply the adapter only in the early steps. Use the V2 full map with img2img 0.75, so the structure (including tassels) is locked early and the init's colours (pale inner ears, light beads) return in the late steps. This is a one-parameter change; the official pipeline exposes it, and the injection hook takes a step counter.

**Nothing here is approved.**
