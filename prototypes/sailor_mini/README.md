# Mini Sailor Generator — isolated prototype

A standalone proof of concept for exactly one garment family:

```
FAMILY        SAILOR_TOP
ARCHITECTURE  CLASSIC_SQUARE_FLAP
```

This is **not** the production generator, not a multi-family system, and not a
rewrite of anything. It lives entirely under `prototypes/sailor_mini/` and
imports nothing from `generator/`, `rngc/` or `tools/` — a test asserts that.
The PNG helpers were copied in rather than imported.

## What it proves

1. structured variables resolve from a seed,
2. dependency rules reject bad combinations before rendering and reroll internally,
3. a resolved garment spec is the contract between design and rendering,
4. that spec translates into **architecture** decisions and then separately into
   **art grammar** decisions,
5. front / side / back render consistently from one construction,
6. twelve variants come out visibly distinct rather than recoloured.

## Run it

```bash
cd prototypes/sailor_mini
python3 -B -m sailor_mini.cli build          # writes out/, about 1 second
python3 -B -m unittest discover -s tests     # 14 invariant tests
```

Previews composite the installed Farmer if Stardew is present. Override the path
with `STARDEW_CONTENT=/path/to/Content (unpacked)`. Without it the sprites still
render, on a flat panel.

## Inspect in this order

| # | File | What to look for |
|---|---|---|
| 1 | `out/sheets/SAILOR_GAMEPLAY_12.png` | Do all twelve read as sailor tops at gameplay size? |
| 2 | `out/sheets/SAILOR_ANATOMY.png` | The construction argument. Yellow is a free edge, red is occlusion. The flap's **top edge has no yellow** — it is attached. |
| 3 | `out/sheets/SAILOR_CONTACT_12.png` | Isolated 16x16 at 5x, all four directions |
| 4 | `out/sheets/SAILOR_PAIR_rear_flap_depth.png` | Controlled pair A: only the flap depth changes |
| 5 | `out/sheets/SAILOR_PAIR_trim_style.png` | Controlled pair B: only the trim count changes |
| 6 | `out/batch.json` | Resolved specs, the systems that painted each garment, and the dependency probe |
| 7 | `ARCHITECTURE.md` | The schema and the stage contract |
| 8 | `EVALUATION.md` | Findings, weaknesses, and the recommendation |

## Pipeline

```
seed
 └─ resolve.py       weighted pick per variable
     └─ rules.py     dependency filter; reject and reroll internally
         └─ ResolvedSpec           <- the contract
             └─ architecture.py    WHERE fabric is, and which edges are FREE vs ATTACHED
                 └─ artgrammar.py  HOW that reads: outline policy, occlusion, light, trim
                     └─ render.py  ops -> role/slot/system grids -> RGBA, 4 directions
                         └─ preview.py / batch.json
```

`left` is `mirror(side)`; the prototype authors no explicit left data.

## Files

| File | Lines | Role |
|---|---:|---|
| `vocabulary.py` | 48 | the eight variables, their weights, and their numeric consequences |
| `rules.py` | 61 | seven dependency rules as data, each with a stated reason |
| `resolve.py` | 128 | seed to ResolvedSpec, with rejection log |
| `palette.py` | 81 | six colour families, four colour architectures, literal colours only |
| `body.py` | 49 | the torso silhouette and its hand-authored shading |
| `architecture.py` | 237 | construction geometry and edge classification |
| `artgrammar.py` | 170 | six named art-grammar rules |
| `render.py` | 89 | op execution and colourisation |
| `batch.py` | 84 | the twelve controlled requests and the two pairs |
| `preview.py` | 171 | Farmer composites and sheets |
| `cli.py` | 109 | `build`, plus the dependency probe |
| `pngio.py` | 149 | copied PNG helpers |
| `tests/test_prototype.py` | 145 | 14 invariants |

## Render target

Fashion Sense assumptions are explicit and match the project's confirmed
contract: 16x16 logical frames, a 16x64 atlas in front/right/left/back order,
`Scale 2`, `BodyPosition (0,32)`, binary alpha, nearest-neighbour only, native
Farmer sleeves. The prototype writes `out/frames/<id>/atlas.png` in that layout
but **does not** build a content pack; it renders isolated previews only.
