"""Palette selection. Literal colours only — no derivation engine in the prototype.

A colour family supplies a dark ramp, a light ramp and one accent. The
COLOR_ARCHITECTURE decides which ramp lands in which garment slot.
Slots: body, collar, trim, accent.
"""

from __future__ import annotations

RGBA = tuple[int, int, int, int]


def _hex(v: str) -> RGBA:
    v = v.lstrip("#")
    return int(v[:2], 16), int(v[2:4], 16), int(v[4:6], 16), 255


def _ramp(deep, shadow, base, light) -> dict[str, RGBA]:
    return {"deep": _hex(deep), "shadow": _hex(shadow), "base": _hex(base), "light": _hex(light)}


FAMILIES = {
    "NAVY_WHITE": {
        "dark":  _ramp("#101725", "#1C2A44", "#2C4269", "#46608C"),
        "light": _ramp("#8A93A0", "#BFC6CF", "#EDF1F5", "#FFFFFF"),
        "accent": _ramp("#5A1A1E", "#8C2A30", "#C93B42", "#E06C6B"),
        "mid":   _ramp("#2B3646", "#465468", "#6E7E93", "#98A6B8"),
    },
    "INK_CREAM": {
        "dark":  _ramp("#14131A", "#26242F", "#3A3846", "#565365"),
        "light": _ramp("#8F8A78", "#C4BBA4", "#EDE4CC", "#FBF6E8"),
        "accent": _ramp("#6B4E1E", "#9C7A33", "#C9A24A", "#E6C877"),
        "mid":   _ramp("#33313C", "#4E4B59", "#726E7E", "#9A96A6"),
    },
    "SEA_GREEN": {
        "dark":  _ramp("#0F1F1C", "#1B352F", "#2A5148", "#427167"),
        "light": _ramp("#8C9A90", "#BECABD", "#E9F0E6", "#FBFDF8"),
        "accent": _ramp("#7A4A12", "#B06F1F", "#E09A33", "#F2C069"),
        "mid":   _ramp("#25382F", "#3D5648", "#5F7A68", "#89A08D"),
    },
    "PORT_RED": {
        "dark":  _ramp("#25101A", "#451E28", "#6C2F3A", "#934B54"),
        "light": _ramp("#9A8F8C", "#CBBFB9", "#F2E9E2", "#FFFAF4"),
        "accent": _ramp("#12293F", "#1F4364", "#2F638F", "#5386B3"),
        "mid":   _ramp("#3B2830", "#5A424A", "#7D6068", "#A2868C"),
    },
    "SLATE_STONE": {
        "dark":  _ramp("#191B20", "#2E3138", "#474B55", "#666B77"),
        "light": _ramp("#7E8188", "#A8ACB4", "#D2D6DC", "#EFF2F5"),
        "accent": _ramp("#6B3320", "#9A4F2E", "#C87344", "#E39A6C"),
        "mid":   _ramp("#33363D", "#4C5058", "#6C707A", "#8F939C"),
    },
    "HARBOUR_BLUE": {
        "dark":  _ramp("#111E2C", "#1E3A4F", "#2E5A78", "#4A7EA0"),
        "light": _ramp("#8E9A9E", "#BFCACD", "#E8F0F2", "#FBFEFF"),
        "accent": _ramp("#6E1F2A", "#A0323F", "#CE5460", "#E68A92"),
        "mid":   _ramp("#26343F", "#3E505E", "#617584", "#8B9DAA"),
    },
}
FAMILY_ORDER = tuple(FAMILIES)

# COLOR_ARCHITECTURE -> which family ramp fills each slot
ARCHITECTURE_MAP = {
    "DARK_BODY_LIGHT_COLLAR":        {"body": "dark",  "collar": "light", "trim": "dark",   "accent": "accent"},
    "LIGHT_BODY_DARK_COLLAR":        {"body": "light", "collar": "dark",  "trim": "light",  "accent": "accent"},
    # collar and body share a ramp: the collar is invisible by colour, so its
    # identity is carried entirely by the free-edge outline and the light trim.
    "MONOCHROME_WITH_CONTRAST_TRIM": {"body": "dark",  "collar": "dark",  "trim": "light",  "accent": "light"},
    # deliberately moderate collar/body separation with one strong accent
    "LOW_CONTRAST_WITH_ACCENT":      {"body": "mid",   "collar": "dark",  "trim": "mid",    "accent": "accent"},
}


def build_palette(family: str, color_architecture: str) -> dict[str, dict[str, RGBA]]:
    fam = FAMILIES[family]
    return {slot: dict(fam[ramp]) for slot, ramp in ARCHITECTURE_MAP[color_architecture].items()}


def contrast(pal, a="collar", b="body") -> float:
    def lum(c): return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    return round(abs(lum(pal[a]["base"]) - lum(pal[b]["base"])), 1)
