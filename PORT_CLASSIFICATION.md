# PORT_CLASSIFICATION.md

What may enter Generator V2, and in what capacity. Classified at
module/directory granularity — individual files are called out only where they
materially differ from their neighbours.

**Nothing here is canonical because it exists.** Tags:

| Tag | Meaning |
|---|---|
| **KEEP** | already correct, V2 uses it as-is |
| **PORT** | sound, moves into V2 with adaptation/review |
| **REFERENCE** | read for evidence and lessons; code/assets do not enter V2 |
| **REBUILD** | the need is real, the implementation is not — rewrite under V2 rules |
| **REJECT** | isolated. Must not enter V2 without explicit approval. |

Classified 2026-09-10 from structure, module docstrings, `PROJECT_MEMORY.md` and
`HEADWEAR_MEMORY.md`. **Rows marked ⚠ are my judgement and need your
confirmation** — mostly where the source-authority rule reverses a prior status.

---

## KEEP

| Unit | Why |
|---|---|
| `test-helpers/StardewVisualQCBridge/` | Working in-game QC bridge. Top authority for visual truth. Do not rebuild. |
| `tools/qc.py`, `qc_run.py`, `qc_metrics.py`, `qc_compare.py`, `qc_worn_sheet.py`, `qc_calibrate.py` | The QC client and the worn/nohat/hatonly measurement method. |
| `generator/png_utils.py` | Dependency-free RGBA8 PNG on the logical pixel grid. Load-bearing; nothing may replace it with PIL. |
| `references/fashion-sense-official/` | Complete official FS technical authority. |
| `references/cheerful-pixels/STUDY.md` | Engineering reference (menu/undo/coordinate patterns only). |
| `source_catalog/catalog.json`, `families.json` | The source index. Queried, never rewritten by V2. |
| `tools/index_fs_reference.py` | Regenerates the FS property matrix from the official wiki. |
| `docs/`, `reports/`, `PROJECT_MEMORY.md`, `HEADWEAR_MEMORY.md` | Evidence and history. |

## PORT

| Unit | Why, and what review it needs |
|---|---|
| **`v5/source/`** — `ingest.py`, `decompose.py`, `dissect.py`, `semantic.py`, `library.py`, `render.py`, `roundtrip.py`, `audit.py`, `pngread.py` | **Primary V2 port candidate.** This subsystem is closest to the new source-authority architecture — it ingests approved packs and measures what they actually draw — but **no module becomes V2 canonical until it is reviewed under the new rules.** Source pixels supply segmentation and construction *evidence*; they do not by themselves establish semantics. Every label this subsystem emits (`semantic.py`, `decompose.py`, `dissect.py` especially) must be re-audited against the full CLAUDE.md §3 verification — source location, worn location, side/profile correspondence, back evidence where relevant, structural vs decorative, positive evidence for the label — before it is trusted. This requirement exists specifically to prevent a recurrence of the visor/emblem failure. |
| `v5/source/cap2_gen.py`, `cap2_pack.py` | The one existing generator that varies *within* a source family (base fixed, palette + one masked motif). The V2 pattern. Review its motif-safe-mask derivation. |
| `v5/rng.py` (`StreamBank`) | Per-decision named streams; adding a decision cannot shift earlier draws. Determinism requirement met. |
| `v5/contracts.py`, `resolver.py`, `schema.py`, `context.py` | One-owner/one-resolution-pass decision model. Sound; must be re-scoped so it composes source components instead of inventing structure. |
| `v5/color.py`, `material.py`, `quality.py`, `fitting.py`, `projection.py`, `pngio.py` | Colour roles, fitting and deterministic projection ("views add zero design entropy"). |
| `v5/library/sailor_*.py` | Frozen Sailor family. Ports as a closed, frozen unit — not reopened. |
| `mods/RNGClothingFitting/` | Player-facing fitting menu, and **it already has real controller support** (`snapToDefaultClickableComponent`, `allClickableComponents`, `applyMovementKey`, `receiveGamePadButton`). `Symmetry.cs`, `FitHistory.cs`, `FitStore.cs`, `FittingGeometry.cs` are reusable. Audit against the vanilla-feel rule: it must not end up depending on the Hand Mirror or debug keys. |
| `mods/RNGClothingFitting.Tests/` | Existing test coverage. |
| `generator/v6/` rarity + diversity machinery ⚠ | Rarity weighting and pairwise-diversity rejection are explicitly in V2's permitted scope. The *art generation* around them is not — port the weighting/diversity logic only. |
| `specs/palettes/` (`color_roles.json`, `material_color_behavior.json`, `palette_stories.json`), `PALETTE_STORY_LIBRARY.json` | Curated palette data; palette change is permitted variation. |
| `tools/analyze_*.py`, `tools/index_fs_reference.py` | Corpus measurement instruments — the same instrument must keep measuring V2 output. |
| `authored/source_bases/cap2/` ⚠ | **Strong PORT candidate, not automatically canonical.** Explicitly source-derived, which is why it ranks above the rest of `authored/`. Still requires provenance confirmation and a §3 re-audit of any labelled region before use. |

## REFERENCE

| Unit | Why it does not enter V2 |
|---|---|
| `v5/grammar.py`, `construction.py`, `aa.py`, `ag.py`, `surface.py`, `ornament.py` ⚠ | The procedural art-invention core. Genuinely good work and the source of most durable lessons — but generating a silhouette from grammar is exactly what the source-authority rule forbids. Read for its rules (outline behaviour, ramp discipline, occlusion-by-MAX); do not call it. |
| `v5/library/brimmed_hat.py`, `brimless_hat.py`, `hat_templates.py`, `hat_motifs.py` ⚠ | Procedural shape vocabularies. The *findings* (families are proportions not names; rims belong at the ramp bottom) are durable; the generators are superseded. |
| `generator/v3/`, `v4/`, `v45/`, `v46/`, `v46b/`, `v5a/`, `v5b/`, `v5c2/`, `v5d/`, `v5e/`, `hybrid_v3/` ⚠ | Successive procedural generations. Evidence of what runtime-validated and what did not; not a V2 code path. |
| `tools/generate_*.py`, `tools/validate_*.py` (except `qc_*`) | Per-experiment scripts. Keep runnable as reproductions of past evidence; do not extend. |
| `specs/garment_grammar_v4/`, `specs/hybrid_garment_compiler/` | Grammar specs for the invention path. |
| `templates/`, `prototypes/sailor_mini/`, `style-profiles/`, `good hats/` | Study material. |
| `authored/bases/`, `authored/decals/`, `authored/measurements/` ⚠ | **REFERENCE pending provenance/approval — deliberately NOT KEEP.** Being visually better than procedural output is not approval, and does not establish that an asset is source-derived. Each asset must be triaged individually; only one that is explicitly approved, source-derived where required, provenance-known, and consistent with the source-authority rule may later be promoted to PORT or KEEP. Until then these are read, not built with. |
| `beret_variant1/` (`hyoung_hats_24`) ⚠ | **Source of the Beret family's first shape. Origin now identified; licence still unestablished.** Byte-identical (md5 `c63ad880`) to `Hats/hyoung_hats_24` in the installed third-party pack `[FS] h young's hats` (author *h young*, FS code by *Mychocolate*, v1.0.0, UniqueID `hyoung_hats.fs`), whose manifest declares no licence. Not in the approved catalogue. Ingested as `authored/bases/beret_01/` for architecture, conversion and testing only. The engine enforces the tag rather than trusting it: a base whose `classification` is REFERENCE is excluded from the slot-wide roll and is reachable only by explicitly naming its family. Promote to PORT only when the origin and licence are established. Provenance record: `authored/source_bases/beret/beret_01/provenance.json`. |
| `Beret/` (7 colourways) | Unattributed beret pack at the repo root, same absence from the catalogue. Not ingested. Read for evidence only — it is a clean worked example of the ColorMask palette axis (one geometry, a 6-step greyscale ramp, and a fixed accent deliberately left out of the recolour). A candidate `beret_02` once provenance is known. |
| `authored/bases/beret_02/` | **The Beret family's second shape, and materially better standing than `beret_01`.** Ingested from `[FS] Cottagecore Set / Hats / Beret` — an approved source pack (plurffle, `SmolHooman.CottagecoreSet`) whose base is composable per `tools/catalog.py family Beret`. Its source authors Front/Right/Back and flips Left, which is why the engine now mirrors whichever profile view a base does not author. Held at REFERENCE with the rest of the family until the family as a whole is cleared; promote ahead of `beret_01` if only one shape can ship. Cottagecore's `Beret (Ribbon)` and `Beret (White Ribbon)` remain REFERENCE-ONLY per the catalogue and were not built on. |
| `authored/bases/beret_01/`, `authored/source_bases/beret/` ⚠ | Inherits REFERENCE from its source above, and carries it explicitly in `base.json` and `provenance.json`. The normalised art (45 source greys snapped to the index's 6 `body` steps) never replaced the original: a byte-identical copy of the source sheet is preserved at `authored/source_bases/beret/beret_01/source/`, and `tools/validate_beret_family.py` checks both md5s on every run. |
| `docs/quality/`, `docs/decisions/` | Recorded failures and locks — read before re-deciding. |
| `references/benchmark|ref_codex|lifestyle|hoodie`, `motif/` | Third-party art corpora and AI-generated motif research: style analysis only, never copied, never construction authority. |
| `Cheerful Pixels …zip`, root `.docx`/`.md` roadmaps | Handoff documents. |

## REBUILD

| Unit | Why |
|---|---|
| `generator/generate_v1.py`, `generate_v2.py`, `v2_recipe_engine.py`, `v2_renderer.py`, `v2_structural.py`, `v2_validator.py`, `recipe_engine.py`, `renderer.py`, `validator.py`, `prepare_v2_recipes.py` ⚠ | **Naming trap:** this "v2" is the *old* generator v2 (early recipe/renderer work), not Generator V2. Superseded by V5. The names must not be reused for new V2 code, or the two become indistinguishable in every future search. |
| A palette/colour analysis tool | The need is real, no executable tool existed — `tools/palette.py`, built this session. |
| A source-catalogue query layer | `tools/catalog.py`, built this session; must surface approval state. |
| Old 16×16 clothing assumptions | Clothing default is native 8×8 at Scale 4. |

## REJECT — isolated, do not import without explicit approval

| Unit | Why |
|---|---|
| `rngc/` | `PROJECT_MEMORY.md` names "old rngc" explicitly not canonical. Whole package isolated. |
| "old renderer", "old AA/AG", "old Sailor renderer" as named in `PROJECT_MEMORY.md` | Explicitly non-canonical. |
| `output/` (4044 files, 57 dirs) | Experimental and superseded generator artifacts. Evidence only. **No asset here enters a V2 pack.** |
| `test-packs/` (1034 files) | Experimental FS test packs, including known-failed ones. |
| Deployed `RNG-*` mod folders in the game's `Mods/` | 15 experimental validation packs installed live. Not V2 content; prune before shipping anything player-facing. |
| `generator/autonomous_recovery/`, `generator/controlled_test/` ⚠ | Recovery/diagnostic experiments. |
| `docs/quality/COASTAL_POLO_MICROFIX_FAILURE_AUDIT.md` subject asset | A recorded failure. |
| `beret_v2.png` (PixelLab MCP candidate, scratchpad) | Generated art, no source provenance. Isolated pending cleanup, directional completion and live QC — see **PixelLab-generated candidates** below. |

---

## PixelLab-generated candidates — REJECT (isolated), with a defined promotion path

A new asset class as of 2026-09-12: art produced by the PixelLab MCP service
rather than drawn by an author or derived from an approved source pack. It gets
its own section because the existing rows assume an asset is either
source-derived or procedurally invented, and this is neither.

### `beret_v2.png`

| Field | Value |
|---|---|
| **Tag** | **REJECT** — isolated. Must not enter V2 without explicit approval. |
| **Origin** | PixelLab-generated (`create_image_pixen`, seed 2, 1 generation, 2026-09-12). Job `69801bd0-947a-4320-87b3-89d5374ee42d`. |
| **Authority** | Generated experimental asset. Ranks **below** approved source art and below authored bases on the §1 visual/construction hierarchy. Carries no provenance and establishes no construction precedent. |
| **Location** | `experiments/pixellab/` — an isolated experiment directory, deliberately outside `generator conent/` and `references/`. Being in the repo is storage, not approval: the REJECT tag and every promotion condition below still apply unchanged. Selected files (`beret_pro_v1_low_classic.png`, `beret_v2.png`, `beret_test.png`, style-reference crops) are kept for reproducibility; bulk candidate grids (`pro_*_candidates/`) and generated metrics (`*_metrics.json`) are gitignored as disposable. |
| **Measured** | True native 32x32 RGBA8, generated at size — not downscaled, so §9's no-resampling rule holds. Binary alpha: 605 fully transparent / 419 fully opaque / **0 semi-transparent**. Content bbox 28x21, centred within 0.5px. |
| **Allowed use** | Scratch, proof-of-concept, pipeline proving, QC bridge input. Demonstrates that the PixelLab route can produce a clean-alpha native-32 sprite at 1 generation. |
| **Disallowed use** | Direct promotion into the approved source corpus. Must not be written into `generator conent/` or `references/` (both read-only per §2). Must not be composed by the generator, shipped in a V2 pack, or used as construction authority for any garment. |

**Known cleanup required** (both minor; **no manual redraw** — the silhouette,
nub, slouch and base band are all present and correct as generated):

1. A detached ground-shadow ellipse at rows 24-25, disconnected from the hat
   body by the near-empty row 23. Artifact of the lying-flat prompt framing used
   to escape a head-and-face result on the first attempt. Clean deletion.
2. 40 distinct colours, most of them near-duplicates (`#cd8c74` / `#cd8d74` /
   `#ce8d74` / `#cd8c73` differ by +/-1 per channel). Collapses to roughly five
   real clusters. Quantise to a small palette.

**Promotion conditions — all six, in order. Meeting some is not partial
approval; the asset stays REJECT until the last one passes:**

1. Shadow removed cleanly, with no residue on the hat body.
2. Palette cleaned up to a small, deliberate ramp.
3. Fitted to the Fashion Sense hat frame — correct dimensions, origin and
   `Position` fields. Note §5: **a float in any `Position` field makes FS reject
   the whole model silently.**
4. Directional completion — front / right / back / left. One front view is not a
   wearable hat. Per `v5/projection.py`'s rule that views add zero design
   entropy, the other three are derived, not separately generated.
5. Live in-game QC through the bridge — `tools/qc.py worn --pack <id>` on the
   real Fashion-Sense-patched renderer, judged at normal Stardew scale. Per §5,
   a pack folder created after the game started needs a **restart**, not
   `fs_reload`. Seating measured from the worn/nohat/hatonly triple.
6. Explicit approval after your visual review. §1: the worn in-game result is
   the top authority, and no passing metric substitutes for it.

Only after all six may this be re-tagged. Nothing about a generated asset
becomes canonical merely because it renders cleanly.

---

## Housekeeping noted, not done

- `memory\context/` is a directory whose name contains a literal backslash — a
  Windows path that leaked into a Linux filename. It duplicates
  `PROJECT_MEMORY.md` / `HEADWEAR_MEMORY.md` / `CLOTHING_MEMORY.md` at root.
  Decide which copy is authoritative, then delete the other. **Not touched.**
- Loose archives in root (`ref_codex.zip`, five mod archives, the Cheerful
  Pixels zip) are unpacked already; they are gitignored.
- Root has two duplicate reference sheets (`sailorstyle_female.png`,
  `SAILORSTYLE_MALE.png`, ~4 MB) and stray screenshots.
