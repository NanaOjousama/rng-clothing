import unittest

from v5 import authored, source_backed


class SourceBackedCapFamily(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib = authored.load()

    def test_plain_preserves_source_and_has_no_decoration(self):
        for shape in source_backed.CAP_SHAPES:
            roll = source_backed.compose_cap(
                10, lib=self.lib, shape_variant=shape, variant="plain"
            )
            self.assertEqual("plain", roll.variant)
            self.assertIsNone(roll.decal_name)
            self.assertIsNone(roll.palette_id)
            self.assertFalse(roll.render.baked)
            self.assertEqual((), roll.render.dropped)

    def test_decorated_uses_only_live_approved_pool(self):
        for shape, approved in source_backed.CAP_DECALS.items():
            if not approved:
                with self.assertRaises(ValueError):
                    source_backed.compose_cap(
                        0, lib=self.lib, shape_variant=shape, variant="decorated"
                    )
                continue
            seen = set()
            for seed in range(200):
                roll = source_backed.compose_cap(
                    seed, lib=self.lib, shape_variant=shape, variant="decorated"
                )
                self.assertIn(roll.decal_name, approved)
                self.assertEqual(source_backed.CAP_DECOR_PALETTE, roll.palette_id)
                self.assertTrue(roll.render.baked)
                self.assertEqual((), roll.render.dropped)
                seen.add(roll.decal_name)
            self.assertEqual(set(approved), seen)

    def test_default_roll_is_deterministic(self):
        for seed in range(100):
            a = source_backed.compose_cap(seed, lib=self.lib)
            b = source_backed.compose_cap(seed, lib=self.lib)
            self.assertEqual(a.shape_variant, b.shape_variant)
            self.assertEqual(a.variant, b.variant)
            self.assertEqual(a.decal_name, b.decal_name)
            self.assertEqual(a.palette_id, b.palette_id)
            self.assertEqual(source_backed.sheet(a.render), source_backed.sheet(b.render))

    def test_both_shapes_and_both_variants_are_reachable(self):
        shapes = set()
        variants = set()
        for seed in range(200):
            roll = source_backed.compose_cap(seed, lib=self.lib)
            shapes.add(roll.shape_variant)
            variants.add(roll.variant)
        self.assertEqual(set(source_backed.CAP_SHAPES), shapes)
        self.assertEqual({"plain", "decorated"}, variants)


if __name__ == "__main__":
    unittest.main()
