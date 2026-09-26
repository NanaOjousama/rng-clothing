"""Connect PT advisory infrastructure to the accepted source trace.

This proof is deliberately identity-only: the accepted 26x26 trace has no
reviewed component masks yet, so no transform is authorized and no art is made.
"""

from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(LAB))

from v5.pngio import read_rgba_png
from pt_source_integration.contracts import RenderRecipe, SourceAuthority
from pt_source_integration.pipeline import prepare_integration

TRACE = LAB / "source_traced_trucker_template_02_native_front"
MODEL = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/PhotoTailor/models/semantic_hats.json")
VIEWS = ("front", "right", "left", "back")


def save_new_or_identical(path, payload):
    if path.exists() and path.read_bytes() != payload:
        raise ValueError(f"Refusing to overwrite different integration evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(payload)


def run():
    frames = {view: read_rgba_png(TRACE / "aligned_source" / f"{view}.png")
              for view in VIEWS}
    authority = SourceAuthority.bind(
        "source_traced_trucker_template_02_native_front",
        frames,
        provenance=str(TRACE / "source_trace_contract.json"),
    )
    model = json.loads(MODEL.read_text()) if MODEL.exists() else None
    result = prepare_integration(
        authority,
        RenderRecipe.identity(authority),
        semantic_model=model,
        semantic_query="trucker hat mesh in the back",
        palette_limit=12,
    )
    report = result.report()
    report["proof_scope"] = {
        "render": "IDENTITY_ONLY",
        "reviewed_component_masks_available": False,
        "styled_outputs_created": 0,
        "batch_created": False,
        "semantic_model": str(MODEL) if model is not None else "NOT_AVAILABLE",
    }
    payload = (json.dumps(report, indent=2) + "\n").encode()
    save_new_or_identical(HERE / "proof" / "integration_report.json", payload)
    print(json.dumps({
        "source_sha256": authority.pixels_sha256,
        "prepared_sha256": result.prepared.pixels_sha256,
        "identity_exact": result.audit.identity_exact,
        "audit_passed": result.audit.passed,
        "semantic_status": result.evidence.semantic_status,
        "palette_candidates": len(result.evidence.palette_candidates),
        "texture_evidence_records": len(result.evidence.texture_evidence),
        "automatic_pixel_operations": list(result.evidence.automatic_pixel_operations),
    }, indent=2))


if __name__ == "__main__":
    run()
