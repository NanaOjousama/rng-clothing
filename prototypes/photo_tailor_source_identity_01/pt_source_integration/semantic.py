"""Typed advisory wrapper around the audited Photo Tailor retriever port."""

from pt_advisory import retrieve

from .contracts import RankedSemanticCandidate, SourceAuthority


def rank_semantics(authority: SourceAuthority, model, query: str, *, limit=8):
    """Return ranked evidence bound to a source; never resolve a template."""
    if not authority.source_id or not authority.pixels_sha256:
        raise ValueError("Semantic evidence requires explicit source authority")
    if limit < 0:
        raise ValueError("limit must be nonnegative")
    result = retrieve(model, query)
    candidates = tuple(
        RankedSemanticCandidate(
            item_id=item["item_id"],
            name=item["name"],
            sprite_index=item["sprite_index"],
            score=item["score"],
        )
        for item in result["candidates"][:limit]
    )
    return result["status"], candidates
