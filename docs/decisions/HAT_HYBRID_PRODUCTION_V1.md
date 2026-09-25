# Hat Hybrid Production V1

Production hats remain anchored to `HAT_PRODUCTION_GOLDEN_V1`.

The native hybrid layer is an independent implementation in `generator/hat_hybrid_enhancements.py`. It does not import Photo Tailor, prototype code, FashionSigLIP, ONNX, or vendor assets.

## Authority
1. Select the already-approved golden source state + palette pair.
2. Render the source-respecting golden result.
3. Apply only bounded recipe-driven feature deltas.
4. Reject the enhancement and return the exact golden pixels if safety gates fail.

## Native bounded features
- normalized pattern coordinates;
- semantic crown/band/brim/hem regions;
- normalized motif anchors;
- front/side/back facing scopes;
- source-derived pattern/contrast changes;
- occupancy-bounded edits;
- exact alpha preservation;
- exact outline preservation.

The enhancement layer never creates construction geometry and never replaces the golden source state.
