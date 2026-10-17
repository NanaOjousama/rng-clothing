# Silver bear hood: constructed versus Phase 4 p10 LoRA (inference-only)

- 2026-10-17. Input = existing exact Silver/uncommon 24x24 RGBA front plus current built back/left/right for reference. Front pixels are held fixed and restored exactly after inference.
- LoRA = Phase 4 four-view p10, not front-only p4e10; same phase4 dataset sheet layout and 30-step clean-front inference. Seeds 7 and 9; no retraining or downloads.
- Constructed: right and left each contain an isolated 8-pixel ear group plus an additional isolated pixel; visual issue = floating far ear. Back has two 21-pixel ear islands.
- p10 seed 7: right/left/back connected by 4-neighbour test, but side views look like an animal head with white collar/fur and snout; loses intended hood framing and subtle silver beads.
- p10 seed 9: right/left main shapes connected apart from 1-pixel islands, but sides again look snouted and lose flap details; back generic brown hood shape.
- Decision: neither result is approved. Rules need ear attachment correction. LoRA p10 is useful as a reference but not a drop-in directional replacement.
- The original source front, constructed directional PNGs, frozen generator, model weights, training data and production settings were not modified. All test outputs live in runs/bear_hood_p10_ab_01 on the laptop.
