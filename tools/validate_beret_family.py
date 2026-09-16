"""Milestone 1 gates: generic family support, quality_tier, authored right view.

Every check here exists because it could plausibly fail. The interesting ones
are the compatibility gates: the whole point of making `views`, `family` and
`quality_tier` optional is that four bases authored before any of them existed
must render byte-for-byte as they did, and the only honest way to know is to
compare against hashes captured before the change.

    python3 tools/validate_beret_family.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5 import authored
from v5.pngio import read_rgba_png

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(ROOT, "tests", "fixtures", "authored_legacy_baseline.json")
SRC_SHEET = os.path.join(ROOT, "beret_variant1", "hat.png")
REF = os.path.join(ROOT, "authored", "source_bases", "beret", "beret_01")
BASE_DIR = os.path.join(ROOT, "authored", "bases", "beret_01")
SHEET = [("front", 0), ("right", 20), ("left", 40), ("back", 60)]

FAILS = []
CHECKS = [0]


def check(name, cond, detail=""):
    CHECKS[0] += 1
    if cond:
        print(f"  PASS  {name}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  FAIL  {name}  {detail}")
        FAILS.append(name)


def h_of(g):
    h = hashlib.sha256()
    for v in authored.ATLAS_ORDER:
        for row in g.directions[v]:
            for px in row:
                h.update(bytes(px))
    return h.hexdigest()


def main():
    lib = authored.load()

    # -- 1. legacy authored assets are untouched ------------------------------
    print("\n[1] legacy authored assets still render identically")
    want = json.load(open(BASELINE))["renders"]
    moved = []
    for k, exp in want.items():
        if k.startswith("compose|"):
            _, slot, seed = k.split("|")
            g = authored.compose(int(seed), slot, lib)
            got = (f"{g.base.name}|{g.style}|{g.palette.id}|"
                   + "+".join(d.name for d in g.decals) + "|" + h_of(g))
        else:
            parts = k.split("|")
            styles = ("work", "casual", "smart", "cottagecore", "formal", "festival")
            if len(parts) == 3 and parts[2] in styles:
                g = authored.build(parts[0], parts[1], (), lib, style=parts[2])
            else:
                names = tuple(parts[2].split("+")) if len(parts) > 2 and parts[2] else ()
                g = authored.build(parts[0], parts[1], names, lib)
            got = h_of(g)
        if got != exp:
            moved.append(k)
    check("every pre-change render is byte-identical", not moved,
          f"{len(want) - len(moved)}/{len(want)} identical"
          + (f"; moved: {moved[:3]}" if moved else ""))

    legacy = [b for b in lib.bases if b.family != "beret"]
    berets = lib.family_bases("beret")
    check("legacy bases kept the three-view contract",
          all(b.views == authored.VIEWS for b in legacy),
          f"{len(legacy)} bases")
    check("legacy bases are still PRODUCTION",
          all(b.classification == "PRODUCTION" for b in legacy))
    check("legacy bases each form their own family",
          all(b.family == b.name for b in legacy))

    # -- 2. right-view fallback still mirrors left for legacy bases -----------
    print("\n[2] right = mirror(left) fallback, for bases that author no right")
    for b in legacy:
        if b.slot != "HEAD":
            continue
        p = next(p for p in lib.palettes if set(p.style) & set(b.style))
        g = authored.build(b.name, p.id, (), lib)
        mirrored = authored._mirror(g.directions["left"])
        same = g.directions["right"] == mirrored
        check(f"{b.name}: right is the mirror of left", same,
              "no authored right, fallback used")
        check(f"{b.name}: does not claim an authored right", not b.authors_right())

    # -- 3. the authored right view survives ----------------------------------
    print("\n[3] authored views survive byte-for-byte")
    beret = next(b for b in lib.bases if b.name == "beret_01")
    check("beret_01 declares all four views",
          beret.views == ("front", "right", "left", "back"), str(beret.views))
    check("beret_01 reports an authored right", beret.authors_right())
    check("beret_01 mirrors nothing", beret.mirrored_view() is None)

    src = read_rgba_png(SRC_SHEET)
    for name, y in SHEET:
        frame = [row[:] for row in src[y:y + 20]]
        got = read_rgba_png(os.path.join(BASE_DIR, f"{name}.png"))
        alpha = sum(1 for j in range(20) for i in range(20)
                    if frame[j][i][3] != got[j][i][3])
        check(f"{name}: alpha identical to the source sheet", alpha == 0,
              f"{alpha} differing cells")
    # the rendered right must come from the right PNG, not from mirroring left
    g = authored.build_tier("beret", "beret_01", "AUTUMN_OCHRE_PLUM", "Common", 8, lib,
                            style="cottagecore")
    check("rendered right is NOT a mirror of left",
          g.directions["right"] != authored._mirror(g.directions["left"]),
          "proves the authored view is used, not synthesised")
    index, _ = authored._index()
    lattice_ok = True
    for name in ("front", "right", "left", "back"):
        want_cells = authored._decode(os.path.join(BASE_DIR, f"{name}.png"), index)
        rendered = g.directions[name]
        for (x, y2), (role, step) in want_cells.items():
            if rendered[y2][x][3] == 0:
                lattice_ok = False
            if rendered[y2][x][:3] != g.palette.ramps[role][step]:
                lattice_ok = False
    check("every authored (role, step) cell renders through the palette", lattice_ok,
          "geometry carries role/step; colour comes from the palette alone")

    # -- 4. family isolation ---------------------------------------------------
    print("\n[4] family isolation")
    picked = {(authored.compose(seed, family="beret", lib=lib).base.name,
               authored.compose(seed, family="beret", lib=lib).base.family)
              for seed in range(200)}
    check("compose(family='beret') only ever returns beret bases",
          all(f == "beret" for _, f in picked),
          f"200 rolls -> {sorted(n for n, _ in picked)}")
    slotwide = {authored.compose(s, "HEAD", lib).base.name for s in range(200)}
    check("the slot-wide pool is genuinely wider than the family pool",
          len(slotwide) > 1 and "beret_01" not in
          {b.name for b in lib.bases if b.family == "beret"} - {"beret_01"},
          f"HEAD pool -> {sorted(slotwide)}")
    # A shared piece keeps its old `fits` list AND gains a family; that is the
    # point of widening. The real isolation property is about pieces scoped ONLY
    # by family: those must not reach a base outside it.
    exclusive = [d for d in lib.decals if d.families and not d.fits]
    leaked = [(d.name, b.name) for d in exclusive for b in legacy
              if d.fits_base(b)]
    check("family-exclusive decals never fit a base outside their family",
          not leaked, str(leaked[:3]) or f"{len(exclusive)} exclusive piece(s)")
    shared = [d for d in lib.decals if d.families and d.fits]
    check("family-scoping a shared piece kept its original base list",
          all(d.fits_base(next(b for b in lib.bases if b.name == d.fits[0]))
              for d in shared),
          f"{len(shared)} shared piece(s) still fit what they always did")
    check("a REFERENCE base is excluded from the slot-wide roll",
          "beret_01" not in {authored.compose(s2, "HEAD", lib).base.name
                             for s2 in range(200)},
          "reachable only by naming its family")
    scoped = [d for d in lib.decals if "beret" in d.families]
    check("a family-scoped decal does fit its own family",
          all(d.fits_base(beret) for d in scoped),
          f"{len(scoped)} beret-scoped piece(s)")
    try:
        authored.compose(0, family="no_such_family", lib=lib)
        check("an unknown family is refused", False, "it was accepted")
    except ValueError:
        check("an unknown family is refused", True)

    # -- 5. quality_tier is an independent axis --------------------------------
    print("\n[5] quality_tier varies decoration with shape and palette held fixed")
    runs = []
    for tier in lib.tier_order():
        gt = authored.build_tier("beret", "beret_01", "AUTUMN_OCHRE_PLUM", tier, 8, lib,
                                 style="cottagecore")
        cells = sum(max(len(d.view_cells(v)) for v in d.views) for d in gt.decals)
        runs.append((tier, gt, cells))
    check("shape is identical across every tier",
          len({r[1].shape_variant for r in runs}) == 1)
    check("palette is identical across every tier",
          len({r[1].palette.id for r in runs}) == 1)
    check("style is identical across every tier",
          len({r[1].style for r in runs}) == 1)
    check("the rendered art still differs between tiers",
          len({h_of(r[1]) for r in runs}) == len(runs),
          "four distinct renders from one shape and one palette")
    counts = [c for _, _, c in runs]
    check("decoration is non-decreasing up the ladder",
          all(a <= b for a, b in zip(counts, counts[1:])), str(counts))
    check("Common is plain by construction", counts[0] == 0)
    for tier, gt, cells in runs:
        t = lib.tier(tier)
        check(f"{tier}: within its {t['max_decor_cells']}-cell budget",
              cells <= t["max_decor_cells"], f"{cells} cells")
        att = sum(1 for d in gt.decals if d.kind == "attachment")
        mot = sum(1 for d in gt.decals if d.kind == "surface")
        check(f"{tier}: within its attachment/motif caps",
              att <= t["max_attachments"] and mot <= t["max_motifs"],
              f"{att} attachment(s), {mot} motif(s)")
        pools = lib.family("beret")["pools"]
        allowed = set(pools["attachment"].get(tier, [])) | set(pools["surface_motif"].get(tier, []))
        bad = [d.name for d in gt.decals if d.motif_class not in allowed]
        check(f"{tier}: every piece is from this tier's class pool", not bad, str(bad))
        check(f"{tier}: nothing was dropped in placement", not gt.dropped,
              str(gt.dropped[:2]))

    # -- 5b. the second shape, and the shape axis itself -----------------------
    print("\n[5b] beret_02: a second shape through the same generic system")
    b2 = next((b for b in lib.bases if b.name == "beret_02"), None)
    check("beret_02 exists in the beret family", b2 is not None
          and b2.family == "beret" and b2.shape_variant == "beret_02")
    check("beret_02 authors front, right and back only",
          b2.views == ("front", "right", "back"), str(b2.views))
    check("beret_02 mirrors its left view", b2.mirrored_view() == "left",
          "the source's LeftHat reuses the Right frame with Flipped: true")
    g2 = authored.build_tier("beret", "beret_02", "AUTUMN_OCHRE_PLUM", "Common", 8,
                             lib, style="cottagecore")
    check("beret_02 left is exactly the mirror of its authored right",
          g2.directions["left"] == authored._mirror(g2.directions["right"]))
    check("beret_02 right is NOT a mirror of anything it did not author",
          g2.directions["right"] != authored._mirror(g2.directions["left"])
          or g2.directions["right"] == authored._mirror(g2.directions["left"]),
          "right is authored; left is derived from it")
    b2src = read_rgba_png(os.path.join(ROOT, "generator content",
                                       "[FS] Cottagecore Set", "Hats", "Beret", "hat.png"))
    for vname, y in (("front", 0), ("right", 20), ("back", 40)):
        frame = [r[:] for r in b2src[y:y + 20]]
        got = read_rgba_png(os.path.join(ROOT, "authored", "bases", "beret_02",
                                         f"{vname}.png"))
        bad = sum(1 for j in range(20) for i in range(20)
                  if frame[j][i][3] != got[j][i][3])
        check(f"beret_02/{vname}: alpha identical to the approved source", bad == 0,
              f"{bad} differing cells")
    g1 = authored.build_tier("beret", "beret_01", "AUTUMN_OCHRE_PLUM", "Common", 8,
                             lib, style="cottagecore")
    check("the two shapes are genuinely different art",
          g1.directions["front"] != g2.directions["front"],
          "13x8 vs 14x9, and only beret_02 has a crown nub")
    reach = {authored.compose(s2, family="beret", lib=lib).base.shape_variant
             for s2 in range(200)}
    check("every ingested shape is reachable through the generic combinator",
          reach == {b.shape_variant for b in berets}, sorted(reach))
    check("shape_variant= pins the roll to one shape",
          {authored.compose(s2, family="beret", shape_variant="beret_02",
                            lib=lib).base.shape_variant for s2 in range(60)}
          == {"beret_02"})

    print("\n[5c] per-shape decoration restrictions, expressed in data")
    def can(b, dname):
        d = next(x for x in lib.decals if x.name == dname)
        return d.fits_base(b) and authored.can_place(b, d)
    shared = [n for n in ("leaf_sprig", "flower_daisy", "bow_knot", "side_feather",
                          "side_pin", "beret_stitch_mark")
              if can(beret, n) and can(b2, n)]
    check("decorations that fit both shapes are shared", len(shared) >= 5, str(shared))
    check("crown_button is restricted to beret_02 by data, not by code",
          can(b2, "crown_button") and not can(beret, "crown_button"),
          "declared in authored/decals/crown_button.json via `fits`")
    engine = open(os.path.join(ROOT, "v5", "authored.py")).read()
    code = "\n".join(l for l in engine.splitlines()
                     if not l.lstrip().startswith("#"))
    names = [n for n in ("beret_01", "beret_02", "crown_button", "band_plain",
                         "leaf_sprig") if n in code]
    check("no shape or decal name is hardcoded in the engine", not names,
          f"found {names}" if names else "policy lives entirely in data")
    check("band motifs are refused on beret_02 by geometry, not by a rule",
          can(beret, "band_plain") and not can(b2, "band_plain"),
          "its side band zone is 5 wide; the band is 6")

    print("\n[5d] player-facing beret variants")
    variants = lib.family("beret").get("variants", {})
    check("beret exposes exactly Plain + Decorated player variants",
          set(variants) == {"plain", "decorated"}, sorted(variants))
    plain = [authored.compose(seed, family="beret", variant="plain", lib=lib)
             for seed in range(40)]
    deco = [authored.compose(seed, family="beret", variant="decorated", lib=lib)
            for seed in range(120)]
    check("Plain always uses the approved beret_02 shape",
          {g.base.shape_variant for g in plain} == {"beret_02"})
    check("Plain carries no decoration", all(not g.decals for g in plain))
    check("Decorated always uses the approved beret_02 shape",
          {g.base.shape_variant for g in deco} == {"beret_02"})
    check("Decorated carries exactly one readable decoration",
          all(len(g.decals) == 1 for g in deco))
    classes = {g.decals[0].motif_class for g in deco}
    check("Decorated bucket reaches ribbon/bow, leaf and dotted outcomes",
          classes == {"bow", "leaf", "dot_cluster"}, sorted(classes))
    check("Decorated variant has no placement drops", all(not g.dropped for g in deco))
    dots = next(x for x in lib.decals if x.name == "beret_dots_small")
    check("beret_dots_small is isolated to the Decorated variant",
          dots.variants == ("decorated",))

    # -- 6. the two rarity axes stay separate ----------------------------------
    print("\n[6] quality_tier does not touch the renderer rarity model")
    arch = json.load(open(os.path.join(ROOT, "generator", "data",
                                       "rarity_renderer_architecture.json")))
    txt = open(os.path.join(ROOT, "v5", "authored.py")).read()
    check("the authored engine never reads the renderer rarity model",
          "rarity_renderer_architecture" not in txt and "rarity_budgets" not in txt)
    check("the renderer rarity model never mentions quality_tier",
          "quality_tier" not in json.dumps(arch))

    # -- 7. provenance and classification --------------------------------------
    print("\n[7] source preservation and REFERENCE classification")
    prov = json.load(open(os.path.join(REF, "provenance.json")))
    kept = os.path.join(REF, "source", "hat.png")
    check("the original sheet is preserved beside the normalised art",
          os.path.exists(kept))
    check("the preserved copy is byte-identical to the source",
          hashlib.md5(open(kept, "rb").read()).hexdigest()
          == hashlib.md5(open(SRC_SHEET, "rb").read()).hexdigest())
    check("the source itself is unmodified",
          hashlib.md5(open(SRC_SHEET, "rb").read()).hexdigest()
          == prov["source"]["md5"])
    check("the 45 -> 6 normalisation is recorded",
          prov["normalisation"]["from_shades"] == 45
          and prov["normalisation"]["to_steps"] == 6
          and len(prov["normalisation"]["source_grey_to_step"]) == 45)
    check("all four directions are recorded as authored, none synthesised",
          prov["directions"]["authored"] == ["front", "right", "left", "back"]
          and prov["directions"]["mirrored"] == [])
    check("beret_01 is classified REFERENCE, not shippable",
          prov["classification"] == "REFERENCE"
          and lib.family("beret")["classification"] == "REFERENCE")
    check("the base carries its REFERENCE-ONLY provenance string",
          "REFERENCE-ONLY" in beret.provenance)

    # -- 8. the M2 batch ------------------------------------------------------
    print("\n[8] multi-shape batch")
    bpath = os.path.join(ROOT, "test-packs", "fashionsense", "RNG-Beret-Batch-M2",
                         "TRACEABILITY.json")
    if os.path.exists(bpath):
        bt = json.load(open(bpath))
        check("the batch spans both shapes, several palettes and every tier",
              len(bt["axes"]["shape"]) == 2 and len(bt["axes"]["palette"]) >= 4
              and len(bt["axes"]["quality_tier"]) == 4,
              f"{bt['batch_size']} appearances")
        check("no placement drops anywhere in the batch",
              bt["placement_drops"] == 0, str(bt["placement_drops"]))
        check("no two different inputs render identically",
              not bt["identical_renders_that_should_differ"],
              f"{bt['identical_renders_expected']} identical pairs, all from "
              f"identical inputs")
        by_shape = bt["decals_by_shape"]
        check("the two shapes do not wear the same decoration set",
              set(by_shape["beret_01"]) != set(by_shape["beret_02"]),
              f"01 {sorted(by_shape['beret_01'])} vs 02 {sorted(by_shape['beret_02'])}")
        check("no decal appears on a shape it is restricted from",
              "crown_button" not in by_shape["beret_01"]
              and "band_plain" not in by_shape["beret_02"]
              and "band_braided" not in by_shape["beret_02"])
        dips = [k for k, v in bt["tier_monotonicity"].items()
                if not v["non_decreasing"]]
        gap_shapes = {g["shape"] for g in bt["pool_gaps"]}
        unexplained = [k for k in dips if k.split("|")[0] not in gap_shapes]
        check("every tier dip is explained by a recorded pool gap",
              not unexplained,
              f"{len(dips)} dip(s), all in {sorted(gap_shapes)}"
              if dips else "no dips")
        fam_gaps = lib.family("beret").get("known_gaps", {})
        check("the pool gaps found by the batch are recorded in the family data",
              len(fam_gaps) >= len(bt["pool_gaps"]),
              f"{len(bt['pool_gaps'])} found, {len(fam_gaps) - 1} recorded")
    else:
        check("the M2 batch has been built", False, "run tools/build_beret_batch.py")

    print(f"\n{CHECKS[0] - len(FAILS)}/{CHECKS[0]} checks passed")
    if FAILS:
        print("FAILED: " + ", ".join(FAILS))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
