import tempfile
import unittest
from pathlib import Path

from source_identity import VIEWS
from v5.pngio import read_rgba_png

from pt_source_integration.analysis import analyze_palette
from pt_source_integration.audit import export_prepared, preview_frames
from pt_source_integration.contracts import (
    EvidenceBundle,
    RegionMask,
    RegionTransform,
    RenderRecipe,
    SourceAuthority,
)
from pt_source_integration.pipeline import prepare_integration


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.frames = {
            view: [[
                (0, 0, 0, 0),
                (20, 40, 60, 255),
                (40, 60, 80, 255),
                (80, 90, 100, 128),
            ]] for view in VIEWS
        }
        self.authority = SourceAuthority.bind(
            "fixture_trucker", self.frames, provenance="unit-test explicit source")
        self.mask = RegionMask.reviewed_mask(
            "rear_mesh", self.authority,
            {view: [(1, 0), (2, 0)] for view in VIEWS},
            provenance="unit-test reviewed coordinates")

    def model(self):
        return {
            "vocabulary": ["trucker", "hat"], "idf": [1, 1],
            "ridge": {"coefficients": [[1, 0], [0, 1]], "intercept": [0, 0]},
            "items": [
                {"item_id": "16", "name": "Trucker", "sprite_index": 16,
                 "latent": [1, 0]},
                {"item_id": "4", "name": "Hat", "sprite_index": 4,
                 "latent": [0, 1]},
            ],
        }

    def test_identity_preview_export_and_audit_are_exact(self):
        result = prepare_integration(
            self.authority, RenderRecipe.identity(self.authority),
            semantic_model=self.model(), semantic_query="trucker hat")
        self.assertTrue(result.audit.identity_exact)
        self.assertTrue(result.audit.passed)
        self.assertEqual(preview_frames(result.prepared), self.authority.as_frames())
        self.assertEqual(result.evidence.automatic_pixel_operations, ())
        with tempfile.TemporaryDirectory() as directory:
            paths = export_prepared(result.prepared, directory)
            self.assertEqual(len(paths), 4)
            for view, path in zip(VIEWS, paths):
                self.assertEqual(read_rgba_png(path), self.frames[view])

    def test_reviewed_region_translation_changes_only_authorized_cells(self):
        transform = RegionTransform.source_relative("rear_mesh", {
            (20, 40, 60): (30, 35, 70),
            (40, 60, 80): (50, 55, 90),
        })
        recipe = RenderRecipe(self.authority.source_id, self.authority.pixels_sha256,
                              (self.mask,), (transform,))
        result = prepare_integration(self.authority, recipe)
        self.assertTrue(result.audit.passed)
        self.assertFalse(result.audit.identity_exact)
        self.assertEqual([view.changed_pixels for view in result.audit.views], [2] * 4)
        self.assertTrue(all(not view.outside_authority for view in result.audit.views))
        self.assertTrue(all(not view.alpha_changes for view in result.audit.views))

    def test_unreviewed_mask_cannot_authorize_transform(self):
        proposed = RegionMask.proposal(
            "rear_mesh", self.authority,
            {view: [(1, 0)] for view in VIEWS}, provenance="PT proposal")
        transform = RegionTransform.source_relative(
            "rear_mesh", {(20, 40, 60): (30, 35, 70)})
        recipe = RenderRecipe(self.authority.source_id, self.authority.pixels_sha256,
                              (proposed,), (transform,))
        with self.assertRaisesRegex(ValueError, "unreviewed"):
            prepare_integration(self.authority, recipe)

    def test_non_relative_mapping_is_rejected(self):
        transform = RegionTransform.source_relative("rear_mesh", {
            (20, 40, 60): (30, 35, 70),
            (40, 60, 80): (60, 60, 90),
        })
        recipe = RenderRecipe(self.authority.source_id, self.authority.pixels_sha256,
                              (self.mask,), (transform,))
        with self.assertRaisesRegex(ValueError, "translation"):
            prepare_integration(self.authority, recipe)

    def test_mask_bound_to_another_source_is_rejected(self):
        other_frames = {view: [[(1, 2, 3, 255)]] for view in VIEWS}
        other = SourceAuthority.bind(
            "other", other_frames, provenance="different source")
        foreign_mask = RegionMask.reviewed_mask(
            "rear_mesh", other, {view: [(0, 0)] for view in VIEWS},
            provenance="reviewed for another source")
        transform = RegionTransform.source_relative(
            "rear_mesh", {(1, 2, 3): (2, 3, 4)})
        recipe = RenderRecipe(self.authority.source_id, self.authority.pixels_sha256,
                              (foreign_mask,), (transform,))
        with self.assertRaisesRegex(ValueError, "different source pixels"):
            prepare_integration(self.authority, recipe)

    def test_collision_with_untouched_color_is_rejected(self):
        transform = RegionTransform.source_relative(
            "rear_mesh", {(20, 40, 60): (80, 90, 100)})
        recipe = RenderRecipe(self.authority.source_id, self.authority.pixels_sha256,
                              (self.mask,), (transform,))
        with self.assertRaisesRegex(ValueError, "collide"):
            prepare_integration(self.authority, recipe)

    def test_palette_suggestions_are_exact_and_never_approved(self):
        candidates = analyze_palette(self.authority, (self.mask,))
        self.assertEqual(candidates[0].rgb, (20, 40, 60))
        self.assertEqual(candidates[0].pixel_count, 4)
        self.assertEqual(candidates[0].regions, ("rear_mesh",))
        self.assertTrue(all(not candidate.approved_for_render for candidate in candidates))

    def test_evidence_cannot_contain_pixel_operations(self):
        with self.assertRaisesRegex(ValueError, "cannot authorize"):
            EvidenceBundle(
                self.authority.source_id, self.authority.pixels_sha256,
                self.authority.pixels_sha256, "NOT_REQUESTED",
                automatic_pixel_operations=("recolor",),
            )


if __name__ == "__main__":
    unittest.main()
