# Stardew Generative Systems — PROJECT_MEMORY

> Purpose: compact persistent context for fresh Claude Code sessions.
> Read this file first. Do **not** treat it as a session log.
> Only read subsystem memory/docs relevant to the current task.

## Project Goal
Build high-quality procedural Fashion Sense content for Stardew Valley using a constrained V5 architecture that produces coherent, intentional designs rather than random pixel noise.

Current major subsystems:
- Clothing V5
- Headwear V5

Final quality is judged **in game at normal Stardew scale**. Metrics, corpus statistics, tests, and reconstruction scores are supporting evidence, not the final authority.

## Canonical V5 Architecture
- One player roll -> hidden dependent decisions -> one coherent item.
- Hierarchy:
  `Slot -> Family -> Architecture -> scoped variables`
- Family = candidate vocabulary.
- Architecture = construction commitment.
- Structural changes belong to Architecture.
- Independent dimensions/modifiers belong to scoped variables.
- Invalid concepts are absent, never represented as None/null/false placeholders.
- Every variable has exactly one owner / one resolution pass.
- Lower passes may not reopen higher structural decisions.
- Repair is bounded inside the current variable domain; no global backtracking.
- One shared complexity pool initially, tagged structural / surface / ornament. Structure spends first.
- Semantic occupancy: exclusive / conditional-share / overlay.
- Style Context may only reweight already-legal choices.
- Color Architecture resolves semantic roles before palette arithmetic.
- Projection adds **zero design entropy**. Views are deterministic realizations of the same resolved item.
- Validity is enforced during generation.
- Diversity is measured post-render.
- Prefer authored closed silhouette / construction vocabularies over free procedural carving.
- Authored motifs/pieces are primary; bounded parameters only where the dimension is genuinely continuous.
- Base lighting belongs to Grammar.
- Local occlusion is construction metadata; compose with MAX.
- Free/attached edges are structural metadata.
- Outline behavior is context/material/slot aware; do not force one universal outline rule.

## Canonical / Deprecated
Canonical:
- V5 Decision
- V5 Construction
- V5 AA
- V5 AG

Do not use as canonical:
- old renderer
- old AA/AG
- old Sailor renderer
- old rngc
- old 16x16 clothing assumptions

For clothing, native 8x8 with Scale 4 remains the default unless a family has evidence for another resolution.

## QC Rules
- Passing tests does not mean an item is visually good.
- In-game normal-scale QC is the hard gate.
- Do not call a subsystem "done" or "locked" while visual output is still obviously weak.
- Distinguish pipeline vs Architecture vs authoring/vocabulary vs QC limitations.
- Classification is diagnostic, not a prohibition. Architecture/pipeline changes are allowed when evidence justifies them.
- Reconstruction and corpus testing answer different questions:
  - corpus matching = are outputs in the right statistical neighborhood?
  - reconstruction = can the grammar intentionally express a known target?

## Workflow Rules
- Preserve durable decisions in memory/docs before starting a fresh context.
- Prefer a fresh Claude context after a major phase rather than carrying an enormous conversation indefinitely.
- Fresh session startup:
  1. read this file
  2. read only the subsystem memory for the task
  3. consult deeper references only when needed
- Do not re-run settled investigations unless new evidence contradicts them.
- Do not turn memory files into chronological logs.
- When a phase ends, update current state, durable decisions, remaining blockers, and links to deeper evidence. Remove stale current-state notes.

## User / Review Preferences
- User is not a programmer; reports should explain what changed and why in plain language.
- User values visual quality over technical self-congratulation.
- Do not overvalue contact sheets or metrics over in-game appearance.
- Do not recommend abandoning a category because of a fixable defect.
- Do not silently reopen frozen work.
- When another agent is already working, do not pile on extra prompts/changes unless asked.

## Subsystem Index
For Headwear work, read:
- `HEADWEAR_MEMORY.md`
- then `KNOWLEDGE_BASE.md` / `GAP_LOG.md` only if the task needs the evidence

For Clothing work, read:
- `CLOTHING_MEMORY.md`
- then the canonical clothing architecture/handoff only if needed

## Frozen
- Sailor clothing family is frozen / good enough.
- Do not reopen Sailor unless a real new bug or regression is demonstrated.

## QC Authority (added phase 4 — durable)
The real Stardew + Fashion Sense render is the authority for wearability and
placement. Synthetic farmer composites are a cheap preview only and must never
be the final placement/fit gate. Three headwear phases were spent optimising an
alpha-mask metric that could not see the defect the user actually reported.

Use `test-helpers/StardewVisualQCBridge` + `tools/qc*.py` for real captures.
See `docs/headwear/QC_BRIDGE.md`.

## Current Project Focus
Headwear V5 is the active subsystem.
Phase 4: live in-game QC bridge + mod-author quality calibration, then the
rendering-quality pass (AG shading, ramps, hat Color Architecture accents).
Geometry/Architecture from phases 1-3 is settled unless real in-game evidence
identifies geometry as a cause.
