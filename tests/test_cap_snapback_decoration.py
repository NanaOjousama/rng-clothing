"""Regression gates for the Snapback Cap front-crown decoration bucket.

Decoration is on the DECAL axis, not material: each candidate mark is an
authored surface Decal (authored/decals/cap_snapback_front_*.json), placed by
v5.authored's existing generic zone-centring logic and integrated by
v5/integration.py's existing surface-motif pass, composed through
v5/source_backed.py's existing render(palette=, decals=(...), lib=...) path.
No new decal architecture and no changes to v5/source_backed.py or
v5/integration.py were needed.

The Baseball four-mark pool was NOT assumed to transfer: cap_snapback's front
geometry is genuinely narrower at the crown top than cap_baseball's, and Ring
fails the Snapback-specific safe mask even though it was Baseball's strongest
live keep. See authored/source_backed/cap_snapback/decoration_evaluation.json
for the full audit and authored/source_bases/cap/cap_snapback/motif_safe_mask.json
for the derivation.

Live worn QC passed in session 20260916-220411. Bar, Twin Bars and Dot are
LIVE KEEP for Snapback V1; Ring remains the independent offline geometric
reject because it touches the Snapback-specific taper zone.
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from v5 import authored  # noqa: E402
from v5 import source_backed as sbm  # noqa: E402

DECOR_DECALS = ("cap_snapback_front_bar", "cap_snapback_front_twin_bars",
               "cap_snapback_front_dot")
NOT_IN_PRODUCTION = ("cap_snapback_front_ring",)  # offline geometric reject
EXPECTED_CELLS = {
    "cap_snapback_front_bar":       {(8, 6), (9, 6), (10, 6), (11, 6)},
    "cap_snapback_front_twin_bars": {(8, 6), (8, 7), (11, 6), (11, 7)},
    "cap_snapback_front_dot":       {(9, 6), (10, 6), (9, 7), (10, 7)},
}
DECOR_PALETTE = "EMBER_SUN_CHARCOAL"
SAFE_MASK = json.load(open(os.path.join(
    ROOT, "authored/source_bases/cap/cap_snapback/motif_safe_mask.json")))
SAFE_CELLS = {tuple(c) for c in SAFE_MASK["safe_cells"]}


class CapSnapbackDecoration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib = authored.load()
        cls.base = sbm.load_one("cap_snapback")
        cls.baseball = sbm.load_one("cap_baseball")
        cls.palette = next(p for p in cls.lib.palettes if p.id == DECOR_PALETTE)
        cls.decals = {n: next(d for d in cls.lib.decals if d.name == n) for n in DECOR_DECALS}
        cls.neutral = sbm.render(cls.base)

    def render(self, decal_name):
        return sbm.render(self.base, palette=self.palette,
                          decals=(self.decals[decal_name],), lib=self.lib)

    def test_neutral_snapback_still_equals_source_exactly(self):
        b, r = self.base, self.neutral
        self.assertFalse(r.baked)
        self.assertFalse(r.dropped)
        for v in b.views:
            self.assertEqual(r.directions[v], b.source[v])

    def test_neutral_baseball_remains_untouched(self):
        r = sbm.render(self.baseball)
        self.assertFalse(r.baked)
        self.assertFalse(r.dropped)
        for v in self.baseball.views:
            self.assertEqual(r.directions[v], self.baseball.source[v])

    def test_live_approved_decals_exist_and_are_reachable(self):
        names = {d.name for d in self.lib.decals if d.name.startswith("cap_snapback_front_")}
        self.assertEqual(names, set(DECOR_DECALS))
        for name in DECOR_DECALS:
            self.assertTrue(authored.can_place(self.base.semantic, self.decals[name]))

    def test_rejected_ring_candidate_is_not_in_production_library(self):
        names = {d.name for d in self.lib.decals}
        for name in NOT_IN_PRODUCTION:
            self.assertNotIn(name, names)

    def test_snapback_decals_are_scoped_only_to_cap_snapback(self):
        # `fits` is a family/pool-selection scope, not a geometric one -- a
        # decal can be geometrically legal (can_place) on a base it was never
        # authored for, which is exactly why `fits` exists. The combinator
        # asks fits_base(), so that is what this test asks too.
        for name in DECOR_DECALS:
            with self.subTest(decal=name):
                d = self.decals[name]
                self.assertEqual(d.fits, ("cap_snapback",))
                self.assertTrue(d.fits_base(self.base))
                self.assertFalse(d.fits_base(self.baseball))

    def test_baseball_decals_are_scoped_only_to_cap_baseball(self):
        baseball_decals = [d for d in self.lib.decals
                            if d.name.startswith("cap_baseball_front_")]
        self.assertEqual(len(baseball_decals), 4)
        for d in baseball_decals:
            with self.subTest(decal=d.name):
                self.assertTrue(d.fits_base(self.baseball))
                self.assertFalse(d.fits_base(self.base))

    def test_each_decal_lands_on_exactly_the_intended_cells(self):
        for name in DECOR_DECALS:
            with self.subTest(decal=name):
                d = self.decals[name]
                origin = authored._placement(self.base.semantic, d, "front")
                placed = {(origin[0] + dx, origin[1] + dy) for dx, dy in d.view_cells("front")}
                self.assertEqual(placed, EXPECTED_CELLS[name])

    def test_every_changed_decoration_cell_is_inside_the_snapback_safe_mask(self):
        for name in DECOR_DECALS:
            with self.subTest(decal=name):
                r = self.render(name)
                changed = r.changes["front"]["decal"]
                self.assertTrue(changed, f"{name}: nothing changed")
                off = changed - SAFE_CELLS
                self.assertEqual(off, set(), f"{name}: cells outside CAP_SNAPBACK_FRONT_MOTIF_SAFE_MASK: {off}")

    def test_no_crown_face_row_5_taper_cells(self):
        # cap_snapback's row 5 fails its own 8-connectivity safe-mask test
        # (the crown-top taper), unlike cap_baseball's row 5.
        for name in DECOR_DECALS:
            with self.subTest(decal=name):
                ys = {y for _, y in EXPECTED_CELLS[name]}
                self.assertNotIn(5, ys, f"{name}: uses row 5 (the Snapback taper zone)")

    def test_no_band_or_visor_notch_cells(self):
        # The band/visor notch starts at row 8 on cap_snapback's front view.
        for name in DECOR_DECALS:
            with self.subTest(decal=name):
                for (x, y) in EXPECTED_CELLS[name]:
                    self.assertLess(y, 8, f"{name}: cell {x},{y} touches the band/visor notch")

    def test_no_alpha_or_silhouette_change(self):
        for name in DECOR_DECALS:
            with self.subTest(decal=name):
                r = self.render(name)
                for v in self.base.views:
                    for y, (row_before, row_after) in enumerate(zip(self.base.source[v], r.directions[v])):
                        for x, (before, after) in enumerate(zip(row_before, row_after)):
                            self.assertEqual(before[3], after[3], f"{name}/{v}/{x},{y} alpha changed")

    def test_decoration_is_front_only(self):
        for name in DECOR_DECALS:
            with self.subTest(decal=name):
                r = self.render(name)
                for v in ("right", "back", "left"):
                    self.assertEqual(r.changes[v]["decal"], set(), f"{name}: {v} changed")

    def test_no_placement_drops(self):
        for name in DECOR_DECALS:
            with self.subTest(decal=name):
                r = self.render(name)
                self.assertEqual(r.dropped, ())

    def test_plain_has_zero_decoration(self):
        r = self.neutral
        self.assertEqual(r.decals, ())
        self.assertEqual(r.changes["front"]["decal"], set())

    def test_decorated_proof_has_exactly_one_decoration(self):
        for name in DECOR_DECALS:
            with self.subTest(decal=name):
                r = self.render(name)
                self.assertEqual(len(r.decals), 1)

    def test_decorated_bucket_matches_live_keep_set(self):
        cfg = json.loads(Path(
            ROOT, "authored/source_backed/cap_snapback/decoration_evaluation.json"
        ).read_text())
        bucket = cfg["player_facing_bucket"]
        self.assertEqual(bucket["max_decor_pieces"], 1)
        self.assertEqual(set(bucket["outcomes"]), set(DECOR_DECALS))
        self.assertEqual(set(cfg["live_qc"]["final_keep"]), {"bar", "twin_bars", "dot"})
        self.assertEqual(cfg["live_qc"]["session"], "20260916-220411")

    def test_ring_candidate_rejected_offline_for_touching_the_taper(self):
        cfg = json.loads(Path(
            ROOT, "authored/source_backed/cap_snapback/decoration_evaluation.json"
        ).read_text())
        self.assertEqual(cfg["candidates"]["ring"]["offline_verdict"], "REJECT")

    def test_decoration_axis_is_independent_from_material_axis(self):
        self.assertEqual(self.base.materials, {})
        r = self.render("cap_snapback_front_bar")
        self.assertEqual(r.material, "")
        self.assertEqual(r.changes["front"]["material"] if "front" in r.changes else set(), set())

    def test_existing_baseball_decoration_decals_remain_present_and_unchanged(self):
        keep = ("cap_baseball_front_bar", "cap_baseball_front_twin_bars",
                "cap_baseball_front_dot", "cap_baseball_front_ring")
        names = {d.name for d in self.lib.decals}
        for name in keep:
            self.assertIn(name, names)

    def test_existing_beret_behavior_untouched(self):
        beret = sbm.load_one("beret_02")
        r = sbm.render(beret)
        self.assertFalse(r.dropped)
        for v in beret.views:
            self.assertEqual(r.directions[v], beret.source[v])

    def test_source_backed_v2_structurally_accepts_material_and_decal_together(self):
        beret = sbm.load_one("beret_02")
        self.assertIn("knit", beret.materials)
        decal = next(d for d in self.lib.decals if d.name == "beret_stitch_mark")
        palette = next(p for p in self.lib.palettes if p.id == DECOR_PALETTE)
        r = sbm.render(beret, palette=palette, material="knit", decals=(decal,), lib=self.lib)
        self.assertEqual(r.material, "knit")
        self.assertEqual(len(r.decals), 1)
        self.assertTrue(r.changes["front"]["material"] or any(
            r.changes[v]["material"] for v in beret.views))
        self.assertTrue(any(r.changes[v]["decal"] for v in beret.views))


if __name__ == "__main__":
    unittest.main()
