"""Stage 3: dependency filtering.

Rules are data. Each rule is (id, reason, predicate) where the predicate takes a
candidate dict of variable values and returns True when the candidate is INVALID.
The resolver rejects and rerolls; nothing downstream ever sees a rejected combo.
"""

from __future__ import annotations

from .vocabulary import COLLAR_SPAN, FIT_COLLAR_WIDENING, FLAP_DEPTH


def collar_cells(c: dict) -> int:
    """Shoulder collar span in logical columns, after RELAXED widening."""
    left, right = COLLAR_SPAN[c["collar_width"]]
    widen = FIT_COLLAR_WIDENING[c["fit"]]
    left = max(2, left - widen); right = min(13, right + widen)
    return (right - left + 1)


def flap_rows(c: dict) -> int:
    return min(9, FLAP_DEPTH[c["rear_flap_depth"]] + FIT_COLLAR_WIDENING[c["fit"]])


RULES: list[tuple[str, str, callable]] = [
    ("WIDE_COLLAR_NEEDS_BODY",
     "A WIDE collar over a SHALLOW flap reads as a bib, not a sailor collar: the front leaves outrun the back panel.",
     lambda c: c["collar_width"] == "WIDE" and c["rear_flap_depth"] == "SHALLOW"),

    ("NARROW_COLLAR_CANNOT_CARRY_DEEP_FLAP",
     "A DEEP flap hung from a NARROW collar span reads as a detached rectangle; the attachment edge is too short to support it.",
     lambda c: c["collar_width"] == "NARROW" and c["rear_flap_depth"] == "DEEP"),

    ("DOUBLE_TRIM_NEEDS_COLLAR_AREA",
     "DOUBLE trim needs two parallel lines with fabric between them; below 9 collar columns the lines merge.",
     lambda c: c["trim_style"] == "DOUBLE" and collar_cells(c) < 9),

    ("DOUBLE_TRIM_NEEDS_FLAP_DEPTH",
     "DOUBLE trim on the rear flap needs at least 6 rows so the second line is not on the attachment edge.",
     lambda c: c["trim_style"] == "DOUBLE" and flap_rows(c) < 6),

    ("KNIT_CANNOT_HOLD_DOUBLE_TRIM",
     "LIGHT_KNIT does not hold a crisp double stripe at this scale; the lines read as noise.",
     lambda c: c["material"] == "LIGHT_KNIT" and c["trim_style"] == "DOUBLE"),

    ("BOW_NEEDS_OPEN_NECKLINE",
     "A BOW needs a STANDARD_V opening to sit inside; on a SHALLOW_V it collides with the collar leaves.",
     lambda c: c["center_detail"] == "BOW" and c["neckline"] != "STANDARD_V"),

    ("CENTER_DETAIL_NEEDS_OPENING",
     "TIE and BOW both require a real neckline opening to hang from.",
     lambda c: c["center_detail"] in ("TIE", "BOW") and c["neckline"] not in ("SHALLOW_V", "STANDARD_V")),
]


def violations(candidate: dict) -> list[dict]:
    return [{"rule": rid, "reason": reason} for rid, reason, pred in RULES if pred(candidate)]


def is_valid(candidate: dict) -> bool:
    return not any(pred(candidate) for _, _, pred in RULES)
