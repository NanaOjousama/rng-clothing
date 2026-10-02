# Experimental Construction Template Pipeline

Goal: prove that candidate multi-view geometry can be converted into a reusable Stardew-ready construction template before adding another AI model upstream.

Current benchmark input is the trucker-cap reference set with known front/right/back views. This is intentional: it gives ground truth for judging geometry instead of accepting plausible-looking hallucinations. Left is mirrored from right for this symmetric cap.

Stages:
1. Reference-view segmentation and silhouette extraction.
2. Pixel-grid reduction into 26x26 directional construction frames.
3. Semantic component mapping.
4. Photo Tailor four-facing recolor/normalization with alpha geometry locked.
5. Per-view Stardew farmer wear-space projection.
6. Formal construction-template contract + technical QC.

The upstream view provider is replaceable. Wonder3D/SyncDreamer/Zero123 can later provide candidate views from a single reference, but their output must pass the same downstream construction and Stardew-fit gates.