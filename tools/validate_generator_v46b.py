#!/usr/bin/env python3
"""Static V4.6B checks. This tool can never promote runtime status."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import encode_rgba_png, read_rgba_png
from generator.renderers.fashionsense import appearance_json_v46b, render_v46b
from generator.v46b import generate_v46b_prototypes, validate_v46b_recipe


OUT = ROOT / "output" / "fashionsense" / "v46b-lower-body-readability"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V46B-LowerBody-Readability"
REPRESENTATIVES = {"front": 0, "right": 6, "back": 12, "left": 6}
FS_ORIENTATION = {
    "Front": {"facing": 2, "idleFrame": 0, "blockY": 0, "flipped": False},
    "Right": {"facing": 1, "idleFrame": 6, "blockY": 2752, "flipped": False},
    "Back": {"facing": 0, "idleFrame": 12, "blockY": 1376, "flipped": False},
    "Left": {"facing": 3, "idleFrame": 6, "blockY": 4128, "flipped": True},
}


def check(value: bool, message: str, errors: list[str]) -> None:
    if not value:
        errors.append(message)


def slug(value: str) -> str:
    return "_".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def bounds(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    return min(xs), min(ys), max(xs), max(ys)


def source_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    first = generate_v46b_prototypes()
    second = generate_v46b_prototypes()
    check(first == second, "semantic generation is nondeterministic", errors)
    check(len(first) == 6, "expected exactly six prototypes", errors)
    counts = {article: sum(r["articleType"] == article for r in first) for article in ("PANTS", "SHORTS", "SKIRT")}
    check(counts == {"PANTS": 2, "SHORTS": 2, "SKIRT": 2}, f"wrong article mix: {counts}", errors)
    check(not any(r["articleType"] == "FOOTWEAR" for r in first), "deferred footwear leaked into V4.6B", errors)

    contract_path = ROOT / "generator" / "data" / "fashionsense" / "v46b" / "article_frame_contracts.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    expected_frame = {
        "width": 32, "height": 64, "scale": 2, "columns": 6,
        "capacityPerDirection": 126, "blockWidth": 192, "blockHeight": 1376,
        "textureWidth": 192, "textureHeight": 5504,
    }
    check(contract["frame"] == expected_frame, "32x64 Scale-2 frame contract changed", errors)
    check(contract["bodyPosition"] == {"X": 0, "Y": 30}, "Scale-2 Pants body anchor changed", errors)
    anchor = contract["anchorContract"]
    check(anchor["nativeFarmerOrigin"] == {"X": 0, "Y": 32}, "native Farmer origin assumption changed", errors)
    source_top = 32 - (32 + anchor["sourceBodyPosition"]["Y"]) * anchor["sourceScale"]
    target_top = 32 - (32 + contract["bodyPosition"]["Y"]) * anchor["targetScale"]
    check(source_top == target_top == -92, f"Scale-2 anchor is not display-equivalent: source={source_top}, target={target_top}", errors)
    check(contract["directionBlocks"] == {"front": 0, "back": 1376, "right": 2752, "left": 4128}, "direction blocks changed", errors)
    check(contract["directionFlips"] == {"front": False, "back": False, "right": False, "left": True}, "official horizontal flip contract changed", errors)
    for label, path_key, digest_key in (
        ("V4.6 contract", "v46Contract", "v46Sha256"),
        ("male Farmer base", "maleBase", "maleBaseSha256"),
        ("female Farmer base", "femaleBase", "femaleBaseSha256"),
    ):
        path = source_path(contract["source"][path_key])
        check(path.exists(), f"missing authoritative {label}: {path}", errors)
        if path.exists():
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            check(actual == contract["source"][digest_key], f"authoritative {label} changed; rebuild contracts", errors)
    check(len(contract["frames"]) == 126, "motion contract is not complete", errors)
    check(sum(bool(frame["highDensityEnvelope"]) for frame in contract["frames"].values()) == 123, "unexpected visible-frame count", errors)

    hashes: dict[str, str] = {}
    summaries: list[dict] = []
    representative_masks: dict[str, set[tuple[int, int]]] = {}
    article_heights: dict[str, list[int]] = {"PANTS": [], "SHORTS": [], "SKIRT": []}
    for recipe in first:
        rid = recipe["id"]
        errors.extend(f"{rid}: {item}" for item in validate_v46b_recipe(recipe))
        rendered = render_v46b(recipe)
        rerendered = render_v46b(recipe)
        check(rendered.texture == rerendered.texture, f"{rid}: nondeterministic pixels", errors)
        check(not rendered.static_errors, f"{rid}: {'; '.join(rendered.static_errors)}", errors)
        check(recipe["runtimeStatus"] == "EXPERIMENTAL" and rendered.runtime_status == "EXPERIMENTAL", f"{rid}: illegal runtime promotion", errors)
        check(all(result["passes"] for result in rendered.identity.values()), f"{rid}: identity gate failed", errors)

        for direction, frame_index in REPRESENTATIVES.items():
            regions = rendered.regions[direction][frame_index]
            cells = set(regions)
            if not cells:
                errors.append(f"{rid}/{direction}: empty representative")
                continue
            _, y0, _, y1 = bounds(cells)
            if direction == "front":
                article_heights[recipe["articleType"]].append(y1 - y0 + 1)
                representative_masks[rid] = cells
            names = set(regions.values())
            if recipe["articleType"] == "PANTS" and direction in {"front", "back"}:
                check({"leftCuff", "rightCuff"} <= names, f"{rid}/{direction}: independent pant terminations missing", errors)
                center = contract["frames"][str(frame_index)]["centerX2"]
                check(any((x, y1) not in cells for x in (center - 1, center)), f"{rid}/{direction}: skirt-like unified termination", errors)
            elif recipe["articleType"] == "SHORTS" and direction in {"front", "back"}:
                check({"leftHem", "rightHem"} <= names, f"{rid}/{direction}: paired short hems missing", errors)
                center = contract["frames"][str(frame_index)]["centerX2"]
                check(all((x, y1) not in cells for x in (center - 1, center)), f"{rid}/{direction}: short legs merged at hem", errors)
            elif recipe["articleType"] == "SKIRT" and direction in {"front", "back"}:
                center = contract["frames"][str(frame_index)]["centerX2"]
                check(any((x, y1) in cells for x in (center - 1, center)), f"{rid}/{direction}: skirt split into false legs", errors)
                check("inseam" not in names, f"{rid}/{direction}: skirt contains inseam", errors)

        native = OUT / slug(recipe["name"]) / f"{slug(recipe['name'])}.png"
        check(native.exists(), f"{rid}: native atlas missing", errors)
        if native.exists():
            png = read_rgba_png(native)
            check((png["width"], png["height"]) == (192, 5504), f"{rid}: wrong atlas dimensions", errors)
            check(set(png["filters"]) == {0}, f"{rid}: PNG uses nonzero row filter", errors)
            check({pixel[3] for row in png["pixels"] for pixel in row} <= {0, 255}, f"{rid}: semitransparent pixels", errors)
            digest = hashlib.sha256(encode_rgba_png(rendered.texture)).hexdigest()
            check(png["sha256"] == digest, f"{rid}: native output differs from renderer", errors)
            hashes[rid] = digest

        model = appearance_json_v46b(recipe, rendered)
        check(model["Format"] == "7.5.0", f"{rid}: wrong Fashion Sense format", errors)
        for direction in ("Front", "Back", "Right", "Left"):
            view = model[direction + "Pants"]
            orientation = FS_ORIENTATION[direction]
            check(view["PantsSize"] == {"Width": 32, "Length": 64}, f"{rid}/{direction}: wrong frame size", errors)
            check(view["Scale"] == 2.0 and view["DisableNativeOffset"] is True, f"{rid}/{direction}: scale/native offset changed", errors)
            check(view["BodyPosition"] == {"X": 0, "Y": 30}, f"{rid}/{direction}: corrected body anchor missing", errors)
            check(view["HideWhileSwimming"] is True and view["HideWhileWearingBathingSuit"] is True, f"{rid}/{direction}: water transition guards missing", errors)
            check(view["HideLegs"] is False, f"{rid}/{direction}: native exposed legs were hidden", errors)
            check(len(view["ColorMaskLayers"]) == 1 and view["DisableGrayscale"] is False, f"{rid}/{direction}: recolor mask missing", errors)
            check(all(0 <= animation["Frame"] < 126 for animation in view["UniformAnimation"]), f"{rid}/{direction}: animation frame out of range", errors)
            check(view["StartingPosition"] == {"X": 0, "Y": orientation["blockY"]}, f"{rid}/{direction}: model points to wrong direction block", errors)
            check(view.get("Flipped", False) is orientation["flipped"], f"{rid}/{direction}: horizontal flip does not match FS direction contract", errors)
            matches = [animation for animation in view["UniformAnimation"] if any(condition.get("Name") == "CurrentFarmerFrame" and int(condition.get("Value")) == orientation["idleFrame"] for condition in animation.get("Conditions", []))]
            check(any(animation["Frame"] == orientation["idleFrame"] for animation in matches), f"{rid}/{direction}: authoritative idle source frame is not mapped", errors)
            for animation in view["UniformAnimation"]:
                frame = animation["Frame"]
                source_x = view["StartingPosition"]["X"] + (frame * 32) % 192
                source_y = view["StartingPosition"]["Y"] + ((frame * 32) // 192) * 64
                check(source_x + 32 <= 192, f"{rid}/{direction}: source rectangle exceeds texture width", errors)
                check(view["StartingPosition"]["Y"] <= source_y and source_y + 64 <= view["StartingPosition"]["Y"] + 1376, f"{rid}/{direction}: source rectangle escapes direction block", errors)
        summaries.append({"id": rid, "article": recipe["articleType"], "rarity": recipe["rarity"], "static": "PASS", "runtime": "NOT_TESTED", "promotionState": "EXPERIMENTAL"})

    check(len(set(hashes.values())) == 6, "prototype atlases are not all unique", errors)
    check(max(article_heights["SHORTS"]) < min(article_heights["PANTS"]), "shorts do not terminate above pants", errors)
    keys = sorted(representative_masks)
    check(all(representative_masks[a] != representative_masks[b] for i, a in enumerate(keys) for b in keys[i + 1:]), "two front silhouettes are identical", errors)

    manifest = json.loads((PACK / "manifest.json").read_text(encoding="utf-8"))
    check(manifest["ContentPackFor"] == {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"}, "test-pack dependency changed", errors)
    appearances = sorted((PACK / "Pants").glob("*/pants.json"))
    check(len(appearances) == 6, "test pack must contain exactly six Pants-category appearances", errors)
    check(not any((PACK / folder).exists() for folder in ("Shoes", "Shirts", "Accessories", "Sleeves", "Hats")), "out-of-scope appearance leaked into pack", errors)
    for path in appearances:
        data = json.loads(path.read_text(encoding="utf-8"))
        png = read_rgba_png(path.with_suffix(".png"))
        check((png["width"], png["height"]) == (192, 5504), f"{path}: wrong pack texture size", errors)
        for direction in ("Front", "Back", "Right", "Left"):
            view = data[direction + "Pants"]
            start = view["StartingPosition"]
            expected = FS_ORIENTATION[direction]
            check(start == {"X": 0, "Y": expected["blockY"]}, f"{path}/{direction}: bad or swapped direction start", errors)
            check(view.get("Flipped", False) is expected["flipped"], f"{path}/{direction}: bad horizontal flip", errors)

    warnings.extend([
        "Static identity PASS is not motion evidence; every prototype remains EXPERIMENTAL.",
        "Back stride and sitting frames are the highest-risk leg-separation states.",
        "Shorts and skirts intentionally retain native exposed legs through HideLegs=false.",
        "Swimming/bathing success means a clean framework-driven hide/transition, not persistent garment visibility.",
        "Multiplayer equip/color synchronization remains NOT TESTED.",
        "Large 192x5504 atlases are a diagnostic cost of four direction-specific 32x64 frame blocks.",
    ])
    status = "PASS_STATIC_ARTICLE_IDENTITY_RUNTIME_NOT_TESTED" if not errors else "FAIL"
    report = {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "fashionSense": "7.5.0",
        "stardew": "1.6.15.24356",
        "logicalFrame": {"width": 32, "height": 64, "scale": 2},
        "counts": counts,
        "textures": hashes,
        "prototypes": summaries,
        "claims": {
            "static": not errors,
            "articleIdentityAtRepresentativeFrames": not errors,
            "idle": False, "walk": False, "run": False, "tools": False,
            "sitting": False, "horse": False, "recolor": False,
        },
    }
    target = OUT / "full_validation.json"
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUT / "validation.json").write_text(json.dumps({
        "status": status,
        "errorCount": len(errors),
        "counts": counts,
        "logicalFrame": report["logicalFrame"],
        "promotionState": "EXPERIMENTAL",
        "runtimeEvidence": "NOT_TESTED",
        "shoesIncluded": False,
        "installedAutomatically": False,
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "errors": errors, "warnings": warnings}, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
