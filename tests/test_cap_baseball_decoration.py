"""Regression gates for the Baseball Cap front-crown decoration bucket.

Decoration is on the DECAL axis, not material: each candidate mark is an
authored surface Decal (authored/decals/cap_baseball_front_*.json), placed by
v5.authored's existing generic zone-centring logic and integrated by
v5/integration.py's existing surface-motif pass, composed through
v5/source_backed.py's existing render(palette=, decals=(...), lib=...) path.
No new decal architecture and no changes to v5/source_backed.py or
v5/integration.py were needed -- see
authored/source_backed/cap_baseball/decoration_evaluation.json for the
KEEP/REJECT audit and the architecture correction this replaces (an earlier,
wrong MaterialMask implementation).
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

DECOR_DECALS = ("cap_baseball_front_bar", "cap_baseball_front_twin_bars",
               "cap_baseball_front_dot", "cap_baseball_front_ring")
REJECTED = ("cap_baseball_front_angle_l", "cap_baseball_front_chevron",
            "cap_baseball_front_zigzag")
EXPECTED_CELLS = {
    "cap_baseball_front_bar":       {(8, 6), (9, 6), (10, 6), (11, 6)},
    "cap_baseball_front_twin_bars": {(8, 6), (8, 7), (11, 6), (11, 7)},
    "cap_baseball_front_dot":       {(9, 6), (10, 6), (9, 7), (10, 7)},
    "cap_baseball_front_ring":      {(9, 5), (10, 5), (8, 6), (11, 6), (9, 7), (10, 7)},
}
DECOR_PALETTE = "EMBER_SUN_CHARCOAL"
SAFE_MASK = json.load(open(os.path.join(
    ROOT, "authored/source_bases/cap2/motif_safe_mask.json")))
SAFE_CELLS = {tuple(c) for c in SAFE_MASK["safe_cells"]}


class CapBaseballDecoration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib = authored.load()
        cls.base = sbm.load_one("cap_baseball")
        cls.palette = next(p for p in cls.lib.palettes if p.id == DECOR_PALETTE)
        cls.decals = {n: next(d for d in cls.lib.decals if d.name == n) for n in DECOR_DECALS}
        cls.neutral = sbm.render(cls.base)

    def render(self, decal_name):
        return sbm.render(self.base, palette=self.palette,
                          decals=(self.decals[decal_name],), lib=self.lib)

    def test_neutral_baseball_still_equals_source_exactly(self):
        b, r = self.base, self.neutral
        self.assertFalse(r.baked)
        self.assertFalse(r.dropped)
        for v in b.views:
            self.assertEqual(r.directions[v], b.source[v])

    def test_neutral_snapback_untouched(self):
        snap = sbm.load_one("cap_snapback")
        r = sbm.render(snap)
        self.assertFalse(r.baked)
        self.assertFalse(r.dropped)
        for v in snap.views:
            self.assertEqual(r.directions[v], snap.source[v])

    def test_four_live_approved_decals_exist_and_are_reachable(self):
        names = {d.name for d in self.lib.decals if d.name.startswith("cap_baseball_front_")}
        self.assertEqual(names, set(DECOR_DECALS))
        for name in DECOR_DECALS:
            self.assertTrue(authored.can_place(self.base.semantic, self.decals[name]))

    def test_live_rejected_marks_are_not_in_production_library(self):
        names = {d.name for d in self.lib.decals}
        for name in REJECTED:
            self.assertNotIn(name, names)

    def test_each_decal_lands_on_exactly_the_intended_old_cap2_cells(self):
        for name in DECOR_DECALS:
            with self.subTest(decal=name):
                d = self.decals[name]
                origin = authored._placement(self.base.semantic, d, "front")
                placed = {(origin[0] + dx, origin[1] + dy) for dx, dy in d.view_cells("front")}
                self.assertEqual(placed, EXPECTED_CELLS[name])

    def test_every_changed_decoration_cell_is_inside_the_approved_safe_mask(self):
        for name in DECOR_DECALS:
            with self.subTest(decal=name):
                r = self.render(name)
                changed = r.changes["front"]["decal"]
                self.assertTrue(changed, f"{name}: nothing changed")
                off = changed - SAFE_CELLS
                self.assertEqual(off, set(), f"{name}: cells outside CAP2_FRONT_MOTIF_SAFE_MASK: {off}")

    def test_no_row_8(self):
        for name in DECOR_DECALS:
            with self.subTest(decal=name):
                ys = {y for _, y in EXPECTED_CELLS[name]}
                self.assertNotIn(8, ys, f"{name}: uses row 8 (the unapproved ext8 extension)")

    def test_no_visor_cells(self):
        # The visor/underside starts at row 9 in the ported CAP2 semantic map.
        for name in DECOR_DECALS:
            with self.subTest(decal=name):
                for (x, y) in EXPECTED_CELLS[name]:
                    self.assertLess(y, 9, f"{name}: cell {x},{y} touches the visor band")

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

    def test_exactly_one_decoration_in_the_decorated_bucket(self):
        cfg = json.loads(Path(
            ROOT, "authored/source_backed/cap_baseball/decoration_evaluation.json"
        ).read_text())
        bucket = cfg["player_facing_bucket"]
        self.assertEqual(bucket["max_decor_pieces"], 1)
        self.assertEqual(set(bucket["outcomes"]), set(DECOR_DECALS))
        for name in DECOR_DECALS:
            r = self.render(name)
            self.assertEqual(len(r.decals), 1)

    def test_plain_has_zero_decoration(self):
        r = self.neutral
        self.assertEqual(r.decals, ())
        self.assertEqual(r.changes["front"]["decal"], set())

    def test_decoration_axis_is_independent_from_material_axis(self):
        # cap_baseball has no authored material (materials are deferred this
        # milestone); a decal composes fine with none declared.
        self.assertEqual(self.base.materials, {})
        r = self.render("cap_baseball_front_bar")
        self.assertEqual(r.material, "")
        self.assertEqual(r.changes["front"]["material"], set())

    def test_source_backed_v2_structurally_accepts_material_and_decal_together(self):
        # Prove the general capability on an existing base that actually HAS an
        # authored material (beret_02's knit rib), rather than inventing a cap
        # material just to exercise this.
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

    def test_existing_beret_behavior_untouched(self):
        beret = sbm.load_one("beret_02")
        r = sbm.render(beret)
        self.assertFalse(r.dropped)
        for v in beret.views:
            self.assertEqual(r.directions[v], beret.source[v])


if __name__ == "__main__":
    unittest.main()
