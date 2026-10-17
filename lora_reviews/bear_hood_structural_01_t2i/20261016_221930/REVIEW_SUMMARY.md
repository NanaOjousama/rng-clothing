# bear_hood_structural_01 — T2I-Adapter comparison: review summary (2026-10-16)

**AI-ORIGINAL (CLAUDE.md §2b).**
- No training. No production settings changed. The frozen generator is untouched.
- Earlier results are untouched: the img2img run was read only, and its A arm was re-run **bit-identical, 8/8**.
- One user-approved download: the 158 MB adapter below. Nothing was installed.

**Question:** does a T2I-Adapter improve the bear hood beyond template img2img, and which structural method is best?

## Pre-download checks

- **Checkpoint:** `TencentARC/t2i-adapter-lineart-sdxl-1.0` at revision `5f1f33b0`.
  - Fetched only `diffusion_pytorch_model.fp16.safetensors` (158,060,440 B, sha256 `c19e9e10…7230f`) and `config.json`.
  - Config: `full_adapter_xl`, 3-channel input, downscale 16 (512 px works).
- **Why lineart:** the structure map is a clean outline drawn from the template, not detector output.
  - Lineart is trained on clean outline drawings.
  - Sketch is trained on rough PidiNet edges; canny on photo edges detected at 384 px.
- **Compatibility:** SDXL base 1.0 is the adapter's base. `StableDiffusionXLAdapterPipeline` (diffusers 0.35.2, already installed) has the SDXL LoRA loader, so p4e10 loads unchanged.
  - **There is no official img2img + adapter pipeline.**
  - Arm C injects the adapter residuals through a UNet pre-hook, using the official kwarg `down_intrablock_additional_residuals`.
  - **The equivalence check X proved it bit-identical to the official pipeline:** max pixel difference 0.
- **VRAM estimate:** at or below the ceiling, about 5.95–6.09 GiB. The measured peaks are in the table below.

## Design

Constant across all arms:
- the same structural template;
- the T2 construction prompt, verbatim; the same negative prompt;
- DPM++ 2M, 28 steps, CFG 8.5, LoRA 1.0;
- seeds 7, 8, 9, 11;
- the same decode.

| arm | method | levels |
|---|---|---|
| A | template img2img | strength 0.60, 0.75 |
| B | adapter only (txt2img, official pipeline) | V1: scale 0.6 / 0.8 / 1.0. V2: 0.4 / 0.8 |
| C | img2img + adapter | V1: strength 0.60 / 0.75 / 0.90 at scale 0.8. V2: strength 0.75 / 0.90 × scale 0.4 / 0.8 |

**Two structure maps, built from the same template and the same part boundaries (background | hood | pale):**
- **V1 "lines":** 2-px lines *between* cells.
- **V2 "grid cells":** every boundary *cell* is filled, on the native grid.

V2 was added after V1 failed, to give the adapter a fair test. It changes exactly one input.

## Results (by eye at x4 worn and x10; numbers advisory)

| arm | mean colours | template IoU | verdict |
|---|---|---|---|
| A i2i 0.60 | 16 (13–21) | 0.98 | **Complete bear hood.** Pale inner ears; pompom tassels on s7 |
| A i2i 0.75 | 14 (8–20) | 0.95 | Tassels start to break |
| **V1** B (adapter only) | 19–33 | 0.30–0.57 | **Fail, 0/12.** The LoRA drops its magenta background and the hood; the map is rendered as an embossed engraving |
| **V1** C (i2i + adapter) | 40–77 | 0.68–0.82 | **Fail, 0/12.** Magenta halos and beveled edges; shading lost. Worse with strength |
| **V2** C i0.75–0.90, a0.4/0.8 | 12–17.5 | **0.976–1.000** | Exact structure even at 0.90; crisp dark outlines; cleanest palettes (top-6 colours cover 81–98%); all 8 tassel cells kept, as dark cords. **But** inner ears turn dark (orange dots at a0.8 read as eyes) and tassels have no beads; flatter shading than A |
| **V2** B a0.4 | 17.8 (15–20) | 0.95 | **Most new design.** p4e10 draws its own shading from noise: brow faces with eyes, nose and cheeks; blushed brow band; new colourways. Ears dark, no inner ear; **tassels lost** (2 of 8 cells) |
| **V2** B a0.8 | 13.8 | 0.78 | Fail: s8/s9 are hollow outline copies of the map; s7 grows frog-eye ears |

**Memory (6,144 MiB RTX 3060):** essentially no difference between arms.
- Peak allocated: A 5,414, B 5,358, C 5,419 MiB.
- Peak device: 5,941–5,975 MiB on every arm.
- Speed was unchanged (no shared-memory spill). Placing the adapter manually (C) and the official pipeline's own offload (B) both fit.

## Verdict

1. **Best structural method today: A, template img2img at 0.60 on p4e10.** It is the only method that keeps all four features *with the right meaning*: round bear ears with pale inner ears, open face, flaps, and tassels with real ends.
2. **The T2I-Adapter does not beat A yet, but with a grid-aligned map it adds two things img2img cannot:**
   - **(a) a structure lock** that holds at any strength (IoU ≥ 0.976 at 0.90, where A has started to drift);
   - **(b) real design generation**: at adapter-only 0.4, the LoRA invents shading, faces and colourways rather than repainting the template.
3. **The V2 limitations come from the map, not the adapter.** Inner-ear and tassel-bead cells were marked as boundaries, so they came out in outline colour.
4. **Line maps (V1) are unusable with this native-grid LoRA.** Lines between 20-px cells ask for sub-cell detail the LoRA cannot draw.
5. **Memory is not a deciding factor** on this laptop.

## Next (not run)

**V3 map:** mark only the outer silhouette and the face-hole edge as cells, and leave inner ears and tassel beads unmarked.

Test, 16 renders:
- B at scale 0.4–0.5;
- C at strength 0.75 and 0.90, scale 0.4.

Goal: combine the adapter's structure lock and B's design freedom with A's correct inner ears and tassels. Then palette-snap, and run worn QC through the bridge.

**Nothing here is approved.**
