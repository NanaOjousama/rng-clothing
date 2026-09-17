"""Neutral-fidelity gates for the Cap family Source-Backed V2 candidates."""
from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from v5 import source_backed as sbm  # noqa: E402

BASES = ("cap_baseball", "cap_snapback")
ORDER = ("front", "right", "left", "back")
LAYOUT_KEYS = ("StartingPosition", "Flipped")


def expected_sheet(b):
    rows = []
    for v in ORDER:
        if v in b.mirrored:
            src = b.source[b.mirrored[v]]
            f = [list(reversed(row)) for row in src]
        else:
            f = b.source[v]
        rows.extend([list(r) for r in f])
    return rows


class CapSourceBackedV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bases = {n: sbm.load_one(n) for n in BASES}

    def test_neutral_pixels_are_exact_source_views(self):
        for n, b in self.bases.items():
            with self.subTest(base=n):
                r = sbm.render(b)
                self.assertFalse(r.baked)
                self.assertEqual(sbm.sheet(r), expected_sheet(b))
                self.assertFalse(r.dropped)

    def test_source_hash_is_pinned(self):
        for n, b in self.bases.items():
            with self.subTest(base=n):
                self.assertEqual(sbm.md5(os.path.join(ROOT, b.source_png)), b.source_md5)

    def test_source_view_and_flip_metadata_is_preserved(self):
        for n, b in self.bases.items():
            with self.subTest(base=n):
                self.assertEqual(b.views, ("front", "right", "back"))
                self.assertEqual(b.mirrored, {"left": "right"})
                self.assertFalse(b.placement_override)
                for v in ORDER:
                    self.assertEqual(b.placement(v), {"X": 0, "Y": 0})

    def test_neutral_hat_json_keeps_non_layout_source_fields(self):
        for n, b in self.bases.items():
            with self.subTest(base=n):
                src = sbm.read_fs_json(os.path.join(ROOT, b.source_png.replace("hat.png", "hat.json")))
                got = sbm.hat_json(sbm.render(b), n)
                for v in ORDER:
                    key = sbm.MODEL_OF[v]
                    want_fields = {k: val for k, val in src[key].items() if k not in LAYOUT_KEYS}
                    got_fields = {k: val for k, val in got[key].items() if k not in LAYOUT_KEYS}
                    self.assertEqual(got_fields, want_fields, f"{n}/{key}")
                    self.assertNotIn("Flipped", got[key])
                    self.assertEqual(got[key]["StartingPosition"], {"X": 0, "Y": ORDER.index(v) * 20})

    def test_baseball_and_snapback_are_not_the_same_construction(self):
        a, b = self.bases["cap_baseball"], self.bases["cap_snapback"]
        for v in ("front", "right", "back"):
            with self.subTest(view=v):
                self.assertNotEqual(a.source[v], b.source[v])


if __name__ == "__main__":
    unittest.main()
