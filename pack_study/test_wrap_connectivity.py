"""Regression tests for wrapped toppers; run: python3 -m unittest pack_study/test_wrap_connectivity.py."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'gen'))
import decorate as D


class WrapAttachmentTests(unittest.TestCase):
    def test_island_is_not_mistaken_for_contact(self):
        # One ornament pixel touches a host but another is disconnected.
        mask = [[0] * 10 for _ in range(10)]
        mask[5][5] = 1
        connected = [[5, 4, (1, 1, 1, 255)], [5, 3, (1, 1, 1, 255)]]
        isolated = connected + [[1, 1, (1, 1, 1, 255)]]
        self.assertTrue(D._all_part_pixels_attached(connected, mask))
        self.assertFalse(D._all_part_pixels_attached(isolated, mask))

    def test_unrepairable_island_rejects_without_inventing_pixels(self):
        mask = [[0] * 12 for _ in range(12)]
        mask[6][6] = 1
        # Distant free-floating piece cannot be connected with 1px shift.
        px = [[6, 5, (1, 1, 1, 255)], [0, 0, (1, 1, 1, 255)]]
        out = D._repair_wrap_islands(px, px, mask, mask, 0, 'right')
        self.assertIsNone(out)

    def test_connected_wrapped_part_remains_pixel_identical(self):
        mask = [[0] * 10 for _ in range(10)]
        mask[5][5] = 1
        px = [[5, 4, (7, 8, 9, 255)]]
        self.assertEqual(D._repair_wrap_islands(px, px, mask, mask, 0, 'right'), px)


if __name__ == '__main__':
    unittest.main()
