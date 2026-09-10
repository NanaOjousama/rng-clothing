"""Build a Fashion Sense validation pack from ACCEPTED BRIMMED_HAT rolls.

Read-only with respect to generation: this imports the pipeline and writes
files.  It does not alter any generator, AA, AG, projection or QC behaviour.

Pack format is taken from the framework's own example pack
(FashionSense/Examples/[FS] Example Pack/Hats/HatTemplate), which is the
authoritative shape of a hat content pack:

    Hats/<Name>/hat.png     20x80, four directions stacked
    Hats/<Name>/hat.json    StartingPosition Y = 0 / 20 / 40 / 60
                            HatSize 20x20, HeadPosition X = 0 (computed),
                            DisableGrayscale true, HideHair per Architecture

Selection is a deterministic greedy set cover over the coverage axes, then
PINNED so the same garments can be compared pass over pass — the Sailor pack
silently swapped members between rounds before it was pinned, which defeats the
only thing a validation pack is for.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from v5 import quality                                     # noqa: E402
from v5.grammar import ATLAS_ORDER, luminance              # noqa: E402
from v5.library import brimmed_hat, brimless_hat           # noqa: E402  (registers contracts)
from v5.library.brimmed_hat import hair_policy_for         # noqa: E402
from v5.pipeline import generate_batch                     # noqa: E402
from v5.pngio import blank_image, blit, nearest_scale, write_rgba_png, draw_text  # noqa: E402
from v5.projection import atlas, fs_hat_metadata           # noqa: E402

PACK = Path("test-packs/fashionsense/RNG-Clothing-V5-Hat-Validation")
UNIQUE_ID = "RNGClothing.FashionSense.V5HatValidation"
BATCH = range(500)
TARGET = 24

# Pinned after the first set-cover run.  Empty the tuple to re-derive.
# The original 18 stay exactly as they were, so every hat reviewed in an
# earlier pass can be compared directly against its own previous screenshot.
# Phase 3 APPENDS five, one per capability that did not exist before and can
# only be judged in game: COLUMN + BRIM_WINGS + ROLLED (15), TIP_DROOP (19),
# VISOR (20), TAIL (22), ROLLED brim on its own (90).  Seed 11 already covers
# FAST and CUFF.
PINNED_SEEDS: tuple = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16,
                       19, 20, 22, 71, 90, 126, 131, 473)


def axes(g) -> dict:
    p = g.spec.parameters
    body = [luminance(c) for c in g.raster["front"].values()]
    med = sorted(body)[len(body) // 2] if body else 0
    return {
        "architecture": g.spec.architecture,
        "crown_profile": p["crown_profile"],
        "brim_profile": p.get("brim_profile", "-"),
        "protrusion": p.get("protrusion", "NONE"),
        "asymmetry": p.get("asymmetry", "NONE"),
        "directional": p.get("directional", "NONE"),
        "cuff": p.get("cuff", "NONE"),
        "hair": hair_policy_for(g.construction),
        "value": "light" if med >= 128 else "dark",
        "palette": g.spec.color_architecture,
        "material": g.spec.material,
    }


REQUIRED = ("architecture", "crown_profile", "protrusion", "asymmetry",
            "directional", "cuff", "hair", "value")
NICE = ("brim_profile", "palette", "material")


def select(garments) -> list:
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
            return (len({(k, a[k]) for k in REQUIRED} - covered),
                    len({(k, a[k]) for k in NICE} - covered),
                    -g.spec.seed)
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


def folder_name(g) -> str:
    p = g.spec.parameters
    kind = "Brim" if g.spec.architecture == "BRIMMED_HAT" else "Cap"
    return (f"V5Hat{g.spec.seed:03d}{kind}"
            f"{p['crown_profile'].title().replace('_', '')}")


def build() -> dict:
    batch = generate_batch(BATCH, slot="HEAD")
    chosen = select(batch)
    if PACK.exists():
        for p in sorted(PACK.rglob("*"), reverse=True):
            p.unlink() if p.is_file() else p.rmdir()
    (PACK / "Hats").mkdir(parents=True, exist_ok=True)

    (PACK / "manifest.json").write_text(json.dumps({
        "Name": "RNG Clothing V5 Hat Validation",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "In-game validation set for BRIMMED_HAT. Native 20x20, "
                       "accepted rolls only, seed-traceable.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense",
                           "MinimumVersion": "7.5.0"},
    }, indent=2))

    trace = []
    for g in chosen:
        name = folder_name(g)
        d = PACK / "Hats" / name
        d.mkdir(parents=True, exist_ok=True)
        # native 20x80 — Fashion Sense scales at draw time; do NOT pre-scale
        write_rgba_png(d / "hat.png", atlas(g.projection, None))
        policy = hair_policy_for(g.construction)
        p = g.spec.parameters
        hat = {
            "Name": f"V5 Hat {g.spec.seed:03d} "
                    f"({p['crown_profile'].title().replace('_', ' ')})",
            "Tags": ["RNG Clothing", "V5 Hat Validation", f"seed {g.spec.seed}",
                     g.spec.architecture, p["crown_profile"],
                     p.get("brim_profile", "-"), p.get("protrusion", "NONE"),
                     p.get("asymmetry", "NONE"),
                     p.get("directional", "NONE"), p.get("cuff", "NONE"), policy,
                     g.spec.color_architecture],
        }
        hat.update(fs_hat_metadata(g.spec, policy == "HIDE"))
        (d / "hat.json").write_text(json.dumps(hat, indent=2))
        trace.append({
            "folder": name,
            "seed": g.spec.seed,
            "coverage": axes(g),
            "hair_policy": policy,
            "verdict": {
                "classification": g.verdict.classification,
                "colors": g.verdict.legibility.get("colors"),
                "warnings": list(g.verdict.warnings),
            },
            "spec": g.spec.as_dict(),
        })

    (PACK / "TRACEABILITY.json").write_text(json.dumps({
        "pack_unique_id": UNIQUE_ID,
        "generated_from": {"seeds": [BATCH.start, BATCH.stop], "slot": "HEAD"},
        "garments": trace,
    }, indent=2, default=str))
    return {"chosen": chosen, "trace": trace}


def docs(trace: list) -> None:
    rows = []
    for t in trace:
        c = t["coverage"]
        rows.append(f"| `{t['folder']}` | {t['seed']} | "
                    f"{c['architecture'].replace('_HAT', '')} | {c['crown_profile']} | "
                    f"{c['brim_profile']} | {c['protrusion']} | {c['asymmetry']} | "
                    f"{c['directional']} | {c['cuff']} | {c['hair']} | {c['value']} |")
    (PACK / "README.md").write_text(f"""# RNG Clothing — V5 Hat Validation

{len(trace)} hats for **in-game validation of BRIMMED_HAT**. Not a content release.

## Install

Drop this folder into `Mods/`. Requires Fashion Sense 7.5.0+. The hats appear
in the Fashion Sense menu tagged `V5 Hat Validation`.

## Format

Native **20×20**, four directions stacked in one 20×80 sheet at
Y = 0 / 20 / 40 / 60 — the vanilla `hats.png` frame size, so the corpus this
family was derived from is directly comparable.

`HeadPosition.X` is **0**, computed rather than authored: Fashion Sense centres
a hat frame on a 20-vanilla-pixel head box, so `X = (w - 20*(4/Scale)) / 2`,
which is exactly zero at this size. Verified against 746 shipping FS hat models.

`HideHair` is the Architecture's declared hair policy. Fashion Sense gives a
custom hat no other lever over hair — it never applies the vanilla
per-hairstyle offset — so the policy is binary by construction.

## What to look for

1. **Does it read as a hat at a glance, in motion, at game zoom?** That is the
   question the offline corpus checks cannot answer.
2. **Placement on the head.** The mass should register to the head, not float
   above it or sit down over the eyes. This is the thing no shirt-style metric
   can see: a hat one row too high passes every occupancy and colour check.
3. **Hair.** Compare a `HIDE` hat against a `PRESERVE` one. Does the preserved
   hair read correctly around the crown, and does the hidden one leave a clean
   head?
4. **Turning.** Front / side / back should describe the same hat. The crown is
   anchored to identical columns in all views and the side brim is symmetric
   about it, so a disagreement is a bug.
5. **The asymmetry motifs** — `TIP_LEAN`, `CROWN_DENT`, `BRIM_FLICK`. Do they
   read as authored character, or as damage?
6. **Hat vs hairstyles you actually wear**, since we cannot compensate per
   hairstyle.
7. **The directional pieces** — seed 20 carries a `VISOR` and seed 22 a
   `TAIL`. Both exist in the LEFT and RIGHT frames only, by design: a cap
   facing you has its visor pointing at you. The thing to watch is the turn.
   The base hat must not appear to move, shift or resize as the Farmer rotates
   — only the extra piece should appear and disappear. Any perceived movement
   of the crown itself is a bug, and a serious one.
8. **The back frame.** It is now derived from the front rather than authored:
   the same hat one row lower with its lowest row repeated. Does the back read
   as the same hat, sitting correctly on the back of the head?
9. **Seed 15** is the first wide-brimmed hat with wings on the brim
   (`COLUMN` + `BRIM_WINGS` + `ROLLED`) — a shape family that did not exist
   before. **Seed 473** is the first hat to carry
   `BRIM_WINGS` — a motif that existed but was unreachable until this pass, so
   it has never been seen in game. **Seed 11** is the first cap with a
   turned-back cuff.

## Contents

| Folder | Seed | Arch | Crown | Brim | Protrusion | Asymmetry | Directional | Cuff | Hair | Value |
|---|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}

## Reporting

Note the seed from the hat's tag. `TRACEABILITY.json` maps it to the exact
resolved specification.
""")


def contact_sheet(chosen) -> None:
    S = 6
    tiles = []
    for g in chosen:
        t = blank_image(20 * S * 3 + 16, 20 * S, (118, 118, 126, 255))
        for i, v in enumerate(("front", "side", "back")):
            blit(t, nearest_scale([[g.raster[v].get((x, y), (0, 0, 0, 0))
                                    for x in range(20)] for y in range(20)], S),
                 i * (20 * S + 8), 0)
        p = g.spec.parameters
        kind = "B" if g.spec.architecture == "BRIMMED_HAT" else "C"
        pr = p.get("protrusion", "NONE")
        tiles.append((f"{g.spec.seed:03d}{kind} {p['crown_profile'][:5]}"
                      f"{'' if pr == 'NONE' else ' ' + pr[:8]}", t))
    tw, th = len(tiles[0][1][0]), len(tiles[0][1])
    cols = 4
    rn = (len(tiles) + cols - 1) // cols
    out = blank_image(cols * (tw + 14) + 14, rn * (th + 20) + 30, (56, 56, 62, 255))
    draw_text(out, "V5 HAT VALIDATION PACK   front / side / back", 12, 6)
    for i, (n, t) in enumerate(tiles):
        x = 12 + (i % cols) * (tw + 14)
        y = 24 + (i // cols) * (th + 20)
        blit(out, t, x, y)
        draw_text(out, n, x, y + th + 3)
    write_rgba_png(PACK / "pack_contents.png", out)


if __name__ == "__main__":
    result = build()
    contact_sheet(result["chosen"])
    docs(result["trace"])
    print(f"{len(result['chosen'])} hats -> {PACK}")
    for t in result["trace"]:
        c = t["coverage"]
        print(f"  {t['folder']:<26} seed {t['seed']:<4} {c['crown_profile']:<10} "
              f"{c['protrusion']:<10} {c['asymmetry']:<11} "
              f"{c['directional']:<6} {c['cuff']:<5} {c['hair']:<8} "
              f"{c['value']}")
    print("\nPINNED_SEEDS =", tuple(t["seed"] for t in result["trace"]))
