"""Legacy output must stay byte-identical while Source-Backed V2 lives beside it.

    python3 -m unittest tests.test_legacy_render_guard -v
"""
from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import legacy_render_guard  # noqa: E402


class LegacyRenderGuard(unittest.TestCase):
    def test_every_legacy_render_is_byte_identical(self):
        want, got, moved, new = legacy_render_guard.check()
        self.assertGreater(len(want), 1900)
        self.assertFalse(moved, f"{len(moved)} legacy renders moved, e.g. {moved[:5]}")
        self.assertFalse(new, f"legacy render set grew unexpectedly: {new[:5]}")


if __name__ == "__main__":
    unittest.main()
