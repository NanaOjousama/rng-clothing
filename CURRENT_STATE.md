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

## 2026-09-23 — Source-Respecting Remix pilot replaces generic hat redraw path
Human review of Batch 09 confirmed the remaining failure was architectural: the generic compositor could still redraw meaningful source construction into weak synthetic stripes/palette treatments. The hat pilot now follows a source-respecting remix model instead.

Guiding principle:
- Preserve the source hat's core construction. Remix the non-core parts.
- Looking recognizably like the approved source art is acceptable and preferred over forced novelty that weakens readability.

Formal model:
- generator/data/source_respecting_remix_model.json defines four feature classes:
  1. LOCKED_CONSTRUCTION — brim, crown, built-in ribbon geometry, default knit band, defining seams, source shading topology. No removal/resample/generic normalization.
  2. MUTABLE_SOURCE_BACKED_FEATURE — source feature geometry stays locked; only declared color/material/highlight treatment inside its stored mask may vary.
  3. OPTIONAL_ADDON — explicit source-backed component only, using exact same-construction patches or declared authored parts.
  4. ALTERNATE_CONSTRUCTION_STATE — whole authored source state, e.g. floppy/cat beanie, messy straw hat, authored ribbon construction.
- Generic donor-delta projection, arbitrary STYLE_PROFILE whole-hat recolor, fake replacement ribbons, generic line synthesis, and runtime brightness-role inference are prohibited in the pilot.
- Palette priority is source family -> material/construction family -> curated transfer group -> generated last resort. Generated-last-resort is disabled for the pilot.

Explicit source-part deconstruction:
- tools/build_hat_source_parts.py writes generator/data/source_parts/hat_pilot_parts.json.
- Beret Dotted, Leaf, Ribbon, and White Ribbon are deconstructed as exact source-coordinate patches and each patch is proven to reconstruct the source-author variant pixel-for-pixel.
- Dotted + Leaf are legal OPTIONAL_ADDON source patches.
- Ribbon + White Ribbon change authored alpha and are therefore classified as ALTERNATE_CONSTRUCTION_STATE, not removable optional parts.
- Exact source RGB -> semantic role maps are stored at extraction time for all pilot source states. Runtime rendering does not infer roles from brightness.
- Fashion Sense Flipped semantics are materialized during extraction/rendering, so stored frames match authored in-game direction behavior.

Pilot compositor:
- generator/source_respecting_hat_remix.py is the new 3-family compositor.
- Beret starts from exact Cottagecore Set source frames; Dots/Leaf use exact same-construction patches; Ribbon variants use whole authored source states.
- Beanie uses whole More Accessories and Stuff authored Regular / Floppy / Cat construction states. Existing knit/cuff/seam art is preserved rather than regenerated.
- Straw Hat uses whole authored Regular / Messy construction states. Warm straw body pixels are locked; the built-in grayscale ribbon is identified by its stored source RGB roles and only that exact mask may be recolored.
- Palette/tint changes preserve source alpha and source shading ratios. No arbitrary compatible STYLE_PROFILE is used.
- Generic projection used: false. Generic synthesized line used: false.

Floating/isolated line rejection:
- Existing hat visual contracts now include minimum contiguous width ratio, minimum pixel length, side-support requirement, and isolated-center-fragment rejection.
- Beret, Beanie, and Straw Hat explicitly opt out of the generic line system and declare SOURCE_RESPECTING_REMIX_ONLY authority.
- The old line validator now rejects short isolated center dashes in families that still use line grammar.

Redo pilot batch:
- experiments/source_respecting_hat_pilot_01 contains 27 candidates:
  - 10 Berets
  - 9 Beanies
  - 8 Straw Hats
- Overview: experiments/source_respecting_hat_pilot_01/SOURCE_RESPECTING_HAT_PILOT_OVERVIEW.png
- Directional sheets: BERET_DIRECTIONAL.png, BEANIE_DIRECTIONAL.png, STRAW_HAT_DIRECTIONAL.png
- Native variants are pixel-identical to source-render frames.
- All recolors preserve source alpha.
- Straw ribbon recolors touch only the built-in source ribbon mask.
- humanArtApproved remains false; this batch is specifically for visual review before expanding the model to the other 17 hat families.

Validation:
- tools/validate_source_respecting_hat_remix.py PASS.
- tools/validate_hat_visual_rules.py PASS including pilot opt-out + isolated-fragment rejection.
- tools/validate_taste_policy.py PASS.
- tools/validate_catalog_template_promotions.py PASS: 47 promoted / 6 deferred.

## 2026-09-23 — Source-Respecting Hat Batch A
Expanded the approved Source-Respecting Remix Model from the 3-family pilot to four more hat families: Boater Hat, Mushroom Hat, Sun Hat, and Tulip Hat.

Batch A source decomposition:
- Boater Hat: exact base + Bow and Ribbons same-construction source patches. Crown/brim/built-in band stay locked; only stored source feature-role pixels may be recolored.
- Mushroom Hat: exact base + Dotted source surface patch. Cap/stem/defining seams stay locked; cap recolor is restricted to explicit body-role pixels.
- Sun Hat: exact base + Flowers source patch; Ribbon is treated as a whole alternate source construction state because it changes authored geometry/palette substantially.
- Tulip Hat: exact base + Striped source surface patch. Petal silhouette/folds stay locked; stripe recolor is restricted to explicit pattern-role pixels.
- Six new source patches are stored in generator/data/source_parts/hat_source_parts.json and each reconstructs its author variant exactly.
- Combined source registry now covers 7 families and 10 source patches total.

Batch A generation:
- experiments/source_respecting_hat_batch_a_01 contains 36 candidates:
  - 9 Boater Hat
  - 8 Mushroom Hat
  - 11 Sun Hat
  - 8 Tulip Hat
- Generic donor projection: disabled.
- Generic synthesized line treatment: disabled.
- Generated palette fallback: disabled.
- All source-native states are preserved pixel-for-pixel.
- All recolors preserve source alpha and remain inside their explicit source RGB semantic masks.
- Batch A overview: experiments/source_respecting_hat_batch_a_01/SOURCE_RESPECTING_HAT_BATCH_A_OVERVIEW.png
- Directional sheets: BOATER_HAT_DIRECTIONAL.png, MUSHROOM_HAT_DIRECTIONAL.png, SUN_HAT_DIRECTIONAL.png, TULIP_HAT_DIRECTIONAL.png.
- humanArtApproved remains false pending visual review.

Validation:
- validate_source_respecting_hat_batch_a.py PASS: 36 candidates, 6 exact patches, 10 native source states pixel-identical, recolor masks enforced.
- validate_source_respecting_hat_remix.py PASS for the original 3-family pilot.
- validate_hat_visual_rules.py PASS after moving all 7 source-respecting families out of the generic line path.
- validate_taste_policy.py PASS.
- validate_catalog_template_promotions.py PASS: 47 promoted / 6 deferred.

## 2026-09-23 — Source-Respecting Hat Conversion COMPLETE (20/20 promoted families)
Finished the remaining 13 promoted hat families on the approved Source-Respecting Remix architecture.

Remaining families converted:
- Alt-Fashion: Beanie, Earmuffs (Horns family), Headband (Studded family).
- Cottagecore: Headband (Daisies family), Headscarf, Hood (Mushroom family).
- More Accessories and Stuff: Bows (Double, Small 1 family), Crown (Diadem 1 family), Earmuffs, Garland (Dried 1 family), Hair Buns, Headband, Hood.

Completion policy:
- Every authored source variant is treated as a whole authored construction state by default.
- Fully grayscale authored states may receive curated role-bound body tints.
- Chromatic authored states remain source-native unless an explicit mutable source mask exists.
- Generic donor projection is disabled.
- Generic synthesized line treatment is disabled.
- Arbitrary whole-hat STYLE_PROFILE recoloring is disabled.
- Generated palette fallback is disabled.

Remaining-family proof batch:
- experiments/source_respecting_hat_remaining_01 contains 84 candidates across the final 13 families.
- Review sheets: REMAINING_BATCH_B_OVERVIEW.png, REMAINING_BATCH_C_OVERVIEW.png, REMAINING_BATCH_D_OVERVIEW.png.
- Per-family directional sheets are included for all 13 families.
- Every native authored state is pixel-identical to its source render frame.
- Every tint preserves source alpha and is confined to explicit source RGB body-role masks.

Validation:
- validate_source_respecting_hat_remaining.py PASS.
- validate_source_respecting_hat_batch_a.py PASS.
- validate_source_respecting_hat_remix.py PASS.
- validate_hat_visual_rules.py PASS with all 20 promoted hats declaring SOURCE_RESPECTING_REMIX_ONLY line authority.
- validate_taste_policy.py PASS.
- validate_catalog_template_promotions.py PASS: 47 promoted / 6 deferred, including 20 hats.

## 2026-09-23 — Photo Tailor Bridge prototype
Built an isolated prototype generator under prototypes/photo_tailor_bridge/ to test whether Photo Tailor-style semantic image understanding is worth integrating.

Prototype pipeline:
- Uses the local Photo Tailor Marqo FashionSigLIP ONNX image encoder plus its label embeddings.
- Keeps ranked category / silhouette / pattern candidates.
- Extracts a hat-focused palette from the reference image.
- Matches the reference to a source-respecting construction.
- Keeps our source-backed geometry authoritative.
- Applies reference color within safe construction pixels.
- Projects only supported semantic patterns (horizontal/vertical stripe, plaid, dot) inside the construction.
- Exposes the existing dad-cap construction as prototype-only so cap references are not forced into beanie geometry.

Prototype dependencies are NOT production dependencies:
- numpy
- Pillow
- onnxruntime
- external local Photo Tailor FashionSigLIP ONNX model + labels

Test batch:
- experiments/photo_tailor_bridge_02/
- 8 clean single-hat/reference inputs from existing project references.
- Contact sheet: PHOTO_TAILOR_BRIDGE_V2_CONTACT.png
- Manifest records model detections, family/state selection, extracted RGB/palette, and source paths.

Production generator was not modified by this prototype.

## 2026-09-24 — Hat goldens frozen; production compositor replaced
The user approved the complete source-respecting hat proof set. All 20 promoted hat families are now frozen as human-approved golden families.

Golden authority:
- experiments/source_respecting_hat_pilot_01/manifest.json -> HUMAN_ART_APPROVED
- experiments/source_respecting_hat_batch_a_01/manifest.json -> HUMAN_ART_APPROVED
- experiments/source_respecting_hat_remaining_01/manifest.json -> HUMAN_ART_APPROVED
- generator/data/source_respecting_hat_goldens.json is the production whitelist.
- 20/20 promoted hat families are mapped to golden source families.
- 147 approved source-state / palette pairs are whitelisted.
- source construction/feature contracts are marked GOLDEN_SOURCE_RESPECTING_V1.
- generic donor projection, generic line synthesis, and legacy STYLE_PROFILE fallback are disabled for production hats.

Production renderer:
- tools/build_hat_production_batch.py was replaced with the source-respecting production path.
- generator/source_respecting_hat_production.py keeps the existing taste-policy recipe system, family-capacity compression, rarity budgets, conflicts/exclusions, and visual precheck.
- Active production test rarities: Common / Uncommon / Rare / Epic.
- Every pixel render must select an approved golden state/palette pair; there is no fallback compositor.
- Presentation lean remains optional and bias-only: neutral / male_leaning / female_leaning. It never hard-locks gender or palette.
- Small approved pools exhaust distinct approved states before reuse instead of fabricating extra rarity clutter.

Final production test batch:
- experiments/hat_production_source_respecting_final_01/
- 80 candidates = 20 families x 4 rarities.
- Rarity counts: Common 20 / Uncommon 20 / Rare 20 / Epic 20.
- Cross-family sheets: FINAL_HAT_PRODUCTION_ALL.png, FINAL_HAT_PRODUCTION_OVERVIEW_A.png, FINAL_HAT_PRODUCTION_OVERVIEW_B.png.
- 20 per-family directional sheets are under family_sheets/.
- Final production batch remains CANDIDATE_REVIEW_REQUIRED until the user visually approves it.

Validation:
- validate_hat_production_source_respecting.py PASS.
- All 80 saved frames pixel-match a fresh render from their approved golden pair.
- Original pilot, Batch A, remaining-13, hat visual rules, taste policy, and catalog-promotion validators all PASS.

## 2026-09-24 — Final 80-hat production batch HUMAN_ART_APPROVED
The user visually approved `experiments/hat_production_source_respecting_final_01/` as clean/good. It is now the production visual golden baseline `HAT_PRODUCTION_GOLDEN_V1`.
- 80/80 candidates are `HUMAN_ART_APPROVED`.
- 20 source-respecting hat families x Common/Uncommon/Rare/Epic.
- Baseline metadata: `generator/data/hat_production_golden_baseline.json`.
- Future Photo Tailor/private-lab experiments must compare against this baseline rather than old failed batches.

## 2026-09-24 — Photo Tailor Private Lab 02 end-to-end challenge
Built isolated `prototypes/photo_tailor_private_lab_02/` and `experiments/photo_tailor_private_lab_02/` after freezing `HAT_PRODUCTION_GOLDEN_V1`. It uses 20 copied reference inputs (16 hats + 4 shirts), FashionSigLIP semantic blueprints, copied construction controls, and the isolated PT-style compiler. Runtime has zero production generator/render imports.
Automated proxy result is MIXED: baseline 8.73 -> enhanced 9.18 (+0.45). Strongest gains: pattern continuity +1.60, motif location +1.92, palette/material resemblance +0.71. Golden baseline remains slightly stronger for pristine coherence/readability/junk control. Do not integrate the whole PT stack yet; keep the private lab for human review and selectively preserve the systems that showed material gains.

## 2026-09-24 — Photo Tailor Private Lab 03 + final A/B/C comparison
Built isolated Lab 03 using the same 20-reference challenge set as Lab 02. Lab 03 keeps copied golden/source pixels authoritative and applies only bounded PT-style feature deltas: normalized patterns, region palettes/color bands, motif/facing scopes, overlays and occupancy cleanup.
Validation: zero production imports; all 80 directional outputs preserve alpha geometry; source outline pixels are preserved exactly.
Automated proxy result: baseline 8.81 -> Hybrid 9.29 (+0.48), decision PROMISING_HYBRID.
Final same-reference comparison: A Golden 8.73, B Full PT Lab 02 9.18, C Hybrid Lab 03 9.29. Hybrid is +0.11 vs Full PT and recovers most coherence/junk-control losses.
Final review package: experiments/photo_tailor_final_comparison/ with FINAL_A_B_C_20_REFERENCE_CONTACT.png, FINAL_A_B_C_SCORECARD.png, FINAL_LAB_01_02_03_OVERVIEW.png, FINAL_COMPARISON.md and JSON.
Lab 01 remains an architectural capability proof and is not assigned a fake same-20-reference numeric score.

## 2026-09-24 — Native Hat Hybrid Production V1
Productionized the winning Lab 03 concepts as an independent native hat enhancement layer on top of `HAT_PRODUCTION_GOLDEN_V1`.

Production code:
- `generator/hat_hybrid_enhancements.py`
- `generator/source_respecting_hat_production.py`
- policy: `generator/data/hat_hybrid_production_policy.json`
- decision doc: `docs/decisions/HAT_HYBRID_PRODUCTION_V1.md`

The production path has no Photo Tailor, prototype, FashionSigLIP, ONNX, or vendor runtime dependency/import. Golden source-respecting pixels remain authoritative.

Hybrid safety:
- exact alpha geometry must match golden;
- exact outline pixels must match golden;
- size must match golden;
- delta ratio is capped by family capacity;
- any failed gate returns the exact golden render.
- tiny families skip procedural hybrid clutter and rely on approved authored states.

Final test batch:
- `experiments/hat_production_hybrid_final_01/`
- 80 candidates = 20 families x Common/Uncommon/Rare/Epic.
- 42/80 received native hybrid deltas.
- 1/80 exceeded its conservative capacity delta cap and automatically fell back to exact golden pixels.
- 37/80 remained effectively golden because their recipe/capacity did not call for a safe enhancement.
- comparison: `HYBRID_VS_GOLDEN_CONTACT.png`.
- final hybrid batch remains CANDIDATE_REVIEW_REQUIRED until visual approval.

## 2026-09-24 — Hat renderer frozen; catalog remains open
Frozen the hat rendering architecture as `HAT_RENDERER_V1`: `HAT_PRODUCTION_GOLDEN_V1` quality authority + native bounded hybrid enhancements. This freezes the renderer, not the family catalog.

Contract:
- `generator/data/hat_renderer_contract.json`
- decision: `docs/decisions/HAT_RENDERER_FROZEN_V1.md`

Production loader/builder no longer require exactly 20 families; the golden registry must be internally consistent and may grow beyond the current 20-family baseline. Ordinary new families must use HAT_RENDERER_V1 rather than redesigning rendering architecture.

Hat-type gap audit:
- `docs/roadmaps/HAT_TYPE_GAP_AUDIT.md`
- machine data: `generator/data/hat_type_gap_audit.json`
- 116 hat-slot source appearances audited.
- 70 appearances are already represented by current production source contracts/states.
- 46 are not represented by current production contracts.
- master production-gap list contains 25 construction/content types.

Important audit findings:
- Cowboy Hat already exists in the primary source corpus and is REVIEW_NEEDED.
- Current normal-cap scope is Baseball + Dad + Trucker. Baseball is in a PT-assisted fresh-reference reboot; old Dad/Trucker experiment art remains quarantined during new construction.
- Snapback is deferred/not required; Mario/reference cap is deferred to separate easter-egg work.
- Slouch Beanie remains a separate existing experiment worth revisiting independently.
- Paperboy Hat source failed live readability and should not be promoted unchanged.
- old source/prototype material should not be deleted before its missing family is promoted or explicitly rejected; archive candidates are documented separately.

## 2026-09-24 — Cap reboot clean-room started
Normal cap scope is now Baseball Cap + Dad Cap + Trucker Cap. Snapback is deferred/not required unless future worn-scale testing proves it meaningfully distinct. Mario/reference cap is excluded from normal caps and deferred to separate easter-egg content.

Hard visual quarantine for fresh cap construction:
- do not open/sample/trace `experiments/dad_cap/`;
- do not open/sample/trace `experiments/dad_cap_v2/`;
- do not open/sample/trace `experiments/trucker_cap/`;
- old cap history remains preserved but is not an active silhouette donor.

Baseball Cleanroom 04 (Python-authored geometry) was visually rejected/superseded and is no longer installed. It remains historical evidence only.

Active Baseball Cap candidate set is **Photo Tailor reboot 04**:
- authoritative local reference folder: `cap reference/`;
- primary front + true back: `Screenshot_20260924_223136.png`;
- primary right-facing side: `Screenshot_20260924_223116.png`;
- `Screenshot_20260924_223057.png`, `caprefimages.jpeg`, and `capefernece.jpeg` are secondary proportion/construction checks;
- PT FashionSigLIP independently classifies front/right/back/overview as `hat -> cap -> standard`;
- reference-derived occupancy drives silhouette; PT normalized cap regions/construction logic drives rendering;
- BackHat is true rear crown/opening/strap only, with no visor/brim behind the player;
- reference logos/motifs are ignored in the base master;
- no old Dad/Trucker/Mario art and no old PT cap control is used;
- PT5 Primary/Balanced is the primary worn-QC candidate; PT6 Primary/Compact is the comparison candidate;
- test pack: `test-packs/fashionsense/RNG-Cap-Reboot-Baseball-PT-04/`;
- installed: `Mods/[FS] RNG Cap Reboot Baseball PT 04`;
- status: CANDIDATE_WORN_QC, not production-approved.

Docs: `docs/caps/CAP_REBOOT_CLEANROOM.md`, `docs/caps/BASEBALL_CAP_PT_04.md`.

## 2026-09-24 — Baseball reboot now uses actual Photo Tailor runtime
The prior PT04 experiment was not the real PT renderer and is superseded for Baseball construction/QC.

Actual Photo Tailor 0.15.1 is installed locally on the Deck and runs under native Linux SMAPI with Linux ONNX Runtime shared libraries supplied alongside the mod. `mods/PhotoTailorPersonalBridge/` adds a personal-only `pt_make_cap` console command which invokes PT's compiled `LocalOutfitAnalyzer` and `SpriteRenderer` by reflection.

For this cap-only helper:
- PT Precise Recognition is used with a full-image crop and category hint `hat`;
- silhouette is explicitly forced to the known class `cap`;
- PT owns blueprint/palette/pattern/canonical artwork/projection/final pixels;
- no custom cap renderer is used;
- old Dad/Trucker/Mario art is not used.

Real PT Baseball checkpoint:
- `experiments/cap_reboot/baseball_cap_pt_real_01/`
- raw candidates: Plain, Colored Front, Colored Side;
- each source is PT's own 20×80 native hat texture;
- `test-packs/fashionsense/RNG-Cap-Reboot-Baseball-PT-REAL-01/` copies those PT sheets unchanged;
- installed QC pack: `Mods/[FS] RNG Cap Reboot Baseball PT REAL 01`;
- exact pixel-match validation passed for all 3 candidates;
- only the PT REAL Baseball pack is installed; earlier fake PT04/Cleanroom packs were removed from the active game.
- status: CANDIDATE_WORN_QC, not production-approved.

Doc: `docs/caps/BASEBALL_CAP_PT_REAL_01.md`.

## 2026-09-25 — cap reboot fallback restored to old source-backed constructions

- User explicitly ended the clean-room/PT cap-construction direction after visual rejection of the PT custom-occupancy 24x24 result.
- Baseball now uses the existing `authored/source_backed/cap_baseball` / More Accessories and Stuff `Cap 2` construction again. This base previously passed live Fashion Sense QC (`qc_bridge/captures/20260916-213415`) and remains geometry-locked while palette/decoration can vary through the source-backed generator.
- A fresh validation roll using `STREET_TEAL_GRAPHITE` + `cap_baseball_front_ring` rendered successfully with no dropped cells; output is under `experiments/cap_reboot/old_baseball_return_01/fresh_roll_teal_ring/`.
- Dad Cap V1/V2 and Trucker experiment folders are reopened as construction candidates; their prior clean-room visual quarantine is lifted.
- Photo Tailor cap geometry experiments are historical/reference evidence only and are no longer the active Baseball construction path.

## 2026-09-25 — full cap source-corpus audit + source-derived cap candidates

- User explicitly requested searching the full repo/reference corpus plus `/home/deck/Downloads/` and `/run/media/deck/USD00/` for cap-like mod-author sources, then building Baseball/Dad/Trucker from the strongest source constructions.
- External content-aware scan found 22 named-cap author assets before construction-group collapse. Important unique construction groups: plurffle Cap1/Cap2 (same alpha), plurffle Snapback, plurffle Paperboy, Jedone Backwards Cap x5 (same alpha), Jedone Vintage Cap x3 (same alpha), Jedone Cap & Headphones x8 (same alpha; Vintage core + headphone pixels), Jedone Officer Cap, Seyph/Ragnarok Boys Cap, PeacefulEnd Maid Cap. A standalone 16px Trucker front reference also exists.
- Audit outputs: `experiments/cap_source_corpus_audit_01/CAP_SOURCE_AUDIT_CONTACT_X10.png`, `cap_source_audit.json`, and `docs/caps/CAP_SOURCE_CORPUS_AUDIT_2026-09-25.md`.
- Selected experimental candidates:
  - Baseball: Seyph/Ragnarok `0_BoysCap.png` exact alpha geometry.
  - Dad: Jedone `Vintage Cap_01` exact alpha geometry.
  - Trucker: plurffle `Cap (Snapback)` exact alpha geometry; Trucker identity comes from panel/material treatment informed by the old 16px Trucker front reference and vanilla #16 Trucker study.
- Source-derived template policy: borrow alpha geometry only; source RGB/design is not copied. Project neutral shading / identity preview / future generator styling is new.
- Exact source/template alpha hash equality verified for all three candidates.
- Candidate outputs live under `experiments/cap_source_corpus_audit_01/selected_templates/`; QC pack prepared at `test-packs/fashionsense/RNG-Cap-Source-Template-QC/`.
- These are NOT yet production-promoted. Existing live-approved Cap2 remains the active Baseball fallback until human contact-sheet + worn QC approval.

## 2026-09-25 — full cap source final-output generator batch

- Built a finished-output batch from every complete unique cap construction in the cap-source audit, plus one Trucker derived from the structured Snapback geometry.
- Batch has 12 final Rare-style rolls, each with front/right/left/back views:
  Cap2 Baseball, Snapback, Ragnarok Boys Cap, Jedone Backwards Cap, Jedone Vintage Cap, Jedone Cap+Headphones, Jedone Officer Cap, plurffle Paperboy, PeacefulEnd Maid Cap, old Dad V1, old Dad V2, and derived Trucker.
- Rendering route is source alpha/silhouette + source value/shading topology -> curated project palette ramp -> bounded HAT_RENDERER_V1 hybrid treatment.
- No source RGB palette is carried forward by the palette-map step.
- Every row preserved alpha; HAT_RENDERER_V1 enhancement applied successfully on all 12 with no fallback.
- Contact sheet: `experiments/cap_source_final_generator_batch_01/ALL_CAPS_FINISHED_CONTACT_X9.png`.
- QC pack: `test-packs/fashionsense/RNG-Cap-Source-Final-Batch-QC/`; installed to Stardew Mods as `[FS] RNG Cap Source Final Batch QC`.
- These remain visual-QC candidates, not production promotion.

## 2026-09-25 — cap final-output failure fix / strict real-pipeline QC

- Rejected the previous `cap_source_final_generator_batch_01` approach as a failed QC shortcut; it is not production authority.
- Added `generator/data/cap_family_production_contracts.json` and `tools/build_cap_real_pipeline_batch.py`.
- New cap gate requires four explicit materialized views, native frame size, no frame resizing, locked alpha, no full-frame contamination, and family-specific identity/design treatment.
- Trucker output may use the validated Snapback four-view construction as geometry but MUST NOT ingest any pixels from the front-only Trucker references; those remain identity/reference evidence only.
- Officer uses the exact Officer source construction and a service-cap-specific badge treatment instead of generic cap decoration.
- Current corrected QC batch contains 9 unique cap families: Baseball, Snapback, Boys Cap, Backwards Cap, Dad/Vintage, Cap+Headphones, Officer, Paperboy, and Trucker.
- Old Dad V1 is intentionally not in the production batch because its front source fills the entire 20x20 frame and is contamination/rescale-suspect. Old Dad V2 is superseded by the stronger Vintage/Dad construction. Maid Cap is off-family and not forced into this cap batch.
- Contact sheet: `experiments/cap_real_pipeline_batch_01/CAP_REAL_PIPELINE_CONTACT_X10.png`. QC pack installed as `[FS] RNG Cap Real Pipeline QC`.

## 2026-09-25 — Photo Tailor permission-backed direct code port

- User supplied explicit author permission to adapt/reuse Photo Tailor code and confirmed proof is retained in the repo.
- Fully decompiled the installed PhotoTailor.dll into `prototypes/photo_tailor_permission_port/full_decompile/` (48 source files, ~620K) using ILSpy.
- Confirmed Photo Tailor hat rendering route: `SpriteRenderer.PreviewHat` selects vanilla HatTemplates[`cap`] = index 5, crops a single 20x80 four-facing template, then runs `Recolor(... FourFacingVertical ...)`.
- Confirmed this is why PT directional rendering is coherent: it preserves one fixed four-view alpha/template rather than independently generating each view.
- Direct Python ports now live under `generator/photo_tailor_port.py` and `generator/cap_photo_tailor_pipeline.py`.
- Ported actual algorithms include CanonicalGarmentCanvas facing projection math, HSL shade-ramp generation, field/pattern color projection, canonical motif anchors, nearest-opaque search, SpriteRenderer topology-boundary detection, source-luma shading, and the PreviewHat/Recolor four-facing loop.
- Existing approved HAT_PRODUCTION_GOLDEN_V1 remains untouched after validation correctly detected that globally swapping renderer math would change frozen goldens; PT code is isolated to the new cap path pending human visual approval.
- New direct-code-port QC batch contains 8 real four-view source constructions: Baseball, Snapback, Boys Cap, Backwards Cap, Dad/Vintage, Cap+Headphones, Officer, Paperboy.
- Trucker is intentionally excluded: the available Trucker reference is front-only, and Photo Tailor's compiler can project art but cannot turn Snapback geometry into a true Trucker construction. Do not fake this family again.
- New contact sheet: `experiments/cap_photo_tailor_port_batch_01/CAP_PT_PORT_CONTACT_X10.png`.
- QC pack installed as `[FS] RNG Cap PhotoTailor Port QC`.

## 2026-09-25 — Photo Tailor trucker-hat runtime extension

- Found the prior personal bridge was forcing every detected hat silhouette to `cap`, which invalidated earlier real-Photo-Tailor cap/trucker experiments.
- Added `pt_make_trucker <imagePath>`. It keeps `Category=hat`, sets `Silhouette=trucker_hat`, and preserves Photo Tailor analysis/palette/pattern evidence.
- Extended Photo Tailor `SpriteRenderer.HatTemplates` at runtime by reflection: `trucker_hat` and `trucker` map to vanilla hat sprite index **16**, which Photo Tailor semantic data identifies as **Trucker Hat** (`Mesh in the back to keep your head cool.`).
- This means Photo Tailor now renders real trucker-photo evidence through its normal compiler/projection pipeline using the actual four-view vanilla Trucker Hat construction instead of generic `cap` template #5.
- Existing `pt_make_cap` no longer force-overwrites all hat silhouettes to `cap`; it preserves the analyzer result.
- Bridge rebuilt and deployed successfully. Current running SMAPI session still has the old DLL loaded and must be restarted before `pt_make_trucker` is available.

## 2026-09-25 — Trucker family A/B construction proof

- Registered the user-supplied transparent 80x80 four-view trucker sprite as the trucker construction authority at `authored/source_bases/cap/cap_trucker/source/trucker_4view_master_80.png`.
- Extracted raw 40x40 front/right/left/back quadrants without repainting.
- Built two normalized production candidates from the exact same construction: A32 (`production_32`) and B24 (`production_24`). Production resolution is intentionally NOT locked yet.
- Added `generator/data/trucker_family_contract.json` with hard identity rules: structured solid front panel, forward brim, mesh rear/side, back opening, front-only motif zone, no motifs on mesh/back opening, preserve source alpha.
- Generated a six-design like-for-like A/B QC batch at `experiments/trucker_ab_resolution_qc_01/`. Contact sheet: `TRUCKER_AB_32_VS_24_CONTACT.png`.
- Structural validation: all six A32 variants preserve A32 alpha exactly; all six B24 variants preserve B24 alpha exactly.
- Human visual decision between 32 and 24 remains pending; do not promote either to production before visual QC.

## 2026-09-25 — Both trucker A/B bases registered in generator

- Registered two ACTIVE temporary trucker QC families in the shared generator registries: `trucker_a32_qc` and `trucker_b24_qc`.
- Each family has its own locked source-backed template contract (`generator/data/templates/trucker_a32_qc.json`, `trucker_b24_qc.json`) pointing to the 32x32 or 24x24 four-view production candidate respectively.
- Both use matching trucker taste rules and front-only motif placements; attachments/hardware are disabled during base selection so resolution is the primary variable.
- `generator.catalog_templates.load_template_for_family()` successfully loads and verifies both contracts: A32=(32,32), B24=(24,24), four views each.
- No winner is selected yet. Keep both active until user chooses the base, then collapse to one production `trucker` family.

## 2026-09-25 — Trucker FINAL-look generator A/B

- User clarified the resolution choice must be judged from finished generator output, not template/proof renders.
- Added `generator/trucker_renderer.py`, a finished trucker renderer that preserves locked silhouette cells/back opening but converts all nonzero template alpha to full production opacity, so source mesh no longer looks faded/disappearing.
- Mesh is rendered as visible woven fabric with alternating value treatment; front remains solid; strong border is preserved; trim/colorblock and front-only motifs follow the registered taste policy.
- Added `tools/build_trucker_final_ab_generator.py`. It loads both ACTIVE generator families through `generator.catalog_templates`, validates each recipe through `generator.taste_policy.evaluate_recipe`, then renders the exact same six legal recipes for A32 and B24.
- Output: `experiments/trucker_final_generator_ab_01/TRUCKER_FINAL_GENERATOR_A32_VS_B24.png`.
- Validation: 6 finished variants per base; every nonzero output alpha is 255 for both A32 and B24; locked silhouette cells and back openings are preserved.
- Final base decision remains pending user visual choice.

## 2026-09-25 — Trucker coherent production base rebuild

- Rejected the sparse reference-derived alpha masks as production geometry because they caused disappearing/fading side and back views.
- Added rebuilt coherent trucker production bases at 32px and 24px under `authored/source_bases/cap/cap_trucker/coherent_production_32/` and `coherent_production_24/`.
- New bases keep full opaque hat mass in all four views; mesh is represented as opaque surface texture; only the intentional back opening remains transparent.
- Updated `trucker_a32_qc` and `trucker_b24_qc` template contracts to point to the rebuilt coherent bases and refreshed hashes.
- Regenerated `experiments/trucker_final_generator_ab_01/TRUCKER_FINAL_GENERATOR_A32_VS_B24.png` through the shared generator/taste pipeline.
- Structural gate: every generated front/right/left/back view across both A32 and B24 is a single connected hat silhouette; zero fragmented/blob views.

## 2026-09-25 — Stock Photo Tailor trucker isolation test

- Added `pt_stock_photo` to PhotoTailorPersonalBridge as a harness for Photo Tailor stock Quick Recognition only: `LocalOutfitAnalyzer.Analyze(imagePath)` followed by stock `SpriteRenderer.Render(spec)` with no category hint, silhouette override, template remap, RNG generator, cleanup, or post-processing.
- Downloaded a real 1024x1024 Richardson-style trucker-hat studio photo to `/home/deck/Downloads/photo_tailor_stock_test/real_trucker_hat.jpg`.
- Stock Photo Tailor detected: category=`hat`, silhouette=`cap`, semantic=`black white gray solid standard cap`. It did not identify a distinct trucker silhouette.
- Raw Photo Tailor output: `/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/PhotoTailor/generated/Robin.PhotoTailor_stock_20260926010014_00_hat.png` (20x80).
- Viewing-only nearest-neighbor contact sheet: `experiments/photo_tailor_stock_trucker_01/PHOTO_TAILOR_STOCK_TRUCKER_CONTACT.png`. No RNG generator code touched the output.

## 2026-09-25 — Photo Tailor real UI-equivalent confirmation test

- Added `pt_ui_equivalent`, which reproduces the installed Photo Tailor normal Quick Recognition confirmation path: `Analyze(imagePath)` -> `SpriteRenderer.Preview(outfit)` -> prepared preview -> `RenderPrepared(spec, preview)`. The UI display layer only copies the prepared pixels into GPU textures and does not alter them.
- Tested the same real 1024x1024 trucker-hat photo used in the stock direct-render test.
- UI-equivalent recognition result: category=`hat`, silhouette=`cap`, semantic=`black white gray solid standard cap`.
- UI-equivalent output: `Robin.PhotoTailor_uiequiv_20260926011407_00_hat.png` (20x80).
- Compared against prior direct stock `Render()` output `Robin.PhotoTailor_stock_20260926010014_00_hat.png`. Result: identical size, identical pixel SHA256 (`60e657819e8209dcc84ba61d0319fa287e4b3add763feb6fd9f91bfbb91dc8a3`), zero differing pixels.
- Conclusion: for the same photo and unadjusted Quick Recognition workflow, using the actual in-game preview/confirm path does NOT change the generated hat pixels. Manual crop/precise-recognition edits could still change the analyzed spec and therefore output.

## 2026-09-25 — Clean vanilla Trucker Hat #16 Photo Tailor test

- Confirmed `SpriteRenderer.PreviewHat` normally loads live `Characters/Farmer/hats`, so patched/modded live assets can contaminate Photo Tailor hat geometry.
- Added test-only bridge path `pt_clean_vanilla_trucker` that temporarily serves a copied clean unpacked vanilla `hats.png`, forces analyzer result to `trucker_hat`, maps that silhouette to vanilla hat index 16, renders through Photo Tailor, then restores normal asset behavior.
- Real 1024x1024 trucker photo analyzed as generic `cap`; test forces only the trucker silhouette/template choice.
- Valid clean-template output: `Robin.PhotoTailor_personal_20260926012811_00_hat.png` (20x80).
- Comparison sheet: `experiments/photo_tailor_clean_vanilla_trucker_01/CLEAN_VANILLA16_VS_PT.png` (left clean vanilla #16, right Photo Tailor result). Opened in Gwenview for visual review.
- If Photo Tailor transfer still looks poor, fallback is straightforward: use clean vanilla Trucker Hat #16 as the generator geometry authority and bypass Photo Tailor for trucker rendering.

## 2026-09-25 — Official trucker family promoted to vanilla Stardew #16

- Promoted clean vanilla Stardew Valley Trucker Hat index 16 to the official `trucker` geometry authority.
- Extracted four clean 20x20 cardinal frames to `authored/source_bases/cap/cap_trucker/vanilla16_official/` and registered `generator/data/templates/trucker.json` + `generator/data/taste_policies/trucker.json`.
- Official geometry lock preserves vanilla silhouette and exact alpha bytes, including partial-alpha edge pixels. No resampling or generic normalization is permitted.
- Retired `trucker_a32_qc` and `trucker_b24_qc` from the active registry; their files remain only for historical QC reproducibility.
- Updated `generator/trucker_renderer.py` with an opt-in `preserve_alpha` path so official vanilla geometry is not rewritten.
- Added `tools/build_trucker_vanilla16_batch.py` and built six production-style variants from the official base with Photo Tailor completely bypassed.
- Output: `experiments/trucker_vanilla16_production_01/TRUCKER_VANILLA16_PRODUCTION_CONTACT.png` plus individual front/right/left/back PNGs and metadata.
- Validation: official `trucker` contract loads and verifies; all 24 generated variant frames preserve the vanilla base alpha bytes exactly.

## 2026-09-25 — Trucker Photo-Tailor-integrated hybrid batch

- Kept clean vanilla Stardew Trucker Hat #16 as the official locked geometry authority.
- Added trucker semantic regions to `generator/hat_hybrid_enhancements.py`.
- Built `tools/build_trucker_pt_hybrid_batch.py` using the pipeline: vanilla #16 geometry -> direct Photo Tailor PreviewHat/Recolor Python port -> bounded hybrid rarity/motif layer.
- This batch intentionally excludes stripe, colorblock, contrast-trim, and wrap-trim rules to avoid the long horizontal band artifact seen in the prior trucker/sunhat-style renderer.
- Photo Tailor port is used on all six variants for source-luma shading/projection. Rare/Epic then receive bounded front motif deltas from the hybrid layer; Common/Uncommon remain Photo-Tailor-shaded only.
- Output: `experiments/trucker_pt_hybrid_v2_01/TRUCKER_PT_HYBRID_V2_CONTACT.png` plus per-view PNGs and metadata.
- Validation: all 24 generated frames preserve vanilla #16 alpha bytes exactly; Photo Tailor port reported used on all six variants; no hybrid fallback occurred.

## 2026-09-25 — Trucker PT-hybrid v3 rich styling batch

- Built a richer Photo-Tailor-integrated trucker renderer while keeping vanilla Stardew Trucker Hat #16 as the locked geometry authority.
- Added `generator/trucker_pt_hybrid_renderer.py` with explicit trucker physical regions derived from vanilla #16 pixels: front view is solid crown only; side views separate solid front panel, rear mesh/body, and visor; back separates rear mesh/body from lower closure.
- Photo Tailor renderer shading/value math is applied per semantic region instead of flattening the whole hat into one generic field.
- Restored two-tone contrast, brim contrast, rear mesh weave, front-panel pinstripe/check patterns, and Rare/Epic motifs. Patterns/contrast are constrained to physical regions, not generic full-width horizontal bands.
- Built eight variants with `tools/build_trucker_pt_hybrid_v3_batch.py`: Classic Moss, Stone Blue, Denim Rust, Teal Pinstripe, Coastal Twotone, Crimson Patch, Indigo Emblem, Autumn Check.
- Output: `experiments/trucker_pt_hybrid_v3_01/TRUCKER_PT_HYBRID_V3_CONTACT.png` plus individual cardinal frames and metadata.
- Validation: all 32 generated frames preserve vanilla #16 alpha bytes exactly. Generated views contain multiple RGB values per view (7–16 depending on variant), confirming visible value/shading variation rather than flat single-color fills.

## 2026-09-25 — PixelLab vs Retro Diffusion trucker construction side experiment

- Side experiment only; no production generator/trucker architecture changed.
- Read the installed PixelLab rotation/resize plugin code and current Retro Diffusion style documentation before prompting.
- PixelLab reference-to-8-rotations only supports documented preset canvases such as 32x32+, so generated one 32x32 trucker turnaround with a construction-only prompt (no head/face/person/logo/text/decoration), then selected rotation 0/front, 2/right, 4/back and made 20x20 + 26x26 nearest-neighbor presentation reductions. Raw eight 32px PL rotations are preserved under `experiments/trucker_ai_construction_20_26/pixellab32/`.
- Retro Diffusion 8-direction rotation workflow does not accept 20/26 native direction cells; advanced rotate bottoms out at 32px. Generated native 20px and 26px front constructions, padded each unchanged to 32px, then used RD advanced rotation to create consistent directional sheets. Extracted RD-generated 32px front/right/back views; final requested-size side/back comparison copies are nearest-neighbor presentation reductions while native RD 20/26 fronts are preserved unchanged.
- Final comparison sheet: `experiments/trucker_ai_construction_20_26/TRUCKER_PL_VS_RD_20_26_CONTACT.png` with four rows: PL20, RD20, PL26, RD26 and columns Front/Right/Back.
- This experiment is for human visual selection only; no structural validator result should be treated as aesthetic approval.

## 2026-09-26 — Locked-anchor PixelLab trucker rotation test
- Approved anchor is exactly `experiments/trucker_ai_construction_20_26/pixellab/pl20_right.png` (20x20), matching original PL rotation frame `pl_rot_02.png`.
- PixelLab docs confirm seed `0` is random; the original exact randomized seed was not preserved in our manual generation log/PNG metadata, so it cannot be recovered.
- New controlled test uses the exact approved right-side PNG, padded to 32x32 without scaling, PixelLab Rotate API, side view, east -> south, fixed seed `424242`, image guidance 7.5.
- Raw generated front saved as `experiments/trucker_pl20_anchor_rotation_03/front_seed424242_raw.png`; 20px nearest-neighbor presentation copy and contact sheet are alongside it.
- Human visual approval still required before this front is accepted into any construction template.

## Trucker generator template promotion — 2026-09-27

The approved RD22-front + PL26-side/back trucker construction is now the active `trucker` source-backed generator template.

- 26x26 locked cardinal frames copied to `authored/templates/trucker_rd22_pl26/`.
- Front authority: RD20 rounded front, nearest-neighbor scaled to 22x22 and centered in the 26x26 contract.
- Right/back authority: PL26; Left is an exact horizontal mirror of Right.
- Reviewed component masks are machine-readable and locked for front panel, rear mesh, brim, top button and back closure. All unmasked outline/seam/opening pixels are protected.
- `generator/data/templates/trucker.json` now points to this approved family and links the source transfer library, trucker roll matrix and ESM wear contract.
- New `generator/data/headwear/trucker_roll_matrix.json` defines rarity, motif, material, view-consistency and incompatibility/exclusion behavior.
- New `generator/data/headwear/trucker_wear_contract.json` records the approved per-view ESM fit defaults.
- Generic normalization, resample-to-fit, synthetic mesh and generic full-width bands are explicitly forbidden.
- Validation: template hash/alpha lock PASS; exact mirrored Left PASS; mask opaque/non-overlap PASS; generator-wide taste policy PASS; source-template tests PASS.

This promotion makes the trucker a reusable generator construction contract; it does not declare the previously packaged source-preserving QC sprite to be the final visual product.

## Measured vanilla Stardew outline/shading grammar — 2026-09-27

Studied the unpacked vanilla `Characters/Farmer/hats.png` and `shirts.png` directly and converted the observed style into a reusable experimental generator finish profile.

Evidence:
- 478 vanilla hat direction frames analyzed; 470 had enough local outline/interior pairs for measurement.
- 1,275 vanilla shirt direction frames analyzed.
- Hats: median outer-boundary darkening is ~47.5 luma relative to adjacent interior; median near-black share is only ~26.8%; median outline saturation ~0.60; median hue drift from local interior ~22.5 degrees.
- Shirts: median boundary darkening ~37.7 luma; median near-black share 0%; median outline saturation ~0.48; median hue drift ~16.5 degrees.
- Hats show a strong vertical light bias: top is ~20.5 luma brighter than bottom on the median analyzed frame; there is almost no consistent left/right brightness bias.

Generator rule derived from that evidence:
- outer silhouette defaults to the darkest local semantic/component ramp color, not global RGB black;
- internal seams should use the second-darkest local ramp unless they are deep physical separations;
- near-black is reserved for deep creases, undersides, negative-space borders and very strong separations;
- outline hue stays close to the adjacent component hue (target <=25 degrees when saturation permits);
- finishing may change RGB only, never locked alpha/silhouette;
- top-to-bottom light hierarchy is preferred; no blanket left/right relighting.

Implementation/proof:
- `generator/data/vanilla_sprite_finish_profile.json`
- `generator/vanilla_sprite_finish.py`
- `experiments/vanilla_hat_style_grammar_01/`
- `experiments/trucker_chromatic_outline_ab_01/TRUCKER_CHROMATIC_OUTLINE_AB.png`

This is currently an experimental finish pass, not yet promoted to production. Human visual approval of the A/B is required before applying it generator-wide.

## Trucker front-visor consistency fix — 2026-09-27

Front visor finishing was revised to follow the stronger side-view visor value hierarchy without changing geometry.

- Only front-view brim RGB was changed; Right/Left/Back frames are byte-identical to the prior batch.
- 40 front-view brim pixels per variant changed, bounded to x=7..19 / y=16..20.
- Alpha/silhouette remained exact.
- The two isolated lower tip cells remain opaque for silhouette fidelity but now use the darkest visor shade, so they visually merge into the underside instead of reading as bright stray dots.
- Front visor now uses an explicit upper-plane -> midtone -> underside-dark progression based on the side-view visor treatment rather than source-luminance rank alone.
- `tools/build_trucker_generator_batch_v1.py` now applies this front-only visor finish consistently to every generated trucker variant.

## Trucker front visor vanilla-reference pass — 2026-09-27

Front-view visor shading now explicitly follows the value grammar measured from vanilla Stardew hat #16 while preserving the approved trucker silhouette.

- Front visor only; side/back/left construction remains unchanged.
- Uses chromatic darkest local visor shade at the rim/tips rather than generic black.
- Upper/front plane is lighter, underside is progressively darker, matching vanilla #16's front-brim value hierarchy.
- The two tiny lower tip cells remain structurally present but are darkest-shade pixels, so they read as part of the underside rather than isolated bright dots.
- No alpha/silhouette edits.

## Trucker front visor silhouette fix — 2026-09-27

The front-view visor shape, not just its shading, was revised to follow vanilla Stardew hat #16 brim geometry more closely.

- Front crown/body geometry is preserved.
- Front visor now uses a compact 3-row silhouette: two equal-width upper visor rows followed by an inset lower row, matching vanilla #16's front-brim shape grammar.
- Removed the prior extra lower visor rows/tip protrusions that made the front brim look boxy and disconnected.
- Right/Left/Back geometry is unchanged.
- Front component mask and locked hashes were updated to the new approved geometry.
- Generator batch regenerated successfully with 24 frames and source-template validation passing.

## 2026-09-27 — ConstructionTemplatePrinter trucker-only proof

- Reviewed the decompiled Photo Tailor source. Its hat path cannot print construction: 5 SigLIP hat labels map to hard-coded vanilla hats (`cap`→#5, `hat`→#4), the photo supplies colour only, `FillCanonicalHat` is one trapezoid, and side/back are re-projections of the front. Review/plan: `~/.claude/plans/pasted-content-id-a8f1-i-want-parsed-hearth.md`.
- Built isolated `prototypes/construction_printer/` (see README). Photo → mask → PT SigLIP (1:1 port) → family gate → measure → clamped integer deltas → print on the approved `authored/templates/trucker_rd22_pl26` master + component masks → validate → neutral 4-view + region masks + JSON.
- Proven: zero delta reproduces the master exactly. All 125 legal parameter combos resolve to contract-valid templates (5 via backoff). The 5 accepted truckers (plus 1 forced) print coherent, distinct 4-view templates whose profile order matches the photos. None of the 5 negatives is accepted.
- Not yet proven: in-game worn QC (game was not running); visor-length variation (no true side trucker photo); panel split from anything but one photo; calibration on held-out photos.
- Resolution rule recorded in `families/trucker.json`: 20–32 per facing, native 26, grow only on overflow, never resample.
- Output: `experiments/construction_printer_trucker_01/CONSTRUCTION_PRINTER_TRUCKER_COMPARE_X8.png` + contact sheet + per-photo dirs.
- Next test: neutral templates in a throwaway FS pack → `tools/qc.py worn`; add true side-view trucker photos to exercise visor/panel.

## Vanilla-only source-backed generator control — 2026-09-27

Created a fully isolated side experiment to answer a narrow question: if the generator receives only known-good vanilla Stardew art as its source corpus, can the current source-backed architecture produce coherent variation without Photo Tailor, AI geometry, or source-quality ambiguity?

Experiment:
- `tools/experiment_vanilla_source_random_batch.py`
- output: `experiments/vanilla_source_only_random_batch_01/`
- contact: `VANILLA_ONLY_RANDOM_BATCH_CONTACT.png`
- deterministic seed: `260927`

Source preparation intentionally mirrors the production source-backed philosophy rather than blindly recoloring a sheet:
1. exact 4-view extraction from unpacked vanilla `hats.png` / `shirts.png`;
2. alpha geometry locked and hashed per view;
3. source-relative 3-group palette deconstruction (`body`, `trim`, `accent`);
4. independent shade ladder preserved inside each source group;
5. outer-boundary vs interior cells derived;
6. existing authored generator palette ramps applied by group;
7. existing material-treatment rules applied only to interior body cells;
8. alpha must hash-identical before/after every generated view.

The test randomly selected 6 usable hats and 6 usable shirts from validated four-view pools (115 hats / 329 shirts). All 48 generated views preserved exact source alpha geometry. Visual contact confirms the generator can produce coherent Stardew-native variation when source construction is already authoritative. This is a CONTROL, not production promotion: no template/taste registries were changed, no motif/attachment operations were attempted without semantic zones, and no Photo Tailor path was involved.

Next optional A/B: run the exact same vanilla inputs through PT-assisted semantic/palette deconstruction while keeping vanilla geometry authoritative, then compare whether PT adds useful region/material evidence or degrades the clean source-backed baseline.

## Trucker front-visor AI reference experiment — 2026-09-27

User clarified the printer's side views are acceptable; the weak visual is specifically the **front-view visor**. Created an isolated reference experiment at `experiments/trucker_reference_ai_compare_01/` to give the construction printer clearer front-brim geometry evidence without changing the approved trucker source template.

- PixelLab Pro Flash: 4 native 32x32 front-view trucker references, with prompts varying compact/short/medium/broad visor width, taper, lower-edge curvature and crown-to-visor join. Batch: `pixellab/PIXELLAB_TRUCKER_FRONT_BATCH_X10.png`.
- Retro Diffusion: 4 native 32x32 front-view references using `rd_mini__fast_low_res`; total tool-reported generation cost US$0.068. Batch: `retro_diffusion/RETRO_DIFFUSION_TRUCKER_FRONT_BATCH_X10.png`.
- Combined sheet: `TRUCKER_FRONT_AI_REFERENCE_COMPARE_X8.png`.
- Claude-facing geometry shortlist: `CLAUDE_FRONT_VISOR_SHORTLIST_X8.png` (PL02, PL03, PL04, RD01, RD04).
- Sprite Fusion retry succeeded after credits became available: 12 native 32x32 front-view references were generated from the front-focused request. Batch: `spritefusion/SPRITE_FUSION_TRUCKER_FRONT_BATCH_X8.png`; status/request details are in `spritefusion/status.json` / `events.json`.
- New representative all-three-tools sheet: `TRUCKER_FRONT_THREE_TOOL_COMPARE_X7.png`.
- Updated Claude shortlist now explicitly targets a **subtle straight-on visor**: improve taper/curve/join without forcing forward projection, because excessive visible visor depth raises the apparent camera angle.

Scope rule: these images are geometry references only. The existing approved trucker family remains construction/style authority, and this experiment should modify only the problematic front visor behavior unless a later QC explicitly reopens side/back geometry.

## Trucker front visor SF0+SF1 hybrid study — 2026-09-27

Created `experiments/trucker_front_hybrid_0_1_01/` after user clarified the desired front visor should land between Sprite Fusion hats 0 and 1: closer to SF1's shallow Stardew-like curve, but with slightly more body/fullness from SF0 and without extra projection that would imply a higher camera angle. A targeted edit returned only two oddly trimmed outputs, so a second `style-reference` pass used SF0+SF1 together and produced nine native 32x32 candidates H0-H8. Main sheets: `TRUCKER_FRONT_HYBRID_0_1_BATCH_X8.png` and `TRUCKER_FRONT_HYBRID_0_1_VISOR_CROP_X12.png`. This is reference/QC only; the construction printer has not been modified from this experiment yet.

## 2026-09-27 — Trucker front-visor revision A/B/C (experimental)

- Adapted the approved trucker front visor toward the SF0/SF1 hybrids (H4 primary, H1, H5, H3, H7). Only front rows 14–18 change; everything else, including wear anchor and lowest row, is identical. A = H4 arch (recommended), B = fuller H1/H7, C = subtle H3/H5.
- Output + notes: `experiments/trucker_front_visor_revision_01/` (README, 4 sheets, `rev_*/` frames + masks). Script: `prototypes/construction_printer/visor_revisions.py`.
- Proven: silhouette checks, construction-printer compatibility on all three. Not proven: in-game worn read. Not promoted.
- Next test: start game → FS/ESM test pack with rev A/B/C → `tools/qc.py worn`.

## 2026-09-27 — Trucker pooled construction fit from AI references (experimental)

- Ran the construction-printer process on the AI reference pool plus the hybrid preference set, replacing photos. Added the `visor_shape` family parameter (current/A/B/C/D, where D = PL02 grammar) and a sprite measurement path zeroed on the family's own masks.
- Candidates: P1 PL02-led (crown −1, panel +2, visor B); P2 preference pool = P3 whole pool (crown 0, panel +2, visor A). All 4-view, contract-valid, anchor unchanged.
- Output: `experiments/construction_printer_trucker_pool_02/` (README, sheets, POOL_FIT.json). Not promoted; worn QC pending.

## Stardew-only remix v3 — distinct piece / same vanilla construction — 2026-09-27

Reworked the failed vanilla-only regression set instead of selecting easier sources. The test reuses the exact 6 hats and 6 shirts from `vanilla_source_only_random_batch_01`, where only hat 82 and some shirts had looked convincing. New isolated builder: `tools/experiment_vanilla_source_variants_v3.py`; output: `experiments/vanilla_source_only_random_batch_02_distinct/`.

The v2 failure mode (forcing every source into guessed body/trim/accent buckets and rebuilding its shade ladder) is bypassed. V3 treats the vanilla sprite itself as art authority: exact alpha/pixel coordinates are locked; extreme-dark construction colors are protected; source RGB identities map consistently across all four views; source color families may move toward curated palette chroma but each original color remains injective; source luminance is retained within <=2.25; no shade quantization, procedural texture, geometry generation, motif, or resampling is allowed.

A new novelty gate enforces the user's actual Stardew-only goal: outputs must be a meaningfully different wardrobe piece, not the identical source or a near-duplicate. A candidate must change >=40% of opaque pixels with average RGB distance >=18. The builder evaluates the existing approved palette library and rejects palettes that do not clear that gate; two visually distinct passing colorways are selected per source, with variant-to-variant diversity preferred.

Result: all 12 original regression sources produced two passing variants each (24 variants total), while exact source alpha/construction and shade topology remain intact. Contact sheets: `STARDEW_ONLY_HAT_REMIX_V3_CONTACT.png`, `STARDEW_ONLY_SHIRT_REMIX_V3_CONTACT.png`, and combined `STARDEW_ONLY_REMIX_V3_CONTACT.png`. This is visual-QC evidence only and is not promoted into production/source-pool config yet. Material/pattern/motif variation remains intentionally deferred until a source has safe semantic masks; this pass proves distinct source-respecting colorway variation first.

## AI-reference trucker construction printer — 2026-09-27 (CANDIDATE, not worn-QC'd)

Fresh, isolated experiment; ignores ALL earlier trucker work (old `prototypes/construction_printer/`, `trucker_rd22_pl26`, photos, pool fits, visor revisions, preference weights) by user instruction.

- Code: `prototypes/construction_printer_ai_trucker/` (README there). Output: `experiments/construction_printer_ai_trucker_01/`.
- Evidence: AI pools `trucker_reference_ai_compare_01/` + `trucker_front_hybrid_0_1_01/style_reference/` only; sf_02/sf_03 rejected by user.
- Recognition: 21/27 pool identified, 0/10 negatives accepted. Button gate added after a boater false positive (not independently validated).
- Candidates C0 consensus (19/21 refs share it), C1 pl02, C2 pl04 — 20x20 native, W=12 crown, all validation checks pass.
- Throwaway FS pack `RNG-AITrucker-QC-01` (tag AITRK) installed to live Mods while the game was closed.
- Not yet proven: worn look in game. Next test: `python3 tools/qc.py worn --pack-dir "<Mods>/RNG-AITrucker-QC-01" --name AITRK` after launching + loading a save.
- Do not: promote anything, or feed old trucker geometry into this experiment.

## Stardew-only v4 — source-derived safe material regions — 2026-09-28

Built the next isolated layer on top of the approved-direction v3 colorway proof: `tools/experiment_vanilla_material_regions_v4.py` with outputs under `experiments/vanilla_source_only_material_regions_01/`. The same 12-source regression set is used again. V4 derives a `material_safe` mask directly from each vanilla sprite: opaque interior only, very-dark construction pixels excluded, isolated/detail-like cells excluded, and treatment marks may not be orthogonally adjacent. Exact vanilla alpha/geometry remains locked; the v3 source-respecting colorway remains the base.

Material treatment is capacity-aware. Large-enough masks receive a conservative `knit`, `plaid`, or `wool` proof; low-capacity items skip instead of forcing decoration. 11/12 regression sources admitted at least one safe treatment; shirt #535 correctly returned `material=none` with zero safe interior cells. This validates the capability boundary rather than forcing universal coverage. Main sheets: `STARDEW_ONLY_V4_HAT_MATERIAL_CONTACT.png`, `STARDEW_ONLY_V4_SHIRT_MATERIAL_CONTACT.png`, and combined `STARDEW_ONLY_V4_MATERIAL_CONTACT.png`. Treatment strength/art direction remains visual-QC pending; this is not production promotion yet.

## Stardew-only v5 — source-backed region styling — 2026-09-28

Added the next isolated Stardew-only generator layer: `tools/experiment_vanilla_region_styling_v5.py`, output under `experiments/vanilla_source_only_region_styling_01/`. The same 6 hats + 6 shirts regression set is reused again, and v4 material renders are the styling base.

V5 moves beyond whole-item recolor/material by deriving two generic source-geometry styling zones per garment. It intentionally does **not** guess fashion semantics from source brightness/color. Hats are split into source-safe upper vs lower construction zones; shirts into source-safe central vs side geometry zones. Both are restricted to the already-proven safe interior: silhouette edges, very-dark construction pixels, and isolated/detail-like cells remain protected. A zone is usable only when it has >=10 safe cells and appears in at least two views. Low-capacity garments skip rather than invent regions; shirt #535 correctly has no valid zones and receives no regional treatment.

Region-specific color treatment uses an alternate approved palette lane while retaining each treated pixel's local luminance, so vanilla shade topology/rounding remains readable. Exact alpha/geometry is hash-locked. All 11 region-capable regression sources produced two region-style proofs; one low-capacity source skipped both safely. Contact sheets: `STARDEW_ONLY_V5_HAT_REGION_CONTACT.png` and `STARDEW_ONLY_V5_SHIRT_REGION_CONTACT.png`.

This validates **region-specific styling capability**, not final semantic labelling or final art direction. `primary`/`secondary` remain generic until source/human review can safely promote them to names such as crown, brim/band, torso, sleeve, collar, cuff, etc. Motifs/components and authored construction swaps remain later layers. Nothing from v5 is promoted into the production content pool yet.

## Stardew-only v6 — safe localized motifs / wrap trims — 2026-09-28

Added `tools/experiment_vanilla_motif_components_v6.py`, output under `experiments/vanilla_source_only_motif_components_01/`, reusing the same 6 hats + 6 shirts regression set and the v5 region-styled outputs as the base.

V6 adds two capacity-aware decoration channels without changing vanilla geometry: (1) a **localized accent** confined to the front view only, because localized motifs must not be blindly copied to every direction; and (2) a **wrap trim** that is allowed only when source-safe lower/edge cells exist coherently in at least three views. Both channels recolor existing source-safe pixels only; no alpha is added, no silhouette changes, no resampling, and no external/mod-author/AI geometry enters the Stardew-only pool.

Results: 11/12 sources admitted a localized accent; hat 52 and hat 79 correctly rejected wrap trim while the remaining region-capable items admitted one; shirt #535 again rejected both channels due to zero safe capacity. Hat localized marks use only 2-3 logical pixels; shirts use 1-2 pixels. This confirms that vanilla-scale content has a real capacity ceiling and the generator should skip rather than overdecorate.

Contact sheets: `STARDEW_ONLY_V6_HAT_MOTIF_COMPONENT_CONTACT.png` and `STARDEW_ONLY_V6_SHIRT_MOTIF_COMPONENT_CONTACT.png`. These prove **safe localized motif + wrap-trim capability**, not large attached components or silhouette-changing add-ons. Larger components should only come later from explicitly compatible vanilla donor constructions or approved authored construction variants. Nothing from v6 is promoted into production yet.

## Stardew-only v7 — full vanilla capability audit + reviewed donor grammar — 2026-09-28

Added `tools/experiment_vanilla_capability_audit_v7.py` and isolated outputs under `experiments/vanilla_source_only_capability_audit_01/`. V7 scans the full vanilla Farmer clothing corpus: 132 hat slots / 122 non-empty hats and 608 shirt slots / 339 non-empty shirt fronts. The broad machine classifier is intentionally treated as a discovery aid only because visual review showed false positives when shading/panels resemble motifs.

A second conservative review layer now defines the usable seed vocabulary in `vanilla_donor_vocabulary_reviewed.json`. Shirt grammar seeds are grouped as `compact_graphic`, `horizontal_stripe_or_band`, `checker_or_plaid`, and `placket_or_buttons`. These are **grammar evidence only**, not approved literal pixel-transfer parts. The reviewed contact is `reviewed_donor_seed_contact_x18.png`. Ambiguous shirt #531 was removed from the reviewed placket/button seeds after visual QC.

The full hat audit changed the design rule: vanilla hats should **not** receive a universal motif axis. Their visual variety is dominated more by whole construction/components, bands, bows, object-shaped silhouettes, and other family-specific geometry. Hats therefore move to the later compatible vanilla-donor construction/component pass rather than generic motif transfer.

V7 remains fully isolated from the production generator and has no rarity logic. The next proof is V8: generate a small mixed vanilla-only batch where each target garment may use only capabilities its own source/capacity supports, guided by the reviewed vanilla grammar seeds rather than generic motifs.

## Stardew-only v8 — mixed capability batch — 2026-09-28

Added `tools/experiment_vanilla_mixed_batch_v8.py` and isolated output under `experiments/vanilla_source_only_mixed_batch_v8_01/`. V8 combines the prior safe vanilla-only layers with the conservative reviewed v7 grammar. No rarity logic is used and nothing is promoted into the production generator.

The first render was rejected internally because all six shirt targets selected the stripe/band branch, which defeated the purpose of a mixed proof. The retained second batch deliberately covers different target-supported vanilla grammars: shirt #225 = horizontal stripe/band; #228 = placket/buttons; #239 = compact graphic; #572 = checker/plaid; #584 = region/material-only control; #535 = low-capacity fallback with no graphic grammar. Grammar categories are accepted only when the target source both appears in the reviewed seed set and exposes the corresponding v7 capability evidence.

The four hats (#52, #66, #79, #98) deliberately skip generic motifs. They use only already-proven source-safe colorway / region-style / wrap-trim axes when supported. This follows the v7 finding that vanilla hat variety is primarily construction/component-driven rather than a universal motif system.

All 10 outputs preserve exact source alpha/geometry. Contact sheets: `STARDEW_ONLY_V8_HAT_MIXED_CONTACT.png` and `STARDEW_ONLY_V8_SHIRT_MIXED_CONTACT.png`. This proves that a vanilla-only content path can select different decoration/styling capabilities per garment instead of applying one universal transformation. The next remaining question is whether compatible vanilla donor constructions/components can safely create stronger hat and clothing variation without leaving Stardew-native design language.

## Stardew-only v8 contact-sheet overlap fix — 2026-09-28

User visually flagged hat #79 and #98 generated rows as failures and questioned hat #66. Inspection of the individual 20x20 output PNGs showed #79/#98 were not broken: the V8 hat contact-sheet renderer placed the SOURCE 4-view group directly against the VARIANT group with no inter-group spacing, so the source Back frame overlapped the variant Front frame and made the generated hats look like two sprites mashed together. `tools/experiment_vanilla_mixed_batch_v8.py` now computes group width dynamically and inserts a dedicated gap between SOURCE and VARIANT groups. The regenerated `STARDEW_ONLY_V8_HAT_MIXED_CONTACT.png` shows clean, separate frames.

Hat labels now include vanilla names when available. Hat #66 is confirmed from vanilla `Data/hats.json` as `Garbage Hat`; its round trash-can-lid / donut-like read is source-authentic, not a generator defect. Hat #79 is `Small Cap`. No generated hat geometry was changed by this correction; this was a QC presentation bug only.

## Stardew-only v8b — hat semantic-capacity correction — 2026-09-29

User clarified that the visually bad part of the earlier hat batch was the added line treatment itself, not the contact-sheet overlap. Updated rule: **technical pixel capacity is not enough; a decoration must land on a semantically sensible hat region**. Small Cap (#79) is now explicitly recolor-only with no added line. Sprite hat #98 was regenerated with a small band on the crown while leaving the brim untouched.

Added isolated experiment `tools/experiment_vanilla_hat_cleanup_v8b.py` with outputs under `experiments/vanilla_source_only_hat_cleanup_v8b_01/`. `V8B_FIX_CONTACT.png` contains the user-flagged corrections. `V8B_NEW_BATCH_CONTACT.png` tests four different vanilla hats under stricter capacity rules: Hunter's Cap (#15), Trucker Hat (#16), and Sailor's Cap (#17) are recolor-only; Fishing Hat (#55) receives a small crown band because its construction has enough readable crown area above a distinct brim.

Current direction: for vanilla hats, **recolor/material treatment is the default capability**. Extra bands/structural accents should be opt-in only for hats with obvious readable space and a semantically appropriate crown/body zone. Generic lower-edge/wrap-trim inference is no longer considered sufficient for hat decoration. This experiment remains isolated; no production generator integration or rarity logic yet.

## Production source-mode integration — VanillaOnly / ModAuthorOnly / Everything — 2026-09-29

The Stardew-only research path is no longer a separate generator architecture. Its validated rules have been promoted into the real production generator through a provenance-aware source router.

New production policy: `generator/data/content_source_policy.json` defines three player/source modes: `VanillaOnly` => `VANILLA`; `ModAuthorOnly` => `MOD_AUTHOR`; `Everything` => `VANILLA + MOD_AUTHOR + CONSTRUCTION_PRINTER`. Filtering happens before recipe selection/rendering so provenance cannot change after selection. `CONSTRUCTION_PRINTER` is represented as a legal Everything source class but currently has zero production-promoted entries; prototype printer content cannot leak into production.

`generator/production_router.py` now exposes one production pool/router. Existing mod-author hats remain on the unchanged authoritative `generator/source_respecting_hat_production.py` path (`GOLDEN_SOURCE_RESPECTING_HYBRID_V1`). Vanilla items route through `generator/vanilla_source_production.py` under `STARDEW_SOURCE_PIXELS_FIRST`, with exact source alpha/geometry locked and source luminance topology preserved.

Initial promoted vanilla contracts live in `generator/data/vanilla_source_contracts.json`: 8 hats + 8 shirts. Hat rules reflect the research result: recolor is default; generic motifs/wrap trim are forbidden; crown bands are opt-in only for explicitly approved medium-capacity hats (#55 and sprite #98). Shirt contracts may additionally allow reviewed vanilla grammar such as stripe/band, placket/buttons, compact graphic, checker/plaid, or region style. No rarity logic was added to the vanilla contract in this milestone.

The first real-generator VanillaOnly proof is under `experiments/production_router_vanilla_only_01/`, with `PRODUCTION_VANILLA_ONLY_HATS.png` and `PRODUCTION_VANILLA_ONLY_SHIRTS.png`. Routing audit passes: VanillaOnly = 8 hats + 8 shirts, all provenance `VANILLA`; ModAuthorOnly = 20 existing golden hats, all `MOD_AUTHOR`; Everything = 28 hats + 8 shirts. A ModAuthorOnly smoke render still reports `GOLDEN_SOURCE_RESPECTING_HYBRID_V1`.

Enhanced Sewing Machine now has player config plumbing via `ModConfig.ContentSourceMode` (`Everything` default; `VanillaOnly`; `ModAuthorOnly`). `GarmentTemplateMetadata` now carries `ContentSource`; tailoring selection filters registered garments by the selected mode. Explicit `ContentSource` wins; legacy compiled garments may infer provenance from `GeneratorId` for backward compatibility. Unknown/unannotated garments are available in Everything but not restrictive modes. This adds the config/filter boundary without introducing a dependency or a new UI requirement.

Validation: `tools/validate_content_source_routing.py` passes; existing source-respecting hat production validator passes all 20 families / 147 approved pairs / 80 rarity candidates; generator-wide taste policy passes; catalog template promotion validator passes (47 promoted / 6 deferred); EnhancedSewingMachine Release build succeeds with 0 warnings / 0 errors and deploys normally to the Steam Deck Mods folder.
