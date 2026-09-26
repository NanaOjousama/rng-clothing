"""Stage-ordered integration around the source-authoritative render kernel."""

from dataclasses import asdict, dataclass

from .analysis import analyze_palette, analyze_texture
from .audit import DiffAudit, audit_diff
from .contracts import EvidenceBundle, RenderRecipe, SourceAuthority
from .render import PreparedPixels, prepare_pixels
from .semantic import rank_semantics


@dataclass(frozen=True)
class IntegrationResult:
    authority: SourceAuthority
    prepared: PreparedPixels
    audit: DiffAudit
    evidence: EvidenceBundle

    def report(self):
        return {
            "schema": "pt-source-integration/v1",
            "source": {
                "source_id": self.authority.source_id,
                "pixels_sha256": self.authority.pixels_sha256,
                "frame_sizes": self.authority.frame_sizes,
                "provenance": self.authority.provenance,
            },
            "prepared": {
                "pixels_sha256": self.prepared.pixels_sha256,
                "operations": self.prepared.operations,
                "preview_export_same_immutable_pixels": True,
            },
            "audit": asdict(self.audit),
            "evidence": asdict(self.evidence),
            "authority_contract": {
                "final_pixels_owned_by": "explicit source + reviewed masks + source-relative transforms",
                "photo_tailor_role": "advisory evidence/ranking/palette/texture/preview structure",
                "automatic_pixel_operations_from_evidence": [],
            },
            "excluded_photo_tailor_systems": (
                "generic_hat_renderer", "recolor", "harmonize", "shade_ramps",
                "canonical_projection", "uv_mapping", "whole_hat_region_authority",
                "procedural_bands", "procedural_patterns", "procedural_motifs",
                "runtime", "menus", "migration_rerender",
            ),
        }


def prepare_integration(authority: SourceAuthority, recipe: RenderRecipe, *,
                        semantic_model=None, semantic_query="", palette_limit=None):
    """Render first, then attach advisory evidence that cannot alter the result."""
    prepared = prepare_pixels(authority, recipe)
    audit = audit_diff(authority, prepared)
    if not audit.passed:
        raise AssertionError("Source-preserving render audit failed")

    # Only reviewed masks enter region-scoped analysis. They still do not own pixels.
    masks = recipe.masks
    palette = analyze_palette(authority, masks, limit=palette_limit)
    texture = analyze_texture(authority, masks)
    if semantic_model is None:
        semantic_status, semantic_candidates = "NOT_REQUESTED", ()
    else:
        semantic_status, semantic_candidates = rank_semantics(
            authority, semantic_model, semantic_query)
    evidence = EvidenceBundle(
        source_id=authority.source_id,
        source_sha256=authority.pixels_sha256,
        prepared_pixels_sha256=prepared.pixels_sha256,
        semantic_status=semantic_status,
        semantic_candidates=semantic_candidates,
        palette_candidates=palette,
        texture_evidence=texture,
    )
    return IntegrationResult(authority, prepared, audit, evidence)
