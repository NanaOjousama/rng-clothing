"""The Fashion Sense export contract, as derived from the official reference.

Every assertion here corresponds to an entry in
`references/fashion-sense-official/BEHAVIOR_MAP.md`.  They exist because each
one is a failure mode that is SILENT in-game: a rejected model, a facing that
draws nothing, or a colour mask that is quietly ignored.
"""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, "tools")

from v5 import authored, hairpolicy


class HairPolicy(unittest.TestCase):
    """BEHAVIOR_MAP B1."""

    def test_policies_map_to_the_right_properties(self):
        self.assertEqual(hairpolicy.flags(hairpolicy.KEEP), {"HideHair": False})
        self.assertEqual(hairpolicy.flags(hairpolicy.HIDE), {"HideHair": True})
        bald = hairpolicy.flags(hairpolicy.BALD)
        self.assertTrue(bald["UseBaldHead"])
        # the hairstyle still draws over a bald head unless it is also hidden
        self.assertTrue(bald["HideHair"])

    def test_unknown_policy_is_rejected(self):
        with self.assertRaises(ValueError):
            hairpolicy.flags("BALDISH")

    def test_default_is_keep(self):
        """114 of 116 source hats keep hair; KEEP is what authors ship."""
        self.assertEqual(hairpolicy.load()["default"], hairpolicy.KEEP)
        for d, p in hairpolicy.for_base("felt_hat").items():
            self.assertEqual(p, hairpolicy.KEEP, d)

    def test_policy_is_resolvable_per_direction(self):
        got = hairpolicy.for_base("soft_cap")
        self.assertEqual(set(got), set(hairpolicy.DIRECTIONS))

    def test_source_declarations_are_preserved(self):
        app = {"directions": {"Front": {"HideHair": True}, "Back": {},
                              "Left": {}, "Right": {"UseBaldHead": True}}}
        got = hairpolicy.from_source(app)
        self.assertEqual(got["front"], hairpolicy.HIDE)
        self.assertEqual(got["right"], hairpolicy.BALD)
        self.assertEqual(got["back"], hairpolicy.KEEP)


class ExportContract(unittest.TestCase):
    """BEHAVIOR_MAP A2, A4, A5."""

    def setUp(self):
        from build_authored_fs_pack import hat_json
        self.hat_json = hat_json
        self.g = authored.build("soft_cap", "EVERYDAY_STONE_BLUE")

    def test_all_four_directions_are_emitted(self):
        """A facing whose model is absent draws NOTHING — no fallback."""
        d = self.hat_json(self.g, "t", 1)
        for key in ("FrontHat", "RightHat", "LeftHat", "BackHat"):
            self.assertIn(key, d)

    def test_positions_are_integers(self):
        """A float makes FS reject the whole appearance, silently."""
        d = self.hat_json(self.g, "t", 1)
        for key in ("FrontHat", "RightHat", "LeftHat", "BackHat"):
            for field in ("StartingPosition", "HeadPosition"):
                for axis in "XY":
                    v = d[key][field][axis]
                    self.assertIsInstance(v, int, f"{key}.{field}.{axis}")

    def test_format_is_declared(self):
        """Without it FS assumes format 1.0.0."""
        self.assertEqual(self.hat_json(self.g, "t", 1)["Format"], "7.5.0")

    def test_baked_colour_opts_out_of_grayscale(self):
        """All colour masks are ignored when DisableGrayscale is true, so the
        two are mutually exclusive; we bake, therefore we must opt out."""
        d = self.hat_json(self.g, "t", 1)
        for key in ("FrontHat", "RightHat", "LeftHat", "BackHat"):
            self.assertTrue(d[key]["DisableGrayscale"])
            self.assertNotIn("ColorMasks", d[key])
            self.assertNotIn("ColorMaskLayers", d[key])

    def test_hair_policy_reaches_the_json(self):
        d = self.hat_json(self.g, "t", 1)
        want = hairpolicy.for_base("soft_cap")
        for key, direction in (("FrontHat", "front"), ("BackHat", "back")):
            for prop, val in hairpolicy.flags(want[direction]).items():
                self.assertEqual(d[key][prop], val, f"{key}.{prop}")


if __name__ == "__main__":
    unittest.main()
