"""COLOR ARCHITECTURE + CHROMATIC RESOLUTION (sections 21-24).

    Color Architecture -> semantic roles -> harmony / contrast / base hue
    -> material-aware ramps -> concrete pixel colours

No garment piece ever rolls an arbitrary RGB.  Pieces reference fabric roles;
AG asks the palette for (role, ramp step).
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass

from .grammar import (FABRIC_ROLES, MIN_RAMP_DEPTH, RAMP_STEPS, luminance,
                      perceptual_distance)
from .material import Material

# ---------------------------------------------------------------------------
# ramp geometry
# ---------------------------------------------------------------------------

# Lightness offset from a role's base value, per named step.
_STEP_L = {"deep": -0.27, "shadow": -0.165, "mid": -0.075,
           "base": 0.0, "light": 0.105, "highlight": 0.195}
# Pixel-art convention: shadows cool and saturate, highlights warm and desaturate.
_STEP_H = {"deep": -0.055, "shadow": -0.036, "mid": -0.015,
           "base": 0.0, "light": 0.018, "highlight": 0.034}
_STEP_S = {"deep": 0.14, "shadow": 0.10, "mid": 0.04,
           "base": 0.0, "light": -0.07, "highlight": -0.14}

_DEPTH_STEPS = {
    4: ("shadow", "mid", "base", "light"),
    5: ("deep", "shadow", "mid", "base", "light"),
    6: RAMP_STEPS,
}


@dataclass(frozen=True)
class RoleSpec:
    """A colour relationship, not a colour."""
    hue_relation: str     # base | analog_warm | analog_cool | complement | neutral | metal
    lightness: float      # target base lightness 0..1
    saturation: float     # multiplier on the garment saturation
    # Draw from another role's ramp instead of minting a parallel one.  The
    # hand-authored references paint the yoke, the sleeves and the shirt body
    # from ONE navy ramp and separate them by form, not by hue — aliasing is how
    # a garment reaches ~11 colours instead of ~19 without losing any region.
    alias: str | None = None


# How low a Color Architecture is allowed to take its darkest ramp step.
# The corpus finding that only 11.6% of garments contain near-black is about
# OUTLINES, not about ramps: all 19 hand-authored sailor tops measured put their
# darkest pixel below luminance 40 (median 28), because navy IS the garment.
# So the floor belongs to the Color Architecture, not to a global clamp.
VALUE_FLOOR = {"midtone": 0.155, "dark_anchor": 0.075}


@dataclass(frozen=True)
class ColorArchitecture:
    name: str
    roles: dict            # role -> RoleSpec
    contrast_tier: float   # 0..1, how far apart the major masses sit
    formality_weight: dict
    value_anchor: str = "midtone"
    # Optional constraint on the garment's base hue.  Used where the authored
    # tradition itself is chromatic: every ground in the reference sailor set is
    # cool, and a brown middy stops reading as a middy.
    hue_band: tuple | None = None


def _ca(name, contrast, formality, value_anchor="midtone", hue_band=None, **roles):
    return ColorArchitecture(name, roles, contrast, formality, value_anchor, hue_band)


COLOR_ARCHITECTURES = {
    a.name: a for a in (
        # Dark-anchored, like the middy palettes: CLASSIC's identity is collar
        # against body, and it only reaches the reference's value depth if the
        # ground is allowed to go properly dark.
        _ca("DARK_BODY_LIGHT_COLLAR", 0.82,
            {"work": 1.0, "casual": 1.2, "smart": 1.2, "formal": 1.1}, "dark_anchor",
            body=RoleSpec("base", 0.26, 1.00),
            trim=RoleSpec("neutral", 0.84, 0.14),
            accent=RoleSpec("complement", 0.55, 1.05),
            secondary_accent=RoleSpec("neutral", 0.84, 0.14, alias="trim"),
            hardware=RoleSpec("neutral", 0.84, 0.14, alias="trim"),
            under_layer=RoleSpec("neutral", 0.78, 0.10)),
        _ca("LIGHT_BODY_DARK_COLLAR", 0.78,
            {"work": 1.1, "casual": 1.1, "smart": 1.0, "formal": 0.9},
            body=RoleSpec("neutral", 0.80, 0.16),
            trim=RoleSpec("base", 0.28, 1.00),
            accent=RoleSpec("complement", 0.50, 1.10),
            secondary_accent=RoleSpec("neutral", 0.80, 0.16, alias="body"),
            hardware=RoleSpec("neutral", 0.80, 0.16, alias="body"),
            under_layer=RoleSpec("base", 0.34, 0.95)),
        _ca("MONOCHROME_CONTRAST_TRIM", 0.55,
            {"work": 1.2, "casual": 0.9, "smart": 1.2, "formal": 1.3},
            body=RoleSpec("base", 0.46, 0.90),
            trim=RoleSpec("base", 0.72, 0.62),
            accent=RoleSpec("base", 0.24, 1.05),
            secondary_accent=RoleSpec("base", 0.72, 0.62, alias="trim"),
            hardware=RoleSpec("base", 0.72, 0.62, alias="trim"),
            under_layer=RoleSpec("base", 0.60, 0.70)),
        _ca("LOW_CONTRAST_STRONG_ACCENT", 0.38,
            {"work": 1.0, "casual": 1.1, "smart": 1.0, "formal": 0.8},
            body=RoleSpec("base", 0.52, 0.78),
            trim=RoleSpec("analog_cool", 0.60, 0.72),
            accent=RoleSpec("complement", 0.52, 1.25),
            secondary_accent=RoleSpec("neutral", 0.86, 0.10),
            hardware=RoleSpec("neutral", 0.86, 0.10, alias="secondary_accent"),
            under_layer=RoleSpec("analog_warm", 0.66, 0.55)),
        # --- HEADWEAR ONLY ------------------------------------------------
        # Measured in the four hats the user picked as good, against 116 vanilla
        # hats and 120 of ours:
        #
        #   pixels in a hue distinct from the body   good 15.6%  vanilla 8.1%
        #                                            OURS 0.0%
        #
        # Not 'low' — zero.  Headwear paints exactly two roles, body and trim,
        # and in every Color Architecture the HAT family was allowed, trim is
        # either the body's own hue or a neutral.  A band could therefore only
        # ever be a lighter or darker stripe of the hat, never a ribbon made of
        # a different material, which is what the references all have.
        #
        # The four references disagree about HOW the accent separates, so these
        # do too rather than picking one recipe:
        #   BoysCap    hue 31deg, VALUE 74, saturation x0.98   value-led
        #   SweetGent  hue 31deg, value 34, SATURATION x0.24   saturation-led
        #   hyoung_11  no chromatic accent at all              must stay legal
        # so MONOCHROME_CONTRAST_TRIM keeps its place in the vocabulary.
        _ca("CHROMATIC_BAND", 0.70,
            {"work": 1.0, "casual": 1.2, "smart": 1.0, "formal": 0.8},
            body=RoleSpec("base", 0.40, 0.95),
            # the band is a different material, so a different hue at full
            # strength — this is the one that moves far-hue share off zero
            trim=RoleSpec("complement", 0.52, 1.30),
            accent=RoleSpec("complement", 0.52, 1.30, alias="trim"),
            secondary_accent=RoleSpec("neutral", 0.86, 0.10),
            hardware=RoleSpec("neutral", 0.86, 0.10, alias="secondary_accent"),
            under_layer=RoleSpec("base", 0.30, 0.90)),
        # Saturation-led, after SweetGent: the band is the same family as the
        # body but washed out, which reads as felt against leather.
        _ca("MUTED_BAND", 0.74,
            {"work": 1.2, "casual": 1.0, "smart": 1.1, "formal": 1.0}, "dark_anchor",
            body=RoleSpec("base", 0.34, 1.05),
            trim=RoleSpec("analog_warm", 0.58, 0.26),
            accent=RoleSpec("analog_warm", 0.58, 0.26, alias="trim"),
            secondary_accent=RoleSpec("neutral", 0.88, 0.08),
            hardware=RoleSpec("neutral", 0.88, 0.08, alias="secondary_accent"),
            under_layer=RoleSpec("base", 0.28, 1.00)),
        _ca("SPLIT_BODY_ACCENT", 0.66,
            {"work": 0.9, "casual": 1.2, "smart": 0.9, "formal": 0.6},
            body=RoleSpec("base", 0.40, 0.95),
            trim=RoleSpec("neutral", 0.86, 0.12),
            accent=RoleSpec("analog_warm", 0.58, 1.15),
            secondary_accent=RoleSpec("complement", 0.48, 1.10),
            hardware=RoleSpec("neutral", 0.86, 0.12, alias="trim"),
            under_layer=RoleSpec("neutral", 0.82, 0.12)),
        # Authored against the SailorStyles reference set: a near-black dominant
        # mass, a near-white under layer, and one strongly saturated accent.
        _ca("DARK_YOKE_LIGHT_BLOUSE", 0.92,
            {"work": 0.7, "casual": 1.2, "smart": 1.3, "formal": 1.2}, "dark_anchor",
            (0.48, 0.78),
            body=RoleSpec("base", 0.19, 1.00),
            trim=RoleSpec("base", 0.19, 1.00, alias="body"),
            accent=RoleSpec("warm_signal", 0.58, 1.65),
            secondary_accent=RoleSpec("neutral", 0.92, 0.07, alias="under_layer"),
            # Pearl studs on navy: the hardware is the same white as the blouse,
            # so it costs no extra ramp.
            hardware=RoleSpec("neutral", 0.92, 0.07, alias="under_layer"),
            under_layer=RoleSpec("neutral", 0.92, 0.07)),
        # Tonal variant: the same dark ground, but the tie is the blouse white
        # rather than a warm signal.  Gives the family real variety without
        # inverting the yoke, which is what stopped MIDDY reading.
        _ca("DARK_YOKE_TONAL", 0.90,
            {"work": 1.0, "casual": 1.0, "smart": 1.2, "formal": 1.1}, "dark_anchor",
            (0.50, 0.78),
            body=RoleSpec("base", 0.21, 0.92),
            trim=RoleSpec("base", 0.21, 0.92, alias="body"),
            accent=RoleSpec("neutral", 0.90, 0.10),
            secondary_accent=RoleSpec("neutral", 0.90, 0.10, alias="accent"),
            hardware=RoleSpec("neutral", 0.90, 0.10, alias="accent"),
            under_layer=RoleSpec("neutral", 0.90, 0.10, alias="accent")),
        # The point of this one is the contrasting dickey, but its collar sat
        # only 57 luminance off the body and the V dissolved.  The collar is now
        # a light neutral, so the relationship it names is preserved while the
        # construction it sits on still reads.
        # The canonical pairing on both reference sheets (section 8, "Navy +
        # White" / "White + Navy"): a near-white shell, a dark cool collar and a
        # warm signal tie.  Everything white in the garment — blouse, braid,
        # hardware — is the same white, which is why it lands near 10 colours.
        _ca("SAILOR_WHITE_NAVY", 0.90,
            {"work": 0.9, "casual": 1.3, "smart": 1.2, "formal": 1.0}, "dark_anchor",
            (0.52, 0.72),
            body=RoleSpec("neutral", 0.88, 0.07),
            trim=RoleSpec("base", 0.21, 1.00),
            accent=RoleSpec("warm_signal", 0.58, 1.55),
            secondary_accent=RoleSpec("neutral", 0.88, 0.07, alias="body"),
            hardware=RoleSpec("neutral", 0.88, 0.07, alias="body"),
            under_layer=RoleSpec("neutral", 0.88, 0.07, alias="body")),
        _ca("CONTRAST_UNDER_LAYER", 0.78,
            {"work": 1.0, "casual": 1.2, "smart": 1.0, "formal": 0.7}, "dark_anchor",
            body=RoleSpec("base", 0.30, 0.92),
            trim=RoleSpec("neutral", 0.86, 0.13),
            accent=RoleSpec("complement", 0.46, 1.20),
            secondary_accent=RoleSpec("neutral", 0.86, 0.13, alias="trim"),
            hardware=RoleSpec("neutral", 0.86, 0.13, alias="trim"),
            under_layer=RoleSpec("complement", 0.40, 1.10)),
    )
}

# An absolute warm band for signal accents.  Not arbitrary RGB: it is a
# relationship to the garment's TEMPERAMENT rather than to its base hue, and it
# is what every bow in the reference set does — red, orange or gold on navy,
# regardless of what the navy is.
SIGNAL_HUE = {"cool": 0.015, "neutral": 0.045, "warm": 0.075}

# Aliasing note: `hardware` no longer mints its own metal ramp anywhere.  A
# stud or a button at 8x8 is one or two cells; giving it a private five-step
# ramp cost 3-5 colours per garment and bought nothing readable.

HARMONIES = {
    "monochrome":   {"analog_warm": 0.0,  "analog_cool": 0.0,  "complement": 0.0},
    "analogous":    {"analog_warm": 0.075, "analog_cool": -0.075, "complement": 0.16},
    "complementary": {"analog_warm": 0.055, "analog_cool": -0.055, "complement": 0.50},
    "split_complement": {"analog_warm": 0.06, "analog_cool": -0.06, "complement": 0.42},
}

# Base hue bands by chromatic temperament (turns of the wheel).
_HUE_BANDS = {
    "cool":    ((0.52, 0.70), (0.42, 0.52)),
    "neutral": ((0.05, 0.14), (0.55, 0.66)),
    "warm":    ((0.94, 1.06), (0.03, 0.12)),
}


def _wrap(h: float) -> float:
    return h % 1.0


def _clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else (hi if v > hi else v)


def _rgb(h, s, l) -> tuple:
    r, g, b = colorsys.hls_to_rgb(_wrap(h), max(0.0, min(1.0, l)), max(0.0, min(1.0, s)))
    return (round(r * 255), round(g * 255), round(b * 255), 255)


@dataclass
class Palette:
    """One garment-level palette shared by every view (INV-11 support)."""
    architecture: str
    harmony: str
    base_hue: float
    saturation: float
    contrast_tier: float
    depth: int
    ramps: dict            # role -> {step_name: rgba}
    steps: tuple           # ordered step names, dark -> light

    def color(self, role: str, step: str) -> tuple:
        ramp = self.ramps[role]
        if step in ramp:
            return ramp[step]
        return ramp[self.steps[len(self.steps) // 2]]

    def shift(self, role: str, step: str, delta: int) -> str:
        """Move `delta` steps darker (+) or lighter (-) inside the role's own ramp."""
        i = self.steps.index(step) if step in self.steps else len(self.steps) // 2
        return self.steps[max(0, min(len(self.steps) - 1, i - delta))]

    @property
    def all_colors(self) -> set:
        return {c for ramp in self.ramps.values() for c in ramp.values()}

    def contrast(self, a: tuple, b: tuple) -> float:
        """Value contrast — what an edge treatment can act on."""
        return abs(luminance(a) - luminance(b))

    def separation(self, a: tuple, b: tuple) -> float:
        """Perceptual separation — what identity checks should act on."""
        return perceptual_distance(a, b)


def resolve_palette(arch_name: str, harmony: str, temperament: str,
                    material: Material, stream, contrast_nudge: float = 0.0,
                    min_depth: int = MIN_RAMP_DEPTH,
                    ramp_spread: float = 1.0) -> Palette:
    """Pass 6B — chromatic resolution."""
    ca = COLOR_ARCHITECTURES[arch_name]
    band = ca.hue_band or _HUE_BANDS[temperament][0 if stream.chance(0.62) else 1]
    base_hue = _wrap(stream.unit() * (band[1] - band[0]) + band[0])
    saturation = 0.30 + 0.42 * stream.unit()
    saturation *= material.saturation_scale
    contrast = max(0.15, min(1.0, ca.contrast_tier + material.contrast_bias + contrast_nudge))

    depth = max(MIN_RAMP_DEPTH, min_depth, material.ramp_depth)
    steps = _DEPTH_STEPS[depth]
    offsets = HARMONIES[harmony]

    ramps: dict[str, dict] = {}
    aliases: dict[str, str] = {}
    for role in FABRIC_ROLES:
        spec = ca.roles.get(role)
        if spec is None:
            continue
        if spec.alias:
            aliases[role] = spec.alias
            continue
        if spec.hue_relation == "warm_signal":
            hue, sat = SIGNAL_HUE[temperament], min(1.0, saturation * spec.saturation)
        elif spec.hue_relation == "metal":
            hue, sat = _wrap(base_hue * 0.0 + 0.11), 0.46
        elif spec.hue_relation == "neutral":
            hue, sat = base_hue, saturation * spec.saturation
        else:
            hue = _wrap(base_hue + offsets.get(spec.hue_relation, 0.0))
            sat = saturation * spec.saturation
        # Contrast tier pushes the major masses apart around mid-lightness, but
        # the ramp is kept off both rails: the corpus shows only 11.6% of
        # garments contain near-black, so ramps must not bottom out (section 3).
        # A slot with a wide ramp also needs somewhere dark to put it.  The
        # "ramps must not bottom out" floor was derived from CLOTHING, where
        # only 11.6% of the corpus contains near-black.  Headwear is the
        # opposite: vanilla hats sit at a darkest luminance of 15 and the four
        # reference hats at 26, against our 47.  The floor is relieved in
        # proportion to the slot's declared spread, so clothing keeps the exact
        # value it has today.
        floor = VALUE_FLOOR[ca.value_anchor] / max(1.0, ramp_spread)
        ceil = 0.965
        light = _clamp(0.5 + (spec.lightness - 0.5) * (0.55 + 0.60 * contrast),
                       floor + 0.05, 0.90)
        amp = material.ramp_amplitude * ramp_spread
        # Compress rather than clamp.  Clamping a dark role against the floor
        # collapses its darkest steps into one flat colour and the ramp stops
        # reading; scaling keeps every step distinct inside the legal range.
        lo = _STEP_L[steps[0]] * amp
        hi = _STEP_L[steps[-1]] * amp
        down = min(1.0, (light - floor) / -lo) if lo < 0 else 1.0
        up = min(1.0, (ceil - light) / hi) if hi > 0 else 1.0
        ramps[role] = {
            step: _rgb(hue + _STEP_H[step] * amp,
                       sat + _STEP_S[step] * amp * 0.8,
                       light + _STEP_L[step] * amp * (down if _STEP_L[step] < 0 else up))
            for step in steps
        }
    for role, target in aliases.items():
        ramps[role] = ramps[target]
    return Palette(arch_name, harmony, base_hue, saturation, contrast, depth, ramps, steps)
