#!/usr/bin/env python3
"""Validate the three-garment external AoT-inspired style-profile stress test."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import encode_rgba_png, nearest_scale, read_rgba_png
from generator.renderers.fashionsense import diagnose_fs_hd_render, render_fs_hd_v2
from generator.v2_recipe_engine import load_v2_data, structural_distance, validate_recipe_v2


REFERENCES = ROOT / "references" / "style-profiles" / "AoTInspired"
PROFILE = ROOT / "style-profiles" / "AoTInspired" / "profile.json"
RECIPES = ROOT / "output" / "recipes" / "aot_style_profile_poc.json"
OUTPUT = ROOT / "output" / "fashionsense" / "style-profile-aot" / "revised"
COMPARISON = ROOT / "output" / "comparisons" / "AOT_STYLE_PROFILE_3WAY.png"
BEFORE_AFTER = ROOT / "output" / "comparisons" / "AOT_STYLE_PROFILE_PREVIOUS_VS_REVISED.png"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-AoT-Style-POC"
STACK_ORDER = ("front", "right", "left", "back")


def _assert(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _slug(name: str) -> str:
    return "_".join(name.lower().replace("-", " ").split())


def _folder(name: str) -> str:
    return "".join(part.title() for part in _slug(name).split("_"))


def _stack(frames):
    return [row for direction in STACK_ORDER for row in frames[direction]]


def _luminance(rgb) -> float:
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def main() -> None:
    profile = _json(PROFILE)
    batch = _json(RECIPES)
    data = load_v2_data()
    actual_refs = sorted(path.name for path in REFERENCES.iterdir() if path.is_file())
    listed_refs = sorted(entry["file"] for entry in profile["referenceCorpus"]["inspectedFiles"])
    _assert(len(actual_refs) == 8, "expected exactly eight supplied references")
    _assert(actual_refs == listed_refs, "profile does not account for every supplied reference")
    _assert(profile["preferredRenderer"]["profile"] == "FS_HIGH_DETAIL_PERMANENT", "renderer profile changed")
    _assert(set(profile["styleStrength"]) == {"SUBTLE", "MODERATE", "STRONG"}, "style strength vocabulary")

    candidates = batch["candidates"]
    selected = [candidate for candidate in candidates if candidate["selection"] == "SELECTED"]
    _assert(len(candidates) == 5, "must generate exactly five semantic recipes")
    _assert(len(selected) == 3, "must render exactly three semantic recipes")
    _assert(
        [candidate["recipe"]["archetype"] for candidate in selected]
        == ["JACKET", "BUTTON_SHIRT", "SWEATER"],
        "revised pool must separate jacket, shirt/vest, and alternate top roles",
    )
    _assert(sum(c["recipe"]["archetype"] == "JACKET" for c in candidates) >= 2, "two jackets required")
    _assert(any(c["recipe"]["archetype"] == "BUTTON_SHIRT" for c in candidates), "button shirt required")
    _assert(any(c["recipe"]["archetype"] == "SWEATER" for c in candidates), "civilian sweater branch required")
    _assert({c["recipe"]["rarity"] for c in candidates} == {"Uncommon", "Rare"}, "rarity mix")
    _assert(all(c["styleStrength"] in {"MODERATE", "STRONG"} for c in candidates), "POC should prefer moderate/strong")

    signatures = []
    for candidate in candidates:
        recipe = candidate["recipe"]
        result = validate_recipe_v2(recipe, data)
        _assert(result.valid, f"{recipe['id']}: invalid recipe {result.errors}")
        _assert(recipe["styleProfile"] == "AoTInspired", f"{recipe['id']}: profile drift")
        _assert(not recipe["microDetails"], f"{recipe['id']}: unnecessary micro detail")
        _assert(recipe["accent"] == "none", f"{recipe['id']}: unsupported decorative accent")
        signatures.append((recipe["archetype"], tuple(recipe["construction"].values()), tuple(recipe["substantialFeatures"])))
    _assert(len(set(signatures)) == 5, "duplicate construction recipes")
    for index, first in enumerate(selected):
        for second in selected[index + 1:]:
            _assert(
                structural_distance(first["recipe"], second["recipe"]) >= 7,
                "revised selected garments are structurally too close",
            )
    _assert(all(len(candidate["recipe"]["substantialFeatures"]) == 2 for candidate in selected), "selected garments must not be plain filler")
    _assert(all(candidate["recipe"]["rarity"] == "Rare" for candidate in selected), "revised reward set should retain designed Rare construction")

    iconic = selected[0]
    iconic_recipe = iconic["recipe"]
    _assert(iconic["styleStrength"] == "STRONG", "iconic candidate strength")
    _assert(iconic_recipe["archetype"] == "JACKET", "iconic candidate archetype")
    _assert(iconic_recipe["construction"] == {
        "fit": "regular",
        "neckline": "open",
        "collar": "wide",
        "closure": "center_open",
        "layering": "visible_inner_layer",
        "hem": "structured",
        "panelLayout": "split_outer_panels",
    }, "iconic field-jacket construction drift")
    _assert(iconic_recipe["paletteFamily"] == "field_tan_olive", "iconic field-jacket palette drift")
    _assert(selected[1]["recipe"]["construction"]["panelLayout"] == "yoke", "shirt/vest yoke missing")
    _assert(selected[1]["recipe"]["construction"]["fit"] == "fitted", "shirt/vest must remain less bulky")
    _assert(selected[2]["branch"] == "darkFormal", "alternate dark branch missing")
    _assert(selected[2]["recipe"]["construction"]["panelLayout"] == "solid", "alternate branch should not repeat yoke panels")

    palette_metrics = {}
    for palette_name in profile["paletteFamilies"]:
        palette = data["palettes"]["families"][palette_name]
        main = palette["defaultDye"]
        secondary = palette["secondary"]
        _assert(_luminance(secondary["shadow"]) < _luminance(secondary["base"]) < _luminance(secondary["light"]), f"{palette_name}: secondary ramp order")
        _assert(_luminance(secondary["light"]) - _luminance(secondary["shadow"]) >= 45, f"{palette_name}: secondary contrast too weak")
        palette_metrics[palette_name] = {
            "mainDyeLuminance": round(_luminance(main), 2),
            "secondaryLuminance": {role: round(_luminance(rgb), 2) for role, rgb in secondary.items()},
        }

    renderer_source = (ROOT / "generator" / "renderers" / "fashionsense" / "hd_garment_v2.py").read_text(encoding="utf-8")
    grammar_bytes = (ROOT / "generator" / "data" / "fashionsense" / "hd_garment_grammar_v2.json").read_bytes()
    _assert("AoTInspired" not in renderer_source and "aot-style" not in renderer_source.lower(), "renderer contains style-specific hack")

    garment_metrics = []
    selected_side_templates = []
    for candidate in selected:
        recipe = candidate["recipe"]
        render = render_fs_hd_v2(recipe)
        rerender = render_fs_hd_v2(recipe)
        diagnostics = diagnose_fs_hd_render(render)
        _assert(render.texture == rerender.texture, f"{recipe['id']}: nondeterministic render")
        _assert(diagnostics.passes and not diagnostics.warnings, f"{recipe['id']}: diagnostics {diagnostics}")
        _assert(not any(render.coverage_missing.values()), f"{recipe['id']}: body coverage")
        slug = _slug(recipe["itemName"])
        native_path = OUTPUT / f"{slug}.png"
        native = read_rgba_png(native_path)
        _assert((native["width"], native["height"]) == (16, 64), f"{slug}: native dimensions")
        _assert(native_path.read_bytes() == encode_rgba_png(render.texture), f"{slug}: logical output drift")
        _assert(set(native["filters"]) == {0}, f"{slug}: PNG filtering")
        _assert({pixel[3] for row in native["pixels"] for pixel in row} <= {0, 255}, f"{slug}: nonbinary alpha")
        preview = read_rgba_png(OUTPUT / f"{slug}-default-8x.png")
        _assert(preview["pixels"] == nearest_scale(_stack(render.default_frames), 8), f"{slug}: preview not nearest-neighbor")

        shirt_dir = PACK / "Shirts" / _folder(recipe["itemName"])
        shirt = _json(shirt_dir / "shirt.json")
        _assert((shirt_dir / "shirt.png").read_bytes() == native_path.read_bytes(), f"{slug}: pack texture mismatch")
        _assert(recipe["itemName"] not in {"Eren", "Levi", "Mikasa", "Survey Corps"}, f"{slug}: copyrighted player-facing name")
        for field, y in (("FrontShirt", 0), ("RightShirt", 16), ("LeftShirt", 32), ("BackShirt", 48)):
            model = shirt[field]
            _assert(model["Scale"] == 2.0, f"{slug}/{field}: scale")
            _assert(model["BodyPosition"] == {"X": 0, "Y": 32}, f"{slug}/{field}: anchor")
            _assert(model["StartingPosition"] == {"X": 0, "Y": y}, f"{slug}/{field}: direction")
            _assert(model["ShirtSize"] == {"Width": 16, "Length": 16}, f"{slug}/{field}: size")
            _assert(model["HideSleeves"] is False, f"{slug}/{field}: native sleeves")
        garment_metrics.append({
            "id": recipe["id"],
            "name": recipe["itemName"],
            "styleStrength": candidate["styleStrength"],
            "branch": candidate["branch"],
            "sideTemplate": render.side_template,
            "activeMainRoles": list(render.active_main_roles),
            "diagnostics": diagnostics.metrics,
        })
        selected_side_templates.append(render.side_template)

    _assert(len(set(selected_side_templates)) == 3, "selected side-view templates must differ materially")

    manifest = _json(PACK / "manifest.json")
    _assert(manifest["ContentPackFor"] == {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"}, "Fashion Sense dependency")
    _assert("EntryDll" not in manifest, "test pack must remain content-only")
    _assert(len(list((PACK / "Shirts").glob("*/shirt.json"))) == 3, "test pack must contain exactly three shirts")
    translations = _json(PACK / "i18n" / "default.json")
    _assert(len(translations) == 6, "three localization-ready name/description pairs required")
    _assert(read_rgba_png(COMPARISON)["width"] > 0, "comparison missing")
    _assert(read_rgba_png(BEFORE_AFTER)["width"] > 0, "previous-vs-revised comparison missing")

    result = {
        "status": "PASS_TECHNICAL_AND_ROLE_DIFFERENTIATION",
        "roleDifferentiationStatus": "PASS_STATIC_GAMEPLAY_FOOTPRINT",
        "selectedRoles": ["CROPPED_FIELD_JACKET", "FITTED_YOKE_SHIRT", "DARK_CIVILIAN_COLLAR_KNIT"],
        "selectedSideTemplatesAllDistinct": True,
        "qualityNoPlainFillers": "PASS_ALL_SELECTED_RARE_WITH_TWO_SUBSTANTIAL_FEATURES",
        "artRecognitionStatus": "PROVISIONAL_REQUIRES_INGAME_UNLABELED_REVIEW",
        "strictImmediateAoTRecognition": "NOT_PROVEN_BY_STATIC_VALIDATION",
        "rendererFrozen": True,
        "rendererSpecificPixelHacks": False,
        "referenceFilesInspected": actual_refs,
        "profileSha256": hashlib.sha256(PROFILE.read_bytes()).hexdigest(),
        "frozenGrammarSha256": hashlib.sha256(grammar_bytes).hexdigest(),
        "recipes": {"generated": 5, "selected": 3, "allValid": True, "allDistinct": True},
        "paletteMetrics": palette_metrics,
        "garments": garment_metrics,
        "runtime": {
            "FashionSense": "7.5.0",
            "logicalFrame": [16, 16],
            "Scale": 2.0,
            "BodyPosition": [0, 32],
            "nativeAnimatedSleeves": True,
            "inGameReview": "PENDING",
        },
        "warning": "Technical/style-coherence guardrails do not prove immediate franchise recognition or reward desirability.",
    }
    _write_json(OUTPUT / "validation.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
