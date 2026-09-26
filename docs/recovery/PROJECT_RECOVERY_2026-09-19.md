# RNG Clothing / Enhanced Sewing Machine — Project Recovery Map
Date: 2026-09-19
Recovery basis: repository files, Git history, generated traces, test packs, live-QC records in CURRENT_STATE.md, and fresh verification runs. Chat memory is not authoritative.

## 1. Recovery rule
This document is the continuity anchor until all recovered implementation is split into clean commits.

For every subsystem:
1. inspect Git/history and current files;
2. classify work as PROVEN, VERIFIED-UNCOMMITTED, EXPERIMENTAL, REJECTED, or UNKNOWN;
3. run the subsystem verification;
4. checkpoint before edits;
5. commit a coherent unit and record the commit hash here.

No commit hash means the work is not considered safely preserved in Git.

## 2. Last clean committed generator baseline
Current branch: main
Recovery-time HEAD: bf4c0a5a41ba097a7d5f16e516fc79687cd33654

Committed milestone chain:
- 57b0410 — Source-Backed V2: source pixels canonical beside legacy path.
- 87d72e5 — source-backed Baseball + Snapback foundations.
- 024441b — Baseball decorated variants approved after live QC.
- bf4c0a5 — Snapback V1 decorated variants approved after live QC.

This is the last clean Git-backed generator state before the large uncommitted ESM/beanie/Soft-Cap work.

## 3. Round Trip — recovered exactly
Status: PROVEN TOOLING / NOT LOST.

Builder:
- tools/build_roundtrip_pack.py

Output:
- test-packs/fashionsense/RNG-RoundTrip

Purpose:
- A = source author's original Fashion Sense files copied byte-for-byte.
- B = same appearance ingested and re-exported through our round-trip pipeline.
- C = our generated Soft Cap comparison.

Subject used by the current builder:
- asset: Beanie
- pack: More Accessories and Stuff
- author: plurffle

The builder uses v5/source/roundtrip.py.

Recovered report facts:
- original A source files are byte-identical to their copied test-pack files;
- B carries DrawOrderOverride, HeadPosition, HatSize, UniformAnimation, and Left Flipped;
- property comparison reports zero differences;
- source Beanie uses 16x16 frames and HeadPosition (-2,-3);
- original source has Front, Right, Back authored; Left reuses/mirrors Right.

This mechanism must not be reinvented from memory.

## 4. Beanie work — recovered
### 4.1 Source-backed Beanie V1
Status: VERIFIED-UNCOMMITTED.

Primary source-backed constructions:
- beanie_cuffed
  - source: generator content/Rural Outfitters/Rural Outfitters/Hats/Beanie
  - attribution: billi — Rural Outfitters, Beanie
- beanie_slouch
  - source-backed alternate construction documented by the current ingest system.

Key files:
- tools/ingest_source_backed.py
- v5/source_backed.py
- tools/build_beanie_source_backed_pack.py
- v5/tests/test_source_beanie_family.py
- authored/source_backed/beanie_cuffed/
- authored/source_backed/beanie_slouch/
- source_catalog/BEANIE_V1_SELECTION.md
- test-packs/fashionsense/RNG-Beanie-SourceBacked-V1/

Fresh recovery verification:
- source-backed beanie family: 4/4 tests PASS.

### 4.2 RuralBeanie V2 generated batch
Status: EXISTING GENERATED PROOF / IMPORTANT RECOVERY EVIDENCE.

Installed/live trace identifies:
- base: rural_beanie
- source control entry: Beanie (source)
- generated entries such as RuralBeanie DenimBlue, EarthMoss, AutumnKnit, etc.
- all generated variants share geometry hash:
  ce1d717b2bae001e39cfb9f518a7165daf9238a90eb310b7fe841d0532e931d8

This proves a wearable beanie geometry had already been promoted into generator output before the failed BEANIE8 experiment.

### 4.3 BEANIE8_QC
Status: REJECTED EXPERIMENT.

The uploaded 96x96 8-direction brown beanie was incorrectly treated as directly wearable directional art. It contains visible empty-hat/interior geometry and produced a bad worn result. Left/right mapping was also initially reversed.

BEANIE8_QC is not an authoritative beanie construction and must not replace the recovered source-backed/RuralBeanie path.

### 4.4 V4BEANIE
Status: DEV QC ONLY.

V4BEANIE is an ESM 32x32 garment-runtime test asset. It proved use of the already-solved runtime contract; it is not the canonical beanie generator construction.

## 5. Enhanced Sewing Machine (ESM) — recovered
Status: VERIFIED-UNCOMMITTED IMPLEMENTATION.

Authority document:
- docs/enhanced_sewing_machine/ESM_MASTER_CHECKPOINT.md

Core recovered architecture:
- custom SMAPI/Harmony garment runtime; Fashion Sense is not a runtime dependency;
- real Stardew Hat carrier (H)RNGClothing.ESM.GeneratedHat;
- per-item persisted render snapshot in item modData;
- custom worn renderer;
- offline generator -> immutable PNG/JSON compiler;
- deterministic Textile + Inspiration + sewing seed selection;
- additive Enhanced shell around vanilla TailoringMenu;
- fitting controls FitOffsetX, FitOffsetY, FitScale;
- controller/Steam Deck and i18n requirements;
- fail-open/vanilla-preserving behavior.

Already-proven 32x32 contract:
- 32x32 source art remains 32x32 on disk;
- physical worn size is controlled independently through RenderScale;
- Variable Hat Size Lab proved 16/20/24/32 logical hats.

Fresh recovery verification:
- Release build: PASS, 0 warnings, 0 errors.
- C# regression tests: 23/23 PASS.
- garment definitions: 20/20 valid.
- tailoring bias validator: PASS.
- generator bridge: 6/8 exact.
  - only Soft Cap seeds 1000 and 1007 drift;
  - Knit, Wide-Brim, Felt fixtures remain exact.

ESM implementation is currently not safely Git-backed as a coherent committed milestone. Recovery must commit it in scoped pieces after removing/isolating rejected QC noise.

## 6. Current Soft Cap drift — identified, not mysterious
Status: EXPERIMENTAL / UNRECONCILED.

Fresh legacy verification:
- 1996 historical renders checked.
- 6 moved.
- all 6 moved entries are soft_cap.

Current working-tree changes explain this:
- authored/bases/soft_cap/base.json adds new crown_top, side, and band placement zones;
- authored/families.json adds an expanded soft_cap family;
- several decals were newly allowed to fit soft_cap:
  band_braided, band_plain, band_striped, bow_knot, crown_button, flower_daisy, pom_small.

Consequences:
- legacy guard reports 6/1996 moved;
- beret validator is 88/89 only because it includes the same legacy baseline guard;
- ESM bridge old Soft Cap fixtures 1000/1007 regenerate to new digests/IDs.

Do NOT update legacy fixtures or bridge fixtures merely to make tests green until this Soft Cap expansion is intentionally reviewed and accepted or discarded.

## 7. Fresh recovery verification matrix
PASS:
- ESM build: 0 warnings / 0 errors
- ESM tests: 23/23
- ESM garment validator: 20/20
- ESM tailoring biases
- source-backed beanie family: 4/4
- source-backed caps: 5/5
- Baseball decoration: 15/15
- Snapback decoration: 21/21

EXPECTED / IDENTIFIED DRIFT:
- ESM generator bridge: 6/8 exact; only two Soft Cap fixtures drift.
- legacy render guard: 1996 checked, 6 moved; every moved render is Soft Cap.
- beret validator: 88/89; only failure is the shared legacy-render guard.

## 8. Recovered project boundaries
Generator:
The generator/source-backed architecture is separate from ESM runtime.
Fashion Sense test packs are QC/export surfaces, not the final runtime dependency.

ESM:
ESM consumes compiled generator outputs and owns runtime garment identity, rendering, fitting, and enhanced tailoring.

Round Trip:
Round Trip is an ingestion/export fidelity test. It is not the ESM runtime and not a new generator family.

These must not be conflated again.

## 9. Remote-work rule
The Steam Deck is remotely connected during assisted development.

The assistant should perform repo inspection, file edits, builds, validators, installs, and safe QC-bridge actions directly when possible. The user should only be asked to do something when it genuinely requires visual/game-UI judgment or physical interaction unavailable through the remote/QC tools.

Do not ask the user to run shell commands that can be run remotely.

## 10. Recovery snapshots
Project recovery snapshot:
- archive/project-recovery/20260919-185911/
- active project-state SHA-256:
  e79c3c046cbb45782e986511e26419e13a96d164bc1440030f4953491c2891f5

Fresh ESM checkpoint:
- archive/esm-checkpoints/ESM_20260919-185912.tar.gz
- SHA-256:
  ac63e025780de880e00dbf85a73d8729a06302943bc31b8415b23695135e02f8

## 10b. Recovery commits created
- Recovery authority + ESM continuity safeguards: 9e3f0ea588bbc96dd1169c5bbbf7b35dc7234501
- Enhanced Sewing Machine runtime + tailoring pipeline: d1d5a8dde3b041e1e97a854527827883f543e080
- Source-backed Beanie V1 constructions: 1ef67fa745a56356c73f34e7cb1e1b97e3e8b7a8

These hashes are the recovered Git anchors.

Additional recovered Git anchors:
- Safe ESM garment-equip QC action: fa81e9d0f40186c11ea7e2316facd8bf7302325c
- Deterministic source-backed cap-family compositor: f61ecac791d5b0867af11fe4efe07ae0f9b9c0f2
- Source corpus/catalog repair: 7e214b7775909afc38f00faac5c58e6854b08649
- Recovered CURRENT_STATE authority: 8a3cf7e79547d8a59bfc63bc2ab4f22ca95b6b4a
- Source-authoritative 26x26 trucker trace, user-approved component masks,
  and isolated Photo Tailor advisory integration:
  782cd855696135d70a7f756e4807dde0d43b0a07

## 11. Recovery order
1. Commit this recovery authority + project safeguards.
2. Reconstruct and commit ESM core/runtime/tests/docs as a coherent milestone, excluding rejected BEANIE8 as an authoritative construction.
3. Reconstruct and commit source-backed Beanie V1 work.
4. Review the uncommitted Soft Cap expansion separately:
   - either accept it and deliberately regenerate baselines/bridge fixtures after live QC;
   - or discard/rework it without touching the known-good committed generator baseline.
5. Resume feature development only after steps 1-4 make the working state understandable again.

## 12. Continuity requirement going forward
Every accepted live milestone must immediately produce:
- updated authoritative status;
- verification result;
- scoped Git commit;
- commit hash recorded in the authority document.

No multi-day accepted milestone should remain only in chat or an uncommitted working tree.


## Accepted post-recovery milestone — directional fitting
Accepted live 2026-09-19.

Commits:
- 9f0a79cdb2cf860db4bef8d487805a2bb18d63cd
- c85c75c1a50f3a37e4755c512bfcc897fe702940
- 23352273b6add2f263a5e1fe829d41ea11181e6d

Result:
- Front / Right / Left / Back X/Y adjustments are independent.
- Scale is global.
- The fitting preview now reflects the selected direction's live offsets.
- Build 0 warnings / 0 errors; tests 26/26 PASS.
- User accepted the live behavior.


## Post-recovery production milestone — ESM Beanie V1
The accepted RuralBeanie EarthMoss source-backed construction was promoted from temporary QC registration to production as `beanie.v1.rural.earth-moss`.

The production definition preserves the accepted 20x20 four-direction source-backed geometry and RNG-RuralBeanie-V2 lineage. Personal directional fitting remains instance-local rather than being baked into the production asset.

Verification: garment definitions 20/20, ESM build 0 warnings / 0 errors, ESM tests 26/26, tailoring bias PASS, generator bridge 8/8 exact, source-beanie family 4/4.
