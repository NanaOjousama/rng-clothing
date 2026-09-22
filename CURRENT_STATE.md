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
