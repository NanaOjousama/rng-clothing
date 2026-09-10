"""Technical, readability, and semantic validators for Generator V1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from generator.png_utils import RGBA, read_rgba_png, unique_opaque_colors
from generator.recipe_engine import validate_recipe
from generator.renderer import (
    DIRECTION_Y,
    FRAME_SIZE,
    MAIN_ROLES,
    MASK_X_OFFSET,
    PREVIEW_SCALE,
    PROTECTED_ROLES,
    RenderedShirt,
)


def luminance(pixel: RGBA | list[int] | tuple[int, int, int]) -> float:
    return 0.2126 * pixel[0] + 0.7152 * pixel[1] + 0.0722 * pixel[2]


def _points(frame: list[list[str | None]], predicate=None) -> set[tuple[int, int]]:
    result = set()
    for y, row in enumerate(frame):
        for x, role in enumerate(row):
            if role is not None and (predicate is None or predicate(role)):
                result.add((x, y))
    return result


def _component_sizes(points: Iterable[tuple[int, int]]) -> list[int]:
    remaining = set(points)
    sizes = []
    while remaining:
        pending = [remaining.pop()]
        size = 0
        while pending:
            x, y = pending.pop()
            size += 1
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    pending.append(neighbor)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def _isolated_role_pixels(frame: list[list[str | None]], role: str) -> int:
    points = _points(frame, lambda value: value == role)
    isolated = 0
    for x, y in points:
        neighbors = {(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)}
        isolated += not bool(points & neighbors)
    return isolated


def _color_region_count(frame: list[list[str | None]]) -> int:
    categories = {
        "main": lambda role: role in MAIN_ROLES,
        "secondary": lambda role: role in {"secondary", "secondary_shadow"},
        "accent": lambda role: role == "accent",
    }
    # Complexity budgets count semantic color regions (main fabric,
    # secondary fabric, accent), not every disconnected collar/hem patch of
    # the same material role. Disconnected opaque geometry is checked
    # separately and must remain zero.
    return sum(bool(_points(frame, predicate)) for predicate in categories.values())


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail}


def validate_rendered_shirt(
    rendered: RenderedShirt, data: dict[str, Any]
) -> dict[str, Any]:
    recipe = rendered.recipe
    recipe_validation = validate_recipe(recipe, data)
    budget = data["budgets"]["rarities"][recipe["rarity"]]
    global_budget = data["budgets"]["global"]
    palette_rules = data["palettes"]
    palette = palette_rules["families"][recipe["paletteFamily"]]

    technical = []
    readability = []
    design = []
    direction_metrics: dict[str, Any] = {}
    expected_role_set = MAIN_ROLES | PROTECTED_ROLES
    for direction, frame in rendered.roles.items():
        occupied = _points(frame)
        components = _component_sizes(occupied)
        accent_pixels = len(_points(frame, lambda role: role == "accent"))
        isolated_accent = _isolated_role_pixels(frame, "accent")
        color_regions = _color_region_count(frame)
        colors = unique_opaque_colors(rendered.default_composites[direction])
        lumas = [luminance(color) for color in colors]
        role_set = {role for row in frame for role in row if role is not None}
        direction_metrics[direction] = {
            "occupiedPixels": len(occupied),
            "connectedComponentSizes": components,
            "meaningfulRenderedColors": len(colors),
            "renderedLuminanceRange": round(max(lumas) - min(lumas), 2),
            "accentPixels": accent_pixels,
            "isolatedDecorativePixels": isolated_accent,
            "colorRegions": color_regions,
            "roles": sorted(role_set),
        }
        technical.append(
            _check(
                f"{direction}: supported logical roles",
                role_set <= expected_role_set,
                f"roles={sorted(role_set)}",
            )
        )
        readability.extend(
            [
                _check(
                    f"{direction}: connected garment",
                    len(components) == 1,
                    f"componentSizes={components}",
                ),
                _check(
                    f"{direction}: occupied-pixel budget",
                    global_budget["minimumOccupiedPixelsPerDirection"]
                    <= len(occupied)
                    <= global_budget["maximumOccupiedPixelsPerDirection"],
                    f"occupied={len(occupied)}",
                ),
                _check(
                    f"{direction}: meaningful-color budget",
                    len(colors) <= budget["maximumMeaningfulRenderedColors"],
                    f"colors={len(colors)}, limit={budget['maximumMeaningfulRenderedColors']}",
                ),
                _check(
                    f"{direction}: luminance range",
                    max(lumas) - min(lumas)
                    >= palette_rules["minimumOverallRenderedLuminanceRange"],
                    f"range={max(lumas) - min(lumas):.2f}",
                ),
                _check(
                    f"{direction}: accent budget",
                    accent_pixels <= budget["maximumAccentPixels"],
                    f"accentPixels={accent_pixels}, limit={budget['maximumAccentPixels']}",
                ),
                _check(
                    f"{direction}: isolated decorative budget",
                    isolated_accent <= budget["maximumIsolatedDecorativePixels"],
                    f"isolated={isolated_accent}, limit={budget['maximumIsolatedDecorativePixels']}",
                ),
                _check(
                    f"{direction}: color-region budget",
                    color_regions <= budget["maximumColorRegions"],
                    f"regions={color_regions}, limit={budget['maximumColorRegions']}",
                ),
            ]
        )

    left = rendered.roles["left"]
    right = rendered.roles["right"]
    exact_mirror = all(left[y][x] == right[y][7 - x] for y in range(8) for x in range(8))
    technical.append(
        _check("left/right derive from one side", exact_mirror, "exact logical-role mirror")
    )

    dye = palette["defaultDye"]
    ramp = palette_rules["mainMaskRamp"]
    shadow_rgb = tuple(channel * ramp["main_shadow"] // 255 for channel in dye)
    base_rgb = tuple(channel * ramp["main_base"] // 255 for channel in dye)
    shade_delta = luminance((*base_rgb, 255)) - luminance((*shadow_rgb, 255))
    readability.append(
        _check(
            "main shadow/base separation",
            shade_delta >= palette_rules["minimumShadowToBaseLuminanceDelta"],
            f"delta={shade_delta:.2f}",
        )
    )

    design.append(
        _check(
            "component combination legal",
            recipe_validation.valid,
            "; ".join(recipe_validation.errors) if recipe_validation.errors else "all compatibility rules pass",
        )
    )
    if recipe["collar"] != "none":
        back_collar = len(
            {
                (x, y)
                for y in range(4)
                for x in range(8)
                if rendered.roles["back"][y][x] in {"secondary", "secondary_shadow"}
            }
        )
        design.append(
            _check("collar has back/yoke logic", back_collar >= 4, f"backCollarPixels={back_collar}")
        )
    details = {recipe["detail"], recipe.get("secondaryDetail")}
    if "chest_accent" in details:
        hidden = all(
            role != "accent"
            for direction in ("back", "left", "right")
            for row in rendered.roles[direction]
            for role in row
        )
        design.append(
            _check("chest accent is front-only", hidden, "back and side views omit the chest mark")
        )
    if "lower_trim" in details:
        wrapping = all(
            any(role in {"secondary", "secondary_shadow"} for role in rendered.roles[direction][6])
            for direction in DIRECTION_Y
        )
        design.append(
            _check("lower trim wraps directions", wrapping, "secondary hem cells exist in all four views")
        )
    if recipe["pattern"] == "horizontal_stripe":
        wrapping = all(
            any(role in {"secondary", "secondary_shadow"} for role in rendered.roles[direction][4])
            for direction in DIRECTION_Y
        )
        design.append(
            _check("horizontal stripe wraps directions", wrapping, "stripe row exists in all four views")
        )
    if "inner_layer" in details:
        front_center = sum(
            rendered.roles["front"][y][x] in {"secondary", "secondary_shadow"}
            for y in range(1, 7)
            for x in (3, 4)
        )
        side_edge = sum(
            rendered.roles["right"][y][6] in {"secondary", "secondary_shadow"}
            for y in range(2, 7)
        )
        design.append(
            _check(
                "inner layer has front and side-edge logic",
                front_center >= 6 and side_edge >= 3,
                f"frontCenter={front_center}, sideForwardEdge={side_edge}",
            )
        )

    groups = {"technical": technical, "readability": readability, "design": design}
    passed_counts = {name: sum(check["passed"] for check in checks) for name, checks in groups.items()}
    total_counts = {name: len(checks) for name, checks in groups.items()}
    all_passed = all(check["passed"] for checks in groups.values() for check in checks)
    # This is intentionally a rejection diagnostic, not a beauty score.
    weights = {"technical": 45, "readability": 30, "design": 25}
    diagnostic_score = round(
        sum(
            weights[name] * passed_counts[name] / max(1, total_counts[name])
            for name in groups
        ),
        1,
    )
    return {
        "status": "PASS" if all_passed else "FAIL",
        "diagnosticScore": diagnostic_score,
        "scoreMeaning": "obvious-failure rejection only; not a measure of beauty",
        "directionMetrics": direction_metrics,
        "checks": groups,
        "recipeWarnings": list(recipe_validation.warnings),
    }


def _assert_nearest_preview(native: dict[str, Any], preview: dict[str, Any], factor: int) -> None:
    if preview["width"] != native["width"] * factor or preview["height"] != native["height"] * factor:
        raise AssertionError("preview dimensions are not exact integer scale")
    for y in range(native["height"]):
        for x in range(native["width"]):
            expected = native["pixels"][y][x]
            for dy in range(factor):
                for dx in range(factor):
                    if preview["pixels"][y * factor + dy][x * factor + dx] != expected:
                        raise AssertionError(f"preview is not nearest-neighbor at ({x},{y})")


def validate_exported_files(
    rendered: RenderedShirt,
    native_path: Path,
    preview_path: Path,
    contact_path: Path,
    data: dict[str, Any],
) -> dict[str, Any]:
    checks = []
    errors = []
    try:
        native = read_rgba_png(native_path)
        preview = read_rgba_png(preview_path)
        contact = read_rgba_png(contact_path)
        checks.append(_check("native dimensions", (native["width"], native["height"]) == (256, 32), f"{native['width']}x{native['height']}"))
        checks.append(_check("native PNG is authored filter-0 RGBA8", set(native["filters"]) == {0} and native["chunks"] == ["IHDR", "IDAT", "IEND"], f"filters={sorted(set(native['filters']))}"))
        checks.append(_check("native bytes match deterministic in-memory render", native["pixels"] == rendered.native_pixels, "decoded pixels are identical"))
        alpha_values = {pixel[3] for row in native["pixels"] for pixel in row}
        transparent_rgbs = {pixel[:3] for row in native["pixels"] for pixel in row if pixel[3] == 0}
        checks.append(_check("binary alpha only", alpha_values <= {0, 255}, f"alpha={sorted(alpha_values)}"))
        checks.append(_check("transparent RGB is zero", transparent_rgbs <= {(0, 0, 0)}, f"transparentRGB={sorted(transparent_rgbs)}"))
        outside = []
        overlap = []
        mask_colors = set()
        for y, row in enumerate(native["pixels"]):
            for x, pixel in enumerate(row):
                if pixel[3] and not (0 <= x < 8 or 128 <= x < 136):
                    outside.append((x, y))
            for x in range(8):
                base = native["pixels"][y][x]
                mask = native["pixels"][y][128 + x]
                if base[3] and mask[3]:
                    overlap.append((x, y))
                if mask[3]:
                    mask_colors.add(mask)
        checks.append(_check("no frame spill", not outside, f"outsidePixels={len(outside)}"))
        checks.append(_check("V1 base/mask cells do not overlap", not overlap, f"overlapPixels={len(overlap)}"))
        checks.append(_check("dye mask is grayscale", all(r == g == b for r, g, b, _ in mask_colors), f"maskColors={len(mask_colors)}"))
        allowed_values = set(data["palettes"]["mainMaskRamp"].values())
        used_values = {pixel[0] for pixel in mask_colors}
        checks.append(_check("mask uses declared ramp", used_values <= allowed_values, f"used={sorted(used_values)}"))
        sleeve = [native["pixels"][row][128] for row in (4, 3, 2)]
        checks.append(_check("sleeve sample cells are opaque grayscale", all(pixel[3] == 255 and pixel[0] == pixel[1] == pixel[2] for pixel in sleeve), f"samples={sleeve}"))
        checks.append(_check("sleeve samples order dark to light", sleeve[0][0] < sleeve[1][0] < sleeve[2][0], f"values={[pixel[0] for pixel in sleeve]}"))
        for direction, y0 in DIRECTION_Y.items():
            occupied = {
                (x, y)
                for y in range(8)
                for x in range(8)
                if native["pixels"][y0 + y][x][3]
                or native["pixels"][y0 + y][MASK_X_OFFSET + x][3]
            }
            expected = _points(rendered.roles[direction])
            checks.append(_check(f"{direction} frame position and occupancy", occupied == expected, f"pixels={len(occupied)}"))
        _assert_nearest_preview(native, preview, PREVIEW_SCALE)
        checks.append(_check("8x preview is exact nearest-neighbor", True, f"{preview['width']}x{preview['height']}"))
        checks.append(_check("labeled contact dimensions", (contact["width"], contact["height"]) == (352, 128), f"{contact['width']}x{contact['height']}"))
    except Exception as exc:  # Validation must report all file failures cleanly.
        errors.append(str(exc))
    passed = not errors and all(check["passed"] for check in checks)
    return {
        "status": "PASS" if passed else "FAIL",
        "nativePath": str(native_path),
        "nativeSha256": hashlib.sha256(native_path.read_bytes()).hexdigest() if native_path.exists() else None,
        "checks": checks,
        "errors": errors,
    }


def validate_pack(
    pack_dir: Path,
    selected_records: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    checks = []
    errors = []
    try:
        manifest = json.loads((pack_dir / "manifest.json").read_text(encoding="utf-8"))
        content = json.loads((pack_dir / "content.json").read_text(encoding="utf-8"))
        i18n = json.loads((pack_dir / "i18n" / "default.json").read_text(encoding="utf-8"))
        checks.append(_check("Content Patcher manifest ID", manifest["UniqueID"] == "RNGClothing.V1", manifest["UniqueID"]))
        checks.append(_check("Content Patcher dependency only", manifest["ContentPackFor"]["UniqueID"] == "Pathoschild.ContentPatcher" and "Dependencies" not in manifest, json.dumps(manifest["ContentPackFor"])))
        checks.append(_check("content format", content["Format"] == "2.8.0", content["Format"]))
        load_actions = [change for change in content["Changes"] if change["Action"] == "Load"]
        edits = [change for change in content["Changes"] if change["Action"] == "EditData" and change["Target"] == "Data/Shirts"]
        checks.append(_check("exactly five texture loads", len(load_actions) == 5, f"loads={len(load_actions)}"))
        checks.append(_check("single Data/Shirts edit", len(edits) == 1, f"edits={len(edits)}"))
        entries = edits[0]["Entries"]
        checks.append(_check("exactly five shirt entries", len(entries) == 5, f"entries={len(entries)}"))
        for record in selected_records:
            item_id = record["itemId"]
            entry = entries[item_id]
            slug = record["slug"]
            output_asset = output_dir / f"{slug}.png"
            pack_asset = pack_dir / "assets" / f"{slug}.png"
            checks.extend(
                [
                    _check(f"{item_id}: item identity", entry["Name"] == item_id and entry["SpriteIndex"] == 0, f"spriteIndex={entry['SpriteIndex']}"),
                    _check(f"{item_id}: dye and sleeves", entry["CanBeDyed"] is True and entry["IsPrismatic"] is False and entry["HasSleeves"] is True, "dyeable single-channel sleeved shirt"),
                    _check(f"{item_id}: localization tokens", entry["DisplayName"] == f"{{{{i18n:shirts.{slug}.name}}}}" and entry["Description"] == f"{{{{i18n:shirts.{slug}.description}}}}", "name and description use i18n"),
                    _check(f"{item_id}: localization keys", f"shirts.{slug}.name" in i18n and f"shirts.{slug}.description" in i18n, "default English keys present"),
                    _check(f"{item_id}: pack asset byte identity", pack_asset.read_bytes() == output_asset.read_bytes(), "pack PNG matches approved output"),
                ]
            )
    except Exception as exc:
        errors.append(str(exc))
    passed = not errors and all(check["passed"] for check in checks)
    return {"status": "PASS" if passed else "FAIL", "checks": checks, "errors": errors}
