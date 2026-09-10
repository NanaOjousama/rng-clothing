"""One-appearance weather hood assembled from the permanent hoodie grammar.

Fashion Sense conditions select the visible state. Animation offsets preserve
the separately calibrated hood-up and hood-down Hat origins, while animation
draw-order overrides keep lowered fabric behind the appropriate Farmer layer.
No reference pixels are read or copied.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from generator.png_utils import RGBA, blank_image, blit
from generator.renderers.fashionsense.hoodie_layers import (
    FSHoodieLayerRender,
    render_fs_hoodie_layers,
)


DIRECTIONS = ("front", "right", "back", "left")
MODEL_KEYS = {
    "front": "FrontHat",
    "right": "RightHat",
    "back": "BackHat",
    "left": "LeftHat",
}


@dataclass(frozen=True)
class FSWeatherHoodRender:
    recipe: dict[str, Any]
    down: FSHoodieLayerRender
    up: FSHoodieLayerRender
    texture: list[list[RGBA]]
    hat_json: dict[str, Any]
    conditions_json: dict[str, Any]
    frame_map: dict[str, dict[str, int]]


def _state_recipe(recipe: dict[str, Any], state: str) -> dict[str, Any]:
    value = copy.deepcopy(recipe)
    value["hoodLayer"]["state"] = state
    return value


def _conditions() -> dict[str, Any]:
    return {
        "HasPrecipitation": [
            {"Name": "IsRaining", "Value": True, "Independent": True},
            {"Name": "IsSnowing", "Value": True, "Independent": True},
        ],
        "IsOutdoorsAndHasPrecipitation": [
            {"Name": "IsOutdoors", "Value": True},
            {"GroupName": "HasPrecipitation", "Value": True},
        ],
        "IsOutdoorsAndNoPrecipitation": [
            {"Name": "IsOutdoors", "Value": True},
            {"GroupName": "HasPrecipitation", "Value": False},
        ],
    }


def _up_conditions() -> list[dict[str, Any]]:
    return [{"GroupName": "IsOutdoorsAndHasPrecipitation", "Value": True}]


def _down_conditions() -> list[dict[str, Any]]:
    return [
        {"Name": "IsOutdoors", "Value": False, "Independent": True},
        {
            "GroupName": "IsOutdoorsAndNoPrecipitation",
            "Value": True,
            "Independent": True,
        },
    ]


def _draw_order(preposition: str, appearance_type: str) -> dict[str, str]:
    return {"Preposition": preposition, "AppearanceType": appearance_type}


def render_fs_weather_hood(recipe: dict[str, Any]) -> FSWeatherHoodRender:
    """Render one semantic hoodie as a weather-responsive Hat appearance."""

    down = render_fs_hoodie_layers(_state_recipe(recipe, "down"))
    up = render_fs_hoodie_layers(_state_recipe(recipe, "up"))
    if down.shirt_texture != up.shirt_texture:
        raise ValueError("hood state must not alter the working Shirt component")

    # Four direction-specific cells per state. Keeping a unique left cell
    # avoids padding/flip changes when 16-wide lowered art enters a 32-wide
    # dynamic Hat frame.
    texture = blank_image(128, 64)
    frame_map = {
        "up": {direction: index for index, direction in enumerate(DIRECTIONS)},
        "down": {direction: index + 4 for index, direction in enumerate(DIRECTIONS)},
    }
    for index, direction in enumerate(DIRECTIONS):
        blit(texture, up.hood_frames[direction], index * 32, 0)
        blit(texture, down.hood_frames[direction], index * 32, 32)

    mask_layers = up.hood_json["FrontHat"]["ColorMaskLayers"]
    models: dict[str, Any] = {}
    for direction in DIRECTIONS:
        key = MODEL_KEYS[direction]
        up_model = up.hood_json[key]
        down_model = down.hood_json[key]
        up_head = up_model["HeadPosition"]
        down_head = down_model["HeadPosition"]
        down_offset = {
            "X": down_head["X"] - up_head["X"],
            "Y": down_head["Y"] - up_head["Y"],
        }
        down_order = (
            _draw_order("After", "Shirt")
            if direction == "back"
            else _draw_order("Before", "Player")
        )
        models[key] = {
            "Scale": 2.0,
            "HideWhileSwimming": True,
            "HideWhileWearingBathingSuit": True,
            "ColorMaskLayers": mask_layers,
            "StartingPosition": {"X": 0, "Y": 0},
            "HeadPosition": dict(up_head),
            "HatSize": {"Width": 32, "Length": 32},
            # FullHair is the default experiment: the complete Hat is behind
            # Hair, preserving bangs and allowing long hair to occlude it.
            "HideHair": False,
            "UniformAnimation": [
                {
                    "Frame": frame_map["up"][direction],
                    "Duration": 100,
                    "Offset": {"X": 0, "Y": 0},
                    "Conditions": _up_conditions(),
                },
                {
                    "Frame": frame_map["down"][direction],
                    "Duration": 100,
                    "Offset": down_offset,
                    "DrawOrderOverride": down_order,
                    "Conditions": _down_conditions(),
                },
            ],
        }

    hat_json = {
        "Name": "Harbor Haze Weather Hood",
        "Format": "7.5.0",
        "Tags": ["RNG Clothing", "Hoodie", "Weather Hood", "Test"],
        **models,
    }
    return FSWeatherHoodRender(
        recipe=recipe,
        down=down,
        up=up,
        texture=texture,
        hat_json=hat_json,
        conditions_json=_conditions(),
        frame_map=frame_map,
    )
