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
