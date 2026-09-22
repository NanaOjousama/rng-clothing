from pathlib import Path

from sf_pipeline.model import (
    CandidateOutput,
    DirectionAsset,
    DirectionSetManifest,
    PromotionStatus,
)
from sf_pipeline.promotion import can_transition, transition
from sf_pipeline.qc import candidate_qc, direction_qc, promotion_allowed


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_promotion_state_machine():
    assert can_transition(
        PromotionStatus.GENERATED_UNREVIEWED,
        PromotionStatus.CANDIDATE_FRONT_APPROVED,
    )
    assert not can_transition(
        PromotionStatus.GENERATED_UNREVIEWED,
        PromotionStatus.PRODUCTION_APPROVED,
    )


def test_candidate_qc_accepts_known_small_sf_asset():
    repo = _repo()
    path = repo / "experiments/spritefusion_beanie_material_rescale_test_01/accepted_32_and_under/material_00.png"
    out = CandidateOutput(
        index=0,
        asset_id="fixture",
        local_path=str(path),
        width=20,
        height=20,
    )
    report = candidate_qc(out)
    assert report["passMechanical"] is True
    assert report["semanticHumanReviewRequired"] is True
    assert max(report["width"], report["height"]) <= 32


def test_direction_qc_requires_all_eight():
    manifest = DirectionSetManifest(
        id="fixture",
        source_candidate_id="fixture",
        source_asset_id="fixture",
        requested_size=16,
    )
    report = direction_qc(manifest)
    assert report["passMechanical"] is False
    assert any(x.startswith("missing_directions:") for x in report["issues"])


def test_production_requires_all_gates():
    assert promotion_allowed(
        PromotionStatus.PRODUCTION_APPROVED,
        candidate_ok=True,
        direction_ok=True,
        human_art_approved=True,
        esm_wear_approved=True,
    )
    assert not promotion_allowed(
        PromotionStatus.PRODUCTION_APPROVED,
        candidate_ok=True,
        direction_ok=True,
        human_art_approved=False,
        esm_wear_approved=True,
    )
    assert not promotion_allowed(
        PromotionStatus.QC_APPROVED,
        candidate_ok=True,
        direction_ok=True,
        human_art_approved=True,
        esm_wear_approved=True,
    )
