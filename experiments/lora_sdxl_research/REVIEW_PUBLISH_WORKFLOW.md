# LoRA review auto-publish: approved workflow (2026-10-14)

After LoRA training AND evaluation complete on the laptop, upload only the finished comparison sheets and concise results notes to GitHub automatically, using the laptop's **post-evaluation finalizer**. No timer, no polling, no GPU use while training.

- Laptop script: `C:\Users\Chris\sdxl_lora_research\tools\complete_lora_review.ps1`
- Laptop detailed instructions: `C:\Users\Chris\sdxl_lora_research\tools\REVIEW_PUBLISH_WORKFLOW.md`
- Destination: **private** GitHub `hewyinw/tfwr` **branch `lora-reviews` only**, under `lora_reviews/<experiment>/<timestamp>/`.
- This is a separate *orphan branch* for review images only. Never push RNG Clothing code or edits to TFWR `main`.
- Never upload training data, safetensors/checkpoints, downloaded/reference artwork ZIPs, caches, large intermediate renders, or secrets.
- Keep x1 / x4 / x10 comparison sheets and summaries only; all hats remain experimental pending user approval.
- After finishing the eval and writing every sheet, use Remote Desktop Commander on LAPTOP-GGEDSK3A to invoke the finalizer, e.g.:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\Chris\sdxl_lora_research\tools\complete_lora_review.ps1" -Experiment "phase4_four_view" -SourceDirectory "C:\Users\Chris\sdxl_lora_research\runs\phase4_eval\sheets" -Checkpoint "phase4_epoch10" -Seeds "7,8,9"
```

- Confirm the finalizer reports `SUCCESS: pushed`. If not, report GitHub authentication as a blocker. The finished review remains in `review_outbox` for later retry by `publish_lora_reviews.ps1`.
- The user approved automatic upload of **finished review results only**; preserve the standing CLAUDE.md no-unapproved-remote-push rule for all other project data.
