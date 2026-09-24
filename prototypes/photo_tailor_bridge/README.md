# Photo Tailor Bridge Prototype

Prototype-only reference-image -> semantic analysis -> source-respecting Stardew hat generator.

This does **not** modify or replace the production generator. It uses Photo Tailor's local FashionSigLIP ONNX model as an experimental semantic front-end, then hands rendering authority to our source-backed/source-respecting constructions.

Pipeline:
1. Load/crop a reference image.
2. Run FashionSigLIP image embedding + Photo Tailor label embeddings.
3. Keep ranked category/silhouette/pattern candidates.
4. Extract a hat-focused reference palette.
5. Match to a source-respecting family/construction.
6. Apply reference palette only inside safe construction pixels.
7. Project supported semantic patterns (stripe/plaid/dot) inside the construction.
8. Render front/right/left/back and build a review contact sheet.

Current proof batch also exposes the existing dad-cap construction as `proto_dad_cap` so cap references are not incorrectly forced into a beanie.

Prototype dependencies (not shipping dependencies): Python, numpy, Pillow, onnxruntime; external local model `PhotoTailor/models/marqo_fashion_siglip_vision_uint8.onnx` and `fashion_siglip_labels.json`.

Run with:
`/home/deck/.cache/rng-photo-proto-venv/bin/python prototypes/photo_tailor_bridge/prototype_generator_v2.py`

Output:
`experiments/photo_tailor_bridge_02/PHOTO_TAILOR_BRIDGE_V2_CONTACT.png`
