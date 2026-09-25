# Baseball Cap — Real Photo Tailor Output 01

Status: CANDIDATE_WORN_QC

This checkpoint uses **Photo Tailor 0.15.1's actual compiled pipeline**:
- `LocalOutfitAnalyzer.Analyze(... precise hat crop ...)`
- `GarmentArtCompiler`
- `SpriteRenderer.Render()`
- native vanilla cap template `cap = 5`

There is no custom cap renderer in this checkpoint.

## Personal PT bridge

Because Photo Tailor 0.15.1 bundles Windows x64 ONNX native files, the Deck install is supplemented with the Linux ONNX Runtime shared libraries already used by the working PT research environment.

`mods/PhotoTailorPersonalBridge/` adds only a console command around PT:
- full-image precise recognition with category hint `hat`;
- known silhouette forced to `cap` for this cap-only command;
- PT still owns blueprint, palette, pattern, canonical artwork, projection, and final pixels.

Old Dad v1/v2, old Trucker, Mario, and old PT cap-control geometry are not construction inputs.

## Current raw PT candidates

- **Plain** — actual PT output from a plain front baseball-cap reference.
- **Colored Front** — actual PT output from the colored/two-tone front reference.
- **Colored Side** — actual PT output from the colored/two-tone side reference.

All three output sheets are 20×80 native PT hat textures: four 20×20 facings.

Fashion Sense QC pack:
`test-packs/fashionsense/RNG-Cap-Reboot-Baseball-PT-REAL-01/`

Installed:
`Mods/[FS] RNG Cap Reboot Baseball PT REAL 01`

The QC pack copies PT's sheets byte-for-pixel unchanged. Human worn review is authoritative.
