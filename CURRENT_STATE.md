# CURRENT_STATE.md

Concise current-milestone state. Not a log — see `PROJECT_MEMORY.md` for
history and `CLAUDE.md` for standing rules.

**Last updated:** 2026-09-10 (setup/audit session)
**Live stack:** Stardew Valley 1.6.15 · SMAPI 4.5.2 · Fashion Sense 7.5.0

---

## CURRENT MILESTONE

**Generator V2 setup — not started.** This session prepared tooling, references,
authority rules and workflow only. V2 design and implementation begin next
session.

Immediately prior work (through 2026-09-09) was **Cap 2**: deriving a hat family
directly from approved source pixels rather than procedurally inventing one —
`tools/cap2_*.py`, packs `RNG-Cap2Fit/Full/Overlay/Rarity/Rolls/Row8`. That
direction is what the new source-authority rule formalises.

---

## PROVEN

- **QC Bridge works end to end.** Real game, real Fashion-Sense-patched
  renderer, file-based JSON protocol. `qc_bridge/latest_state.json` holds a
  genuine session (2026-09-09 21:29) with a Cap2 appearance equipped and full
  farmer/view/hat state resolved, including FS id and texture path.
- **Worn-fit measurement from real captures.** The worn / nohat / hatonly
  capture triple makes hat seating measurable; an isolated sprite cannot.
- **All four authored bases captured live** (2026-09-10, session
  `20260910-013851`): 20 appearances x 4 directions = **80 frames, every one
  drawing real pixels**. All seated — centre +0.0, top +4, contact 5, 0 floating
  columns. Closes the long-standing "no in-game capture of any authored output
  yet". Evidence: `qc_bridge/captures/20260910-013851/`, `fit_metrics.json`.
- **The QC bridge CLI is verified against a live game**, including both guards
  tested for failure: a wrong `--expect` refuses, and a pack installed
  mid-session is caught before any capture runs.
- **Fashion Sense technical reference is complete and machine-readable**
  (`references/fashion-sense-official/`, gathered 2026-09-08 from the official
  `development` branch): 39 wiki pages, C# appearance models, 45 Example Pack
  JSONs, 30 releases with changelogs, `property_matrix.json`, `exporter_gap.json`.
- **The generator is dependency-free and runs.** `validate_generator_v6.py`
  passes all gates on a bare `python3` (verified this session).
- **Authored art beat procedural output visually** (user decision, headwear
  phase). Four bases (`felt_hat`, `wide_brim_hat`, `soft_cap`, `knit_cap`) each
  classify as their own corpus family. Note: that visual judgement is **not**
  approval for V2 — `authored/bases|decals|measurements` are REFERENCE pending
  per-asset provenance under `PORT_CLASSIFICATION.md`.
- **Sailor clothing family is frozen / good enough.** Do not reopen without a
  demonstrated regression.
- Vanilla shirt/clothing FS structures: `FITTED_SHIRT`, `SWEATER_TOP`,
  `VEST_TOP`, `CROPPED_JACKET`, `SHORT_OUTERWEAR` proven at runtime.

## NOT YET PROVEN

- Highlight share of authored bases is 1–4% against corpus families' 6–16%.
- `wide_brim_hat` carries 93 cells against its family's 108.
- True long coats / long outerwear: rejected from output, lower-body
  animation and layering unproven.
- V4.5 Pants / Skirt / Footwear / Mantle: fixtures exist, all runtime-EXPERIMENTAL.
- **Everything the older reports call "proven" is unverified by me.** I have not
  re-run the V4/V5/V6 validators beyond V6, and none of it has been visually
  re-checked in game this session.

## LOCKED DECISIONS

- **Two authority hierarchies** (technical behaviour vs. visual/construction) —
  `CLAUDE.md` §1. Not one combined list.
- **Approved source pixels are the construction authority.** No redrawing,
  procedural silhouette invention, source averaging, reinterpretation, or
  regenerating a "similar" version. Generator scope is palette, approved
  overlays, source-derived components, rarity weighting, deterministic
  composition, player fitting. `CLAUDE.md` §2.
- **Nothing from V1 is canonical because it exists.** Everything carried toward
  V2 is tagged KEEP/PORT/REFERENCE/REBUILD/REJECT in `PORT_CLASSIFICATION.md`.
- **In-game normal-scale visual QC is the hard gate.** Metrics are supporting
  evidence and never override obviously wrong output.
- Semantic labels require the six-point verification in `CLAUDE.md` §3.
- Player-facing UX must feel vanilla and be controller/Steam-Deck-first;
  Hand Mirror and QC tooling are development-only.
- Generator stays dependency-free; `.venv` is for analysis tools only.
- Canonical: V5 Decision / Construction / AA / AG. Not canonical: old renderer,
  old AA/AG, old Sailor renderer, old `rngc`, old 16×16 clothing assumptions.
- Clothing default is native 8×8 at Scale 4 unless a family has evidence otherwise.

## KNOWN FAILURES

Each cost real time. Do not re-enter them.

- **A metric optimised for three headwear phases could not see the defect the
  user actually reported.** Cause of the QC-authority rule.
- **The visor's lit surface was labelled a decorative "emblem"** from pixel
  separability alone. Cause of the semantic verification rule; the corrected
  method is documented in `tools/cap2_semantic_map.py`.
- **Fashion Sense loads pack textures once at startup.** Three capture runs lost
  before `fs_reload` existed. A pack *folder* created after game start is not
  registered with SMAPI at all — FS lists its appearances but draws nothing,
  which looks exactly like broken art. Requires a restart.
- **A float in any `Position` field makes FS reject the whole model silently.**
- **Two false root causes** came from comparing captures across game sessions.
- Fashion Sense caches `HeadPosition` at pack load.
- `compose(style=…)` picked a base before honouring the requested style.
- Rims drawn one step up from the ramp bottom measured wrong; so did an interior
  as dark as its rim. The *delta* is what reads.
- Coastal Polo microfix failure — see `docs/quality/`.

## SETUP COMPLETED 2026-09-10

- `.venv` + `tools/env.sh` — Pillow 12.3.0, NumPy 2.5.3, for **analysis only**.
  Correction to an earlier belief: the generator is pure-stdlib and always was,
  so `validate_*.py` never needed a venv. SciPy not installed; nothing needs it.
- `CLAUDE.md`, `CURRENT_STATE.md`, `PORT_CLASSIFICATION.md` at root;
  `.claude/settings.json` allowlists read-only reference queries and pins the
  source packs + third-party corpora read-only.
- `references/stardew-official/` — the gap that mattered. 32 official `Modding:`
  wiki pages, SMAPI docs + API source (266 files, sparse depth-1), and a
  metadata index of the installed 1.6.15 assembly (1093 types).
  Built by `tools/index_stardew_reference.py` + `tools/AssemblyIndex`.
- `tools/catalog.py` — read-only source-catalogue queries that surface approval
  state: 12 REUSABLE / 43 BASE-SPECIFIC / 108 REFERENCE-ONLY variants across
  53 families, 319 appearances, 5 packs.
- `tools/palette.py` + `tools/palette_calibrate.py` — offline colour analysis,
  thresholds calibrated against 146 approved source appearances, and every flag
  prints its corpus error bar.
- `tools/qc.py` — subcommands (`ping`/`state`/`packs`/`refresh`/`worn`/
  `compare`/`menu-probe`/`smapi-log`/`raw`) that make the reload and new-pack
  guards unskippable. `qc_run.py` and friends still import cleanly.
- `tools/corpus_manifest.py` — hashes the 3181 out-of-band corpus files so a
  second machine can prove it holds the same source authority.
- No MCP server was built. Not needed for any capability so far.

## NEXT TEST

1. **Decide on decal back-view coverage.** Live capture confirmed
   `brim_edge` contributes **nothing to the back frame** on `wide_brim_hat` —
   it declares `views: ['front','left']`, so the render matches the data and
   this is an authoring gap, not a bug. **21 of 44 decals have no back view.**
   For a wide brim, which is fully visible from behind, that may read as an
   inconsistency in game. Your art call; capture evidence is in
   `qc_bridge/captures/20260910-013851/Auth07WideFCMDecal/`.
2. **Explain the seating difference between sessions.** Authored bases measure
   top +4 / contact 5 / face 914-994px; the SourceCap set in the same scene
   measured top +0 / contact 1 / face 742-790px. Same hairstyle and scene, so
   the difference is real and unexplained. Not yet a defect — a question.
3. Only then begin Generator V2 design.

Unrelated, noted not fixed: the SMAPI log shows repeated vanilla
`FarmAnimal`/`GameLocation.IsOutOfBounds` NullReferenceExceptions — an orphan
building in the save, not our mods. `tools/repair_save_orphan_buildings.py`
already exists for it.

## DO NOT REDO

- Do not rebuild the QC Bridge. It works; wrap it.
- Do not re-clone or re-derive the Fashion Sense reference. It is complete.
- Do not add PIL/NumPy/SciPy to any generation or validation path.
- Do not reopen Sailor, or headwear geometry/Architecture from phases 1–3,
  without new in-game evidence.
- Do not re-run settled investigations without contradicting evidence.
- Do not optimise a metric against a defect that was reported visually.

---

## Deferred: git and PC ↔ Steam Deck sync

**State as of this session.** The project had **no version control** — `.git/`
existed but was an empty directory. There were no remotes, no branches, no
upstream, no unpushed commits, and **no partial PC/Deck sync setup of any kind**.

Done now (minimal, local only): `git init` on `main`, a `.gitignore`, and one
initial commit — 1404 files, ~19 MB.

**Deliberately not tracked:** regenerable `output/` and `test-packs/`, QC
captures, and the third-party art corpora (`generator conent/`,
`references/benchmark|ref_codex|style-profiles|lifestyle|hoodie`, `motif/`).
Those corpora are the source-construction authority but are other authors'
Fashion Sense packs — kept out on size and redistribution grounds, and
verifiable across machines via `tools/corpus_manifest.py`.

**Deferred, needs a decision:** no remote exists. PC ↔ Steam Deck sync needs
(a) a private remote — `gh` is **not installed** on this Deck, so that means
installing it or using a token — and (b) a decision on how the untracked
source-pack corpora reach the other machine (rsync/Syncthing, not git).
Nothing will be pushed without explicit approval.
