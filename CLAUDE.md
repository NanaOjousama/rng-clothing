# CLAUDE.md — standing operating rules for RNG_clothing

Roles of the three root files. Keep them distinct.

| File | Role |
|---|---|
| **CLAUDE.md** (this) | standing operating rules, authority, workflow. Always loaded. |
| **CURRENT_STATE.md** | concise current milestone state. Read at session start. |
| **PROJECT_MEMORY.md** | broader historical/project memory. Read the parts a task needs. |

Project: procedurally *varied* Fashion Sense clothing for Stardew Valley, built
on approved source art, judged in game at normal Stardew scale.
Live stack: **Stardew Valley 1.6.15 / SMAPI 4.5.2 / Fashion Sense 7.5.0**.

---

## 1. Two authority hierarchies

Do not collapse these into one list. Ask first which kind of question it is.

### Technical behaviour — "what does the framework/game actually do?"

1. Actual in-game / runtime result
2. Official Stardew / SMAPI source and docs
3. Official Fashion Sense source / docs / examples / releases
4. Proven project tests and measurements
5. Third-party engineering references
6. Claude inference

### Visual / construction — "what should this garment look like, and what is it made of?"

1. Actual worn in-game result
2. Actual approved source artwork
3. Proven project visual / QC evidence
4. Vanilla Stardew visual corpus
5. Lospec / general pixel-art and colour theory
6. Third-party art references
7. Claude inference

Three rules hold across both:

- **A passing metric or test never overrides obviously wrong visual output.** If
  the render looks wrong, the render is right and the metric is wrong.
- **Mathematically separable pixels do not prove semantic meaning.** See §3.
- **Uncertain framework behaviour is checked against official references before
  inference, not after.** See §4.

---

## 2. Source authority — approved source art is the construction basis

For approved source packs, the **actual source pixels are the construction
authority**. Use them directly.

Do **not**:
- redraw the garment from scratch
- procedurally invent a replacement silhouette
- average or blend multiple source garments together
- reinterpret the source construction
- regenerate a "similar" version
- import rejected or experimental generator assets into V2

Generator responsibility is limited to **controlled, legal variation**:
- palette changes
- approved overlays / details
- compatible source-derived components
- rarity weighting
- deterministic composition
- player fitting / customisation

Source packs are **read-only**. Never write into `generator conent/` or
`references/`. Approval and provenance state is queryable — use it:

    python3 tools/catalog.py --help

**Nothing from V1 is canonical merely because it exists.** Every unit brought
toward V2 carries an explicit tag in `PORT_CLASSIFICATION.md`:
`KEEP` / `PORT` / `REFERENCE` / `REBUILD` / `REJECT`. Rejected and experimental
assets stay isolated unless explicitly approved.

---

## 3. Semantic verification rule

Never promote a label — **emblem, visor, crown, seam, trim, collar, cuff,
pocket, attachment** — on the strength of segmentation, enclosure, colour
grouping or pixel separability alone.

Before promotion, verify all of:

1. exact location on the source sprite
2. exact location on the worn farmer
3. corresponding structure in the side / profile views
4. back-view evidence where relevant
5. whether it is **structural or decorative**
6. positive evidence for that specific semantic label

Visual garment meaning outranks extraction heuristics. If the checks cannot be
completed, the region stays unlabelled.

---

## 4. Consult triggers — query before inferring

These are automatic. No reminder needed.

| When | Consult, first |
|---|---|
| Fashion Sense property, model, default or behaviour is uncertain | `rg <term> references/fashion-sense-official/` — `wiki-git/` (39 official pages), `src/` (authoritative C# models), `examplepack/` (45 JSONs), `property_matrix.json`, `exporter_gap.json`, `BEHAVIOR_MAP.md`; release history in `meta/releases.json` (30 releases with changelogs) |
| FS runtime behaviour, live | `BEHAVIOR_MAP.md`, then `python3 tools/qc.py get_render_state` |
| SMAPI event, API, config, i18n, Harmony, multiplayer, save data, compatibility | `rg <term> references/stardew-official/` (`wiki/`, `smapi/docs/`, `smapi/src/`) |
| Vanilla class, menu, controller snapping, tailoring internals | `references/stardew-official/assembly/stardew_index.json` — metadata index of the installed 1.6.15 assembly (1093 types). Outranks any wiki page. Rebuild: `dotnet run --project tools/AssemblyIndex`. |
| A colour / palette / contrast decision | `python3 tools/palette.py …` against real source art. **Its checks are advisory and carry a measured error bar**: approved source art trips value-order on 21% of items and role-collapse on 30% (`tools/palette_calibration.json`), so a flag is a question, never a verdict. Treat role-collapse as meaningful for a *generated* palette (a wasted slot), not as a defect in source-derived work. Lospec never outranks source art or the in-game result. |
| Any claim about how something *looks* | a QC Bridge capture. Never inference. See §5. |
| Which source garment, family, variant, author, provenance, approval | `python3 tools/catalog.py …` — `approval` for what may be composed at all; REFERENCE-ONLY variants must never be composed |
| In-game pixel-editor / menu engineering | `references/cheerful-pixels/STUDY.md` — engineering reference only, see §8 |

Do not answer from memory when a local reference covers it. `rg` over these
trees is cheap and allowlisted; guessing is what has cost this project time.

---

## 5. Visual QC is the top authority — use the bridge

The QC Bridge runs the real game with the real Fashion-Sense-patched renderer.
Client: `tools/qc.py`. The game must be running with a save loaded.

    python3 tools/qc.py ping
    python3 tools/qc.py refresh --pack <id> --expect <n>   # reload + verify
    python3 tools/qc.py worn --pack <id>                   # 4-direction worn set
    python3 tools/qc.py smapi-log --errors
    python3 tools/qc.py menu-probe

Sequencing traps that have already cost capture runs — the CLI now enforces
them, do not bypass with raw `send`:

- Fashion Sense loads pack textures **once at startup**. A rebuilt pack needs
  `fs_reload`, or captures silently show stale art.
- A pack **folder created after the game started** is not registered with SMAPI.
  FS lists its appearance names but draws nothing — indistinguishable from
  broken art. Restart the game; `fs_reload` cannot fix it.
- `world_ready` passing does not mean textures reloaded.
- A float in any `Position` field makes FS reject the whole model **silently**.
- Seating is measured from the worn/nohat/hatonly capture triple, never from an
  isolated sprite.

---

## 6. Vanilla-feel requirement (player-facing)

Final player-facing UX must feel like a natural Stardew extension.

Prefer: sewing machine / tailoring · dresser / wardrobe · shops and NPCs ·
vanilla-style menus and sounds · controller focus and snapping.

Final features must **not** depend on: the Fashion Sense Hand Mirror ·
dev-only tools · arbitrary debug keybinds · mouse-only UI · anything that feels
like an external editor.

The Hand Mirror, QC Bridge and debug commands remain **development tools**.
That carve-out does not extend to shipped features.

---

## 7. Steam Deck / controller requirement

Player-facing features are designed for Steam Deck and gamepad from the start,
plus keyboard/mouse. Controller support is never bolted on later. Use proper
focus/snapping (`snapToDefaultClickableComponent`, populated
`allClickableComponents`, working neighbour IDs) and standard Stardew
interaction patterns.

---

## 8. Cheerful Pixels — engineering reference only

From `references/cheerful-pixels/STUDY.md`. Adaptable **concepts**: deferred
menu opening (set a flag in the input event, open on the next
`OnUpdateTicked`), a single `ScreenToCanvas` coordinate contract, bounded
snapshot undo, dirty-region texture updates, readability preview, symmetry,
disciplined layout/hit-testing.

Do **not** copy: mouse-only design · free HSV colour selection · soft/blended
brushes · full studio UI style · unrestricted canvas · loose PNG-export
workflow.

---

## 9. Code constraints

- **The generator is dependency-free and stays that way.**
  `generator/png_utils.py` builds RGBA8 PNGs from `zlib` + `struct`; nothing
  under `generator/` or `tools/validate_*.py` imports PIL, NumPy or SciPy, and
  every validator runs on a bare `python3`. Keep it so.
- `.venv` exists for **analysis** tools only (`tools/palette.py`). Activate with
  `source tools/env.sh`. Never make a generation or validation path need it.
- No bilinear / bicubic / Lanczos / smoothing / anti-aliasing. Sprites are
  constructed on the target format's logical pixel grid — never drawn large and
  shrunk.
- Do not modify TFWR or add runtime dependencies to it.
- Distinguish **confirmed / likely / untested** capabilities explicitly.

---

## 10. Session and context hygiene

This project has previously become very expensive through long-running
contexts. **The repo carries project state; the conversation is not the memory.**

At each milestone, in order:

1. update `CURRENT_STATE.md` (milestone · proven · not yet proven · locked
   decisions · known failures · next test · do not redo)
2. update the relevant memory/docs
3. run the tests
4. commit when appropriate
5. recommend `/compact` before continuing if context has grown large

Do not push to a remote without asking. There is currently no remote — see
`CURRENT_STATE.md` for the deferred PC ↔ Steam Deck sync decision.
