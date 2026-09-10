"""The pack emitter has to satisfy Fashion Sense, not just produce JSON."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
from v5.source import cap2_pack


WEAR = {"Front": {"HeadPosition": {"X": 1, "Y": -2},
                  "HatSize": {"Width": 20, "Length": 20}},
        "Right": {"HeadPosition": {"X": -3, "Y": 4}},
        "Left": {}, "Back": None}


class TestItemId(unittest.TestCase):
    def test_slug_strips_id_hostile_characters(self):
        # Our labels carry spaces and '#'; a qualified id is parsed as
        # '(H)<id>' and travels through shop data and console commands.
        s = cap2_pack.slug("Cap2 Rare Pastel ring+clasp #905331759")
        self.assertEqual(s, "Cap2_Rare_Pastel_ring_clasp_905331759")
        self.assertNotIn(" ", s)
        self.assertNotIn("#", s)

    def test_slug_collapses_runs_and_trims(self):
        self.assertEqual(cap2_pack.slug("  a ## b  "), "a_b")

    def test_item_id_uses_the_fs_format(self):
        self.assertEqual(cap2_pack.item_id("P.Q", "Cap 2 #1"),
                         "P.Q/Hat/Cap_2_1/Item")


class TestHatJson(unittest.TestCase):
    def setUp(self):
        self.doc = cap2_pack.hat_json("Cap 2 #1", WEAR, pack_id="P.Q",
                                      price=250, description="d")

    def test_item_declares_the_two_required_fields(self):
        # SpritePosition and SpriteSize are REQUIRED by FS; without them the
        # appearance never becomes a real item and the sewing machine cannot
        # hold it.
        item = self.doc["Item"]
        self.assertEqual(item["SpritePosition"], {"X": 0, "Y": 0})
        self.assertEqual(item["SpriteSize"], {"Width": 20, "Length": 20})

    def test_item_id_is_explicit_not_left_to_fs(self):
        self.assertEqual(self.doc["Item"]["Id"], "P.Q/Hat/Cap_2_1/Item")
        self.assertEqual(self.doc["Item"]["DisplayName"], "Cap 2 #1")

    def test_every_direction_gets_its_own_atlas_row(self):
        # A missing direction draws NOTHING in FS -- there is no mirroring and
        # no fallback -- so all four must be present.
        for j, d in enumerate(cap2_pack.DIRS):
            self.assertEqual(self.doc[f"{d}Hat"]["StartingPosition"],
                             {"X": 0, "Y": j * 20})

    def test_authored_wear_properties_survive(self):
        self.assertEqual(self.doc["FrontHat"]["HeadPosition"],
                         {"X": 1, "Y": -2})

    def test_starting_position_is_never_carried_from_source(self):
        # The source atlas has its own layout; ours is four stacked frames.
        src = {"Front": {"StartingPosition": {"X": 99, "Y": 99}}}
        doc = cap2_pack.hat_json("n", src, pack_id="P")
        self.assertEqual(doc["FrontHat"]["StartingPosition"], {"X": 0, "Y": 0})


class TestDefaults(unittest.TestCase):
    def test_missing_head_position_defaults_to_zero(self):
        d = cap2_pack.default_head_positions(WEAR)
        self.assertEqual(d["Left"], {"X": 0, "Y": 0})
        self.assertEqual(d["Back"], {"X": 0, "Y": 0})

    def test_authored_head_position_is_recorded_for_reset(self):
        # Reset must restore the GENERATED default exactly. 63% of source hats
        # rely on a non-zero HeadPosition, so assuming {0,0} would move them.
        d = cap2_pack.default_head_positions(WEAR)
        self.assertEqual(d["Front"], {"X": 1, "Y": -2})
        self.assertEqual(d["Right"], {"X": -3, "Y": 4})


class TestAtlas(unittest.TestCase):
    def test_four_frames_stacked_in_dirs_order(self):
        f = {d: [[(i, 0, 0, 255)] * 20 for _ in range(20)]
             for i, d in enumerate(cap2_pack.DIRS)}
        a = cap2_pack.atlas(f)
        self.assertEqual(len(a), 80)
        for i in range(4):
            self.assertEqual(a[i * 20][0][0], i)


class TestSidecarAgainstRealRolls(unittest.TestCase):
    """The sidecar is only useful if it matches what was actually drawn."""

    @classmethod
    def setUpClass(cls):
        os.chdir(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))))
        from v5 import authored
        from v5.source.cap2_gen import Cap2Generator
        cls.gen = Cap2Generator(authored.load())

    def side(self, seed):
        spec = self.gen.roll(seed)
        frames = self.gen.render(spec)
        return spec, frames, cap2_pack.fitting_json(
            spec, self.gen, frames, pack_id="P", name=spec.label())

    def test_base_pixels_cover_the_whole_safe_mask(self):
        # Moving a motif means repainting what it left behind, so every safe
        # cell needs a known no-motif colour.
        _, _, s = self.side(846106117)
        safe = {tuple(c) for c in s["motif"]["safe_cells"]}
        got = {tuple(int(v) for v in k.split(",")) for k in s["motif"]["base_pixels"]}
        self.assertEqual(safe, got)

    def test_base_pixels_are_the_undrawn_colour_not_the_motif_colour(self):
        spec, frames, s = self.side(846106117)
        self.assertNotEqual(spec.motif_id, "plain")
        colour = s["motif"]["colour"]
        for c in s["motif"]["cells"]:
            key = f"{c[0]},{c[1]}"
            # the frame currently shows the motif here...
            self.assertEqual(list(frames["Front"][c[1]][c[0]])[:3], colour)
            # ...but the sidecar remembers the crown underneath
            self.assertNotEqual(s["motif"]["base_pixels"][key][:3], colour)

    def test_non_motif_safe_cells_match_the_rendered_frame(self):
        _, frames, s = self.side(846106117)
        motif = {tuple(c) for c in s["motif"]["cells"]}
        for k, v in s["motif"]["base_pixels"].items():
            x, y = (int(t) for t in k.split(","))
            if (x, y) in motif:
                continue
            self.assertEqual(list(frames["Front"][y][x]), v, f"cell {k}")

    def test_plain_cap_has_no_motif_colour(self):
        _, _, s = self.side(530893608)
        self.assertEqual(s["motif"]["id"], "plain")
        self.assertEqual(s["motif"]["cells"], [])
        self.assertIsNone(s["motif"]["colour"])

    def test_motif_cells_are_inside_the_safe_mask(self):
        for seed in (905331759, 846106117, 721353155):
            _, _, s = self.side(seed)
            safe = {tuple(c) for c in s["motif"]["safe_cells"]}
            for c in s["motif"]["cells"]:
                self.assertIn(tuple(c), safe, f"seed {seed} cell {c}")

    def test_locked_rolls_never_add_back_hardware(self):
        for seed in range(100):
            spec = self.gen.roll(seed)
            self.assertEqual(spec.closure_id, "none")
            self.assertEqual(spec.closure_cells, [])
            self.assertNotIn("closure_contrast", spec.contrast)

    def test_legacy_buckle_spec_cannot_paint_back_hardware(self):
        spec = self.gen.roll(905331759)
        original = self.gen.render(spec)["Back"]
        spec.closure_id = "clasp"
        spec.closure_cells = [(10, 6)]
        self.assertEqual(self.gen.render(spec)["Back"], original)

    def test_front_motif_uses_lowest_legal_placement(self):
        for name in self.gen.marks:
            cells, _ = self.gen.place(name)
            self.assertTrue(all(cell in self.gen.safe for cell in cells))
            self.assertFalse(all((column, row + 1) in self.gen.safe
                                 for column, row in cells))

    def test_export_persists_replayable_spec(self):
        import tempfile
        from dataclasses import asdict
        spec = self.gen.roll(846106117)
        frames = self.gen.render(spec)
        with tempfile.TemporaryDirectory() as directory:
            side = cap2_pack.write_cap(directory, spec, self.gen, frames,
                                      pack_id="P", name=spec.label())
            with open(os.path.join(directory, "spec.json")) as saved:
                self.assertEqual(json.load(saved), json.loads(json.dumps(asdict(spec))))
            self.assertTrue(side["player_fitting"])


if __name__ == "__main__":
    unittest.main()
