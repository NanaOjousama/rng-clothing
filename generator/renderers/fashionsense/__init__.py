"""Optional Fashion Sense content-pack renderer backend."""

from generator.renderers.fashionsense.hd_jacket import (
    BodyCoverageValidation,
    FashionSenseJacketRender,
    build_body_coverage_envelopes,
    composite_default_frame,
    render_mistral_hd_jacket,
    validate_body_coverage,
)
from generator.renderers.fashionsense.hd_art_grammar import (
    HDArtTreatment,
    composite_art_default_frame,
    load_hd_art_grammar,
    render_hd_art_treatment,
)
from generator.renderers.fashionsense.hd_garment_v2 import (
    FSPermanentGarmentRender,
    build_hd_regions,
    classify_edge_exposure,
    load_hd_garment_grammar_v2,
    render_fs_hd_v2,
    select_side_template,
    validate_hd_coverage,
)
from generator.renderers.fashionsense.hd_quality import (
    FSHDQualityDiagnostics,
    diagnose_fs_hd_render,
)
from generator.renderers.fashionsense.surface_v3 import (
    FSV3Diagnostics,
    FSV3SurfaceRender,
    diagnose_fs_v3,
    render_fs_v3,
)
from generator.renderers.fashionsense.article_v4 import (
    FSV4ArticleRender,
    load_v4_article_grammar,
    render_fs_v4,
)
from generator.renderers.fashionsense.extended_v45 import (
    FSV45PrototypeRender,
    load_v45_fs_grammar,
    render_v45_prototype,
)
from generator.renderers.fashionsense.lower_body_v46 import (
    V46Render,
    appearance_json as appearance_json_v46,
    render_v46,
)
from generator.renderers.fashionsense.lower_body_v46b import (
    V46BRender,
    appearance_json_v46b,
    render_v46b,
)
from generator.renderers.fashionsense.unified_v5a import (
    FSV5AUnifiedRender,
    load_v5a_fs_grammar,
    render_fs_v5a,
)
from generator.renderers.fashionsense.upper_v5b import (
    FSV5BUpperRender,
    load_v5b_fs_grammar,
    render_fs_v5b,
)

__all__ = [
    "BodyCoverageValidation",
    "FashionSenseJacketRender",
    "build_body_coverage_envelopes",
    "composite_default_frame",
    "render_mistral_hd_jacket",
    "validate_body_coverage",
    "HDArtTreatment",
    "composite_art_default_frame",
    "load_hd_art_grammar",
    "render_hd_art_treatment",
    "FSPermanentGarmentRender",
    "build_hd_regions",
    "classify_edge_exposure",
    "load_hd_garment_grammar_v2",
    "render_fs_hd_v2",
    "select_side_template",
    "validate_hd_coverage",
    "FSHDQualityDiagnostics",
    "diagnose_fs_hd_render",
    "FSV3Diagnostics",
    "FSV3SurfaceRender",
    "diagnose_fs_v3",
    "render_fs_v3",
    "FSV4ArticleRender",
    "load_v4_article_grammar",
    "render_fs_v4",
    "FSV45PrototypeRender",
    "load_v45_fs_grammar",
    "render_v45_prototype",
    "V46Render",
    "appearance_json_v46",
    "render_v46",
    "V46BRender",
    "appearance_json_v46b",
    "render_v46b",
    "FSV5AUnifiedRender",
    "load_v5a_fs_grammar",
    "render_fs_v5a",
    "FSV5BUpperRender",
    "load_v5b_fs_grammar",
    "render_fs_v5b",
]
