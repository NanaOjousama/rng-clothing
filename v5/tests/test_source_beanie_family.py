import hashlib, unittest
from pathlib import Path
from v5 import source_backed
from v5.pngio import read_rgba_png

ROOT=Path(__file__).resolve().parents[2]

class BeanieSourceBackedV1(unittest.TestCase):
    def test_both_constructions_load_and_render_neutral(self):
        for name in ("beanie_cuffed","beanie_slouch"):
            b=source_backed.load_one(name)
            r=source_backed.render(b)
            self.assertEqual((),r.dropped)
            self.assertFalse(r.baked)

    def test_expected_sizes_and_direction_contracts(self):
        cuffed=source_backed.load_one("beanie_cuffed")
        slouch=source_backed.load_one("beanie_slouch")
        self.assertEqual((20,20),cuffed.size)
        self.assertEqual(("front","right","left","back"),cuffed.views)
        self.assertEqual({},cuffed.mirrored)
        self.assertEqual((16,16),slouch.size)
        self.assertEqual(("front","right","back"),slouch.views)
        self.assertEqual({"left":"right"},slouch.mirrored)

    def test_semantic_alpha_exact_and_cuff_zone_present(self):
        for name in ("beanie_cuffed","beanie_slouch"):
            b=source_backed.load_one(name)
            for view in b.views:
                alpha={(x,y) for y,row in enumerate(b.source[view]) for x,p in enumerate(row) if p[3]}
                self.assertEqual(alpha,set(b.semantic.view(view)))
                self.assertIn("cuff",b.semantic.zones[view])

    def test_source_hash_is_pinned(self):
        for name in ("beanie_cuffed","beanie_slouch"):
            b=source_backed.load_one(name)
            p=ROOT/b.source_png
            got=hashlib.md5(p.read_bytes()).hexdigest()
            self.assertEqual(b.source_md5,got)

if __name__=="__main__":
    unittest.main()
