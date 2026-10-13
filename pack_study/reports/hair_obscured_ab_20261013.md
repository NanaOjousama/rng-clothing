# Real Obscured hair policy A/B — 2026-10-13

## Mechanism and scope
- Fashion Sense hat JSON `HideHair` supports full/hidden only. `DrawOrderOverride`/`UseBaldHead` are not equivalent to vanilla covered-hair rendering.
- Enhanced Sewing Machine `GarmentHairMode`: `Full`, `Obscured`, `Hidden`, mapped respectively to `hat.hairDrawType` 0/1/2. For `Obscured`, Stardew's covered hairstyle alternate is used when the vanilla hairstyle provides a `coveredIndex`; it is a different **whole hairstyle**, not a pixel-specific crown mask. FS custom hairstyles may not supply that alternate.
- Built three pairs from original FS QC2 hats 01 (propeller cap), 05 (messy straw), 10 (blue straw) in installed ESM QC folders `assets/garments/qc/hair_policy_ab` and `assets/qc/hair_policy_ab`. Source art was copied byte-for-byte. In each ESM pair all fields except `Id`, `HairMode` and `Metadata.Label` are identical.
- ESM definitions' frame anchors were calibrated against FS from original `AnchorY=13` to `AnchorY=16`. This corrects a 12px display position discrepancy. **All 36 Full ESM renderings (3 hairstyles x 3 hats x 4 directions) are pixel-for-pixel identical to the existing original FS HAIR ON renderings**. Therefore differences between ESM Full/Obscured truly isolate the hair policy, not rendering geometry.

## Game tests and evidence
- Real loaded game, session `qc_bridge/captures/20261013-015846`, Stardew Valley 1.6.15 / SMAPI 4.5.2.
- Hairstyle IDs 0, 16 and 38; three hats x two modes x four directions: 72 isolated worn PNG screenshots (plus earlier FS on/off test already completed).
- Final capture directories `qc_bridge/captures/20261013-015846/esm2_hair{000,016,038}_QC2_{01,05,10}_{full,obscured}`. Early `esm_hair016_` trial screenshots have uncalibrated 12px placement difference and **must not be used** for visual approval.
- Index: `qc_bridge/captures/20261013-015846/esm_obscured_capture_index_v2.json`, 18 complete captures.
- Sheets: `pack_study/out/hair_policy_qc_20261013/review/esm_obscured_hair000_corrected.png`, `esm_obscured_hair016_corrected.png`, `esm_obscured_hair038_corrected.png`.
- Automated pixel comparison verified FS HAIR ON vs ESM Full equals zero different RGBA pixels for all 36 four-direction captures; ESM Obscured differs from Full in every case.

## Preliminary worn findings
- **Hairstyle 16:** ESM Obscured removes protruding hair above both straw-hat crowns, preserving hair below the brim. It changes the sides/back hairstyle substantially and is NOT automatically a user-approved fit.
- **Hairstyle 38:** Obscured changes the face-side and nape shape into a different covered hairstyle. It may look less natural than Full even though its crown is clean. Full already does not noticeably poke through the crown for these hats.
- **Hairstyle 0:** Obscured makes comparatively minor shape changes; Full is already acceptable regarding crown penetration.
- **Hat 01:** Obscured changes hair sides/back but doesn't alter the source-authored awkward cap visor. Hair policy must not be used to disguise geometry problems.
- `Hidden` (full hair removal) from the prior test looked poor; user confirmed this. Do not use global HideHair as clipping fix.

## Next policy design, not yet implemented
1. Preserve source author's existing hair policy by default; on hats whose real worn clipping is detected, test Obscured on representative hairstyles and require user QC approval.
2. `Obscured` is a *vanilla covered hairstyle substitution*, not precision scalp cropping and not necessarily appropriate for modded Fashion Sense hair.
3. Long-term flexible option: selective crown-only hair clipping with preservation of bangs/sideburns/nape, implemented noninvasively per garment/per hairstyle (not a global farmer renderer patch). This needs design and compatibility review before production.
4. No persistent generator hair-policy changes have been made based on these preliminary tests.

## Safety
All new files confined to isolated ESM QC garment assets and repo test scripts. No FS QC pack altered. QC bridge cleared newly equipped test items between captures (avoids filling player inventory), and restored no hat, original hairstyle 38, and front facing after capture. No game save was initiated.
