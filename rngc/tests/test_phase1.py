"""Phase 1 architecture tests. Run: python3 -m unittest rngc.tests.test_phase1

The first two tests are the NO-POLISH INVARIANT: every opaque output cell must
trace to the blank or an authored piece, and the compositor must not contain
neighbour-inspecting shading logic.
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

from rngc.colorize import colorize
from rngc.compose import compose
from rngc.data import DATA, Library
from rngc.roleimage import DIRECTIONS, SIZE, SRC_NONE
from rngc.validate import validate

PKG = Path(__file__).resolve().parents[1]
FORBIDDEN_IN_COMPOSE = ("neighbor", "neighbour", "luminance", "exterior", "contour", "polish", "smooth", "outline", "[y - 1]", "[y + 1]", "[y-1]", "[y+1]", "x - 1", "x + 1", "x-1", "x+1")


class Phase1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib = Library.load(DATA)
        cls.built = {}
        for pid, plan in cls.lib.plans.items():
            r = compose(plan, cls.lib); f = colorize(r, cls.lib.palettes[plan.palette])
            cls.built[pid] = (r, f, validate(r, f, cls.lib))

    # ---- NO-POLISH INVARIANT ----
    def test_every_opaque_cell_has_provenance(self):
        for pid, (r, _, _) in self.built.items():
            for d in DIRECTIONS:
                img = r.images[d]
                for y in range(SIZE):
                    for x in range(SIZE):
                        if img.role[y][x]:
                            self.assertNotEqual(img.src[y][x], SRC_NONE, (pid, d, x, y))
                            self.assertNotEqual(img.provenance(x, y, r.piece_ids), "NONE")

    def test_compositor_has_no_neighbour_logic(self):
        src = (PKG / "compose.py").read_text(encoding="utf-8")
        lines = src.splitlines()
        # strip docstrings (by AST line range) and comments, then scan executable code only
        tree = ast.parse(src)
        drop = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.Module, ast.ClassDef)) and node.body and isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0], "value", None), ast.Constant):
                drop.update(range(node.body[0].lineno - 1, node.body[0].end_lineno))
        body = "\n".join(l.split("#")[0] for i, l in enumerate(lines) if i not in drop)
        for token in FORBIDDEN_IN_COMPOSE:
            self.assertNotIn(token, body, f"compose.py must not contain {token!r}")
        # no function in compose/colorize reads a cell other than the one it writes
        for mod in ("compose.py", "colorize.py"):
            text = (PKG / mod).read_text(encoding="utf-8")
            self.assertNotRegex(text, r"role\[y\s*[+-]\s*1\]|role\[ny\]|\[x\s*[+-]\s*1\]", mod)

    def test_no_legacy_imports(self):
        for py in PKG.glob("*.py"):
            text = py.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"^\s*(from|import)\s+generator\b", f"{py.name} imports legacy generator")
            self.assertNotRegex(text, r"^\s*(from|import)\s+tools\b", f"{py.name} imports legacy tools")

    # ---- structural ----
    def test_all_plans_validate(self):
        for pid, (_, _, rep) in self.built.items():
            self.assertEqual(rep["status"], "PASS", (pid, [c for c in rep["checks"] if c["status"] == "FAIL"]))

    def test_left_is_mirror_when_no_left_data(self):
        for pid, (r, _, _) in self.built.items():
            if r.explicit_left: continue
            m = r.images["right"].mirrored()
            self.assertEqual(m.role, r.images["left"].role, pid); self.assertEqual(m.slot, r.images["left"].slot, pid)

    def test_exactly_one_blank_and_piece_budget(self):
        self.assertEqual(len(self.lib.blanks), 1)
        self.assertLessEqual(len(self.lib.pieces), 12)

    def test_reuse_gate(self):
        usage = {pid: [p for p in self.lib.plans if any(pp.id == pid for pp in self.lib.plans[p].pieces) and p.startswith("bench_")] for pid in self.lib.pieces}
        reused = [pid for pid, plans in usage.items() if len(plans) >= 2]
        self.assertGreaterEqual(len(reused), 3, usage)

    def test_cross_products_exist_and_pass(self):
        x = [pid for pid in self.built if pid.startswith("xprod_")]
        self.assertGreaterEqual(len(x), 3)
        for pid in x:
            self.assertEqual(self.built[pid][2]["status"], "PASS", pid)

    def test_no_plan_paints_on_transparent(self):
        for pid, (r, _, _) in self.built.items():
            self.assertEqual(r.skipped, [], (pid, r.skipped))

    def test_determinism(self):
        for pid, plan in self.lib.plans.items():
            a = compose(plan, self.lib); b = compose(plan, self.lib)
            for d in DIRECTIONS:
                self.assertEqual(a.images[d].role, b.images[d].role); self.assertEqual(a.images[d].src, b.images[d].src)


if __name__ == "__main__":
    unittest.main()
