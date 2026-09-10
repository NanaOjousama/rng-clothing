"""Prototype invariants. Run from prototypes/sailor_mini:

    python3 -B -m unittest discover -s tests
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from sailor_mini.batch import BASE_SEED, PAIRS, PALETTE_FAMILY, REQUESTS
from sailor_mini.body import COVERAGE_ROWS, W
from sailor_mini.render import DIRECTIONS, build_garment
from sailor_mini.resolve import derive, resolve
from sailor_mini.rules import is_valid, violations

PKG = Path(__file__).resolve().parents[1] / "sailor_mini"


def build(vid):
    label, pins = next((l, p) for i, l, p in REQUESTS if i == vid)
    spec = resolve(derive(BASE_SEED, vid) % 10_000_000, spec_id=vid, pinned=pins,
                   palette_family=PALETTE_FAMILY[vid])
    return spec, build_garment(spec)


class PrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.built = {vid: build(vid) for vid, _, _ in REQUESTS}

    # ---- isolation -------------------------------------------------------
    def test_no_imports_from_main_repo(self):
        for py in PKG.glob("*.py"):
            text = py.read_text(encoding="utf-8")
            for banned in ("generator", "rngc", "tools"):
                self.assertNotRegex(text, rf"^\s*(from|import)\s+{banned}\b",
                                    f"{py.name} imports {banned}")

    # ---- the construction invariant --------------------------------------
    def test_no_outline_on_attached_edges(self):
        """An ATTACHED edge must never receive a free-edge outline op.

        This is what stops the rear flap reading as a pasted square: its top and
        upper sides are attached and are deliberately left as fabric.
        """
        for vid, (spec, g) in self.built.items():
            for view, plan in g.plans.items():
                attached = {c for cells in plan.attached_edges.values() for c in cells}
                for op in g.render_plan[view]:
                    if "free_edge_outline" in op.system:
                        self.assertNotIn((op.x, op.y), attached, (vid, view, op.system))

    def test_flap_top_row_is_attached_and_unoutlined(self):
        for vid, (spec, g) in self.built.items():
            plan = g.plans["back"]
            flap = plan.regions["flap_back"]
            top = {(x, 0) for a, b in flap.rows[0] for x in range(a, b + 1)}
            self.assertTrue(top <= plan.attached_edges["flap_back"], vid)
            self.assertFalse(top & plan.free_edges["flap_back"], vid)

    def test_flap_casts_occlusion(self):
        for vid, (spec, g) in self.built.items():
            self.assertTrue(g.plans["back"].occlusion, f"{vid}: flap casts no shadow")

    def test_every_opaque_cell_has_provenance(self):
        for vid, (spec, g) in self.built.items():
            for d in DIRECTIONS:
                f = g.frames[d]
                for y in range(W):
                    for x in range(W):
                        if f.role[y][x]:
                            self.assertIsNotNone(f.system[y][x], (vid, d, x, y))

    # ---- render contract -------------------------------------------------
    def test_binary_alpha_and_dimensions(self):
        for vid, (spec, g) in self.built.items():
            for d in DIRECTIONS:
                img = g.images[d]
                self.assertEqual((len(img), len(img[0])), (W, W))
                self.assertTrue(all(p[3] in (0, 255) for r in img for p in r), vid)

    def test_single_connected_component(self):
        for vid, (spec, g) in self.built.items():
            for d in DIRECTIONS:
                cells = set(g.frames[d].alpha())
                todo = [next(iter(cells))]; seen = set()
                while todo:
                    c = todo.pop()
                    if c in seen: continue
                    seen.add(c); x, y = c
                    todo += [n for n in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)) if n in cells and n not in seen]
                self.assertEqual(seen, cells, (vid, d))

    def test_shoulder_coverage_intact(self):
        for vid, (spec, g) in self.built.items():
            for d in DIRECTIONS:
                for y in range(COVERAGE_ROWS):
                    self.assertTrue(any(g.frames[d].role[y][x] for x in range(W)), (vid, d, y))

    def test_left_is_mirror_of_right(self):
        for vid, (spec, g) in self.built.items():
            self.assertEqual(g.frames["right"].mirrored().role, g.frames["left"].role, vid)

    # ---- resolution ------------------------------------------------------
    def test_determinism(self):
        for vid, _, _ in REQUESTS:
            a = build(vid)[1]; b = build(vid)[1]
            for d in DIRECTIONS:
                self.assertEqual(a.images[d], b.images[d], vid)

    def test_dependency_rules_reject_known_bad_combinations(self):
        bad = {"fit": "REGULAR", "material": "COTTON", "collar_width": "NARROW",
               "rear_flap_depth": "DEEP", "neckline": "STANDARD_V", "trim_style": "SINGLE",
               "center_detail": "TIE", "color_architecture": "DARK_BODY_LIGHT_COLLAR"}
        self.assertFalse(is_valid(bad))
        self.assertEqual(violations(bad)[0]["rule"], "NARROW_COLLAR_CANNOT_CARRY_DEEP_FLAP")
        bow = {**bad, "rear_flap_depth": "STANDARD", "neckline": "SHALLOW_V", "center_detail": "BOW"}
        self.assertFalse(is_valid(bow))

    def test_resolver_never_emits_an_invalid_spec(self):
        for vid, (spec, g) in self.built.items():
            self.assertTrue(is_valid({k: getattr(spec, k) for k in
                                      ("fit", "material", "collar_width", "rear_flap_depth",
                                       "neckline", "trim_style", "center_detail", "color_architecture")}), vid)

    def test_controlled_pairs_differ_in_exactly_one_variable(self):
        keys = ("fit", "material", "collar_width", "rear_flap_depth", "neckline",
                "trim_style", "center_detail", "color_architecture", "palette_family")
        for a, b, var in PAIRS:
            sa, sb = self.built[a][0], self.built[b][0]
            diff = [k for k in keys if getattr(sa, k) != getattr(sb, k)]
            self.assertEqual(diff, [var], (a, b, diff))

    def test_batch_is_twelve_and_covers_the_space(self):
        self.assertEqual(len(REQUESTS), 12)
        specs = [s for s, _ in self.built.values()]
        for field in ("collar_width", "rear_flap_depth", "trim_style", "center_detail"):
            self.assertGreaterEqual(len({getattr(s, field) for s in specs}), 3, field)
        self.assertGreaterEqual(len({s.color_architecture for s in specs}), 4)


if __name__ == "__main__":
    unittest.main()
