# CURRENT_STATE.md

Recovered authoritative state — 2026-09-19

Detailed recovery evidence:
docs/recovery/PROJECT_RECOVERY_2026-09-19.md

Do not reconstruct project state from chat memory.

## Git-backed recovery anchors

- Recovery authority + continuity safeguards:
  9e3f0ea588bbc96dd1169c5bbbf7b35dc7234501
- Enhanced Sewing Machine runtime + tailoring pipeline:
  d1d5a8dde3b041e1e97a854527827883f543e080
- Source-backed Beanie V1 constructions:
  1ef67fa745a56356c73f34e7cb1e1b97e3e8b7a8
- Recovery commit hashes recorded:
  f8cbb64f446cce06da36afd556eef81e2e3d61d3
- Safe ESM garment-equip QC action:
  fa81e9d0f40186c11ea7e2316facd8bf7302325c
- Deterministic source-backed cap-family compositor:
  f61ecac791d5b0867af11fe4efe07ae0f9b9c0f2
- Source corpus/catalog path repair + verified manifest:
  7e214b7775909afc38f00faac5c58e6854b08649

## Enhanced Sewing Machine

Status: RECOVERED, GIT-BACKED, VERIFIED.

Architecture:
- custom SMAPI/Harmony runtime; no Fashion Sense runtime dependency;
- real Stardew Hat carrier (H)RNGClothing.ESM.GeneratedHat;
- immutable per-item render snapshot in modData;
- custom worn rendering;
- offline generator -> compiled PNG/JSON bridge;
- deterministic Textile + Inspiration + sewing seed selection;
- additive Enhanced shell around vanilla TailoringMenu;
- fitting via FitOffsetX, FitOffsetY, FitScale;
- controller/Steam Deck + i18n + fail-open compatibility are first-class.

32x32 support is already solved. Do not invent another rendering path.

Fresh recovered verification:
- ESM Release build: PASS, 0 warnings, 0 errors
- C# tests: 23/23 PASS
- active garment definitions: 19/19 valid
- tailoring biases: PASS
- generator bridge: 8/8 exact

V4BEANIE remains a dev/runtime QC asset only.

BEANIE8_QC is REJECTED and is not in the active garment index.

## Generator / source-backed hats

Last clean pre-recovery generator baseline:
bf4c0a5a41ba097a7d5f16e516fc79687cd33654

Recovered source-backed Beanie V1:
- beanie_cuffed
  - Rural Outfitters / Beanie
  - 20x20
  - authored Front/Right/Left/Back
- beanie_slouch
  - More Accessories and Stuff / Beanie (Floppy)
  - 16x16
  - authored Front/Right/Back; mirrored Left

Beanie family tests: 4/4 PASS.

The previously generated RuralBeanie V2 batch remains important evidence that wearable beanie geometry had already been promoted into generator output. Do not restart beanie work from the rejected 8-direction sprite.

Round Trip is recovered and lives at:
- builder: tools/build_roundtrip_pack.py
- pipeline: v5/source/roundtrip.py
- proof pack: test-packs/fashionsense/RNG-RoundTrip

The current Round Trip subject is plurffle's More Accessories and Stuff / Beanie. Its exported B copy preserves the source wear properties with zero property differences.

## Cap / beret recovered verification

- source-backed caps: 5/5 PASS
- Baseball decoration: 15/15 PASS
- Snapback decoration: 21/21 PASS
- source-backed cap-family compositor: 4/4 PASS
- legacy render guard: 1996 checked, 0 moved
- beret validator: 89/89 PASS

## Soft Cap experiment

The uncommitted Soft Cap expansion was the cause of:
- 6 legacy render drifts;
- beret validator 88/89;
- ESM bridge 6/8 exact.

It has been quarantined, not deleted:
archive/project-recovery/softcap-quarantine/softcap_unfinished_20260919.patch

Patch SHA-256:
5f4b4c19939b3d5ceb999f9207311e543c21ac68a48f1231267afb54df77531e

After restoring the committed Soft Cap baseline:
- legacy guard returned to 0 moved;
- beret returned to 89/89;
- ESM bridge returned to 8/8 exact.

Do not reapply or bless that Soft Cap patch without intentional review and live QC.

## Source corpus

Canonical source corpus directory:
generator content/

The old typo generator conent/ no longer exists.

python3 tools/corpus_manifest.py verify currently passes all seven corpora.

## Remote / workflow rule

When the Steam Deck remote is connected, repository inspection, editing, builds, validators, installs, and safe QC-bridge actions are performed remotely by the assistant.

Only ask the user for actions that genuinely require their visual judgment or physical interaction.

After every accepted live milestone:
1. update authoritative state;
2. run relevant verification;
3. make a scoped Git commit;
4. report the actual commit hash.

No commit hash = not safely preserved.


## Accepted milestone — per-direction ESM fitting

Accepted live in-game on 2026-09-19.

Implemented and verified:
- independent Front / Right / Left / Back X/Y fitting offsets;
- global scale remains shared;
- View previous/next controls in the tailoring fitting UI;
- per-view position reset;
- reset-all clears all directional offsets and scale;
- preview now reflects the selected direction's live X/Y fit values;
- old front-only saved fit fields remain backward-compatible.

Implementation commits:
- 9f0a79cdb2cf860db4bef8d487805a2bb18d63cd — per-direction fitting controls/state
- c85c75c1a50f3a37e4755c512bfcc897fe702940 — explicit side-view preview direction
- 23352273b6add2f263a5e1fe829d41ea11181e6d — preview honors directional offsets

Verification at acceptance:
- ESM build: 0 warnings / 0 errors
- ESM tests: 26/26 PASS
- live user QC: accepted; side scaling and side X/Y both work and preview matches


## Accepted milestone — ESM Beanie V1 production promotion

Promoted on 2026-09-19 after live QC acceptance of the source-backed RuralBeanie EarthMoss construction.

Production garment:
- Id: `beanie.v1.rural.earth-moss`
- Frame: 20x20, four authored directions
- Palette: `EARTH_MOSS`
- Generator lineage: `RNG-RuralBeanie-V2` v2, seed `2024493570`
- Family / construction: `knit_cap`
- Classification: `PRODUCTION`
- Texture: `assets/source_backed/beanie_v1_rural_earth_moss.png`
- Definition: `assets/garments/source_backed/beanie_v1_rural_earth_moss.json`

The temporary `qc.beanie.rural.earth-moss` registry entry was removed. User X/Y/scale fitting remains per garment instance and is intentionally not baked into the production geometry.

Verification:
- ESM garment validator: 20/20
- ESM build: 0 warnings / 0 errors
- ESM tests: 26/26 PASS
- tailoring bias validator: PASS
- generator bridge: 8/8 exact
- source-backed beanie tests: 4/4 PASS
- live QC of the same source-backed construction: accepted

The production registry entry requires the next game restart to be loaded into the live ESM registry.

## Slouch Beanie generator matrix — 2026-09-20

PixelLab 24px multi-direction slouch (`experiments/slouch_beanie_compare/pixellab/pl_24_sheet.png`) is now frozen as **CONSTRUCTION-ONLY** reference. Cardinal source frames are Front=0, Right=2, Back=4, Left=6. It is useful for coherent slouch geometry, angle, backward drape, and band placement, but its outline/shading and current live-QC size are explicitly not production targets.

Canonical generator data now lives at `generator/data/headwear/slouch_beanie_roll_matrix.json`. It defines weighted rolls for presentation lean (soft preference, never a hard gender lock), slouch depth, band/cuff type, drape, crown shape, opening fit, knit structure, pattern, motif, decoration style, and motif placement, plus rarity guidance and 17 compatibility/exclusion rules. Final production art must preserve the slouch construction first. Generic `BRIMLESS_HAT` / generic V5 headwear normalization is explicitly forbidden for this family; outline/shading must be slouch-specific and QC-approved.

Validation command: `python3 tools/validate_slouch_beanie_roll_matrix.py`.

### ESM fitting regression resolved

The 2026-09-20 Front/Back coupling was traced to one global `FitScale` shared by all directions. X/Y offsets were already independent. ESM now stores scale independently for Front/Right/Left/Back, and tests explicitly verify Front-scale and Back-scale isolation plus all existing X/Y isolation.

## Slouch Beanie Motif Library V1 — 2026-09-20

Created a native-pixel modular motif library at `authored/motifs/slouch_beanie_v1/` from the user-provided slouch-beanie reference examples plus prior online research. The photos are reference-only; no photo pixels are copied.

Library contents: 31 reusable assets — 11 symbol motifs, 5 patch/label carriers, 2 pom attachments, 1 button hardware accent, 1 contrast-stitch accent, 6 surface-pattern swatches, and 5 knit-texture swatches. Canonical preview: `authored/motifs/slouch_beanie_v1/slouch_beanie_motif_sheet.png`; manifest: `authored/motifs/slouch_beanie_v1/manifest.json`.

The generator roll matrix now binds these assets directly and adds modular `carrierStyle`, `attachment`, and `hardwareAccent` rolls. New supported composition possibilities include pattern + side label, pattern + small label + pom, symbol + patch carrier, direct-stitch symbol, cuffless body motif, extra-slouch + minimal label, and button accent without pom. Exclusions increased from 17 to 24 so unstable/busy combinations are rejected.

Validation: `python3 tools/validate_slouch_beanie_roll_matrix.py` checks all 14 axes, every bound asset path, required pom/carrier assets, and exclusion invariants. Source-backed beanie family remains 4/4 PASS.

## ESM per-direction fit scale fix — 2026-09-20

The deferred fitting coupling bug is fixed. Root cause: X/Y offsets were already stored per facing direction, but scale still used one global `FitScale`, so changing Front scale also changed Back/Right/Left. ESM now stores and renders scale independently for Front, Right, Left and Back. The legacy `FitScale` field remains the Front/down value for save compatibility; new directional scale fields default to 1.0 when absent in older saves.

Affected source:
- `mods/EnhancedSewingMachine/GarmentRuntime/GarmentInstanceData.cs`
- `mods/EnhancedSewingMachine/GarmentRuntime/GarmentRuntimeHost.cs`
- `mods/EnhancedSewingMachine/EnhancedTailoring/EnhancedTailoringShell.cs`
- `mods/EnhancedSewingMachine.Tests/Tests.cs`

Verification after rebuilding both projects:
- ESM Release build: 0 warnings / 0 errors; ModBuildConfig redeployed it to the live Mods folder.
- ESM tests: ALL PASS, including explicit Front-scale isolation and Back-scale isolation plus existing X/Y independence.

### Slouch generic-tuning rollback — 2026-09-20

The slouch-specific generic V5/`BRIMLESS_HAT` style-translation proof and every rarity-QC asset built from it were deleted after visual regression. The roll matrix, 24 exclusions, motif library, and ESM per-direction fitting fix are retained.

Hard guard: **do not use generic `BRIMLESS_HAT` normalization or the removed generic V5 headwear style-translation path for slouch beanies.** Slouch construction is authoritative; future outline/shading work must preserve that geometry and be QC-approved before generation uses it.

## Source-backed template generator — 2026-09-20

New generator architecture is now defined and implemented around **template-owned geometry + deconstructed source-owned variation**.

Authoritative pieces:
- contract/planner: `v5/source/template_transfer.py`
- transfer catalog builder: `tools/build_source_transfer_library.py`
- transfer catalog: `source_catalog/SOURCE_TRANSFER_LIBRARY.json`
- human-readable transfer inventory: `source_catalog/SOURCE_TRANSFER_LIBRARY.md`
- validator: `tools/validate_source_template_generator.py`
- architecture doc: `docs/source_backed/SOURCE_BACKED_TEMPLATE_GENERATOR.md`
- template registry: `generator/data/templates/index.json`

Current source reclassification covers all 319 catalogued Fashion Sense appearances and 53 deconstructed source families. It exposes 53 family style donors, 12 reconstruction-proven FAMILY_REUSABLE parts, 43 SAME_BASE_ONLY parts, and 108 ALTERNATE_CONSTRUCTION/reference-only variants. Cross-template reuse now requires an explicit semantic zone/anchor on the target template; REUSABLE no longer means “paint these source coordinates anywhere.”

### First registered construction template: slouch_pl24

The approved coherent PixelLab 24px slouch construction is now copied into tracked template authority at `authored/templates/slouch_pl24/`: Front=0, Right=2, Left=6, Back=4.

Contract: `generator/data/templates/slouch_pl24.json`.

All four files are SHA-256 pinned and their alpha geometry is independently hashed. The hand-edited curved front band, head contact, rear slouch mass and directional silhouette are locked. The contract forbids resampling and generic normalization. Base styling may not change alpha; only contract-approved attachments/hardware may add alpha, and never remove locked base cells.

The slouch roll matrix now points to this template contract plus `SOURCE_TRANSFER_LIBRARY.json`. Palette/tone, material/pattern, motif, attachment and hardware variation are intended to come from approved deconstructed source vocabulary or the existing slouch motif library, filtered by template compatibility and the 24 slouch exclusions.

The temporary RD-based/resampled `SLB2` QC builder and live pack were deleted; they are not authoritative evidence.

Validation:
- `python3 tools/validate_source_template_generator.py` — PASS
- `python3 tools/validate_slouch_beanie_roll_matrix.py` — PASS
- `python3 -m unittest v5.tests.test_template_transfer` — 5/5 PASS

## First rendered source-backed recipe proof — 2026-09-21

The planner proof is now rendered end-to-end.

Recipe:
- construction: locked `slouch_pl24`
- style donor: `More Accessories and Stuff::Hats::Beanie`
- motif donor: `Cottagecore Set::Beret (Leaf)`
- geometry policy: `LOCKED_TEMPLATE_ALPHA`

Implementation:
- renderer: `v5/source/source_backed_renderer.py`
- proof runner: `tools/render_source_template_recipe_proof.py`
- rendered frames: `experiments/source_template_recipe_proof/rendered/{front,right,left,back}.png`
- report: `experiments/source_template_recipe_proof/render_report.json`
- QC strip: `experiments/source_template_recipe_proof/rendered_strip_x8.png`

Important correction discovered during proof rendering: raw source-family diffs were too broad because the Cottagecore Leaf variant also nudges an ordinary base shade (214 -> 217). The renderer now reconstructs motif ink from sparse variant-only colours, which isolates a 3x3 / 7-pixel leaf mark in every direction. Palette drift is therefore not misclassified as a transferable motif.

The donor style profile changes only value-role treatment. Motif placement is mapped through the target crown/surface anchor and must fit entirely inside existing locked alpha. Every rendered view is checked against the original template alpha and rejected if any silhouette cell is added or removed.

Validation:
- `python3 tools/render_source_template_recipe_proof.py` — PASS
- combined renderer/template/beanie/cap tests — 16/16 PASS
- all four rendered directions preserve exact PL24 alpha geometry

## Slouch rarity QC batch 01 — 2026-09-21

Created a controlled 8-variant / 32-frame QC batch on the locked `slouch_pl24` construction so rarity quality can be reviewed without silhouette changes confounding the result.

Distribution:
- Common: 2
- Uncommon: 2
- Rare: 2
- Epic: 2

Batch:
- Common: cocoa solid; stone fine rib
- Uncommon: sage seed + leaf; indigo twin stripe + star
- Rare: autumn jacquard + flower cluster; wine cable + stitched badge
- Epic: arcane cable + twin stripe + extended botanical; jade jacquard + contrast finish + extended botanical

Authority/policy:
- all 32 rendered views preserve exact PL24 alpha geometry
- no attachments/poms in this batch; alpha-growth is intentionally deferred so this test isolates rarity/surface quality
- palettes come from `authored/palettes.json`
- motif/pattern primitives come from `authored/motifs/slouch_beanie_v1/`
- batch manifest: `experiments/source_template_rarity_batch_01/batch_manifest.json`
- contact sheet: `experiments/source_template_rarity_batch_01/rarity_contact_sheet.png`
- builder: `tools/build_slouch_rarity_qc_batch.py`

Validation:
- rarity distribution: 2/2/2/2 PASS
- 8 unique variants PASS
- 32/32 frames preserve locked PL24 alpha PASS

## SLB3 Fashion Sense live QC pack — 2026-09-21

The 8-hat slouch rarity QC batch is packaged for Fashion Sense and installed in the live Stardew Mods directory.

Search tag/name prefix: `SLB3`

Source pack:
`test-packs/fashionsense/RNG-SLB3-Rarity-QC/`

Live installed pack:
`/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/RNG-SLB3-Rarity-QC/`

Entries:
- SLB3 C1 Cocoa Solid
- SLB3 C2 Stone Fine Rib
- SLB3 U1 Sage Seed Leaf
- SLB3 U2 Indigo Twin Star
- SLB3 R1 Autumn Jacquard Flower
- SLB3 R2 Wine Cable Badge
- SLB3 E1 Arcane Cable Stripe Botanical
- SLB3 E2 Jade Jacquard Botanical

All 8 entries contain the `SLB3` Fashion Sense tag. Frames are 24x24 and use the locked PL24 rarity-batch art. Initial HeadPosition follows the previously tested slouch-family directional convention; in-game QC remains authority for final fit.

## SLB4 round-trip slouch QC — 2026-09-21

SLB3 exposed two Fashion Sense-only presentation bugs:
- direct 24x24 FS export drew larger than the ESM presentation because the FS pack had no matching scale contract;
- surface/motif placement was not direction-aware enough, so front-owned motifs appeared like stickers that persisted on side/back views.

SLB4 is an A/B round-trip QC pack with one pair per rarity:
- C2 Common
- U1 Uncommon
- R1 Rare
- E1 Epic

For each pair:
- A = direct SLB3 behavior
- B = corrected round-trip behavior

Corrected B contract:
- Fashion Sense Scale = 3.3333333333333335, matching ESM 0.833333 presentation against FS base scale 4;
- exact locked PL24 alpha is preserved;
- decorative pattern/motif pixels may only modify interior alpha cells, never the silhouette boundary;
- front-owned motifs are authored only on the Front frame for this diagnostic batch, and are absent on Right/Left/Back instead of persisting like a screen-space sticker.

Validation:
- 16/16 corrected B directional frames preserve exact PL24 alpha;
- zero decorative changes touch the alpha boundary;
- motif placement reports contain Front only for motif-bearing variants;
- live Fashion Sense pack contains 8 searchable SLB4 A/B hats.

Source:
- tools/build_slb4_roundtrip_qc.py
- experiments/source_template_roundtrip_slb4/

Live pack:
/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/RNG-SLB4-RoundTrip-QC/

## SLB5 different-template round-trip QC — 2026-09-21

User confirmed in-game that SLB4 round-trip motif behavior was correct, while the SLB3-style direct prototype kept the motif at one apparent screen-space location across facing changes.

SLB5 retests the rule on a different approved source-backed construction: beret_02 from the Cottagecore source corpus.

Important correction:
- no fixed 20px policy is imposed by the builder;
- frame width/height are derived from the source-backed base and its Fashion Sense model;
- beret_02 naturally resolves to 20x20 because that is what its source declares.

SLB5 cases:
- P0 plain baseline
- M1 leaf: decal declares Front + Right + Left only, so Back has no leaf
- M2 dots: decal declares all four facings and is independently seated per view
- M3 bow: decal declares all four facings and is independently seated per view

For each case:
- A DIRECT is rendered through the real v5/source_backed.py renderer
- B ROUNDTRIP is then re-ingested and re-exported through v5/source/roundtrip.py

Validation:
- 4/4 A->B wear-property comparisons have zero differences
- all motif-bearing A and B sheets contain four distinct directional frames
- leaf visibility contract is inherited from decal views, not forced front-only
- live Fashion Sense pack contains 8 searchable SLB5 entries

Live pack:
/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/RNG-SLB5-Beret-RoundTrip-QC/

## B16QC live in-game 16px beanie comparison — 2026-09-21

Built and installed a live Fashion Sense QC pack from the matched 16px comparison batch.

Pack contents:
- 8 PixelLab 16px variants tagged B16PL
- 8 RoundTrip-source 16px variants tagged B16RT
- all 16 entries share B16QC

Wear contract for comparison:
- HatSize 16x16
- HeadPosition -2,-3 for both template families
- same eight rarity concepts on both sides
- explicit Front/Right/Left/Back frames in each sheet

Live pack:
/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/RNG-B16QC/

Search tags:
- B16QC = all 16
- B16PL = PixelLab 16 only
- B16RT = RoundTrip-source 16 only

## Sprite Fusion Pixel Snapper integration — 2026-09-21

Added Sprite Fusion Pixel Snapper as an optional local cleanup/QC stage.

Installed locally:
- official source clone: tools/vendor/spritefusion-pixel-snapper (revision ae20461)
- native binary: tools/bin/spritefusion-pixel-snapper
- Rust + portable Zig build toolchains live on USD00 under tools/toolchains/
- home Rust/Cargo locations are compatibility symlinks to the SD-card copies
- no SteamOS package-manager/system modification was required

Project adapter:
- tools/pixel_snapper_adapter.py
- default behavior preserves original canvas metadata
- Pixel Snapper raw transparent-padding crop is reseated onto the original canvas
- alpha/silhouette geometry is compared after reseating
- any silhouette change is REJECTED by default and marked approvalRequired
- only explicit --approve-silhouette-change accepts changed geometry
- custom palette, color-count, pixel-size, and reseating anchor are supported

Validated smoke test:
- clean 16x16 beanie was cropped by raw Pixel Snapper to 12x13
- adapter restored a 16x16 canvas
- unapproved geometry drift exited 3 and did not publish output
- explicit approval accepted the changed silhouette

## Sprite Fusion remote API slouch test — 2026-09-21

Verified Sprite Fusion API can be driven through Remote Desktop Commander from the Steam Deck.

Test:
- operation: style-reference
- target size request: 16
- references:
  - authored/templates/slouch_pl24/front.png
  - authored/source_backed/beanie_slouch/semantic/front.png
- generated 9 slouch-beanie candidates
- request consumed 15 credits (1005 -> 990)
- originals preserved under experiments/spritefusion_slouch_test_01/native/
- contact: experiments/spritefusion_slouch_test_01/contact_slouch_spritefusion_native_x9.png
- observed returned PNG canvases ranged from 20x20 to 23x23 despite size=16 request; originals intentionally left untouched for evaluation

## Material batch decision — 2026-09-21

- experiments/spritefusion_beanie_material_rescale_test_01 is now approved as a CANDIDATE material/pattern batch.
- All 9 accepted outputs are 19x19 or 20x20 and fit the preferred 16-24 px Stardew-scale range.
- User decided the separate 40px+ -> 24px material-transfer path is not needed for this batch because the direct Sprite Fusion retry already preserves the material look well enough at native small scale.
- Keep the transfer experiment only as a fallback/research technique, not the normal generator path.

## Slouch beanie Sprite Fusion deconstruction + roll integration — 2026-09-21

Integrated the approved Sprite Fusion slouch/material work into generator data.

Construction candidates:
- 9 prior Sprite Fusion slouch beanies are cataloged in generator/data/headwear/slouch_beanie_spritefusion_deconstruction.json
- each is ALTERNATE_CONSTRUCTION, status CANDIDATE_FRONT_ONLY
- they are NOT live rollable constructions yet
- require approved directional template frames + wear QC before promotion
- no front-only AI silhouette can silently become production geometry

Material/pattern donors:
- authored/materials/slouch_beanie_v1/manifest.json
- six semantic donor profiles:
  - rib_knit
  - cable_knit
  - heather_knit
  - stripe_colorblock
  - plaid_woven
  - fleece_wool
- oversized labeled Sprite Fusion material tests provide semantic evidence
- approved 19-20px retry batch provides small-scale Stardew readability evidence
- raw Sprite Fusion RGB is evidence only; palette remains a separate roll
- source alpha/silhouette and blind source coordinates never transfer

Roll integration:
- existing knitStructure and pattern axes remain the authoritative material/pattern rolls
- added knitStructure.fleece_wool
- added pattern.plaid_woven
- added materialPatternLibrary + materialPatternBindings
- roll semantics now explicitly separate construction, material structure, pattern overlay, motif, attachment, hardware, and palette

Exclusions:
- plaid_woven blocks cable/chunky/waffle and busy motif combinations
- cable blocks plaid_woven plus existing dense pattern conflicts
- fleece_wool blocks dense jacquard/twist/cable-plus-stripe and knit-in decoration
- heather avoids contrast-stitch stacking
- exclusions are validated as hard guards

Validation:
- PASS slouch beanie roll matrix
- PASS source-backed template generator

## SFB1 slouch accent generator + rarity QC — 2026-09-21

Implemented approved beanie design ideas into the slouch-beanie generator contract.

New roll axes:
- trimAccent: none, band_trim_line, crown_trim_line, double_trim_lines
- microAccent: none, cuff_patch_small, side_bow_small, diagonal_wrap_band, tiny_label_tag

Hard placement rule:
- tiny_label_tag is edge-only
- allowed only at cuff_side_left/right or body_side_left/right
- never center-front, crown-center, or floating in the middle of the beanie

New reusable micro-accent assets:
- cuff_patch_small
- side_bow_small
- diagonal_wrap_band
- tiny_label_tag

New exclusions:
- double trim avoids plaid/jacquard/cable+stripe and diagonal wrap
- side bow avoids plaid plus dense cable/chunky surfaces
- diagonal wrap avoids stripe/color-block/plaid and conflicting trim lines
- label tag has hard side-edge placement-only rule

Validation:
- PASS slouch beanie roll matrix
- 16 roll axes
- 32 exclusions
- existing material/pattern donor profiles remain intact

SFB1 in-game QC:
- live Fashion Sense pack: /run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/RNG-SFB1-Accent-Rarity-QC
- searchable tag: SFB1
- 8 hats total
- Common 2 / Uncommon 2 / Rare 2 / Epic 2
- all frames preserve locked PL24 alpha geometry

## SFB1 visual failure diagnosis + SFB2 source-fidelity test — 2026-09-21

- SFB1 was rejected for visual fidelity.
- Root cause: the SFB1 QC builder did not transfer Sprite Fusion source art; it approximated source categories with generic authored tile swatches, straight procedural trim rows, and hard-coded micro-accent pixels.
- Therefore Sprite Fusion was source/evidence in metadata, but not actual rendering authority.
- SFB1 live QC pack was removed after rejection.

Corrective test:
- tools/test_sf_structural_transfer.py tests row-relative source structure transfer onto locked PL24 geometry.
- tools/build_sfb2_source_fidelity_qc.py builds SFB2 using actual approved 19-20px Sprite Fusion donor RGB/value structure mapped row-by-row onto PL24.
- no procedural texture tiles, trim synthesis, or micro-accent synthesis are used in SFB2.
- target PL24 alpha/silhouette remains locked in all four directions.
- live pack: /run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/RNG-SFB2-Source-Fidelity-QC
- search tag: SFB2
- 8 hats: 2 Common / 2 Uncommon / 2 Rare / 2 Epic.

Production direction pending QC:
- prefer real source-structure transfer from approved source donors;
- do not silently fall back to generic procedural approximations when a source-backed donor exists;
- palette separation can be reintroduced after source-structure fidelity is proven.

## SFB3 true Sprite Fusion directions — 2026-09-21

Directional rendering fix after SFB2 QC:
- Sprite Fusion officially supports direction-set through POST /api/v1/generate.
- direction-set accepts exactly one source image, no prompt, optional size 16/32/64, and returns exactly 8 labeled directions.
- Generated true direction sets for all 8 current SFB source hats.
- Reused the already-paid SF01 direction set; generated SF02-SF08 as seven new requests.
- Total direction-set generation cost for all 8 hats: 120 credits including the first test request.
- All returned directional sprites were 16-23 px, within the accepted <=32 px range.

Stardew cardinal mapping:
- S -> front
- E -> right
- W -> left
- N -> back
- diagonal outputs remain preserved as source evidence but are not used by Fashion Sense.

SFB3 QC:
- source: experiments/sfb3_spritefusion_directions/
- rendered QC: experiments/sfb3_directional_qc/
- live pack: /run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/RNG-SFB3-Directional-QC
- search tag: SFB3
- 8 hats total: Common 2 / Uncommon 2 / Rare 2 / Epic 2
- direct Sprite Fusion cardinal art is used.
- each directional sprite is transparent-padded/bottom-centered to 24x24 only.
- no scale, no row remap, no silhouette rewrite, no procedural side/back generation.
- obsolete SFB2 live pack removed.

Production rule:
- front-only AI/source art may be a candidate or material donor, but may not become production directional output by projection alone.
- for AI-generated candidates, obtain approved directional source frames (Sprite Fusion direction-set is the current preferred method) before directional wear QC.

## Directional design-consistency contract — 2026-09-21

Added explicit cross-view propagation semantics to the slouch-beanie generator.

Three classes:
- WHOLE_HAT: material/all-over pattern identity remains consistent across Front/Right/Back/Left.
- WRAPAROUND_REGION: a design on a continuous semantic region (especially cuff/headband/crown trim) must continue on that same region in every view where the region is visible.
- LOCALIZED: motif/emblem/tag/patch is placement-specific and does not need to appear in every view unless its definition declares that visibility.

Defaults:
- knitStructure + pattern = WHOLE_HAT
- trimAccent = WRAPAROUND_REGION
- motif + microAccent + carrier/decoration = LOCALIZED
- diagonal_wrap_band is explicitly WRAPAROUND_REGION
- tiny_label_tag / side_bow / cuff_patch are explicitly LOCALIZED
- contrast_cuff is WRAPAROUND_REGION

Examples now enforced by contract:
- a line on the headband may not exist only on Front and disappear on side/back;
- all-over heather/plaid/rib treatment must remain the same hat design across cardinal views;
- a front emblem can legitimately disappear on side/back;
- an edge label remains physically attached to its intended edge/side and may not be duplicated as a fixed screen-space sticker.

Validator now checks the view-consistency classes/defaults/critical overrides.
SFB3 batch manifest references this policy for directional QC.

## ESM ingredient-free QC Preview mode — 2026-09-21

Added a non-crafting QC browser directly to Enhanced Sewing Machine.

Behavior:
- QC Preview is available from the ESM/Tailoring UI without inserting ingredients or Fashion Fragments.
- QC Preview cycles registered garments tagged as QC candidates.
- Preview garments are temporary menu state only:
  - no inventory item is created
  - no ingredients are consumed
  - the player's real equipped hat is not replaced
  - the real equipped hat is restored after every preview draw
- existing ESM fitting controls are reused for QC garments:
  - Front / Right / Back / Left
  - X/Y offset
  - per-direction scale
  - reset position / scale / all
- controller/keyboard focus includes QC Preview, Previous Hat, and Next Hat.
- if a QC garment fails to load while QC mode is active, fit controls fail closed instead of falling back to editing the player's real generated hat.

SFB3 integration:
- 8 SFB3 true-direction candidates are registered under assets/garments/qc/sfb3/.
- each uses direct Sprite Fusion cardinal art.
- each is packed as 24x96 (Front, Right, Back, Left).
- RenderScale = 0.8333333333333334, matching the previously validated PL24 ESM normalization.
- Metadata QualityTier=QC and Classification=QC_CANDIDATE, so they appear in the QC browser.
- helper builder: tools/register_sfb3_esm_qc.py

Verification:
- EnhancedSewingMachine Release build: 0 warnings / 0 errors; auto-deployed to live Mods folder.
- EnhancedSewingMachine.Tests executable: ALL TESTS PASSED.
- SFB3 ESM QC registry: 8/8 definitions validated; all textures 24x96; normalized scale confirmed.

## Sprite Fusion workflow rebuild / generator pipeline v2 — 2026-09-21

Canonical handoff:
- docs/SPRITE_FUSION_WORKFLOW.md is the source of truth for GPT/Claude/Codex.
- AGENTS.md now requires future agents to read that file before AI-assisted generator work.

Preserved:
- template/silhouette contracts
- source deconstruction/provenance
- roll matrices, rarity guidance, exclusions, placement, view-consistency semantics
- trusted source-backed render paths
- ESM runtime/fitting/QC preview
- QC/contact-sheet infrastructure

Deprecated for finished SF-backed art:
- SFB1-style generic procedural redraw of donor materials/trim/micro accents
- SFB2-style front-only projection into side/back
- automatic Pixel Snapper pass on clean native Sprite Fusion output

New SF-assisted pipeline:
- sf_pipeline/policy.json defines size/reference/API-operation policy.
- sf_pipeline/model.py defines candidate/direction manifests and promotion states.
- sf_pipeline/reference_bundle.py validates role-based reference sets and builds style-reference request specs.
- sf_pipeline/client.py is a reusable API client; it does not auto-retry charged requests.
- tools/sf_run_request.py executes checked request specs and downloads outputs/provenance locally.
- sf_pipeline/qc.py provides candidate + direction mechanical gates and mandatory semantic human-review checklists.
- sf_pipeline/promotion.py enforces legal lifecycle transitions.
- sf_pipeline/registry.json + tools/sf_pipeline_cli.py provide persistent promotion history.
- generator/data/ai_assisted_visual_pipeline.json connects this pipeline to generator policy.
- slouch_beanie_roll_matrix now requires PRODUCTION_APPROVED plus candidate mechanical QC, direction mechanical QC, human art approval, and ESM wear approval.

Smoke verification:
- PASS SF pipeline policy
- PASS candidate mechanical gate
- PASS 8-direction mechanical gate
- PASS production fail-closed gate
- PASS slouch beanie roll matrix
- PASS dependency-free SF pipeline unit assertions
- PASS SF request runner CLI load

## SFP1 three-rule Sprite Fusion proof — 2026-09-22

Purpose:
- prove the rebuilt SF-assisted generator on WHOLE_HAT, WRAPAROUND_REGION, and LOCALIZED behavior before any rarity batch.

Front generation:
- SFP1 WHOLE_HAT: 9 style-reference outputs; selected output #4, asset 74f928e6-677f-440c-b6e9-b8eaf05d4910, 22x22.
- SFP1 WRAPAROUND: initial request failed and was fully refunded; retry used a 16x16 reference card preserving the original tiny cuff-trim pixels; selected retry output #1, asset 224e0b90-7023-4ca5-bbf5-e38746231c3a, 20x20.
- SFP1 LOCALIZED: initial request failed and was fully refunded; retry used 16x16 reference cards preserving the tiny edge-label pixels; selected retry output #4, asset 5cd0e781-aeff-4fd9-ae54-a6d91b1fb9d4, 20x20.
- All 27 generated front candidates passed the mechanical candidate gate.
- Front selections were visually clean and approved only for direction testing, not production.
Direction proof:
- Each selected front was sent through Sprite Fusion direction-set.
- Each returned all 8 labeled directions and passed the mechanical direction gate.
- Stardew cardinal review uses S=Front, E=Right, N=Back, W=Left.
- WHOLE_HAT pre-ESM semantic review: PASS; knit/material identity remains the same garment across cardinals.
- WRAPAROUND_REGION pre-ESM semantic review: PASS; cuff/headband treatment continues across the visible cardinal views.
- LOCALIZED pre-ESM semantic review: PASS; edge accent behaves as a localized feature rather than an all-over repeated treatment.
- Registry status for all three: CANDIDATE_DIRECTIONAL. Human final art approval and ESM wear approval remain false.
- Combined art sheet: experiments/sfp1_proof/SFP1_cardinal_proof.png.

ESM QC:
- required ESM checkpoint created: archive/esm-checkpoints/ESM_20260922-000240.tar.gz.
- three SFP1 candidates registered into ingredient-free ESM QC Preview.
- native cardinal art is not resized; it is padded/bottom-centered into 24x24 frames.
- presentation scale is normalized from native generated frame width, not opaque bounding-box width.
- Release build: PASS, 0 warnings / 0 errors.
- EnhancedSewingMachine.Tests executable: ALL TESTS PASSED.

## Headwear directional workflow locked — 2026-09-22

SFP1 follow-up proved Sprite Fusion direction-set is unreliable for isolated hats: repeated runs hallucinated wearer/body contamination. The successful production method is now EDIT-CARDINAL.

Production headwear direction construction:
- Front = approved Sprite Fusion candidate.
- Right = Sprite Fusion edit from the approved Front; select compact hat-only result.
- Back = Sprite Fusion edit from the approved Front; select compact hat-only result.
- Left base = deterministic horizontal mirror of the approved Right base for mirror-safe construction.
- Do not spend a separate AI edit on Left unless construction explicitly forbids mirroring and Nana approves an exception.
- LOCALIZED motifs/tags/patches are applied after base cardinal construction by generator semantic zones/anchors/visibility rules.
- direction-set remains only for legacy research/evidence; it is not production authority for hats.
- WHOLE_HAT and WRAPAROUND_REGION tests passed visually with this edit-based method.
- LOCALIZED test showed independent Left AI edit drift; this is why Left is now mirrored and localized decoration remains deterministic.

Implementation:
- sf_pipeline now has DirectionMethod with legacy-direction-set and edit-cardinal.
- direction_qc accepts 4-cardinal edit manifests and preserves legacy 8-direction evidence support.
- sf_pipeline/headwear_directional.py owns deterministic Right->Left mirroring.
- policy/docs/roll-matrix/AI-assisted config all point to edit-cardinal for headwear production.
- validator now explicitly tests both legacy evidence and edit-cardinal production.


## 2026-09-22 — SFP2 8-hat rarity proof batch
- Generated 8 seeded slouch-beanie recipes: 2 Common / 2 Uncommon / 2 Rare / 2 Epic.
- Coverage deliberately spans WHOLE_HAT, WRAPAROUND_REGION, and LOCALIZED consistency classes.
- Generated 72 Sprite Fusion front candidates (9 per recipe); all passed front mechanical size/alpha QC.
- Model-curated one front per recipe for direction testing; humanArtApproved remains false for every candidate.
- Ran EDIT-CARDINAL Right + Back from the selected Fronts. Sprite Fusion returned 2 outputs per edit.
- Provider returned HTTP 402 Payment Required at SFP2_EPIC_1 right; no blind retry was attempted.
- Mechanical directional status:
  - complete: COMMON_1, UNCOMMON_1, UNCOMMON_2, RARE_2
  - replacement Right required: COMMON_2, RARE_1
  - Epic directional edits pending credits: EPIC_1, EPIC_2
- Added tools/apply_sfp2_localized_accents.py: post-cardinal LOCALIZED compositor using authored motif assets, semantic visibility rules, and a hard source-alpha preservation assertion.
- LOCALIZED proof:
  - UNCOMMON_2 flower/woven-patch appears Front + Left for cuff_side_left.
  - RARE_2 leaf/direct-stitch + cuff patch appears Front-only for body_lower_front.
  - EPIC_2 flower/patch Front proof created; remaining base directions are pending credits.
- Built per-rarity candidate pool, raw directional QC, localized, and final-cardinal contact sheets under experiments/sfp2_rarity_batch/.
- Final cardinal manifests remain fail-closed: human art approval and ESM wear approval are still pending.
- Validation: py_compile PASS; slouch roll-matrix validator PASS; scoped git diff --check PASS.


## 2026-09-22 — Beanie rarity gates tightened
- Common is now hard-gated to simple everyday designs: subtle patterns only (solid/heather), quieter knit structures, simple none/narrow/standard cuff construction, no motif/emblem/localized decoration.
- Uncommon requires a noticeable non-motif design feature (stronger stripe/colorblock/jacquard pattern, stronger knit, deeper/rolled construction, trim/wrap, attachment, or hardware), but still forces motif/carrier/decoration/motifPlacement off.
- Motifs/emblems/patches/badges/localized decoration now have minimum rarity Rare.
- Strong stripe/colorblock patterns are minimum Uncommon; cable_plus_stripe is minimum Rare.
- Cuffless hats can no longer roll band_trim_line or double_trim_lines.
- SFP2 proof target slots changed to Common WHOLE+WRAP, Uncommon WHOLE+WRAP, Rare WHOLE+LOCALIZED, Epic WRAP+LOCALIZED.
- Credit-free reroll v2 created under experiments/sfp2_rarity_batch/reroll_v2. No Sprite Fusion generation was called.
- Validator updated to enforce the new rarity floors.

## 2026-09-22 — Generator-wide four-layer taste policy
Implemented the four-layer taste/rarity system as shared generator infrastructure, not a slouch-only evaluator.

Shared architecture:
- `generator/taste_policy.py` is the family-agnostic evaluator.
- `generator/data/taste_policy_registry.json` registers active template families and fails closed when an active template family lacks taste policy coverage.
- Active source-backed/template/AI-assisted recipes must pass this gate before paid visual generation.
- Legacy generator versions keep their frozen rarity systems until intentionally migrated; the new source-backed/template path cannot bypass the shared gate.

Four layers:
1. Hard rarity floors:
   - Common = simple/subtle; no motif/emblem/localized decoration.
   - Uncommon = stronger pattern/material/construction identity; still no motif/emblem.
   - Rare+ = motif/emblem/patch/badge/localized decoration allowed.
2. Complexity budgets:
   - Common 0–1, Uncommon 1–2, Rare 2–4, Epic 3–5.
   - Maximum active visual channels and Secondary/Accent counts are also bounded.
3. Incompatibility/conflict rules:
   - Dense surface conflicts, competing large focal points, extra-slouch/top-heavy conflicts, wrap-vs-double-trim conflicts, side-bow quiet-surface rules, plus semantic completeness checks.
4. Design roles / visual channels:
   - SURFACE, PATTERN, REGION, GRAPHIC, ATTACHMENT, HARDWARE.
   - Construction can consume budget but remains BASE.
   - At most one PRIMARY; bounded SECONDARY and ACCENT support.
   - Multiple competing dominant features are rejected.

Slouch beanie is the first registered family policy because it is currently the only active family in generator/data/templates/index.json. Future active template families must register their own family data but use the same shared engine.

SFP2 planner now calls the registered-family taste API directly and persists a taste report per recipe (complexity, budget, channels, PRIMARY, SECONDARY, ACCENT, errors).
Credit-free reroll v2 obeys the new grammar:
- Common: WHOLE_HAT + WRAPAROUND; no motifs.
- Uncommon: WHOLE_HAT + WRAPAROUND; no motifs.
- Rare: WHOLE_HAT + LOCALIZED.
- Epic: WRAPAROUND + LOCALIZED.
No Sprite Fusion credits were spent for this reroll.

Verification:
- generator-wide synthetic policy test PASS.
- active template-family registry coverage PASS.
- slouch integration PASS.
- chaotic Epic recipe correctly rejected for conflicts, complexity 14>5, 6 visual channels, excessive supports, and competing dominant features.
- slouch roll-matrix validator PASS.
- scoped git diff --check PASS.

## 2026-09-22 — Catalog FAMILY_BASE promotion into formal templates
Systematic source-catalog promotion is now implemented for the new source-backed/template generator.

Coverage:
- Audited all 53 `FAMILY_BASE` entries in `source_catalog/MASTER_CATALOG.json`.
- Promoted 47 suitable static families into formal `source-backed-template/v1` contracts:
  - 20 Hats
  - 7 Shirts
  - 20 Accessories
- Deferred 6 specialized sources:
  - Bow (Side 1): intentionally missing Left cardinal construction
  - Decorative Bells (Singles): animated/stateful
  - Veil: animated/stateful
  - Puffy Sleeves: full sleeves state/animation contract requires specialized adapter
  - Cape: animated/stateful
  - Plumbob (Animated): animated/stateful

Contract behavior:
- Formal contracts reference exact rectangles from local `generator content` source sheets; third-party source PNGs are not copied into Git.
- Exact extracted-frame pixel hashes and alpha-geometry hashes are locked.
- Source-declared Left mirroring, wear offsets, draw/hide fields, and per-view frame sizes are preserved.
- Contract loader now supports source-sheet rectangles and legitimate per-view frame sizes without padding/resampling.
- Every promoted template remains `CANDIDATE_READY` and requires human art/wear approval before production.

Taste / generator integration:
- Every promoted family has its own registered taste policy under `generator/data/taste_policies/catalog/`.
- `generator/catalog_templates.py` provides template discovery/loading, family taste evaluation, source-family lookup, and compatible-donor discovery.
- Promoted templates are linked to `source_catalog/SOURCE_TRANSFER_LIBRARY.json`:
  - 53 source style profiles
  - 216 deconstructed parts
- Donor selection uses existing `template_transfer.decision()` semantics.
- Same-base-only parts work only for the exact canonical source base.
- Alternate constructions remain denied and must become their own template rather than overlaying another construction.
- Example regression: Alt-Fashion Belt template accepts its 5 SAME_BASE_ONLY parts while accepting zero ALTERNATE_CONSTRUCTION parts.

Validation:
- generator-wide taste policy: PASS
- slouch-beanie taste/roll matrix: PASS
- catalog promotion validator: PASS
- all 47 promoted contracts verify source pixel/alpha hashes
- all 47 family taste policies validate a default Common recipe
- no copied PNGs exist under `generator/data/templates/catalog/`

## 2026-09-22 — Catalog family promotion completion / reproducibility
Continued the interrupted catalog-family promotion milestone from commit 4dc5c3f.

Promotion scope:
- 53 catalog FAMILY_BASE entries examined from the tracked source-catalog model.
- 47 families promoted into formal source-backed template contracts and active family taste policies:
  - Hats: 20
  - Shirts: 7
  - Accessories: 20
- Every promoted family is loadable through generator/catalog_templates.py, validates its default Common recipe through the shared taste engine, and can query compatible donor parts from SOURCE_TRANSFER_LIBRARY.json.
- Typical donor result per promoted family: ~59–70 allowed parts with incompatible transfers rejected.

Deferred (6) remain explicit and fail-closed rather than being fabricated:
- Hats / More Accessories and Stuff / Bow (Side 1): missing_cardinal:left. Source JSON has no LeftHat block; unlike accepted mirrored-left constructions, no explicit Flipped Left contract is present.
- Hats / Decorative Bells (Singles): animated_or_stateful.
- Hats / Veil: animated_or_stateful.
- Sleeves / Cottagecore Set / Puffy Sleeves: category_requires_specialized_adapter; source uses a large stateful sleeve animation contract and must not be flattened to a static four-cardinal template.
- Accessories / Cape: animated_or_stateful.
- Accessories / Plumbob (Animated): animated_or_stateful.

Reproducibility fixes:
- tools/build_master_generator_catalog.py is now part of the tracked toolchain.
- Removed its hidden Pillow dependency; it now uses project-native v5.pngio.
- tools/promote_catalog_families.py rebuilds the derived master catalog from tracked source_catalog/catalog.json + families.json before promotion.
- Deferred family IDs/reasons are recorded in both the template registry and taste-policy registry.
- Promotion validator now proves all 53 FAMILY_BASE entries are accounted for exactly once as promoted or deferred.
- Re-running the entire catalog-build/promotion pipeline produced an identical combined generated-output SHA-256 before/after:
  94db684f556f1933a4802f2576fc9944f92764820f3ada688cecffbad9f35d54
- Catalog promotion validator PASS: 47 promoted / 6 deferred.

## 2026-09-22 — Catalog promoter deep audit
The interrupted catalog-promoter result was re-audited against live source files and strengthened.

Verified:
- Existing promoter is deterministic: rerun produced 47 promoted / 6 deferred again with no tracked contract/policy drift.
- All 47 promoted contracts load and re-verify exact source-frame pixel hashes and alpha geometry.
- All 47 map back to a source family in SOURCE_TRANSFER_LIBRARY.json.
- All 47 have at least one allowed STYLE_PROFILE donor and transferable source parts.
- All 47 successfully compile a real source-backed generation recipe through v5/source/template_transfer.py with LOCKED_TEMPLATE_ALPHA.
- All 47 expose at least one valid Common, Uncommon, Rare, and Epic recipe through the shared taste engine.
- Permanent validator tools/validate_catalog_template_promotions.py now checks actual compilation + all four rarity tiers for every promoted family.

Deferred family requirements confirmed from source JSON:
- Bow (Side 1): Front/Right/Back only; no LeftHat block. Requires an explicit mirror-safe/static-cardinal adapter before promotion.
- Decorative Bells (Singles): 4-frame MovementAnimation. Requires animated/stateful headwear template support.
- Veil: side/back MovementAnimation. Requires animated/stateful headwear template support.
- Puffy Sleeves: full Fashion Sense farmer-state sleeve animation contract. Requires specialized sleeves adapter.
- Cape: movement-conditioned multi-frame accessory animation. Requires animated/stateful accessory template support.
- Plumbob (Animated): explicit 4-frame UniformAnimation. Requires animated accessory template support.

Usability boundary:
- The 47 are systematically usable as CANDIDATE_READY construction families in the new generator.
- Their generated catalog taste policies are baseline category-level policies, not hand-tuned final taste profiles for every individual family.
- Human art/wear approval remains mandatory before production.
- Explicit compatible donor transfers remain available through semantic zones/anchors; alternate constructions remain fail-closed.

## 2026-09-23 — Family capacity caps rarity complexity
Implemented geometry-derived family capacity across the shared source-backed generator so small hat families do not get forced into visually overcrowded Rare/Epic designs.

Architecture:
- generator/taste_policy.py now computes the effective rarity budget as the minimum of rarity allowance and family physical capacity.
- High rarity remains available for small families by compressing the required minimum budget to the family cap instead of disabling Rare/Epic.
- Family-capacity blocked values are enforced before generation.
- Catalog-promoted contracts now record per-view opaqueCells as geometry evidence.
- tools/promote_catalog_families.py derives a familyCapacity profile from average opaque cells and writes it into each generated family taste policy.
- Capacity profiles expose surfaceAreaClass, maxComplexity, maxVisualChannels, maxSecondary, maxAccents, maxMotifFootprintCells, maxAttachmentFootprintClass, blockedValues, and COMPRESS_BUDGET_NOT_DISABLE_TIER.
- Manual slouch_pl24 is explicitly registered as large capacity (avg 307.75 opaque cells) so it does not bypass the shared rule.

Current promoted hat capacity distribution:
- tiny: 4 — Bows (Double, Small 1), Headband, Headband (Studded), Headband (Daisies)
- small: 3 — Crown (Diadem 1), Hair Buns, Garland (Dried 1)
- medium: 8 — Earmuffs, Earmuffs (Horns), Boater Hat, Headscarf, two Beanies, Beret, Tulip Hat
- large: 5 — Straw Hat, Sun Hat, Mushroom Hat, Hood, Hood (Mushroom)

Capacity behavior:
- tiny: max complexity 2, max 1 visual channel; blocks large motif, large attachment, dense pattern, wrap.
- small: max complexity 3, max 2 channels; blocks large motif/attachment.
- medium: max complexity 4, max 3 channels; blocks large motif.
- large: max complexity 5, max 3 channels.
- A tiny Epic can therefore be valid at complexity 2, but cannot accumulate extra channels just to satisfy the normal Epic 3–5 budget.

Validation:
- generator-wide taste policy PASS, including synthetic tiny-family Epic compression regression.
- slouch beanie roll matrix PASS.
- catalog template promotions PASS: 47 promoted / 6 deferred.
- every promoted family still has at least one valid Common, Uncommon, Rare, and Epic recipe after capacity caps.
- legitimate zero-opaque directional views are preserved and counted rather than treated as invalid.
- No ESM/QC promotion performed; contact-sheet approval remains the next visual gate.

## 2026-09-23 — Targeted-RNG gameplay bookmark + capacity-aware hat contact sheet
- Future gameplay design saved at docs/decisions/DUPLICATE_CLOTHING_TARGETING.md.
- Bookmark rule: 3 matching Category Tokens + 1 Clothing Catalyst = guaranteed category + strong catalyst-family bias.
- Catalyst rarity does not directly copy rarity onto the result; exact economy weights remain intentionally untuned.
- No gameplay code was implemented for the token/catalyst system yet.

Capacity-aware cross-family hat contact sheet:
- tools/build_cross_family_hat_rarity_contact.py now pairs each visual candidate with a policy-valid recipe evaluated through generator/catalog_templates.py.
- Contact matrix deliberately spans tiny / small / medium / large capacity families for every rarity tier.
- Strongest valid recipe is selected per family+rarity, so the sheet proves compressed high-rarity behavior rather than forcing normal Epic complexity onto tiny families.
- Current Epic proof: tiny 2/2, small 3/3, medium 4/4 cap, large 5/5 cap.
- Visuals remain real source-backed front candidates; recipe/capacity proof is recorded in experiments/catalog_hat_rarity_test/selection_manifest.json.
- Contact sheet: experiments/catalog_hat_rarity_test/CROSS_FAMILY_HAT_ALL_RARITIES_CONTACT.png.
- humanArtApproved remains false. No ESM/QC promotion performed.

## 2026-09-23 — First full multi-family hat production candidate batch
- Added tools/build_hat_production_batch.py.
- Generated 80 source-backed hat candidates: 20 promoted hat families × Common/Uncommon/Rare/Epic.
- Output lives in experiments/hat_production_batch_01/ with manifest.json, 320 directional frames, and two review contact sheets.
- Recipe selection stays capacity-aware and taste-policy valid for every candidate.
- Rendering uses locked template geometry, source-backed style profiles, semantic trim treatment, and permitted MATERIAL_PATTERN / MOTIF / ATTACHMENT / HARDWARE donors.
- Hat candidates now prefer hat-category donors when a compatible hat donor exists.
- Additive attachment/hardware pixels are connectivity-filtered so detached floating pixels are discarded.
- Validation PASS: 80 candidates, 20 families, 4 rarities each; all recipes valid; base alpha preserved; additive alpha only for permitted attachment/hardware paths.
- Transfer usage in batch: MATERIAL_PATTERN 51, MOTIF 23, ATTACHMENT 16, HARDWARE 12.
- Capacity coverage: medium 32, large 20, tiny 16, small 12 candidates.
- humanArtApproved remains false; these are production candidates for visual curation, not promoted shipping assets.
- Review sheets: experiments/hat_production_batch_01/HAT_PRODUCTION_BATCH_01_1.png and HAT_PRODUCTION_BATCH_01_2.png.

## 2026-09-23 — Hat proportional line grammar + palette sanity/harmony gate
Implemented after human review of production Batch 01 identified two repeatable failures: over-thick/misplaced horizontal bands and palette choices that preserved silhouette but weakened hat readability.

Proportional line/ribbon grammar:
- Added generator/data/hat_visual_contracts.json with a visual contract for all 20 promoted hat families.
- Every family now declares: lineAllowed, lineSemanticType, lineZone, lineCenterYRatio, lineThicknessPxMax, lineWidthRatioRange, lineMayTouchOutline, lineMayOverlapBrimBand, lineContrastMaxStep, lineCountMax, lineForbiddenRowsRelativeToBottom, lineCenterToleranceRatio, and semantic brim boundary.
- Line placement is normalized against the hat's opaque bounding box and the usable opaque width of the target crown row, not a loose absolute anchor.
- Hard max thickness is 1 px for the current hat families.
- Line color may move only one adjacent value-ramp step from the midtone.
- Line rows may not touch outer silhouette edges, forbidden bottom rows, or semantic brim rows.
- Pattern/motif rendering is prevented from overwriting the accepted line cells, eliminating trim/pattern band stacking.
- Families that should not have a horizontal treatment fail closed at recipe planning; trim is not silently drawn somewhere else.
- Family behavior is explicit: beanie/beret use crown-mid treatment, boater/straw/sun use crown-base ribbon treatment, headscarf uses upper-crown stitch treatment, tulip uses crown-mid stitch treatment, and hoods/headbands/bows/earmuffs/crown/garland/hair-buns/mushroom-cap families disallow the generic line treatment.

Palette sanity/harmony layer:
- Added generator/hat_visual_rules.py as a dependency-free generator-side visual gate.
- Every style vocabulary is assigned explicit outline/shadow/midtone/light/accent roles.
- Palette donors are classified into soft_neutral, earthy_warm, cottage_pastel, muted_cool, alt_monochrome, or bright_playful.
- Per-family contracts declare allowed and preferred harmony families.
- Donor selection now prefers an exact source-family palette when it is valid; otherwise it limits selection to the family's preferred harmony tags before falling back to other allowed tags.
- Donor palettes with collapsed outline->midtone or midtone->light value structure are filtered before rendering.
- Capacity accent budgets are enforced at tiny 8%, small 10%, medium 14%, large 18%, with discrete floors of 2/3/5/8 pixels so tiny art remains mathematically usable.
- Accent budgets now follow the taste engine's semantic roles: PRIMARY and SECONDARY motifs/attachments are not incorrectly charged as ACCENT; only features classified as ACCENT consume the accent budget.
- Family accent-system caps prevent clutter; hood families allow one motif/attachment/hardware accent system max.
- Palette checks reject excessive disconnected accent islands, excessive accent-to-neighbor value jumps, crown accent dominance, muddy yellow+brown+cream major-role stacks, and new harsh horizontal value bands.
- Harsh-band detection is relative to the source-styled reference frame, so authored/source structural shading is not falsely penalized.
- Zone-aware crown/brim checks only apply brim-specific rules to families that actually have a semantic brim.

Automatic reject/retry:
- tools/build_hat_production_batch.py now prechecks line legality, harmony eligibility, role/value sanity, and post-render visual metrics.
- A failing candidate is rejected before it reaches the contact sheet and the deterministic generator tries another legal recipe/donor combination.
- Rejection reason, palette metrics, line-placement metrics, semantic roles, harmony tag, and rejected attempts are written into the candidate manifest.
- tools/validate_hat_visual_rules.py adds regression coverage for all 20 contracts, proportional position/thickness/width rejection, family line prohibition, explicit palette roles/harmony tags, and accent-budget behavior.

Governed proof batch:
- experiments/hat_production_batch_09/ is the post-rule proof batch: 80 candidates / 20 families / 4 rarities / 320 directional frames.
- All 80 final candidates completed with zero final visual-rule errors.
- 10 intermediate attempts were automatically rejected before a clean candidate was accepted; the recorded repeat failure in that final run was newly-created harsh horizontal banding.
- Contact sheets: experiments/hat_production_batch_09/HAT_PRODUCTION_BATCH_09_1.png and HAT_PRODUCTION_BATCH_09/HAT_PRODUCTION_BATCH_09_2.png.
- humanArtApproved remains false. Numeric/structural gates prevent known repeat failures but do not replace human art review.

Validation:
- tools/validate_taste_policy.py PASS.
- tools/validate_catalog_template_promotions.py PASS: 47 promoted / 6 deferred, including all 20 hat families.
- tools/validate_hat_visual_rules.py PASS.
