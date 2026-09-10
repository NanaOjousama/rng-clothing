"""Build a Fashion Sense validation pack from ACCEPTED Sailor rolls.

Read-only with respect to generation: this imports the pipeline and writes
files.  It does not alter any generator, AA, AG, projection or QC behaviour.

Pack format is taken from the shipping third-party reference pack
(references/[FS]SubabyTvanZ's Sailor Suit Set), which is the authoritative
example of a native 8x8 Fashion Sense shirt:

    Shirts/<Name>/shirt.png    8x32, four frames stacked
    Shirts/<Name>/shirt.json   StartingPosition Y = 0 / 8 / 16 / 24
                               ShirtSize 8x8, BodyPosition 0,0,
                               DisableGrayscale true, no Scale field

Selection is a deterministic greedy set-cover over the coverage axes, so the
same batch always yields the same pack.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from v5 import quality                                     # noqa: E402
from v5.grammar import ATLAS_ORDER, luminance              # noqa: E402
from v5.library import sailor_top                          # noqa: E402  (registers contracts)
from v5.pipeline import generate_batch                     # noqa: E402
from v5.pngio import blank_image, blit, nearest_scale, write_rgba_png, draw_text  # noqa: E402
from v5.projection import atlas                            # noqa: E402

PACK = Path("test-packs/fashionsense/RNG-Clothing-V5-Sailor-Validation")
UNIQUE_ID = "RNGClothing.FashionSense.V5SailorValidation"
BATCH = range(96)
TARGET = 14


# ---------------------------------------------------------------------------
# coverage axes
# ---------------------------------------------------------------------------

def axes(g) -> dict:
    p = g.spec.parameters
    body = [luminance(g.raster["front"][c]) for c, pc in g.art.paint["front"].items()
            if pc.role == "body" and c in g.raster["front"]]
    body_med = sorted(body)[len(body) // 2] if body else 0
    return {
        "architecture": g.spec.architecture,
        "repair": "repaired" if any(n.startswith("retention:") for n in g.art.notes)
                  else "untouched",
        "value": "light_ground" if body_med >= 128 else "dark_ground",
        "tie": g.spec.layers.get("tie_style", "NONE"),
        "tie_present": "tie" if "tie_style" in g.spec.layers else "no_tie",
        "flap_edge": p["flap_edge"],
        "flap_depth": f"flap{p['rear_flap_depth']}",
        "sleeve_cap": p["sleeve_cap"],
        "palette": g.spec.color_architecture,
    }


# Axes the pack must span.  Every value of every listed axis should appear.
REQUIRED = ("architecture", "repair", "value", "tie_present",
            "flap_edge", "flap_depth", "sleeve_cap")
NICE = ("tie", "palette")


# The pack's membership is PINNED to the seeds chosen for validation pass 01.
# Greedy set cover re-derives membership from whatever the coverage axes happen
# to be, so an authored-geometry fix silently swapped garments in and out
# between passes — which defeats the pack's only job, letting the same shirt be
# looked at again after a change.  Selection still runs when the pin is empty.
#
# 13 stays in the pack though it now fails QC (CLASSIC on LIGHT_BODY_DARK_COLLAR
# whose dickey-vs-collar separation collapses).  It is carried so the reported
# garment can still be inspected; its verdict is recorded in TRACEABILITY.json
# and it is NOT evidence the gate changed.
PINNED_SEEDS = (0, 1, 2, 3, 4, 11, 13, 14, 17, 25, 27, 40, 45, 83)


def select(garments) -> list:
    """Greedy set cover: repeatedly take the roll adding the most new coverage."""
    if PINNED_SEEDS:
        byseed = {g.spec.seed: g for g in garments}
        missing = [s for s in PINNED_SEEDS if s not in byseed]
        if missing:
            raise SystemExit(f"pinned seeds not in batch: {missing}")
        return [byseed[s] for s in PINNED_SEEDS]
    pool = [g for g in garments if g.verdict.classification == quality.ACCEPT]
    wanted = set()
    for g in pool:
        a = axes(g)
        wanted |= {(k, a[k]) for k in REQUIRED}
    chosen, covered = [], set()
    while pool and (wanted - covered or len(chosen) < TARGET):
        def gain(g):
            a = axes(g)
            req = len({(k, a[k]) for k in REQUIRED} - covered)
            nice = len({(k, a[k]) for k in NICE} - covered)
            return (req, nice, -g.spec.seed)          # deterministic tie-break
        best = max(pool, key=gain)
        if gain(best)[0] == 0 and gain(best)[1] == 0 and wanted <= covered:
            if len(chosen) >= TARGET:
                break
        pool.remove(best)
        chosen.append(best)
        a = axes(best)
        covered |= {(k, a[k]) for k in REQUIRED + NICE}
        if len(chosen) >= TARGET and wanted <= covered:
            break
    return sorted(chosen, key=lambda g: g.spec.seed)


# ---------------------------------------------------------------------------
# emit
# ---------------------------------------------------------------------------

def folder_name(g) -> str:
    kind = "Middy" if g.spec.architecture == "MIDDY_YOKE" else "Classic"
    return f"V5Sailor{g.spec.seed:03d}{kind}"


def shirt_json(g) -> dict:
    pal = g.spec.palette
    sleeves = [list(pal.color("body", s))[:3]
               for s in ("shadow", "base", "light") if s in pal.steps]
    a = axes(g)
    common = {
        "DisableGrayscale": True,
        "HideSleeves": False,
        "SleeveColors": sleeves,
        "BodyPosition": {"X": 0, "Y": 0},
        "ShirtSize": {"Width": g.spec.envelope.width, "Length": g.spec.envelope.height},
    }
    out = {
        "Name": f"V5 Sailor {g.spec.seed:03d} "
                f"({'Middy' if g.spec.architecture == 'MIDDY_YOKE' else 'Classic'})",
        # Tags carry the trace into the in-game Fashion Sense menu, so a garment
        # that misbehaves can be named without leaving the game.
        "Tags": ["RNG Clothing", "V5 Sailor Validation",
                 f"seed {g.spec.seed}", g.spec.architecture,
                 g.spec.color_architecture, a["value"], a["repair"],
                 a["tie_present"], a["flap_edge"], a["sleeve_cap"]],
    }
    for i, direction in enumerate(ATLAS_ORDER):
        key = {"front": "FrontShirt", "right": "RightShirt",
               "left": "LeftShirt", "back": "BackShirt"}[direction]
        out[key] = dict(common, StartingPosition={"X": 0, "Y": i * g.spec.envelope.height})
    return out


def build() -> dict:
    batch = generate_batch(BATCH)
    chosen = select(batch)
    if PACK.exists():
        for p in sorted(PACK.rglob("*"), reverse=True):
            p.unlink() if p.is_file() else p.rmdir()
    (PACK / "Shirts").mkdir(parents=True, exist_ok=True)

    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Clothing V5 Sailor Validation",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "In-game validation set for the locked V5 Sailor pool. "
                       "Native 8x8, accepted rolls only, seed-traceable.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"},
    }, indent=2))

    trace = []
    for g in chosen:
        name = folder_name(g)
        d = PACK / "Shirts" / name
        d.mkdir(parents=True, exist_ok=True)
        # native 8x32 — Fashion Sense scales at draw time, exactly as the
        # reference pack does; do NOT pre-scale the sheet
        write_rgba_png(d / "shirt.png", atlas(g.projection, None))
        (d / "shirt.json").write_text(json.dumps(shirt_json(g), indent=2))
        trace.append({
            "folder": name,
            "seed": g.spec.seed,
            "coverage": axes(g),
            "verdict": {
                "classification": g.verdict.classification,
                "identity": {k: round(v, 1) for k, v in g.verdict.identity.items()},
                "identity_composite": g.verdict.legibility.get("identity_composite"),
                "min_retention": g.verdict.legibility.get("min_retention"),
                "colors": g.verdict.legibility["colors"],
                "warnings": list(g.verdict.warnings),
            },
            "aa_notes": g.art.notes,
            "spec": g.spec.as_dict(),
        })

    (PACK / "TRACEABILITY.json").write_text(json.dumps({
        "pack_unique_id": UNIQUE_ID,
        "generated_from": {"seeds": [BATCH.start, BATCH.stop], "module": "v5"},
        "qc": "locked — see docs/decisions/SAILOR_QC_LOCK.md",
        "garments": trace,
    }, indent=2, default=str))
    return {"chosen": chosen, "trace": trace}


def contact_sheet(chosen) -> None:
    S = 14
    tiles = []
    for g in chosen:
        t = blank_image(8 * S * 3 + 12, 8 * S, (208, 206, 202, 255))
        for i, v in enumerate(("front", "side", "back")):
            blit(t, nearest_scale([[g.raster[v].get((x, y), (0, 0, 0, 0))
                                    for x in range(8)] for y in range(8)], S),
                 i * (8 * S + 6), 0)
        tiles.append((f"{g.spec.seed:03d} "
                      f"{'M' if g.spec.architecture == 'MIDDY_YOKE' else 'C'} "
                      f"{axes(g)['tie'][:5]}", t))
    tw, th = len(tiles[0][1][0]), len(tiles[0][1])
    cols = 4
    rn = (len(tiles) + cols - 1) // cols
    out = blank_image(cols * (tw + 12) + 12, rn * (th + 16) + 26, (243, 241, 237, 255))
    draw_text(out, "V5 SAILOR VALIDATION PACK   FRONT / SIDE / BACK", 12, 4)
    for i, (n, t) in enumerate(tiles):
        x = 12 + (i % cols) * (tw + 12)
        y = 20 + (i // cols) * (th + 16)
        blit(out, t, x, y)
        draw_text(out, n, x, y + th + 2)
    write_rgba_png(PACK / "pack_contents.png", out)


# ---------------------------------------------------------------------------
# human-readable docs
#
# build() wipes the pack directory, so these MUST be emitted here rather than
# hand-written into it: a rebuild silently dropped them once already.  Both are
# derived from `trace`, so they cannot drift from the sheets beside them.
# ---------------------------------------------------------------------------

def docs(trace: list) -> None:
    repaired = sorted(t["seed"] for t in trace if t["coverage"]["repair"] == "repaired")
    (PACK / "README.md").write_text(f"""# RNG Clothing \u2014 V5 Sailor Validation

A {len(trace)}-garment Fashion Sense pack for **in-game validation of the locked
V5 Sailor pool**. Not a content release.

## Install

Drop this folder into `Mods/`. Requires Fashion Sense 7.5.0+. The shirts appear
in the Fashion Sense menu tagged `V5 Sailor Validation`.

## Format

Native **8\u00d78**, four frames stacked in one 8\u00d732 sheet
(front / right / left / back at Y = 0 / 8 / 16 / 24), `DisableGrayscale: true`,
no pre-scaling \u2014 matching the shipping reference pack
`references/[FS]SubabyTvanZ's Sailor Suit Set`, which is the authoritative
example of a native 8\u00d78 FS shirt.

## Round 03 \u2014 what changed

Carries the fixes from `docs/decisions/SAILOR_INGAME_VALIDATION_02.md`. Four
shared authored motifs, no QC/palette/generator changes:

1. **strap silhouettes** \u2014 split neck opening closed, notch depth 3\u21922,
   back armpit bite closed
2. **side profile** \u2014 row-1 gap closed, removing the enclosed cell that
   made the chest read as a protruding box
3. **front shoulder corners** \u2014 returned to the body; identity trim never
   occupies them, and the articulation there is now a shadow, not a highlight
4. **rear flap hem** \u2014 tapered inboard so it ends before the arm columns

Membership is now **pinned** to these 14 seeds so the same garments can be
compared pass over pass.

Re-check the reported seeds first:

| seed | was reported as |
|---|---|
| 000 | side profile blocky / protruding |
| 001 | split neck hole under the chin |
| 002 | back armpit / side hole |
| 003 | front collar edge lying on the arm |
| 004 | white seam between sleeve and arm |
| 011 | back armpit / side hole |
| 013 | rear flap a flat horizontal band |
| 014 | front collar flat, weak V |
| 025 | rear striped flap blocky |
| 040 | collar too wide/flat; back flap a bar |
| 045 | flap reads as bars through the arms |
| 083 | front insert a box under the chin |

**Seed 013 now fails QC** (`IDENTITY_TOO_WEAK`, composite 0.89) and is carried
anyway so it can still be inspected. It is CLASSIC on `LIGHT_BODY_DARK_COLLAR`,
where dickey-vs-collar separation collapses. Its verdict is in
`TRACEABILITY.json`.

## What to look for

1. **Does it read as a sailor top at a glance, in motion, at game zoom?**
   That is the question the offline QC cannot answer.
2. **The {len(repaired)} `repaired` garments** (seeds {", ".join(str(s) for s in repaired)})
   had detail held off an identity piece during composition. If any looks wrong,
   the retention constraint is the first suspect.
3. **Frame continuity while walking** \u2014 front/side/back describe the same
   garment; projection carries zero design entropy, so a disagreement is a bug.
4. **Shoulder coverage** \u2014 no skin showing at the neck or shoulder line.
   Held as borderline from round 01; confirm only if it repeats.
5. **Sleeve colours** against the Farmer's arm sprite.

## Reporting

Note the seed from the garment's tag. `TRACEABILITY.md` and `TRACEABILITY.json`
map it to the exact resolved specification.

Per `docs/decisions/SAILOR_QC_LOCK.md`, QC changes only on a **repeatable**
in-game failure pattern.
""")

    rows = []
    for t in trace:
        c, v = t["coverage"], t["verdict"]
        pal = c["palette"].replace("_", " ").title()
        rows.append(
            f"| `{t['folder']}` | {t['seed']} | "
            f"{'MIDDY' if c['architecture'] == 'MIDDY_YOKE' else 'CLASSIC'} | "
            f"{pal} | {c['value'].split('_')[0]} | {c['repair']} | {c['tie']} | "
            f"{c['flap_edge'].lower()}/{c['flap_depth'][-1]} | "
            f"{c['sleeve_cap'].lower()} | {v['colors']} |")

    (PACK / "TRACEABILITY.md").write_text(
        "# V5 Sailor validation pack \u2014 traceability\n\n"
        "Every garment here is an **accepted** roll from seeds "
        f"{BATCH.start}\u2013{BATCH.stop - 1} of the locked Sailor pool.\n"
        "Generation logic was not modified to produce this pack.\n\n"
        "Full machine-readable records \u2014 resolved spec, roll context, complexity\n"
        "ledger, AA notes, identity measurements \u2014 are in `TRACEABILITY.json`,\n"
        "keyed by folder.\n\n"
        "## Tracing an in-game problem\n\n"
        "Each garment's Fashion Sense **tags** carry its seed, architecture and\n"
        "palette, so a misbehaving shirt can be identified from the in-game menu\n"
        "without leaving the game. To reproduce it exactly:\n\n"
        "```bash\n"
        "python3 -c \"import sys;sys.path.insert(0,'.');import v5.library.sailor_top;\\\n"
        "from v5.pipeline import generate;g=generate(SEED);print(g.spec.as_dict())\"\n"
        "```\n\n"
        "## Contents\n\n"
        "| Folder | Seed | Arch | Palette | Ground | QC | Tie | Flap edge/depth |"
        " Cuff | Colours |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        + "\n".join(rows) + "\n")


if __name__ == "__main__":
    result = build()
    contact_sheet(result["chosen"])
    docs(result["trace"])
    print(f"{len(result['chosen'])} garments -> {PACK}")
    for t in result["trace"]:
        c = t["coverage"]
        print(f"  {t['folder']:<24} seed {t['seed']:<3} {c['architecture'][:7]:<7} "
              f"{c['value']:<12} {c['repair']:<9} {c['tie']:<13} "
              f"{c['flap_edge']:<7} {c['flap_depth']} {c['sleeve_cap']}")
