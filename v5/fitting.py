"""Per-item fitting adjustments for generated hats.

MEASURED CONSTRAINTS, not assumed (session 20260909-104628, nine models, one
sprite, only HeadPosition varying):

    integer offsets  76/76 exact pixel match; each unit moves exactly 4 screen
                     pixels at Scale 4, crisply, with no interpolation.
    half offsets     X+0.5, X-0.5, Y+0.5, Y-0.5 all produced BYTE-IDENTICAL
                     output to one another -- sign and axis made no difference
                     -- and the hat was not drawn at all. `Position` is
                     `int X, int Y`, so a fractional value fails to
                     deserialise and Fashion Sense silently declines to render
                     while still LISTING the appearance.

So one adjustment step is one sprite pixel, and fractional values are never
written. The exporter's integer assertion stays as the last line of defence.

DIRECTION. Fashion Sense's HeadPosition runs opposite to screen direction:
HeadPosition X+1 moved the hat 4px LEFT, Y+1 moved it 4px UP. Players should
never meet that. The mapping is inverted here, once, so "Move Right" moves the
hat right on screen and the sign convention stays inside this module.

DEFAULTS ARE NOT OVERWRITTEN. A generated item keeps its authored position;
the player's adjustment is a separate delta added at export time, so Reset is
always possible and re-rolling the same seed still reproduces the same base.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict

# One step is one sprite pixel = 4 screen pixels at Scale 4.
STEP = 1
SCREEN_PX_PER_STEP = 4

# Hat adjustment is deliberately bounded: fitting is nudging, not relocating.
HAT_RANGE = 3

STORE = "authored/fitting_adjustments.json"


@dataclass
class Fit:
    """A player's adjustment for one generated item, in SCREEN directions.

    right/down are positive. The Fashion Sense sign inversion is applied only
    in `head_position()`, so nothing outside this module has to know about it.
    """
    item_id: str
    hat_right: int = 0
    hat_down: int = 0
    motif_right: int = 0
    motif_down: int = 0

    def head_position(self, default_x: int, default_y: int) -> dict:
        """Final HeadPosition: the authored default plus the player's delta.

        Inverted, because HeadPosition X+1 draws 4px LEFT and Y+1 draws 4px UP.
        """
        # Validate BEFORE converting. An earlier version called int() first
        # and then compared, which silently truncated 0.5 to 0 and could never
        # fire -- exactly the class of bug this guard exists to catch, since a
        # fractional HeadPosition makes Fashion Sense stop drawing the hat.
        for name, v in (("default_x", default_x), ("default_y", default_y),
                        ("hat_right", self.hat_right),
                        ("hat_down", self.hat_down)):
            if float(v) != int(v):
                raise ValueError(
                    f"{name}={v!r} is fractional; HeadPosition is integer-only "
                    "and a fractional value makes Fashion Sense silently skip "
                    "drawing the appearance")
        return {"X": int(default_x) - int(self.hat_right),
                "Y": int(default_y) - int(self.hat_down)}

    def screen_offset(self) -> tuple:
        """What the player should see, in screen pixels."""
        return (self.hat_right * SCREEN_PX_PER_STEP,
                self.hat_down * SCREEN_PX_PER_STEP)

    def is_default(self) -> bool:
        return not (self.hat_right or self.hat_down
                    or self.motif_right or self.motif_down)


def clamp_hat(fit: Fit) -> tuple:
    """(fit, blocked) — hat movement is bounded, and a blocked move is refused
    rather than silently clamped to something the player did not ask for."""
    blocked = []
    for name in ("hat_right", "hat_down"):
        v = getattr(fit, name)
        if abs(v) > HAT_RANGE:
            blocked.append(name)
            setattr(fit, name, max(-HAT_RANGE, min(HAT_RANGE, v)))
    return fit, blocked


def move_hat(fit: Fit, dx: int, dy: int) -> tuple:
    """Try a hat nudge. Returns (ok, reason)."""
    nx, ny = fit.hat_right + dx, fit.hat_down + dy
    if abs(nx) > HAT_RANGE or abs(ny) > HAT_RANGE:
        return False, f"outside the +/-{HAT_RANGE} px fitting range"
    fit.hat_right, fit.hat_down = nx, ny
    return True, ""


def move_motif(fit: Fit, cells, safe, dx: int, dy: int) -> tuple:
    """Try a motif nudge. Returns (ok, reason, new_cells).

    Every cell of the SHIFTED shape must be legal. A motif that would leave the
    safe mask is blocked whole -- never clipped, never deformed, never partly
    moved -- because a half-moved mark is a different mark.
    """
    nx, ny = fit.motif_right + dx, fit.motif_down + dy
    moved = [(x + nx, y + ny) for (x, y) in cells]
    outside = [c for c in moved if c not in safe]
    if outside:
        return (False,
                f"blocked: {len(outside)} cell(s) would leave the safe mask "
                f"({outside[:3]})", None)
    fit.motif_right, fit.motif_down = nx, ny
    return True, "", moved


def apply_motif(fit: Fit, cells):
    return [(x + fit.motif_right, y + fit.motif_down) for (x, y) in cells]


def reset_hat(fit: Fit) -> Fit:
    fit.hat_right = fit.hat_down = 0
    return fit


def reset_motif(fit: Fit) -> Fit:
    fit.motif_right = fit.motif_down = 0
    return fit


# --- persistence: per generated item, so a reopened item keeps its fit -------

def load_all(path: str = STORE) -> dict:
    if not os.path.isfile(path):
        return {}
    raw = json.load(open(path))
    return {k: Fit(**v) for k, v in raw.get("fits", {}).items()}


def load(item_id: str, path: str = STORE) -> Fit:
    return load_all(path).get(item_id, Fit(item_id=item_id))


def save(fit: Fit, path: str = STORE) -> None:
    fits = load_all(path)
    if fit.is_default():
        fits.pop(fit.item_id, None)        # a default fit stores nothing
    else:
        fits[fit.item_id] = fit
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({"_comment": "Player fitting adjustments, per generated item. "
                           "Stored as SCREEN directions (right/down positive); "
                           "the Fashion Sense sign inversion is applied at "
                           "export. Defaults are never overwritten -- an item "
                           "absent here is at its authored position.",
               "step_sprite_px": STEP,
               "screen_px_per_step": SCREEN_PX_PER_STEP,
               "hat_range": HAT_RANGE,
               "fits": {k: asdict(v) for k, v in fits.items()}},
              open(path, "w"), indent=1)
