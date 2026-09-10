#!/usr/bin/env python3
"""Generate the four installable V4.6 lower-body runtime prototypes."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, write_rgba_png
from generator.renderers.fashionsense import appearance_json_v46, render_v46
from generator.v46 import generate_v46_prototypes


OUT = ROOT / "output" / "fashionsense" / "v46-lower-body-runtime"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V46-LowerBody-Runtime"
COMPARE = ROOT / "output" / "comparisons" / "V46_LOWER_BODY_RUNTIME.png"
BG: RGBA = (231, 222, 207, 255); TILE: RGBA = (204, 197, 186, 255); INK: RGBA = (49, 45, 42, 255); BORDER: RGBA = (71, 64, 59, 255)
DIRECTION_FRAMES = (("front", 0), ("back", 8), ("right", 4), ("left", 12))
DIAGNOSTIC_FRAMES = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 29, 54, 55, 64, 65, 66, 72, 73, 74, 75, 96, 104, 105, 116, 117, 125)


def _json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _slug(value): return "_".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())
def _folder(value): return "".join(word.title() for word in _slug(value).split("_"))


def _default_palette(recipe):
    if recipe["id"] == "v46-pants-common-01": return {54:(73,61,45,255),102:(128,110,76,255),154:(181,161,118,255),205:(220,204,167,255)}
    if recipe["id"] == "v46-pants-rare-01": return {54:(39,45,32,255),102:(58,68,43,255),154:(91,105,69,255),205:(140,151,104,255)}
    if recipe["id"] == "v46-shoes-common-01": return {54:(37,35,36,255),102:(52,50,52,255),154:(74,69,66,255),205:(112,103,95,255)}
    return {54:(45,29,24,255),102:(68,42,31,255),154:(91,59,43,255),205:(139,94,62,255)}


def _colored(recipe, frame):
    palette = _default_palette(recipe)
    return [[palette.get(pixel[0], pixel) if pixel[0] == pixel[1] == pixel[2] and pixel[3] else pixel for pixel in row] for row in frame]


def _tile(canvas, image, x, y):
    draw_rect(canvas, x - 2, y - 2, len(image[0]) + 4, len(image) + 4, BORDER)
    draw_rect(canvas, x - 1, y - 1, len(image[0]) + 2, len(image) + 2, TILE)
    blit(canvas, image, x, y)


def _directions(recipe, render, scale):
    sw, sh = 16 * scale, 32 * scale; gap = 18; top = 48
    canvas = blank_image(70 + 4 * (sw + gap), top + sh + 18, BG)
    draw_text(canvas, f"{recipe['name']} - {recipe['rarity']} - EXPERIMENTAL", 7, 7, color=INK)
    draw_text(canvas, "REPRESENTATIVE IDLE SOURCES - RUNTIME NOT TESTED", 7, 22, color=INK)
    for i, (direction, frame_index) in enumerate(DIRECTION_FRAMES):
        x = 70 + i * (sw + gap); draw_text(canvas, direction, x, 35, color=INK)
        _tile(canvas, nearest_scale(_colored(recipe, render.frame_previews[frame_index]), scale), x, top)
    return canvas


def _diagnostic(recipe, render):
    scale = 4; cols = 8; cell_w, cell_h = 16*scale+10, 32*scale+19; top = 43
    canvas = blank_image(cols*cell_w+10, top + 4*cell_h+10, BG)
    draw_text(canvas, f"{recipe['name']} - SELECTED FARMER SOURCE FRAMES", 7, 7, color=INK)
    draw_text(canvas, "USE FS DISPLAY PLAYER FRAMES TO CORRELATE RUNTIME", 7, 21, color=INK)
    for i, frame_index in enumerate(DIAGNOSTIC_FRAMES):
        x = 6+(i%cols)*cell_w; y=top+(i//cols)*cell_h
        draw_text(canvas, f"F{frame_index}", x, y, color=INK)
        _tile(canvas, nearest_scale(_colored(recipe, render.frame_previews[frame_index]), scale), x, y+13)
    return canvas


def _comparison(rendered):
    scale=4; cell_w=190; cell_h=186
    canvas=blank_image(4*cell_w, 38+cell_h, BG); draw_text(canvas,"V4.6 FULL-FRAME LOWER-BODY RUNTIME PROOF",8,8,color=INK); draw_text(canvas,"STATIC CONTRACT VALID - ALL RUNTIME STATES NOT TESTED",8,21,color=INK)
    for i,(recipe,render) in enumerate(rendered):
        x=i*cell_w+25; y=76
        draw_text(canvas, recipe["name"][:25], x, 43, color=INK); draw_text(canvas, f"{recipe['articleType']} {recipe['rarity']}",x,56,color=INK)
        _tile(canvas, nearest_scale(_colored(recipe,render.frame_previews[0]),scale),x,y)
        draw_text(canvas,"EXPERIMENTAL",x,y+136,color=INK)
    return canvas


def main():
    recipes=generate_v46_prototypes(); rendered=[]
    _json(ROOT/"output"/"recipes"/"v46_lower_body_runtime_prototypes.json", {"generatorVersion":"4.6-runtime-proof","count":4,"recipes":recipes})
    for recipe in recipes:
        render=render_v46(recipe); rendered.append((recipe,render)); slug=_slug(recipe["name"]); target=OUT/slug
        write_rgba_png(target/f"{slug}.png",render.texture)
        write_rgba_png(target/f"{slug}-directions-8x.png",_directions(recipe,render,8))
        write_rgba_png(target/f"{slug}-gameplay-size.png",_directions(recipe,render,4))
        write_rgba_png(target/f"{slug}-selected-frame-diagnostic.png",_diagnostic(recipe,render))
        _json(target/f"{slug}-summary.json", {"recipe":recipe,"contractSource":render.contract["source"],"texture":render.contract["texture"],"usedFrameCount":len(render.contract["usedFrames"]),"intentionallyEmptyUsedFrames":render.contract.get("intentionallyEmptyUsedFrames",[]),"staticErrors":list(render.static_errors),"runtimeStatus":"EXPERIMENTAL","runtimeEvidence":"NOT_TESTED"})
        category="Pants" if recipe["articleType"]=="FITTED_PANTS" else "Shoes"; stem=category.lower(); dest=PACK/category/_folder(recipe["name"])
        _json(dest/f"{stem}.json", appearance_json_v46(recipe,render)); write_rgba_png(dest/f"{stem}.png",render.texture)
    compare=_comparison(rendered); write_rgba_png(COMPARE,compare); write_rgba_png(OUT/"V46_LOWER_BODY_RUNTIME.png",compare)
    _json(PACK/"manifest.json", {"Name":"RNG Clothing V4.6 Lower-Body Runtime Proof","Author":"RNG Clothing Experiment","Version":"0.1.0","Description":"Development-only full-frame runtime test pack: two fitted pants and two footwear appearances.","UniqueID":"RNGClothing.FashionSense.V46LowerBodyRuntime","UpdateKeys":[],"ContentPackFor":{"UniqueID":"PeacefulEnd.FashionSense","MinimumVersion":"7.5.0"}})
    _json(PACK/"i18n"/"default.json", {key:value for r in recipes for key,value in ((f"appearance.{r['id']}.name",r['name']),(f"appearance.{r['id']}.description",r['description']))})
    (PACK/"README.md").write_text("""# RNG Clothing V4.6 Lower-Body Runtime Proof\n\nDevelopment-only Fashion Sense content pack. Every appearance is **EXPERIMENTAL** until the manual checklist is completed.\n\nCopy this entire `RNG-Clothing-V46-LowerBody-Runtime` folder into your Stardew Valley `Mods` folder. Install Fashion Sense 7.5.0 separately. Restart through SMAPI, obtain a Hand Mirror with `fs_add_mirror`, then equip the appearances in the Pants and Shoes tabs.\n\nUseful Fashion Sense diagnostics:\n\n- `fs_display_player_frames` toggles the current Farmer frame overlay.\n- `fs_display_movement` toggles movement debug data.\n- `fs_record_frames` starts/stops recording Farmer frames.\n- `fs_play_next_frame` steps through recorded frames.\n- `fs_clear_recorded_frames` clears the recording.\n- `fs_reload RNGClothing.FashionSense.V46LowerBodyRuntime` reloads only this test pack after asset changes.\n\nRecord evidence in `reports/V46_RUNTIME_TEST_CHECKLIST.md`. Pack loading or a clean idle pose is not a runtime pass. Pants and shoes deliberately hide while swimming and in bathing clothes; the checklist verifies those transitions are clean.\n""",encoding="utf-8")
    _json(OUT/"validation.json", {"status":"STATIC_GENERATION_COMPLETE_RUNTIME_NOT_TESTED","appearanceCount":4,"counts":{"FITTED_PANTS":2,"FOOTWEAR":2},"runtimeStatus":"EXPERIMENTAL","installedAutomatically":False})
    print("Generated four V4.6 EXPERIMENTAL lower-body appearances")


if __name__=="__main__": main()
