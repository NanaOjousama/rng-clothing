"""Stage 8 input: the 12 controlled test variants.

Each request pins the variables the batch is designed to exercise and leaves the
rest to the resolver. Two controlled pairs change exactly one variable.
"""

from __future__ import annotations

BASE_SEED = 771020

# (id, label, pins)
REQUESTS: list[tuple[str, str, dict]] = [
    # --- coverage of collar states -----------------------------------------
    ("v01_narrow_shallow", "Narrow collar / shallow flap", {
        "collar_width": "NARROW", "rear_flap_depth": "SHALLOW", "trim_style": "SINGLE",
        "center_detail": "TIE", "neckline": "SHALLOW_V", "fit": "FITTED", "material": "COTTON",
        "color_architecture": "DARK_BODY_LIGHT_COLLAR"}),
    ("v02_standard_standard", "Standard collar / standard flap", {
        "collar_width": "STANDARD", "rear_flap_depth": "STANDARD", "trim_style": "SINGLE",
        "center_detail": "TIE", "neckline": "STANDARD_V", "fit": "REGULAR", "material": "WOVEN",
        "color_architecture": "DARK_BODY_LIGHT_COLLAR"}),
    ("v03_wide_deep", "Wide collar / deep flap", {
        "collar_width": "WIDE", "rear_flap_depth": "DEEP", "trim_style": "DOUBLE",
        "center_detail": "BOW", "neckline": "STANDARD_V", "fit": "RELAXED", "material": "WOVEN",
        "color_architecture": "DARK_BODY_LIGHT_COLLAR"}),

    # --- controlled pair A: flap depth is the only difference ---------------
    ("pairA1_flap_standard", "PAIR A: standard flap", {
        "collar_width": "STANDARD", "rear_flap_depth": "STANDARD", "trim_style": "SINGLE",
        "center_detail": "NONE", "neckline": "STANDARD_V", "fit": "REGULAR", "material": "COTTON",
        "color_architecture": "LIGHT_BODY_DARK_COLLAR"}),
    ("pairA2_flap_deep", "PAIR A: deep flap", {
        "collar_width": "STANDARD", "rear_flap_depth": "DEEP", "trim_style": "SINGLE",
        "center_detail": "NONE", "neckline": "STANDARD_V", "fit": "REGULAR", "material": "COTTON",
        "color_architecture": "LIGHT_BODY_DARK_COLLAR"}),

    # --- controlled pair B: trim count is the only difference ---------------
    ("pairB1_trim_single", "PAIR B: single trim", {
        "collar_width": "WIDE", "rear_flap_depth": "STANDARD", "trim_style": "SINGLE",
        "center_detail": "TIE", "neckline": "STANDARD_V", "fit": "REGULAR", "material": "WOVEN",
        "color_architecture": "MONOCHROME_WITH_CONTRAST_TRIM"}),
    ("pairB2_trim_double", "PAIR B: double trim", {
        "collar_width": "WIDE", "rear_flap_depth": "STANDARD", "trim_style": "DOUBLE",
        "center_detail": "TIE", "neckline": "STANDARD_V", "fit": "REGULAR", "material": "WOVEN",
        "color_architecture": "MONOCHROME_WITH_CONTRAST_TRIM"}),

    # --- centre detail coverage --------------------------------------------
    ("v08_no_detail_knit", "No centre detail, light knit", {
        "collar_width": "STANDARD", "rear_flap_depth": "STANDARD", "trim_style": "NONE",
        "center_detail": "NONE", "neckline": "SHALLOW_V", "fit": "RELAXED", "material": "LIGHT_KNIT",
        "color_architecture": "LOW_CONTRAST_WITH_ACCENT"}),
    ("v09_bow_light_body", "Bow, light body dark collar", {
        "collar_width": "STANDARD", "rear_flap_depth": "DEEP", "trim_style": "SINGLE",
        "center_detail": "BOW", "neckline": "STANDARD_V", "fit": "FITTED", "material": "COTTON",
        "color_architecture": "LIGHT_BODY_DARK_COLLAR"}),

    # --- colour architecture coverage --------------------------------------
    ("v10_mono_trim", "Monochrome with contrast trim", {
        "collar_width": "STANDARD", "rear_flap_depth": "STANDARD", "trim_style": "DOUBLE",
        "center_detail": "TIE", "neckline": "STANDARD_V", "fit": "REGULAR", "material": "COTTON",
        "color_architecture": "MONOCHROME_WITH_CONTRAST_TRIM"}),
    ("v11_low_contrast", "Low contrast with accent", {
        "collar_width": "NARROW", "rear_flap_depth": "STANDARD", "trim_style": "SINGLE",
        "center_detail": "TIE", "neckline": "STANDARD_V", "fit": "FITTED", "material": "LIGHT_KNIT",
        "color_architecture": "LOW_CONTRAST_WITH_ACCENT"}),
    ("v12_wide_relaxed_knit", "Wide relaxed knit, shallow V", {
        "collar_width": "WIDE", "rear_flap_depth": "STANDARD", "trim_style": "SINGLE",
        "center_detail": "NONE", "neckline": "SHALLOW_V", "fit": "RELAXED", "material": "LIGHT_KNIT",
        "color_architecture": "DARK_BODY_LIGHT_COLLAR"}),
]

# palette families are pinned per request so the two controlled pairs differ in
# exactly one variable and nothing else, including colour.
PALETTE_FAMILY = {
    "v01_narrow_shallow": "NAVY_WHITE", "v02_standard_standard": "HARBOUR_BLUE",
    "v03_wide_deep": "INK_CREAM", "pairA1_flap_standard": "PORT_RED",
    "pairA2_flap_deep": "PORT_RED", "pairB1_trim_single": "SLATE_STONE",
    "pairB2_trim_double": "SLATE_STONE", "v08_no_detail_knit": "SEA_GREEN",
    "v09_bow_light_body": "NAVY_WHITE", "v10_mono_trim": "INK_CREAM",
    "v11_low_contrast": "SEA_GREEN", "v12_wide_relaxed_knit": "PORT_RED",
}

PAIRS = [("pairA1_flap_standard", "pairA2_flap_deep", "rear_flap_depth"),
         ("pairB1_trim_single", "pairB2_trim_double", "trim_style")]
