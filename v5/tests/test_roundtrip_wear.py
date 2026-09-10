"""SOURCE PACK ROUND-TRIP WEAR FIDELITY — mandatory for source-derived assets.

Exact pixel reconstruction is not sufficient and was never the thing that was
broken.  A hat wears according to the model properties AROUND its pixels, and
the first source exporter dropped them: it hardcoded HeadPosition {0, 0} while
293 of the 462 direction blocks in the library declare a non-zero one.  Art
that was correct got re-anchored by up to 16 screen pixels.

These tests assert that a source appearance survives our pipeline with its wear
behaviour intact, so the failure cannot come back silently.
"""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from v5.source import roundtrip

CATALOG = "source_catalog/catalog.json"


def _catalog():
    return json.load(open(CATALOG))


@unittest.skipUnless(os.path.isfile(CATALOG), "source catalog not built")
class RoundTripWearFidelity(unittest.TestCase):

    def setUp(self):
        self.hats = [a for a in _catalog()["appearances"]
                     if a["category"] == "Hats"
                     and not a["analysis"].get("error")
                     and a["analysis"].get("boxes")]

    def test_no_wear_property_is_dropped(self):
        """Whatever the author declared must survive the round-trip."""
        for app in self.hats:
            doc, _, rep = roundtrip.export(app)
            self.assertEqual(rep["properties_dropped"], {},
                             f"{app['name']}: dropped {rep['properties_dropped']}")

    def test_every_property_matches_the_source(self):
        """StartingPosition is rewritten by design; nothing else may differ."""
        for app in self.hats:
            doc, _, _ = roundtrip.export(app)
            cmp = roundtrip.compare(app, doc)
            self.assertEqual(cmp["differences"], [],
                             f"{app['name']}: {cmp['differences'][:2]}")

    def test_head_position_is_never_silently_zeroed(self):
        """The specific bug: a non-zero HeadPosition must come through."""
        checked = 0
        for app in self.hats:
            blocks = roundtrip.source_blocks(app)
            doc, _, _ = roundtrip.export(app)
            for d, src in blocks.items():
                want = src.get("HeadPosition")
                if not want or (want.get("X"), want.get("Y")) == (0, 0):
                    continue
                got = doc[f"{d}Hat"].get("HeadPosition")
                self.assertEqual(got, want, f"{app['name']} {d}")
                checked += 1
        self.assertGreater(checked, 200,
                           "expected the library's ~293 non-zero HeadPosition "
                           "blocks to be exercised")

    def test_per_direction_values_are_not_flattened(self):
        """Some hats anchor each facing differently; one value for all is wrong."""
        varied = []
        for app in self.hats:
            blocks = roundtrip.source_blocks(app)
            seen = {json.dumps(b.get("HeadPosition"), sort_keys=True)
                    for b in blocks.values() if b.get("HeadPosition")}
            if len(seen) > 1:
                varied.append(app)
        self.assertTrue(varied, "expected hats with per-direction HeadPosition")
        for app in varied:
            doc, _, _ = roundtrip.export(app)
            cmp = roundtrip.compare(app, doc)
            self.assertEqual(cmp["differences"], [], app["name"])

    def test_flipped_is_preserved(self):
        """`Flipped` reuses one drawn side for both facings; losing it mirrors
        the wrong way or duplicates a frame."""
        flipped = []
        for app in self.hats:
            blocks = roundtrip.source_blocks(app)
            if any(b.get("Flipped") for b in blocks.values()):
                flipped.append(app)
        self.assertTrue(flipped, "expected sources using Flipped")
        for app in flipped:
            doc, _, _ = roundtrip.export(app)
            blocks = roundtrip.source_blocks(app)
            for d, src in blocks.items():
                self.assertEqual(doc[f"{d}Hat"].get("Flipped"),
                                 src.get("Flipped"), f"{app['name']} {d}")


if __name__ == "__main__":
    unittest.main()
