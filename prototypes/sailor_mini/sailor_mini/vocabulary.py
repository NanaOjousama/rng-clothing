"""Stage 2 input: the variable vocabulary for SAILOR_TOP / CLASSIC_SQUARE_FLAP.

Only these eight variables exist in the prototype. Values carry weights so the
resolver has a defined prior; weights are not probabilities of quality.
"""

from __future__ import annotations

VARIABLES: dict[str, dict[str, int]] = {
    "fit":                {"FITTED": 3, "REGULAR": 4, "RELAXED": 3},
    "material":           {"COTTON": 4, "WOVEN": 3, "LIGHT_KNIT": 3},
    "collar_width":       {"NARROW": 3, "STANDARD": 4, "WIDE": 3},
    "rear_flap_depth":    {"SHALLOW": 3, "STANDARD": 4, "DEEP": 3},
    "neckline":           {"SHALLOW_V": 4, "STANDARD_V": 4},
    "trim_style":         {"NONE": 3, "SINGLE": 4, "DOUBLE": 3},
    "center_detail":      {"NONE": 3, "TIE": 4, "BOW": 3},
    "color_architecture": {"DARK_BODY_LIGHT_COLLAR": 4, "LIGHT_BODY_DARK_COLLAR": 3,
                           "MONOCHROME_WITH_CONTRAST_TRIM": 3, "LOW_CONTRAST_WITH_ACCENT": 3},
}

ORDER = tuple(VARIABLES)

# ---------------------------------------------------------------------------
# Numeric consequences of each value. These are ARCHITECTURE inputs (geometry),
# kept beside the vocabulary so the whole design space is readable in one file.
# ---------------------------------------------------------------------------

# collar span at the shoulder: (left_col, right_col) in the 16-wide logical frame
COLLAR_SPAN = {"NARROW": (4, 11), "STANDARD": (3, 12), "WIDE": (2, 13)}

# rear flap depth in logical rows, measured from row 0
FLAP_DEPTH = {"SHALLOW": 5, "STANDARD": 7, "DEEP": 9}

# row of the front V apex
V_DEPTH = {"SHALLOW_V": 5, "STANDARD_V": 7}

# lower-body taper applied by fit: cells removed from each side on rows 12-14
FIT_TAPER = {"FITTED": 1, "REGULAR": 0, "RELAXED": 0}

# RELAXED widens collar and flap proportions slightly (dependency rule 5)
FIT_COLLAR_WIDENING = {"FITTED": 0, "REGULAR": 0, "RELAXED": 1}

# material consequences (art grammar inputs)
MATERIAL = {
    "COTTON":     {"crisp_collar_edge": True,  "hem_rib": False, "fold_density": 1},
    "WOVEN":      {"crisp_collar_edge": True,  "hem_rib": False, "fold_density": 2},
    "LIGHT_KNIT": {"crisp_collar_edge": False, "hem_rib": True,  "fold_density": 0},
}
