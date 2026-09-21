import json
import unittest
from pathlib import Path

from v5.pngio import read_rgba_png
from v5.source.source_backed_renderer import apply_style_profile, extract_unique_motif
from v5.source.template_transfer import alpha_cells, load_contract, template_frames

ROOT = Path(__file__).resolve().parents[2]


class SourceBackedRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tpl = load_contract(ROOT / "generator/data/templates/slouch_pl24.json")
        cls.frames = template_frames(cls.tpl)
        cls.lib = json.loads((ROOT / "source_catalog/SOURCE_TRANSFER_LIBRARY.json").read_text())
        cls.catalog = json.loads((ROOT / "source_catalog/catalog.json").read_text())

    def test_style_transfer_preserves_locked_alpha(self):
        style = next(p for p in self.lib["parts"]
                     if p.get("id") == "More Accessories and Stuff::Hats::Beanie")
        for frame in self.frames.values():
            styled = apply_style_profile(frame, style)
            self.assertEqual(alpha_cells(frame), alpha_cells(styled))

    def test_cottagecore_leaf_reconstructs_sparse_3x3_mark(self):
        base = next(a for a in self.catalog["appearances"]
                    if a.get("pack")=="Cottagecore Set" and a.get("name")=="Beret")
        leaf = next(a for a in self.catalog["appearances"]
                    if a.get("pack")=="Cottagecore Set" and a.get("name")=="Beret (Leaf)")
        bs = read_rgba_png(Path(base["png_path"]))
        vs = read_rgba_png(Path(leaf["png_path"]))
        for view, box in base["analysis"]["boxes"].items():
            x,y,w,h = box
            b = [row[x:x+w] for row in bs[y:y+h]]
            v = [row[x:x+w] for row in vs[y:y+h]]
            motif = extract_unique_motif(b, v)
            self.assertEqual(7, len(motif), view)
            self.assertLessEqual(max(px for px,_,_ in motif)+1, 3)
            self.assertLessEqual(max(py for _,py,_ in motif)+1, 3)

    def test_rendered_proof_preserves_template_geometry(self):
        rendered = ROOT / "experiments/source_template_recipe_proof/rendered"
        for view, frame in self.frames.items():
            out = read_rgba_png(rendered / f"{view}.png")
            self.assertEqual(alpha_cells(frame), alpha_cells(out), view)


if __name__ == "__main__":
    unittest.main()
