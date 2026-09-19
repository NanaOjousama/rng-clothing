# Project Agent Rules

## Enhanced Sewing Machine (ESM) safeguard

Before modifying anything under `mods/EnhancedSewingMachine/`, `mods/EnhancedSewingMachine.Tests/`, or the ESM-specific tools/docs:

1. Read `docs/enhanced_sewing_machine/ESM_MASTER_CHECKPOINT.md`.
2. Run `tools/checkpoint_esm.sh`.
3. Inspect the current code/tests rather than reconstructing ESM architecture from chat memory.
4. Do not redirect an ESM task into Fashion Sense unless the user explicitly requests Fashion Sense.
5. Do not use direct SMAPI TTY injection via `/dev/pts/*`.
6. Preserve vanilla behavior, controller/Steam Deck support, i18n, and fail-open compatibility.
7. Do not add dependencies without explicit user approval.

For ESM 32x32 hats, the size/runtime problem is already solved. Reuse the existing Garment Runtime contract and fitting system instead of inventing a new rendering path.

## Project recovery / continuity safeguard

Before generator, Fashion Sense QC, source-backed, or ESM work:
1. Read docs/recovery/PROJECT_RECOVERY_2026-09-19.md.
2. Treat Git + repository evidence as authoritative; chat memory is not project state.
3. Do not reinvent a subsystem until its existing builders, traces, tests, and packs have been searched.
4. When remote access is available, perform shell/file/build/QC-bridge work directly instead of delegating it to the user.
5. After a user-accepted live milestone: update the authoritative status, run verification, create a scoped commit, and report the actual commit hash.
6. Never claim work was committed without an observed commit hash.
7. Quarantine rejected experiments from authoritative constructions. BEANIE8_QC is rejected and must not replace the recovered source-backed beanie path.
8. Do not bless the current Soft Cap working-tree changes by updating fixtures until the Soft Cap expansion is intentionally reviewed and accepted.
