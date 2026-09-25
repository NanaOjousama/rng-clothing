# Photo Tailor permission-backed code port

This directory contains a full decompile of the locally installed Photo Tailor DLL,
captured after the project owner obtained explicit permission from the author to
adapt/reuse the code for this project.

Production-facing ports live in:
- `generator/photo_tailor_port.py`
- `generator/cap_photo_tailor_pipeline.py`

The port currently includes the actual Photo Tailor mechanics for:
- four-facing hat frame routing;
- canonical front/right/left/back projection;
- canonical nearest-opaque motif placement;
- HSL shade-ramp construction;
- normalized pattern/color-field projection;
- topology-boundary shading;
- the `PreviewHat -> Recolor` source-luminance preservation loop.

The full decompile remains reference material, not a runtime dependency.
