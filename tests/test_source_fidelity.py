"""SOURCE FIDELITY regression.

A source-backed base, rendered with neutral options, must reproduce its source
artwork exactly -- pixels AND Fashion Sense rendering semantics -- except for the
documented layout transformations in DOCUMENTED. Each stage has its own test so
a failure names WHERE fidelity is lost.

Two paths are covered:

  SourceBackedV2        v5/source_backed.py. Must be green. Its material proof
                        is the REAL authored plaid mask for beret_02
                        (authored/source_backed/beret_02/materials/plaid.json).
  LegacySixStepPath     authored.py's ingest-to-six-steps path, kept for legacy
                        bases. Its source losses were diagnosed in the
                        2026-09-14 audit and are pinned as expectedFailure: if
                        that path ever changes, the suite says so.

    python3 -m unittest tests.test_source_fidelity -v
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from v5 import authored  # noqa: E402
from v5 import source_backed as sbm  # noqa: E402
from v5.pngio import read_rgba_png, write_rgba_png  # noqa: E402
import extract_material_mask  # noqa: E402
from trace_source_fidelity import (  # noqa: E402
    FS, ORDER, base_of, changed_cells, first_unexpected_stage, index_palette, lstar,
    pick_decals, provenance, render, restack, s1_source, s2_ingested, shading_report, v2_stages)
from validate_material_mask import Sheet, describe, mask_from_diff, violations  # noqa: E402

# Bases whose PIXELS come from a source sheet. beret_03 is excluded on purpose:
# its provenance takes only outline and silhouette from the user's drawing.
SOURCE_BACKED = ("beret_02", "beret_01")
PALETTE = "EVERYDAY_STONE_BLUE"
# The authored-material proof: one real mask, one shape, a spread of tints.
PLAID_BASE = "beret_02"
PLAID_PALETTES = (None, "EVERYDAY_STONE_BLUE", "CUTE_COCOA_GOLD", "CUTE_ROSE_CREAM")

DOCUMENTED = (
    "frames restacked to Fashion Sense order front/right/left/back",
    "a view the source's hat.json draws Flipped is materialised as the mirror of the "
    "frame it flips, and the Flipped flag is dropped",
)
LAYOUT_KEYS = ("StartingPosition", "Flipped")


def _cells(sheet):
    return {(x, y): sheet[y][x] for y in range(len(sheet)) for x in range(FS) if sheet[y][x][3]}


def _first(a, b, limit=5):
    bad = [(x, y, "#%02x%02x%02x" % a[y][x][:3], "#%02x%02x%02x" % b[y][x][:3])
           for y in range(len(a)) for x in range(FS) if a[y][x] != b[y][x]]
    return f"{len(bad)} px differ, e.g. {bad[:limit]}"


def _allowed(r, kinds):
    out = set()
    for i, v in enumerate(ORDER):
        for k in kinds:
            out |= {(x, y + i * FS) for x, y in r.changes[v][k]}
    return out


class SourceBackedV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib = authored.load()
        cls.bases = {n: sbm.load_one(n) for n in SOURCE_BACKED}
        cls.pal = next(p for p in cls.lib.palettes if p.id == PALETTE)
        cls.plaid_pals = [None if p is None else next(x for x in cls.lib.palettes if x.id == p)
                          for p in PLAID_PALETTES]

    # -- source_pixels ----------------------------------------------------------
    def test_stored_source_pixels_are_the_source(self):
        for n, b in self.bases.items():
            with self.subTest(base=n):
                self.assertEqual(sbm.md5(os.path.join(ROOT, b.source_png)), provenance(n)["source"]["md5"])
                s = restack({v: b.source[v] for v in b.views}, b.mirrored)
                self.assertTrue(s == s1_source(n), _first(s1_source(n), s))

    def test_neutral_render_is_source_pixel_exact(self):
        for n, b in self.bases.items():
            with self.subTest(base=n):
                r = sbm.render(b)
                self.assertFalse(r.baked)
                s = sbm.sheet(r)
                self.assertTrue(s == s1_source(n), _first(s1_source(n), s))

    # -- rendering semantics + placement -----------------------------------------
    def test_neutral_pack_keeps_source_fashion_sense_semantics(self):
        """Every non-layout field of every source model block survives verbatim:
        HeadPosition, grayscale/tint (an absent DisableGrayscale stays absent),
        ColorMasks, animation, size."""
        for n, b in self.bases.items():
            with self.subTest(base=n):
                src = sbm.read_fs_json(os.path.join(ROOT, b.source_png.replace("hat.png", "hat.json")))
                j = sbm.hat_json(sbm.render(b), n)
                for v in ORDER:
                    blk = sbm.MODEL_OF[v]
                    want = {k: val for k, val in src[blk].items() if k not in LAYOUT_KEYS}
                    got = {k: val for k, val in j[blk].items() if k not in LAYOUT_KEYS}
                    self.assertEqual(got, want, f"{n}/{blk}")
                    self.assertNotIn("Flipped", j[blk])
                    self.assertEqual(j[blk]["StartingPosition"], {"X": 0, "Y": ORDER.index(v) * FS})

    def test_placement_is_the_source_placement_not_a_family_offset(self):
        want = {"beret_02": {"X": 0, "Y": 1}, "beret_01": {"X": 0, "Y": 0}}
        for n, b in self.bases.items():
            with self.subTest(base=n):
                self.assertFalse(b.placement_override)
                for v in ORDER:
                    self.assertEqual(b.placement(v), want[n])

    def test_view_metadata_matches_the_source_json(self):
        self.assertEqual(self.bases["beret_02"].mirrored, {"left": "right"})
        self.assertEqual(self.bases["beret_02"].views, ("front", "right", "back"))
        self.assertEqual(self.bases["beret_01"].mirrored, {})
        self.assertEqual(self.bases["beret_01"].views, ("front", "right", "left", "back"))

    # -- semantic_map --------------------------------------------------------------
    def test_semantic_map_describes_the_same_cells_as_the_legacy_base(self):
        for n, b in self.bases.items():
            with self.subTest(base=n):
                legacy = base_of(self.lib, n)
                for v in b.views:
                    self.assertEqual(b.semantic.view(v), legacy.view(v))
                self.assertEqual(b.semantic.zones, legacy.zones)
                self.assertEqual(b.semantic.anchors, legacy.anchors)

    # -- palette ---------------------------------------------------------------------
    def test_palette_keeps_geometry_alpha_and_value_order(self):
        for n, b in self.bases.items():
            with self.subTest(base=n):
                src, r = s1_source(n), sbm.render(b, self.pal)
                s = sbm.sheet(r)
                self.assertTrue(r.baked)
                self.assertEqual(set(_cells(src)), set(_cells(s)))
                tint = self.pal.color(sbm.TINT_ROLE, sbm.TINT_STEP)
                want = [[sbm._tint(p, tint) if p[3] else p for p in row] for row in src]
                self.assertTrue(s == want, _first(want, s))
                cs = sorted(_cells(src), key=lambda c: lstar(src[c[1]][c[0]]))
                la = [lstar(s[y][x]) for x, y in cs]
                self.assertTrue(all(b2 >= a2 - 0.6 for a2, b2 in zip(la, la[1:])),
                                "palette bake inverted the source's value order")
                self.assertTrue(sbm.hat_json(r, n)["FrontHat"]["DisableGrayscale"])

    # -- material: the real authored plaid -------------------------------------------
    def test_authored_plaid_exists_for_beret_02_only(self):
        m = self.bases[PLAID_BASE].materials.get("plaid")
        self.assertIsNotNone(m)
        self.assertEqual(m.authored_for, PLAID_BASE)
        self.assertEqual(set(m.views), {"front", "right", "back"})
        self.assertNotIn("plaid", self.bases["beret_01"].materials)

    def test_material_changes_only_mask_cells_and_keeps_form_shading(self):
        b = self.bases[PLAID_BASE]
        m = b.materials["plaid"]
        for p in self.plaid_pals:
            with self.subTest(palette=p.id if p else "neutral"):
                before = sbm.sheet(sbm.render(b, p))
                r = sbm.render(b, p, "plaid")
                after = sbm.sheet(r)
                allowed = _allowed(r, ("material",))
                want = set()
                for i, v in enumerate(ORDER):
                    src_v = v if v in m.views else b.mirrored[v]
                    cells = m.views[src_v]
                    if v in b.mirrored:
                        cells = {(FS - 1 - x, y) for x, y in cells}
                    want |= {(x, y + i * FS) for x, y in cells}
                self.assertEqual(allowed, want)
                self.assertEqual(changed_cells(before, after), allowed)
                rep = shading_report(before, after, allowed)
                self.assertEqual(rep["order_inversions"], 0, rep)
                for x, y in allowed:     # a value ratio, never an absolute ramp step
                    self.assertEqual(after[y][x], sbm._scale(before[y][x], m.factor))

    def test_authored_plaid_is_one_logical_pixel_thick(self):
        b = self.bases[PLAID_BASE]
        for p in self.plaid_pals:
            with self.subTest(palette=p.id if p else "neutral"):
                s = Sheet(sbm.sheet(sbm.render(b, p, "plaid")))
                mask, pol = mask_from_diff(s, Sheet(sbm.sheet(sbm.render(b, p))))
                v = violations(s, mask, pol)
                self.assertFalse(v, [describe(s, x) for x in v])

    def test_material_keeps_alpha_placement_and_render_semantics(self):
        b = self.bases[PLAID_BASE]
        for p in self.plaid_pals:
            with self.subTest(palette=p.id if p else "neutral"):
                r0, r1 = sbm.render(b, p), sbm.render(b, p, "plaid")
                self.assertEqual(set(_cells(sbm.sheet(r0))), set(_cells(sbm.sheet(r1))))
                self.assertEqual(r0.baked, r1.baked)
                self.assertEqual(sbm.hat_json(r0, "x"), sbm.hat_json(r1, "x"))
        neutral = sbm.hat_json(sbm.render(b, None, "plaid"), "x")
        self.assertNotIn("DisableGrayscale", neutral["FrontHat"])
        self.assertEqual(neutral["FrontHat"]["HeadPosition"], {"X": 0, "Y": 1})

    def test_no_authored_mask_means_refused_not_procedural(self):
        cases = (("beret_01", "plaid"), ("beret_02", "knit"))
        for n, t in cases:
            with self.subTest(base=n, treatment=t):
                with self.assertRaises(sbm.Incompatible):
                    sbm.render(self.bases[n], self.pal, t)

    def test_authored_mask_overrides_procedural(self):
        b = self.bases[PLAID_BASE]
        authored_r = sbm.render(b, self.pal, "plaid")
        opted = sbm.render(b, self.pal, "plaid", lib=self.lib, experimental_procedural=True)
        self.assertEqual(sbm.sheet(opted), sbm.sheet(authored_r))
        self.assertEqual(opted.changes, authored_r.changes)

    def test_experimental_procedural_is_opt_in_and_a_value_ratio(self):
        b = self.bases[PLAID_BASE]
        before = sbm.sheet(sbm.render(b, self.pal))
        r = sbm.render(b, self.pal, "knit", lib=self.lib, experimental_procedural=True)
        after = sbm.sheet(r)
        allowed = _allowed(r, ("material",))
        self.assertEqual(changed_cells(before, after) - allowed, set())
        self.assertEqual(shading_report(before, after, allowed)["order_inversions"], 0)

    def test_beret_02_plaid_is_refused_on_another_shape(self):
        b1 = dataclasses.replace(self.bases["beret_01"],
                                 materials={"plaid": self.bases[PLAID_BASE].materials["plaid"]})
        with self.assertRaises(sbm.Incompatible):
            sbm.render(b1, self.pal, "plaid")

    def test_a_reference_mask_for_another_shape_is_refused_not_refitted(self):
        _, mask = extract_material_mask.extract(extract_material_mask.REFERENCE, "plaid")
        back = frozenset(tuple(c) for c in mask["views"]["back"])
        for n, b0 in self.bases.items():
            with self.subTest(base=n):
                m = sbm.MaterialMask("plaid", n, {"back": back}, mask["factor"], "hat_8 reference")
                b = dataclasses.replace(b0, materials={"plaid": m})
                with self.assertRaises(sbm.Incompatible):
                    sbm.render(b, self.pal, "plaid")

    def test_reference_plaid_extraction_keeps_its_authored_topology(self):
        _, mask = extract_material_mask.extract(extract_material_mask.REFERENCE, "plaid")
        back = mask["topology"]["back"]
        self.assertEqual(back["v_lines_at_x"], [4, 7, 12, 15])
        self.assertEqual(back["h_lines_at_y"], [5, 8, 11, 14])
        self.assertEqual(back["components"], 1)
        self.assertFalse([v for v in mask["thickness_violations"] if v[2] == "back"])

    # -- motif / attachment ----------------------------------------------------------
    def test_decals_change_only_their_seated_and_shaded_cells(self):
        for n, b in self.bases.items():
            with self.subTest(base=n):
                decals = pick_decals(self.lib, b)
                self.assertTrue({d.kind for d in decals} >= {"surface", "attachment"}, decals)
                before = sbm.sheet(sbm.render(b, self.pal))
                r = sbm.render(b, self.pal, None, decals)
                after = sbm.sheet(r)
                allowed = _allowed(r, ("decal", "occlusion"))
                self.assertTrue(changed_cells(before, after))
                self.assertEqual(changed_cells(before, after) - allowed, set())

    def test_decals_without_a_palette_are_refused(self):
        b = self.bases["beret_02"]
        with self.assertRaises(sbm.Incompatible):
            sbm.render(b, None, None, pick_decals(self.lib, b))

    def test_bake_over_rgb_keyed_source_masks_is_refused(self):
        b0 = self.bases["beret_02"]
        models = json.loads(json.dumps(b0.models))
        models["FrontHat"]["ColorMaskLayers"] = [{"Name": "x", "Values": [[81, 81, 81]]}]
        b = dataclasses.replace(b0, models=models)
        sbm.render(b)                                    # neutral stays legal
        with self.assertRaises(sbm.Incompatible):
            sbm.render(b, self.pal)

    # -- pack --------------------------------------------------------------------------
    def test_render_to_pack_is_exact(self):
        cases = [(n, None, pick_decals(self.lib, b)) for n, b in self.bases.items()]
        cases.append((PLAID_BASE, "plaid", ()))
        for n, mat, decals in cases:
            with self.subTest(base=n, material=mat):
                r = sbm.render(self.bases[n], self.pal, mat, decals)
                with tempfile.TemporaryDirectory() as tmp:
                    write_rgba_png(os.path.join(tmp, "hat.png"), sbm.sheet(r))
                    self.assertTrue(read_rgba_png(os.path.join(tmp, "hat.png")) == sbm.sheet(r))

    # -- the trace itself --------------------------------------------------------------
    def test_trace_finds_no_unexpected_stage(self):
        for n in SOURCE_BACKED:
            with self.subTest(base=n):
                stages = v2_stages(n, PALETTE, "plaid")
                self.assertEqual([s["name"] for s in stages],
                                 ["S1_source", "S2_ingest", "S3_neutral", "S4_palette",
                                  "S5_material", "S6_motif", "S7_pack"])
                self.assertIsNone(first_unexpected_stage(stages),
                                  {s["name"]: sorted(s["unexpected"])[:5] for s in stages})
                applied = "incompatible" not in stages[4]["notes"]
                self.assertEqual(applied, n == PLAID_BASE)

    def test_trace_names_the_first_bad_stage(self):
        stages = v2_stages(PLAID_BASE, PALETTE, "plaid")
        stages[4]["unexpected"] = {(0, 0)}
        stages[6]["unexpected"] = {(1, 1)}
        self.assertEqual(first_unexpected_stage(stages), "S5_material")


class LegacySixStepPath(unittest.TestCase):
    """The pre-V2 path. Losses diagnosed 2026-09-14 are pinned, not hidden."""

    @classmethod
    def setUpClass(cls):
        cls.lib = authored.load()

    def test_preserved_copy_is_the_source(self):
        for name in SOURCE_BACKED:
            with self.subTest(base=name):
                src = provenance(name)["source"]
                with open(os.path.join(ROOT, src["preserved_copy"]), "rb") as fh:
                    self.assertEqual(hashlib.md5(fh.read()).hexdigest(), src["md5"])

    def test_ingest_keeps_alpha(self):
        for name in SOURCE_BACKED:
            with self.subTest(base=name):
                self.assertEqual(set(_cells(s1_source(name))), set(_cells(s2_ingested(name))))

    def test_neutral_render_reproduces_ingested_base(self):
        for name in SOURCE_BACKED:
            with self.subTest(base=name):
                b = s2_ingested(name)
                n = render(self.lib, base_of(self.lib, name), index_palette())
                self.assertTrue(b == n, _first(b, n))

    @unittest.expectedFailure
    def test_ingest_keeps_every_source_colour_class(self):
        """Known loss: beret_01 45 greys -> 6; beret_02 #a4a4a4 merged into #a5a5a5."""
        a, b = _cells(s1_source("beret_01")), _cells(s2_ingested("beret_01"))
        back = {}
        for p in a:
            back.setdefault(b[p], set()).add(a[p])
        self.assertFalse({k: v for k, v in back.items() if len(v) > 1})

    @unittest.expectedFailure
    def test_ingest_keeps_source_values(self):
        """Known loss: every grey rewritten onto #202020..#E0E0E0."""
        a, b = s1_source("beret_02"), s2_ingested("beret_02")
        self.assertTrue(a == b, _first(a, b))

    @unittest.expectedFailure
    def test_neutral_render_reproduces_source(self):
        """Known loss: the legacy neutral render is the index greys, not the source."""
        a = s1_source("beret_02")
        n = render(self.lib, base_of(self.lib, "beret_02"), index_palette())
        self.assertTrue(a == n, _first(a, n))


if __name__ == "__main__":
    unittest.main()
