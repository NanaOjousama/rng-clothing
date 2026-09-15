# CURRENT_STATE.md

Concise current-milestone state. Not a log — see `PROJECT_MEMORY.md` for
history and `CLAUDE.md` for standing rules.

**Last updated:** 2026-09-14 (Source-Backed V2 built beside legacy — awaiting user approval + in-game source comparison)
**Live stack:** Stardew Valley 1.6.15 · SMAPI 4.5.2 · Fashion Sense 7.5.0

---

## CURRENT MILESTONE

**Beret family Milestone 2 — two shapes, verified in game. Complete.**

Milestone 1 landed the generic family axis, `quality_tier`, optional authored
right views and a `classification` gate. Milestone 2 added a second shape and
put the whole thing under a 48-appearance batch, which found five real defects
(all fixed) and one library gap (recorded, not papered over).

- **`beret_02`** is ingested from the **approved** Cottagecore Set beret
  (plurffle) — better provenance than `beret_01`, and a genuinely different
  shape: 14x9 with a crown nub against 13x8 without one.
- **Ingest is now generic.** `tools/ingest_hat_base.py` drives every shape from
  one spec table; nothing in it knows what a beret is.
- **The mirror fallback is symmetric.** A base may author either profile view
  and have the other mirrored. `beret_02` authors Front/Right/Back and flips
  Left, which is the Fashion Sense `Flipped` convention its own source uses.
- **`can_place()`** is one shared predicate applied by both the combinator and
  the reporting tools, so pool coverage asks exactly the question selection asks.
- **Per-shape restrictions are data.** `crown_button` is restricted to
  `beret_02`'s nub through `fits`; the band motifs are refused on `beret_02` by
  geometry alone. No shape name appears anywhere in `v5/authored.py`.

Packs: `test-packs/fashionsense/RNG-Beret-Family-M1/` (4) and
`RNG-Beret-Batch-M2/` (48). Both are installed under the game's `Mods/` and
need a game restart before they register.

Immediately prior work (through 2026-09-09) was **Cap 2**: deriving a hat family
directly from approved source pixels rather than procedurally inventing one —
`tools/cap2_*.py`, packs `RNG-Cap2Fit/Full/Overlay/Rarity/Rolls/Row8`. That
direction is what the source-authority rule formalises.

---

## SOURCE-BACKED V2 (2026-09-14) — ACCEPTED BY USER

**Status: ACCEPTED and frozen. Do not redesign V2. No library expansion without
approval. Next: one real authored plaid mask for beret_02 only.**

- `v5/source_backed.py`: a separate base type. Source pixels (md5-pinned preserved
  copy) are canonical; the (role, step) semantic map is stored separately under
  `authored/source_backed/<name>/semantic/`; placement, views and Fashion Sense
  colouring fields are read from the source hat.json. `authored.py` is untouched.
- Ingested: `beret_02`, `beret_01` (`tools/ingest_source_backed.py`).
- **Proven offline:** neutral render == source pixel-exact for both; neutral pack
  keeps every non-layout source model field verbatim (HeadPosition 0,1 / 0,0; no
  DisableGrayscale -> still tinted in game); palette bake = source x tint, alpha
  and value order kept; material changes only mask cells by a value ratio; decals
  change only seated/shaded cells; render == pack. `trace_source_fidelity.py`
  (v2 default) reports **no unexpected stage** for either base.
- Semantic map, zones and anchors equal the legacy base's exactly.
- **Legacy unchanged:** `tools/legacy_render_guard.py` — 1996 renders captured
  before V2, 0 moved. `validate_beret_family.py` 81/81, material-mask 14/14.
- Materials: no authored plaid mask exists for either shape, so plaid is
  **refused**, not procedurally fitted. The hat_8 reference plaid extracts cleanly
  (back: v-lines x4/7/12/15, h-lines y5/8/11/14, 1 component) and is
  INCOMPATIBLE with both shapes (`tools/extract_material_mask.py`).
- **In game, session `20260914-231749`: source pack vs V2 neutral IDENTICAL.**
  `tools/compare_source_v2_worn.py`: beret_02 (Cottagecore `Beret`) and beret_01
  (`hyoung_hats_24`) vs `SB2Beret02Neutral` / `SB2Beret01Neutral`, all four
  directions: worn diff 0 px, hat-only diff 0 px, scene diff 0 px, hat bounds
  offset 0. Non-vacuous: 1728-2576 hat px per direction. Source HeadPosition
  reproduces the author's placement; the explicit mirrored left frame renders
  identically to FS `Flipped` (HeadPosition X=0). Evidence:
  `experiments/source_fidelity/v2_worn/20260914-231749/`.
  Limit: the farmer's FS hat tint was white, so non-white tinting was not
  exercised in game (identical pixels + identical render fields imply it).
  SMAPI errors in that session are a vanilla FarmAnimal NullReference at save
  load, unrelated to Fashion Sense.
- Pre-existing, unrelated: `validate_generator_v6.py` crashes on missing
  `output/v6-production-batch/design-rarity-table.json`.

## SOURCE-FIDELITY AUDIT (2026-09-14) — DIAGNOSIS ONLY, NOTHING FIXED

Art tuning is paused. Question: where does a good source stop looking like
itself? `tools/trace_source_fidelity.py` walks a base through S1 source → S2
ingested → S3 neutral render → S4 palette → S5 material → S6 pack → S7 worn;
evidence in `experiments/source_fidelity/<base>/` (stage PNGs, x8 strips, diffs,
`report.json`). Regression test: `tests/test_source_fidelity.py`; it is **red on
purpose** (6 failures, 3 stage tests x 2 bases).

- **First pixel-level break is S2, ingest, for both source-backed berets.**
  `tools/ingest_hat_base.py` rewrites every source grey onto the index's fixed
  `#202020..#E0E0E0` ramp. Alpha and geometry are exact.
  - `beret_02` (approved Cottagecore): 333/333 px change value, the 5 source
    levels keep their order, one 1-px `#a4a4a4` stray merges into `#a5a5a5`.
    Visually it stays itself: S4 with EVERYDAY_STONE_BLUE lands close to the
    simulated Fashion Sense tint of the untouched source (L* 15/30/57/69/82 vs
    19/27/54/70/81).
  - `beret_01`: 45 near-flat dark greys (edge-contrast median 2.5 L*) are
    bucketed `equal_width` into 6 steps spread over the whole ramp (12.9 L*).
    A subtle dark hat becomes a high-contrast shaded one with a bright back
    highlight. **This is the first stage where a source visibly stops looking
    like itself.**
- **S2→S3 is exact** (render path adds nothing). **S4→S6 pack is exact** at
  Common. **S6→S7 is exact**: every hat pixel is drawn as shipped, 0 hidden.
- **S5 material is destructive to source shading**: plaid lifts 49 of
  `beret_02`'s 88 `#d6d6d6` cells onto the `#fefefe` highlight step.
- **Placement is not the source's.** The source `beret_02` hat.json has
  `HeadPosition Y=1`; every pack ships `Y=-2`. In FS source HeadPosition is the
  draw origin offset, so ours draws **3 logical px lower** than the author
  placed it — likely the cause of "beret_02 reads lower and bulkier" below.
  Inferred from DrawManager.cs, **not yet captured in game**.
- The source is a greyscale **tint mask** (no `DisableGrayscale`); our packs
  bake colour with `DisableGrayscale: true`. No capture of the source itself
  worn exists — the Cottagecore Set is not installed in `Mods/`.
- `beret_03` is out of scope by its own provenance: shading not taken from source.

Next test (not run): capture the untouched Cottagecore beret worn (needs the pack
installed before game start) against a `beret_02` pack at `HeadPosition Y=1`.

---

## PROVEN

- **The family/quality/right-view changes are inert for existing assets.**
  133 pre-change renders (every legacy base x compatible palette, plus 12
  `compose()` rolls) hash byte-identical afterwards —
  `tests/fixtures/authored_legacy_baseline.json`, captured before the edit.
- **`beret_01`'s four authored directions survive the ingest**: alpha identical
  to the source sheet in all four frames, bounding boxes unmoved, and the
  rendered right view provably not a mirror of left.
- **`quality_tier` is a real independent axis**: with family, shape, palette and
  style pinned, the four tiers still produce four distinct renders with
  monotonically increasing decoration.
- **The shape axis does something.** Across the 48-appearance batch the two
  shapes wear different decoration sets, there are **0 placement drops**, and no
  two different inputs render identically.
- **`tools/validate_beret_family.py` is 81 checks** and covers legacy
  byte-identity, both mirror directions, per-shape restrictions, tier budgets
  and the batch statistics.
- **In game, 2026-09-13, session `20260913-220258`: 52 appearances x 4
  directions = 208 frames, all drawing.** For every one of the 8 shape x
  direction combinations, **0 px of the shipped art is missing** — the renderer
  draws the pack frames pixel for pixel.
- **Seating is uniform and correct**: centre +0.0, hat_top +4, contact band 5 on
  all 52. `HeadPosition 0,-2` is verified and was **not changed**.
- **The authored right view survives into the game.** `beret_01`'s left differs
  from its mirrored right by 112 px (its authored right is genuinely used);
  `beret_02`'s left is an exact 0-px mirror of its right, which is the
  `Flipped` fallback behaving correctly. Both are what the design intends.
- **The axes are live, not just static**: same shape and palette across tiers
  changes the drawn hat (Common vs RarePlus 240-288 px), and the same shape and
  tier across palettes recolours it (992-1936 px).
- **Face intrusion and hair-above-hat are within or better than the accepted
  authored-base baseline** (`20260910-013851`): face_pixels mean 913 vs 952,
  hair-above mean 244 vs 288 in profile and 356 vs 448 at the back.

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

- **`beret_02` reads lower and bulkier than `beret_01` when worn.** Its profile
  edge sits just above the eye where `beret_01` clears it comfortably. Every
  metric is inside the accepted baseline and no art is missing, so this is a
  design judgement for the user, not a defect. The dark notch in its back view
  is faithful to the approved Cottagecore source, not an artefact.
- **4 floating columns in every profile view**, a 1-logical-pixel gap under the
  beret's trailing edge. 5 of the 20 already-accepted authored bases show the
  same signature, so it is within tolerance rather than clean.
- **`beret_02` has no premium surface motif.** At RarePlus its allowed surface
  classes are woven_trim, band and badge; both bands are 6 wide against its
  5-wide side band zone, and `brooch_round` is a surface piece in the
  overhanging `side` zone. So RarePlus carries one piece where Rare carries two.
  Recorded in `authored/families.json` under `known_gaps`; the fix is a new
  decal, which is library expansion.
- `beret_variant1` / `hyoung_hats_24` has **no established provenance**; it is
  REFERENCE, and the engine enforces that by excluding it from the slot-wide
  roll. It must not be promoted without an origin.
- Only **two** beret shapes exist, both REFERENCE. Neither has been seen worn.

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
