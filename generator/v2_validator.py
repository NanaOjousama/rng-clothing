"""Technical, semantic, and obvious-collapse validation for Generator V2."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from generator.png_utils import RGBA, read_rgba_png, unique_opaque_colors
from generator.v2_recipe_engine import feature_color_region, validate_recipe_v2
from generator.v2_renderer import (
    FRAME_SIZE,
    MAIN_ROLES,
    MASK_X_OFFSET,
    PROTECTED_ROLES,
    RenderedV2Shirt,
)
from generator.v2_structural import PREVIEW_SCALE, VANILLA_DIRECTION_Y


COLOR_LIMITS = {"Common": 6, "Uncommon": 8, "Rare": 9}


def luminance(pixel: RGBA | list[int] | tuple[int, int, int]) -> float:
    return 0.2126 * pixel[0] + 0.7152 * pixel[1] + 0.0722 * pixel[2]


def _points(frame: list[list[Any]], predicate=None) -> set[tuple[int, int]]:
    return {
        (x, y)
        for y, row in enumerate(frame)
        for x, value in enumerate(row)
        if value is not None and (predicate is None or predicate(value))
    }


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
    return sum(
        not bool(points & {(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)})
        for x, y in points
    )


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail}


def _region_count(
    regions: dict[str, list[list[str | None]]], direction: str, names: set[str]
) -> int:
    return sum(value in names for row in regions[direction] for value in row)


def _mirror_region(value: str | None) -> str | None:
    return {
        "OUTER_PANEL_RIGHT": "OUTER_PANEL_LEFT",
        "OUTER_PANEL_LEFT": "OUTER_PANEL_RIGHT",
    }.get(value, value)


def _feature_checks(rendered: RenderedV2Shirt, data: dict[str, Any]) -> list[dict[str, Any]]:
    checks = []
    regions = rendered.regions
    recipe = rendered.recipe
    construction = recipe["construction"]
    for feature in recipe["substantialFeatures"]:
        color_region = feature_color_region(feature, recipe, data)
        if feature == "contrast_inner_layer":
            front = _region_count(regions, "front", {"INNER_LAYER"})
            side = _region_count(regions, "right", {"INNER_LAYER"})
            passed = front >= 12 and side >= 6 and color_region == "inner_layer"
            detail = f"frontInner={front}, sideInner={side}"
        elif feature == "broad_collar":
            counts = {
                direction: _region_count(regions, direction, {"COLLAR"})
                for direction in ("front", "back", "right")
            }
            collar_rows = {
                direction: [
                    y
                    for y, row in enumerate(regions[direction])
                    if any(value == "COLLAR" for value in row)
                ]
                for direction in ("front", "back", "right")
            }
            maximum_row_width = max(
                sum(value == "COLLAR" for value in row)
                for direction in ("front", "back", "right")
                for row in regions[direction]
            )
            front_is_interrupted = all(
                regions["front"][y][3] == "INNER_LAYER"
                and regions["front"][y][4] == "INNER_LAYER"
                for y in collar_rows["front"]
            )
            shallow_anatomy = (
                len(collar_rows["front"]) <= 2
                and len(collar_rows["back"]) <= 1
                and len(collar_rows["right"]) <= 2
                and maximum_row_width <= 4
                and front_is_interrupted
            )
            passed = (
                counts["front"] >= 6
                and counts["back"] >= 4
                and counts["right"] >= 4
                and shallow_anatomy
            )
            detail = json.dumps(
                {
                    "counts": counts,
                    "rows": collar_rows,
                    "maximumRowWidth": maximum_row_width,
                    "frontCenterInterrupted": front_is_interrupted,
                },
                sort_keys=True,
            )
        elif feature == "ribbed_hem":
            counts = {
                direction: _region_count(regions, direction, {"RIBBING"})
                for direction in ("front", "back", "right")
            }
            passed = all(value >= 6 for value in counts.values())
            detail = json.dumps(counts, sort_keys=True)
        elif feature == "center_placket":
            front = _region_count(regions, "front", {"PLACKET"})
            side = _region_count(regions, "right", {"PLACKET"})
            passed = front >= 8 and side >= 5
            detail = f"frontPlacket={front}, sidePlacket={side}"
        elif feature == "wrapping_stripe":
            counts = {
                direction: _region_count(regions, direction, {"STRIPE"})
                for direction in ("front", "back", "right")
            }
            passed = all(value >= 5 for value in counts.values())
            detail = json.dumps(counts, sort_keys=True)
        elif feature == "yoke":
            counts = {
                direction: _region_count(regions, direction, {"YOKE", "COLLAR"})
                for direction in ("front", "back", "right")
            }
            passed = counts["front"] >= 6 and counts["back"] >= 8 and counts["right"] >= 5
            detail = json.dumps(counts, sort_keys=True)
        elif feature == "split_outer_panels":
            left = _region_count(regions, "front", {"OUTER_PANEL_LEFT"})
            right = _region_count(regions, "front", {"OUTER_PANEL_RIGHT"})
            passed = left >= 8 and right >= 8
            detail = f"frontLeft={left}, frontRight={right}"
        elif feature == "structured_lower_band":
            counts = {
                direction: _region_count(regions, direction, {"HEM"})
                for direction in ("front", "back", "right")
            }
            passed = all(value >= 4 for value in counts.values())
            detail = json.dumps(counts, sort_keys=True)
        elif feature == "major_panel_contrast":
            names = {
                "placket": {"PLACKET"},
                "inner_layer": {"INNER_LAYER"},
                "yoke": {"YOKE"},
                "hem": {"HEM"},
            }[color_region]
            counts = {
                direction: _region_count(regions, direction, names)
                for direction in ("front", "back", "right")
            }
            passed = counts["front"] >= 4 and counts["back"] >= 4 and counts["right"] >= 3
            detail = f"region={color_region}, counts={json.dumps(counts, sort_keys=True)}"
        else:
            passed = False
            detail = "unknown substantial feature"
        checks.append(_check(f"feature {feature} has substantial directional area", passed, detail))
    return checks


def validate_rendered_v2(
    rendered: RenderedV2Shirt, data: dict[str, Any]
) -> dict[str, Any]:
    recipe = rendered.recipe
    recipe_validation = validate_recipe_v2(recipe, data)
    rarity_budget = data["budgets"]["rarities"][recipe["rarity"]]
    allowed_regions = set(data["structuralMasks"]["regionLegend"].values()) - {"TRANSPARENT"}
    technical = []
    readability = []
    design = []
    direction_metrics = {}
    for direction in VANILLA_DIRECTION_Y:
        roles = rendered.roles[direction]
        regions = rendered.regions[direction]
        occupied = _points(roles)
        components = _component_sizes(occupied)
        role_set = {value for row in roles for value in row if value is not None}
        region_set = {value for row in regions for value in row if value is not None}
        colors = unique_opaque_colors(rendered.default_composites[direction])
        lumas = [luminance(color) for color in colors]
        accent_pixels = len(_points(roles, lambda value: value == "accent"))
        isolated_accent = _isolated_role_pixels(roles, "accent")
        protected_pixels = len(_points(roles, lambda value: value in PROTECTED_ROLES))
        direction_metrics[direction] = {
            "occupiedPixels": len(occupied),
            "connectedComponentSizes": components,
            "meaningfulRenderedColors": len(colors),
            "renderedLuminanceRange": round(max(lumas) - min(lumas), 2),
            "accentPixels": accent_pixels,
            "isolatedDecorativePixels": isolated_accent,
            "protectedPixels": protected_pixels,
            "majorRegions": dict(sorted(Counter(value for row in regions for value in row if value).items())),
            "roles": sorted(role_set),
        }
        technical.extend(
            [
                _check(
                    f"{direction}: supported logical roles",
                    role_set <= MAIN_ROLES | PROTECTED_ROLES,
                    f"roles={sorted(role_set)}",
                ),
                _check(
                    f"{direction}: supported named regions",
                    region_set <= allowed_regions,
                    f"regions={sorted(region_set)}",
                ),
                _check(
                    f"{direction}: role/region occupancy agrees",
                    _points(roles) == _points(regions),
                    f"rolePixels={len(_points(roles))}, regionPixels={len(_points(regions))}",
                ),
            ]
        )
        readability.extend(
            [
                _check(
                    f"{direction}: connected garment",
                    components == [len(occupied)],
                    f"componentSizes={components}",
                ),
                _check(
                    f"{direction}: vanilla occupancy envelope",
                    50 <= len(occupied) <= 64,
                    f"occupied={len(occupied)}",
                ),
                _check(
                    f"{direction}: meaningful-color budget",
                    len(colors) <= COLOR_LIMITS[recipe["rarity"]],
                    f"colors={len(colors)}, limit={COLOR_LIMITS[recipe['rarity']]}",
                ),
                _check(
                    f"{direction}: luminance range",
                    max(lumas) - min(lumas) >= data["palettes"]["minimumOverallRenderedLuminanceRange"],
                    f"range={max(lumas) - min(lumas):.2f}",
                ),
                _check(
                    f"{direction}: accent budget",
                    accent_pixels <= rarity_budget["maximumAccentPixelsPerDirection"],
                    f"accent={accent_pixels}, limit={rarity_budget['maximumAccentPixelsPerDirection']}",
                ),
                _check(
                    f"{direction}: isolated decorative budget",
                    isolated_accent <= rarity_budget["maximumIsolatedDecorativePixelsPerDirection"],
                    f"isolated={isolated_accent}, limit={rarity_budget['maximumIsolatedDecorativePixelsPerDirection']}",
                ),
            ]
        )

    role_mirror = all(
        rendered.roles["left"][y][x] == rendered.roles["right"][y][7 - x]
        for y in range(8)
        for x in range(8)
    )
    region_mirror = all(
        rendered.regions["left"][y][x]
        == _mirror_region(rendered.regions["right"][y][7 - x])
        for y in range(8)
        for x in range(8)
    )
    technical.extend(
        [
            _check("left/right logical roles derive from one side", role_mirror, "exact role mirror"),
            _check("left/right named regions derive from one side", region_mirror, "mirror with outer-panel handedness"),
        ]
    )
    dye = data["palettes"]["families"][recipe["paletteFamily"]]["defaultDye"]
    ramp = data["palettes"]["mainMaskRamp"]
    shadow_rgb = tuple(channel * ramp["main_shadow"] // 255 for channel in dye)
    base_rgb = tuple(channel * ramp["main_base"] // 255 for channel in dye)
    shade_delta = luminance((*base_rgb, 255)) - luminance((*shadow_rgb, 255))
    readability.append(
        _check(
            "main shadow/base separation",
            shade_delta >= data["palettes"]["minimumShadowToBaseLuminanceDelta"],
            f"delta={shade_delta:.2f}",
        )
    )
    design.append(
        _check(
            "construction-first recipe is legal",
            recipe_validation.valid,
            "; ".join(recipe_validation.errors) if recipe_validation.errors else "all schema, compatibility, rarity, and color-block rules pass",
        )
    )
    secondary_region = recipe["colorBlocking"]["secondaryRegion"]
    if secondary_region != "none":
        protected_front = direction_metrics["front"]["protectedPixels"]
        design.append(
            _check(
                "secondary structural block has meaningful area",
                protected_front >= 4,
                f"frontProtectedPixels={protected_front}",
            )
        )
    design.extend(_feature_checks(rendered, data))

    archetype = recipe["archetype"]
    if archetype == "T_SHIRT":
        forbidden = {"COLLAR", "YOKE", "PLACKET", "INNER_LAYER", "OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT", "RIBBING"}
        used = {value for frame in rendered.regions.values() for row in frame for value in row if value}
        design.append(_check("tee remains minimally constructed", not bool(used & forbidden), f"regions={sorted(used)}"))
    elif archetype == "SWEATER":
        counts = {
            direction: _region_count(rendered.regions, direction, {"RIBBING", "HEM"})
            for direction in ("front", "back", "right")
        }
        design.append(_check("sweater has heavy lower termination", all(value >= 5 for value in counts.values()), json.dumps(counts)))
    elif archetype == "BUTTON_SHIRT":
        front_placket = _region_count(rendered.regions, "front", {"PLACKET"})
        back_tailoring = _region_count(rendered.regions, "back", {"COLLAR", "YOKE"})
        side_placket = _region_count(rendered.regions, "right", {"PLACKET"})
        design.append(
            _check(
                "button shirt placket/collar survive directions",
                front_placket >= 8 and back_tailoring >= 8 and side_placket >= 5,
                f"frontPlacket={front_placket}, backTailoring={back_tailoring}, sidePlacket={side_placket}",
            )
        )
    elif archetype == "JACKET":
        sleeve_samples = [rendered.roles["front"][row][0] for row in (4, 3, 2)]
        design.append(
            _check(
                "jacket uses a deliberate deep cuff sample",
                sleeve_samples == ["main_deep", "main_base", "main_light"],
                f"dark/mid/light={sleeve_samples}",
            )
        )
        if recipe["construction"]["panelLayout"] == "split_outer_panels":
            counts = {
                "frontLeft": _region_count(rendered.regions, "front", {"OUTER_PANEL_LEFT"}),
                "frontRight": _region_count(rendered.regions, "front", {"OUTER_PANEL_RIGHT"}),
                "frontInner": _region_count(rendered.regions, "front", {"INNER_LAYER"}),
                "sideInner": _region_count(rendered.regions, "right", {"INNER_LAYER"}),
                "backOuter": _region_count(rendered.regions, "back", {"OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT"}),
            }
            passed = (
                counts["frontLeft"] >= 10
                and counts["frontRight"] >= 10
                and counts["frontInner"] >= 12
                and counts["sideInner"] >= 6
                and counts["backOuter"] >= 24
            )
            design.append(_check("jacket is layered outerwear in front/back/side", passed, json.dumps(counts, sort_keys=True)))
    elif archetype == "SAILOR_TOP":
        counts = {
            direction: _region_count(rendered.regions, direction, {"YOKE", "COLLAR"})
            for direction in ("front", "back", "right")
        }
        passed = counts["front"] >= 14 and counts["back"] >= 20 and counts["right"] >= 12
        design.append(_check("sailor collar/yoke dominates upper garment", passed, json.dumps(counts, sort_keys=True)))

    groups = {"technical": technical, "readability": readability, "design": design}
    passed_counts = {name: sum(check["passed"] for check in checks) for name, checks in groups.items()}
    total_counts = {name: len(checks) for name, checks in groups.items()}
    all_passed = all(check["passed"] for checks in groups.values() for check in checks)
    weights = {"technical": 40, "readability": 30, "design": 30}
    rejection_score = round(
        sum(weights[name] * passed_counts[name] / max(1, total_counts[name]) for name in groups),
        1,
    )
    return {
        "status": "PASS" if all_passed else "FAIL",
        "diagnosticScore": rejection_score,
        "scoreMeaning": "obvious-failure rejection only; not beauty or desirability",
        "directionMetrics": direction_metrics,
        "checks": groups,
        "recipeWarnings": list(recipe_validation.warnings),
    }


def _assert_nearest_preview(native: dict[str, Any], preview: dict[str, Any], factor: int) -> None:
    if (preview["width"], preview["height"]) != (
        native["width"] * factor,
        native["height"] * factor,
    ):
        raise AssertionError("preview dimensions are not exact integer scale")
    for y in range(native["height"]):
        for x in range(native["width"]):
            expected = native["pixels"][y][x]
            for dy in range(factor):
                for dx in range(factor):
                    if preview["pixels"][y * factor + dy][x * factor + dx] != expected:
                        raise AssertionError(f"preview is not nearest-neighbor at ({x},{y})")


def validate_exported_v2_files(
    rendered: RenderedV2Shirt,
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
        checks.append(_check("native bytes match deterministic render", native["pixels"] == rendered.native_pixels, "decoded pixels are identical"))
        alpha_values = {pixel[3] for row in native["pixels"] for pixel in row}
        transparent_rgb = {pixel[:3] for row in native["pixels"] for pixel in row if pixel[3] == 0}
        checks.append(_check("binary alpha only", alpha_values <= {0, 255}, f"alpha={sorted(alpha_values)}"))
        checks.append(_check("transparent RGB is zero", transparent_rgb <= {(0, 0, 0)}, f"transparentRGB={sorted(transparent_rgb)}"))
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
        checks.append(_check("base and dye-mask cells do not overlap", not overlap, f"overlapPixels={len(overlap)}"))
        checks.append(_check("dye mask is grayscale", all(r == g == b for r, g, b, _ in mask_colors), f"maskColors={len(mask_colors)}"))
        allowed_values = set(data["palettes"]["mainMaskRamp"].values())
        used_values = {pixel[0] for pixel in mask_colors}
        checks.append(_check("mask uses declared ramp", used_values <= allowed_values, f"used={sorted(used_values)}"))
        sleeve = [native["pixels"][row][128] for row in (4, 3, 2)]
        checks.append(_check("sleeve samples are opaque grayscale mask cells", all(pixel[3] == 255 and pixel[0] == pixel[1] == pixel[2] for pixel in sleeve), f"samples={sleeve}"))
        checks.append(_check("sleeve samples order dark to light", sleeve[0][0] < sleeve[1][0] < sleeve[2][0], f"values={[pixel[0] for pixel in sleeve]}"))
        for direction, y0 in VANILLA_DIRECTION_Y.items():
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
    except Exception as exc:
        errors.append(str(exc))
    passed = not errors and all(check["passed"] for check in checks)
    return {
        "status": "PASS" if passed else "FAIL",
        "nativePath": str(native_path),
        "nativeSha256": hashlib.sha256(native_path.read_bytes()).hexdigest() if native_path.exists() else None,
        "checks": checks,
        "errors": errors,
    }


def validate_v2_pack(
    pack_dir: Path,
    records: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    checks = []
    errors = []
    try:
        manifest = json.loads((pack_dir / "manifest.json").read_text(encoding="utf-8"))
        content = json.loads((pack_dir / "content.json").read_text(encoding="utf-8"))
        i18n = json.loads((pack_dir / "i18n" / "default.json").read_text(encoding="utf-8"))
        checks.append(_check("Content Patcher manifest ID", manifest["UniqueID"] == "RNGClothing.V2", manifest["UniqueID"]))
        checks.append(_check("Content Patcher dependency only", manifest["ContentPackFor"]["UniqueID"] == "Pathoschild.ContentPatcher" and "Dependencies" not in manifest, json.dumps(manifest["ContentPackFor"])))
        checks.append(_check("content format", content["Format"] == "2.8.0", content["Format"]))
        loads = [change for change in content["Changes"] if change["Action"] == "Load"]
        edits = [change for change in content["Changes"] if change["Action"] == "EditData" and change["Target"] == "Data/Shirts"]
        checks.append(_check("exactly ten texture loads", len(loads) == 10, f"loads={len(loads)}"))
        checks.append(_check("single Data/Shirts edit", len(edits) == 1, f"edits={len(edits)}"))
        entries = edits[0]["Entries"]
        checks.append(_check("exactly ten shirt entries", len(entries) == 10, f"entries={len(entries)}"))
        for record in records:
            item_id = record["itemId"]
            slug = record["slug"]
            entry = entries[item_id]
            output_asset = output_dir / f"{slug}.png"
            pack_asset = pack_dir / "assets" / f"{slug}.png"
            checks.extend(
                [
                    _check(f"{item_id}: item identity", entry["Name"] == item_id and entry["SpriteIndex"] == 0, f"spriteIndex={entry['SpriteIndex']}"),
                    _check(f"{item_id}: native dye/sleeve settings", entry["CanBeDyed"] is True and entry["IsPrismatic"] is False and entry["HasSleeves"] is True, "single native dye channel and sleeves"),
                    _check(f"{item_id}: localization tokens", entry["DisplayName"] == f"{{{{i18n:shirts.{slug}.name}}}}" and entry["Description"] == f"{{{{i18n:shirts.{slug}.description}}}}", "localized name and description"),
                    _check(f"{item_id}: localization keys", f"shirts.{slug}.name" in i18n and f"shirts.{slug}.description" in i18n, "default keys present"),
                    _check(f"{item_id}: pack asset byte identity", pack_asset.read_bytes() == output_asset.read_bytes(), "pack asset matches approved output"),
                ]
            )
    except Exception as exc:
        errors.append(str(exc))
    passed = not errors and all(check["passed"] for check in checks)
    return {"status": "PASS" if passed else "FAIL", "checks": checks, "errors": errors}
