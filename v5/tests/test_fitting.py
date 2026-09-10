"""The fitting system's rules, each tied to a measured fact.

Session 20260909-104628 established: integer HeadPosition offsets move the hat
exactly 4 screen pixels per unit with a 76/76 exact pixel match, while any
fractional value silently prevents the hat from rendering at all. These tests
keep both facts enforced.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from v5 import fitting as F


class Directions(unittest.TestCase):
    """Fashion Sense's sign inversion must never reach the player."""

    def test_move_right_moves_right_on_screen(self):
        f = F.Fit("t")
        F.move_hat(f, 1, 0)
        # HeadPosition X+1 draws 4px LEFT, so moving right DECREASES X
        self.assertEqual(f.head_position(0, 0)["X"], -1)
        self.assertEqual(f.screen_offset()[0], 4)

    def test_move_down_moves_down_on_screen(self):
        f = F.Fit("t")
        F.move_hat(f, 0, 1)
        self.assertEqual(f.head_position(0, 0)["Y"], -1)
        self.assertEqual(f.screen_offset()[1], 4)

    def test_one_step_is_four_screen_pixels(self):
        f = F.Fit("t")
        F.move_hat(f, 2, 3)
        self.assertEqual(f.screen_offset(), (8, 12))


class IntegerOnly(unittest.TestCase):
    """A fractional value makes Fashion Sense silently not draw the hat."""

    def test_head_position_is_always_integer(self):
        f = F.Fit("t", hat_right=2, hat_down=-1)
        hp = f.head_position(0, -2)
        for axis in ("X", "Y"):
            self.assertIsInstance(hp[axis], int)

    def test_fractional_default_is_refused(self):
        with self.assertRaises(ValueError):
            F.Fit("t").head_position(0.5, 0)


class Bounds(unittest.TestCase):
    def test_hat_range_is_bounded(self):
        f = F.Fit("t")
        for _ in range(F.HAT_RANGE):
            self.assertTrue(F.move_hat(f, 1, 0)[0])
        ok, why = F.move_hat(f, 1, 0)
        self.assertFalse(ok)
        self.assertIn("range", why)

    def test_a_blocked_move_changes_nothing(self):
        f = F.Fit("t", hat_right=F.HAT_RANGE)
        before = f.hat_right
        F.move_hat(f, 1, 0)
        self.assertEqual(f.hat_right, before)


class MotifMask(unittest.TestCase):
    """A motif is blocked whole, never clipped or deformed."""

    def setUp(self):
        self.safe = {(x, y) for y in (6, 7) for x in range(7, 13)}
        self.cells = [(8, 6), (9, 6)]

    def test_legal_move_is_allowed(self):
        f = F.Fit("t")
        ok, why, moved = F.move_motif(f, self.cells, self.safe, 1, 0)
        self.assertTrue(ok, why)
        self.assertEqual(moved, [(9, 6), (10, 6)])

    def test_move_leaving_the_mask_is_blocked(self):
        f = F.Fit("t")
        # the mask has only rows 6-7; two rows down leaves it entirely
        ok, why, moved = F.move_motif(f, self.cells, self.safe, 0, 2)
        self.assertFalse(ok)
        self.assertIsNone(moved)
        self.assertIn("leave the safe mask", why)

    def test_a_blocked_move_does_not_partially_apply(self):
        f = F.Fit("t")
        F.move_motif(f, self.cells, self.safe, -5, 0)
        self.assertEqual((f.motif_right, f.motif_down), (0, 0))

    def test_partial_escape_blocks_the_whole_motif(self):
        f = F.Fit("t")
        # the mask spans x 7-12; shifting right by 4 puts (13,6) outside while
        # (12,6) stays legal — a partial escape must still block the whole mark
        ok, why, _ = F.move_motif(f, self.cells, self.safe, 4, 0)
        self.assertFalse(ok)
        self.assertIn("leave the safe mask", why)


class Persistence(unittest.TestCase):
    def setUp(self):
        self.path = tempfile.mktemp(suffix=".json")

    def tearDown(self):
        if os.path.isfile(self.path):
            os.remove(self.path)

    def test_adjustments_survive_a_reload(self):
        f = F.Fit("cap2-seed-123", hat_right=2, hat_down=-1, motif_right=1)
        F.save(f, self.path)
        back = F.load("cap2-seed-123", self.path)
        self.assertEqual((back.hat_right, back.hat_down, back.motif_right),
                         (2, -1, 1))

    def test_reset_restores_the_authored_default(self):
        f = F.Fit("x", hat_right=3, hat_down=2, motif_right=1, motif_down=1)
        F.reset_hat(f)
        F.reset_motif(f)
        self.assertTrue(f.is_default())
        self.assertEqual(f.head_position(0, -2), {"X": 0, "Y": -2})

    def test_a_default_fit_stores_nothing(self):
        F.save(F.Fit("y", hat_right=1), self.path)
        F.save(F.Fit("y"), self.path)
        self.assertNotIn("y", F.load_all(self.path))

    def test_defaults_are_never_overwritten(self):
        """The player's delta is separate; the authored position is intact."""
        f = F.Fit("z", hat_right=3)
        self.assertEqual(f.head_position(0, -2), {"X": -3, "Y": -2})
        F.reset_hat(f)
        self.assertEqual(f.head_position(0, -2), {"X": 0, "Y": -2})


if __name__ == "__main__":
    unittest.main()
