"""Static guardrails for V5B upper articles and coordinated sleeves.

These checks prove pack/schema/frame integrity and reject obvious construction
collapse. They explicitly do not promote any custom sleeve to runtime pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.v4 import diagnose_v4_article


@dataclass(frozen=True)
class V5BArticleDiagnostics:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


@dataclass(frozen=True)
class V5BCollectionDiagnostics:
    passes: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict[str, Any]


def _opaque(frame) -> frozenset[tuple[int, int]]:
    return frozenset((x, y) for y, row in enumerate(frame) for x, pixel in enumerate(row) if pixel[3])


def diagnose_v5b_article(render) -> V5BArticleDiagnostics:
    recipe = render.recipe; intent = recipe["sleeveIntent"]
    errors: list[str] = []; warnings: list[str] = []
    base = diagnose_v4_article(render.base)
    errors.extend(f"frozen V4 base: {message}" for message in base.errors)
    warnings.extend(f"frozen V4 base: {message}" for message in base.warnings)
    if len(render.texture) != 64 or any(len(row) != 16 for row in render.texture):
        errors.append("shirt texture must be 16x64 with four 16x16 direction frames")
    alpha = sorted({pixel[3] for row in render.texture for pixel in row})
    if any(value not in {0, 255} for value in alpha): errors.append(f"shirt alpha is not binary: {alpha}")
    if any(render.coverage_missing.values()): errors.append(f"body-coverage regression: {render.coverage_missing}")
    occupied = {direction: len(_opaque(render.frames[direction])) for direction in DIRECTION_ORDER}
    if min(occupied.values()) < 55: errors.append(f"one shirt direction has implausibly little construction mass: {occupied}")
    if intent == "SLEEVELESS":
        if render.hide_native_sleeves: errors.append("sleeveless recipe must not hide the Fashion Sense arm layer")
        if not render.companion_required: errors.append("sleeveless recipe requires a skin-tone-masked animated arm companion")
    elif intent == "SHORT_SLEEVE":
        if render.hide_native_sleeves or render.companion_required: errors.append("short sleeves must use the native animated sleeve path")
    else:
        if not render.companion_required or render.sleeves_texture is None or render.sleeves_json is None:
            errors.append(f"{intent} requires a generated FS Sleeves companion")
        else:
            atlas = render.sleeves_texture; model = render.sleeves_json
            if len(atlas) != 1344 or any(len(row) != 384 for row in atlas): errors.append("sleeves atlas must be 384x1344")
            sleeve_alpha = sorted({pixel[3] for row in atlas for pixel in row})
            if sleeve_alpha != [0, 255]: errors.append(f"sleeves alpha must be binary, found {sleeve_alpha}")
            expected_counts = {"FrontSleeves": 62, "BackSleeves": 28, "RightSleeves": 42, "LeftSleeves": 42}
            for key, count in expected_counts.items():
                part = model[key]
                if part.get("SleevesSize") != {"Width": 32, "Length": 64}: errors.append(f"{key} wrong SleevesSize")
                if part.get("Scale") != 2.0: errors.append(f"{key} wrong Scale")
                if part.get("BodyPosition") != {"X": 0, "Y": 0}: errors.append(f"{key} wrong BodyPosition")
                if not part.get("DisableNativeOffset"): errors.append(f"{key} must DisableNativeOffset")
                if not part.get("DrawBeforeShirt"): errors.append(f"{key} must draw before shirt")
                if not part.get("UseShirtColors"): errors.append(f"{key} must use coordinated shirt colors")
                animation = part.get("UniformAnimation", [])
                if len(animation) != count: errors.append(f"{key} animation count {len(animation)} != {count}")
                if max((a.get("Frame", -1) for a in animation), default=-1) >= 252: errors.append(f"{key} references outside 252-frame atlas")
            if not model["LeftSleeves"].get("Flipped"): errors.append("left sleeves must use the FS template's horizontal flip")
            cuff = render.sleeve_metrics.get("cuffCells", 0)
            if intent == "SLEEVELESS" and render.sleeve_metrics.get("bareArmCells", 0) <= 0:
                errors.append("sleeveless companion did not convert cloth masks to skin-tone masks")
            if intent in {"ROLLED_CUFFED_SLEEVE", "LAYERED_INNER_OUTER_SLEEVE"} and cuff <= 0:
                errors.append(f"{intent} did not author a target-resolution cuff region")
            if render.sleeve_idle_frames and any(len(_opaque(frame)) == 0 for frame in render.sleeve_idle_frames.values()):
                errors.append("one standing sleeves direction is empty")
            warnings.append("custom Sleeves atlas is statically valid but remains runtime-unproven for tools, sitting, and horse poses")
    metrics = {
        "articleType": recipe["articleType"], "constructionVariant": recipe["constructionVariant"],
        "sleeveIntent": intent, "shirtDimensions": [16, 64], "shirtFrame": [16, 16], "shirtScale": 2,
        "shirtBodyPosition": [0, 32], "alphaValues": alpha, "occupiedCells": occupied,
        "modifiedCells": {d: len(render.modified_cells[d]) for d in DIRECTION_ORDER},
        "bodyCoverageMissing": {d: list(render.coverage_missing[d]) for d in DIRECTION_ORDER},
        "companionRequired": render.companion_required, "sleeveMetrics": render.sleeve_metrics,
        "promotion": "EXPERIMENTAL", "runtimeClaim": "NOT_TESTED",
    }
    return V5BArticleDiagnostics(not errors, tuple(errors), tuple(warnings), metrics)


def diagnose_v5b_collection(recipes, renders, diagnostics) -> V5BCollectionDiagnostics:
    errors: list[str] = []; warnings: list[str] = []
    if len(recipes) != 12 or len(renders) != 12: errors.append("V5B benchmark must contain exactly twelve visible garments")
    article_counts = {name: sum(r["articleType"] == name for r in recipes) for name in ("FITTED_SHIRT", "SWEATER", "VEST_TOP", "CROPPED_JACKET", "STANDARD_JACKET", "BLOUSE")}
    if any(value != 2 for value in article_counts.values()): errors.append(f"expected two of every article family, found {article_counts}")
    rarity_counts = {rarity: sum(r["baseArticleRecipe"]["designRecipe"]["rarity"] == rarity for r in recipes) for rarity in ("Common", "Uncommon", "Rare")}
    if rarity_counts != {"Common": 4, "Uncommon": 4, "Rare": 4}: errors.append(f"expected balanced 4/4/4 rarity distribution, found {rarity_counts}")
    sleeve_counts = {name: sum(r["sleeveIntent"] == name for r in recipes) for name in ("SLEEVELESS", "SHORT_SLEEVE", "FITTED_LONG_SLEEVE", "ROLLED_CUFFED_SLEEVE", "LAYERED_INNER_OUTER_SLEEVE")}
    if any(value == 0 for value in sleeve_counts.values()): errors.append(f"safe V5B sleeve families are not all demonstrated: {sleeve_counts}")
    for recipe, diagnostic in zip(recipes, diagnostics):
        errors.extend(f"{recipe['id']}: {message}" for message in diagnostic.errors)
        warnings.extend(f"{recipe['id']}: {message}" for message in diagnostic.warnings)
    semantic_signatures = [
        (r["articleType"], r["constructionVariant"], r["sleeveIntent"], r["shoulderIntent"], r["necklineIntent"], r["collarIntent"], r["baseArticleRecipe"]["designRecipe"]["paletteStory"])
        for r in recipes
    ]
    if len(set(semantic_signatures)) != len(semantic_signatures): errors.append("exact V5B upper-construction duplicate detected")
    silhouette_signatures = [tuple(sorted((d, x, y) for d in DIRECTION_ORDER for x, y in _opaque(render.frames[d]))) for render in renders]
    unique_silhouettes = len(set(silhouette_signatures))
    if unique_silhouettes < 5: errors.append(f"upper articles collapsed to only {unique_silhouettes} shirt silhouettes")
    style_profiles = {r["baseArticleRecipe"]["designRecipe"]["styleProfile"] for r in recipes}
    if "AoTInspired" not in style_profiles: errors.append("required AoT/fieldwear stress garment is absent")
    metrics = {
        "articleCounts": article_counts, "rarityCounts": rarity_counts, "sleeveCounts": sleeve_counts,
        "uniqueSemanticSignatures": len(set(semantic_signatures)), "uniqueShirtSilhouettes": unique_silhouettes,
        "styleProfiles": sorted(style_profiles), "promotion": "EXPERIMENTAL",
    }
    return V5BCollectionDiagnostics(not errors, tuple(errors), tuple(warnings), metrics)
