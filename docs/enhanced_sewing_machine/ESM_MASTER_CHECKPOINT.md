# Enhanced Sewing Machine — MASTER CHECKPOINT

Last reconstructed: 2026-09-19
Project root: `/run/media/deck/USD00/RNG_clothing`
ESM source: `mods/EnhancedSewingMachine`
Tests: `mods/EnhancedSewingMachine.Tests`

## Why this file exists

This is the authoritative recovery/source-of-truth document for ESM. Do not rely on chat memory for ESM architecture or status. Before changing ESM, read this file, inspect current code/tests, and create a checkpoint with `tools/checkpoint_esm.sh`.

ESM is the custom Stardew/SMAPI garment runtime and enhanced sewing-machine path. Fashion Sense is not the runtime dependency for this system. Do not divert an ESM task into Fashion Sense unless the user explicitly asks for a Fashion Sense proof/export.

## Confirmed history reconstructed from prior work

1. Initial fitting/sewing prototype established a C# fitting model, catalogue/store, sewing-machine hook, save/load reapply, controller-aware menu behavior, and whole-pixel fitting. Half-pixel placement was found unreliable.
2. Garment Runtime Phase 1 proved custom 32x32 worn hat rendering using a real Stardew Hat carrier plus a custom draw layer.
3. The 32px proof uses `RenderScale = 0.5`, giving 2 display pixels per source pixel and a nominal 64px worn width at normal farmer scale.
4. Phase 2 generalized the hardcoded proof into a garment registry + per-item persisted render snapshot stored in item modData.
5. The V5 authored generator was bridged offline into immutable runtime PNG + JSON definitions. Stardew never runs Python.
6. Tailoring selection was implemented as deterministic `Textile + Inspiration + sewing seed -> compiled production GarmentId`, excluding dev and REFERENCE-only garments.
7. Enhanced Tailoring shell was implemented around the real vanilla `TailoringMenu`, with Enhanced ON/OFF, Textile, Inspiration, Fashion Fragment slot, hidden result, controller reachability, and consume-last transaction ordering.
8. Fitting controls were expanded to live per-item `FitOffsetX`, `FitOffsetY`, and `FitScale` with Reset Position / Reset Scale / Reset All.
9. Variable Hat Size Lab live-tested 16 / 20 / 24 / 32 logical hats. 32x32 support is solved and must not be re-invented.
10. On 2026-09-19, uploaded 32x32 beanie test was added directly to ESM as `V4BEANIE` using the existing 32px proof contract. This is a test garment, not a new runtime architecture.

## Core architecture

Player-facing item identity remains a real Stardew `Hat` carrier:
- current carrier: `(H)RNGClothing.ESM.GeneratedHat`
- legacy proof carrier retained for dev-save compatibility

Vanilla carrier texture is transparent. Harmony adds ESM's custom worn layer only for ESM carrier hats. Vanilla hats are not globally replaced.

Garment definition owns:
- stable Id / Category / DefinitionVersion
- worn texture path
- FrameWidth / FrameHeight
- RenderScale
- VanillaReferenceAnchor
- per-direction source rectangle, anchor, logical offset, optional mirror/flip
- construction/provenance metadata

Generated Hat item modData owns the resolved instance snapshot so an already-created item does not silently change when registry/generator logic changes.
## 32x32 rendering contract — already solved

Reference definition: `assets/garments/dev_proof32.json`

Known-good contract:
- frame: 32x32
- `RenderScale = 0.5`
- reference anchor: X=10, Y=16
- Front source: 0,0; anchor 16,25; offset 0,-4
- Right source: 0,32; anchor 12,25; offset 0,-4
- Back source: 0,64; anchor 16,25; offset 0,-4
- Left mirrors Right; anchor 20,25; offset 0,-4; FlipX=true

Rule: do not resize the PNG to fix seating. Physical size is controlled by RenderScale. Seating is controlled by anchors/offsets. User-facing fitting is controlled by FitOffsetX/Y + FitScale.

Variable-size lab proved:
- 16x16
- 20x20
- 24x24
- 32x32

Lab examples normalize to ~80px nominal worn width using size-specific RenderScale. This is separate from the original dev.proof32 64px proof.

## Fitting system

Current fitting state lives on the garment instance:
- `FitOffsetX`
- `FitOffsetY`
- `FitScale` (default 1.0)

Current fitting UI range:
- scale min 0.85
- scale max 1.25
- step 0.05

The fitting preview is intentionally a stable front-facing orthographic preview. Do not hardcode random per-hat offsets before observing the worn result when the existing fit controls can handle adjustment.
## Generator -> ESM bridge

Tool: `tools/compile_esm_garments.py`

Flow:
`V5 authored generator -> deterministic seed -> immutable PNG + runtime JSON -> GarmentRegistry -> real GeneratedHat`

Production bridge rules:
- only `Classification = PRODUCTION`
- source-backed/reference-only masters are excluded
- dropped authored cells reject the compile
- generated paths are content-addressed
- old assets are not deleted, preserving old saved items

Original integration pool:
- soft_cap: 1000, 1007
- knit_cap: 1003, 1004
- wide_brim_hat: 1002, 1016
- felt_hat: 1005, 1014

Important 2026-09-19 note: generator bridge validator currently reports drift on soft-cap seeds 1000 and 1007 because the authored `soft_cap` source changed after the original compiled fixtures. The other six regenerate exactly. Do not interpret those two failures as Garment Runtime corruption.

## Tailoring selection

Bias file: `assets/tailoring/biases.json`

Development Textiles:
- cotton
- wool
- canvas (profile exists; no player-facing vanilla item mapping yet)

Development Inspirations:
- sunflower
- frozen-tear
- ancient-doll
Current player ingredient mapping:
- Cloth (O)428 -> cotton
- Wool (O)440 -> wool
- Sunflower (O)421 -> sunflower
- Frozen Tear (O)84 -> frozen-tear
- Ancient Doll (O)103 -> ancient-doll

Fashion Fragment:
- `(O)RNGClothing.ESM.FashionFragment`
- prototype cost: 5
- current icon is a development placeholder

Enhanced sewing transaction:
validate Textile -> validate Inspiration -> validate Fragment stack -> choose sewing seed -> deterministic garment selection -> construct real GeneratedHat -> consume 1 Textile -> consume 1 Inspiration -> consume 5 Fragments -> place result on cursor.

Failure before successful item construction must not consume ingredients.

## Enhanced Sewing Machine shell

The shell attaches additively to Stardew's real `TailoringMenu`.
- OFF mode stays vanilla.
- No global input suppression.
- Enhanced-owned controls only are intercepted in Enhanced mode.
- custom Fragment slot returns leftovers with Stardew `Utility.CollectOrDrop`.
- controller navigation/focus graph is explicitly supported.
- all new player-facing text belongs in i18n.

The user accepted the sewing/fitting function as functionally good; visual polish remains separate.

## Current verification status — 2026-09-19

Fresh verification:
- Release build: PASS, 0 warnings, 0 errors
- C# tests: 23/23 PASS
- generic garment validator: 19/19 definitions valid (includes V4BEANIE)
- tailoring bias validator: PASS for all 3 Textiles + 3 Inspirations
- generator bridge validator: 6/8 exact; 2 stale soft-cap fixtures due later authored source changes

Historical live milestones reconstructed from conversation:
- 32x32 worn proof passed live in-game
- generic runtime / generated garment pipeline passed live
- generator -> compiled garment -> registry -> real Hat -> custom renderer passed live
- authored fit-sign translation was corrected
- Enhanced shell sewing flow was live-tested
- generated output presentation was patched after an invisible/generic output issue
- variable size lab 16/20/24/32 was live-tested
- fitting offsets + scale controls were live-tested and accepted functionally
## V4BEANIE current test

ESM definition: `assets/garments/V4BEANIE.json`
Texture: `assets/V4BEANIE.png`
Garment Id: `V4BEANIE`

It uses the existing 32px proof contract. It is an ESM test garment. It must not be recreated as a Fashion Sense content pack unless explicitly requested.

## Dev commands

Garment runtime:
- `rng_garment list`
- `rng_garment reload`
- `rng_garment give <id> [seed]`
- `rng_garment equip <id> [seed]`
- `rng_garment inspect`
- legacy: `rng_garment_hat`

Tailoring:
- `rng_tailor profiles`
- `rng_tailor reload`
- `rng_tailor shell`
- `rng_tailor fragments [count]`
- `rng_tailor roll <textile> <inspiration> <seed>`
- `rng_tailor equip <textile> <inspiration> <seed>`

QC bridge has safe game-thread actions including `equip_garment`, fitting probes, render state, and captures. Do not use direct SMAPI TTY injection.

## Important safety / workflow rules

1. BEFORE ESM changes: run `tools/checkpoint_esm.sh`.
2. Never use `git clean`, hard reset, or broad cleanup on ESM without a checkpoint.
3. Do not replace ESM with Fashion Sense because an old proof pack exists.
4. For ESM tasks, inspect this file + current code first; do not reconstruct architecture from chat memory.
5. Preserve vanilla behavior; fail open; no global input suppression.
6. Keep player-facing strings in i18n.
7. Keep controller/Steam Deck navigation first-class.
8. New dependencies require explicit user approval.
9. Use the clean QC save `nana_447310232` for ESM live testing; do not use the broken WONG save.
10. Do not use direct `/dev/pts/*` SMAPI command injection.

## Recovery artifacts

A pre-checkpoint archive was created:
`archive/ESM_RECOVERY_20260919-0215.tar.gz`
SHA-256:
`4e3e8bcd3c97f00e251568b5cb8ec8ad67b84dacb2edd4f6078100c7d045313c`

This archive contains ESM source, tests, ESM docs, ESM tools, and the QC bridge.

## Open / later work

- broader art-quality/content expansion
- final Fashion Fragment art
- player-facing Canvas textile mapping if desired
- deeper horse/swim/multiplayer/action-frame compatibility gates
- resolve/recompile stale soft-cap generator fixtures when that authored base is intentionally stabilized
- shirts/pants/other garment categories after hat runtime is considered mature
- UI visual polish after function remains stable
