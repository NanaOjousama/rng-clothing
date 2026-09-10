"""PART 5 — how wrong was the synthetic composite?

One exact hat, one direction, one hairstyle, one idle frame.

  A) the old synthetic composite   (tools/wear.py: farmer_base + hairstyles + hat,
                                    pasted at a hand-derived offset)
  B) the real Fashion Sense render (qc_bridge isolated capture, same renderer
                                    the player sees)

Both are 4x sprite scale, so they are directly comparable once the FARMER BODY
is aligned — which is the point: align on the thing both agree about (the head),
then measure how far apart the two put the HAT.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing")
sys.path.insert(0, "/home/deck/.claude/jobs/426d8000/tmp")
from v5.pngio import (blank_image, blit, draw_text, nearest_scale,      # noqa: E402
                      read_rgba_png, write_rgba_png)

CAP = "qc_bridge/captures/20260906-031652/PART5_seed000"
SEED = 0
HAIRSTYLE = 38


def colour_diff(a, b):
    """Pixels where two renders DISAGREE — the hat's real footprint, including
    everywhere it covers the head.  A coordinate-set difference silently drops
    exactly those pixels, which is the whole point of the measurement."""
    return {(x, y) for y in range(len(a)) for x in range(len(a[0]))
            if a[y][x] != b[y][x]}


def opaque(rows, t=8):
    return {(x, y) for y in range(len(rows)) for x in range(len(rows[0]))
            if rows[y][x][3] > t}


def bounds(cells):
    if not cells:
        return None
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    return dict(x0=min(xs), x1=max(xs), y0=min(ys), y1=max(ys),
                w=max(xs) - min(xs) + 1, h=max(ys) - min(ys) + 1, n=len(cells))


def synthetic(direction=0):
    """The old preview, at 4x so it lines up with the real capture."""
    import wear
    from v5.library import brimmed_hat, brimless_hat                    # noqa: F401
    from v5.pipeline import generate

    g = generate(SEED, slot="HEAD")
    hat = wear.ours_hat(g, "front" if direction == 0 else "side")
    worn = wear.wear(hat, d=direction, style=HAIRSTYLE % 8)
    bare = wear.farmer(direction, HAIRSTYLE % 8)
    return nearest_scale(worn, 4), nearest_scale(bare, 4), g


def main():
    real_worn = read_rgba_png(os.path.join(CAP, "front_worn.png"))
    real_bare = read_rgba_png(os.path.join(CAP, "front_nohat.png"))
    real_hat = read_rgba_png(os.path.join(CAP, "front_hatonly.png"))
    syn_worn, syn_bare, g = synthetic()

    rb = bounds(opaque(real_bare))
    sb = bounds(opaque(syn_bare))
    rh = bounds(opaque(real_hat))
    sh = bounds(colour_diff(syn_worn, syn_bare))

    # Align on the BARE FARMER: both renders agree what a farmer is, so any
    # remaining difference in hat position is the composite's error.
    dx = rb["x0"] - sb["x0"]
    dy = rb["y0"] - sb["y0"]

    print("=== PART 5 — synthetic composite vs the real Fashion Sense render ===")
    print(f"hat: seed {SEED}  {g.spec.architecture}  {g.spec.parameters['crown_profile']}")
    print(f"direction: front   hairstyle {HAIRSTYLE}   idle frame\n")
    print(f"bare farmer  real  x{rb['x0']}..{rb['x1']}  y{rb['y0']}..{rb['y1']}  "
          f"{rb['w']}x{rb['h']}  {rb['n']}px")
    print(f"bare farmer  synth x{sb['x0']}..{sb['x1']}  y{sb['y0']}..{sb['y1']}  "
          f"{sb['w']}x{sb['h']}  {sb['n']}px")
    print(f"alignment offset applied to the synthetic: ({dx:+}, {dy:+}) screen px\n")

    sx0, sy0 = sh["x0"] + dx, sh["y0"] + dy
    sx1, sy1 = sh["x1"] + dx, sh["y1"] + dy
    print(f"HAT  real   x{rh['x0']}..{rh['x1']}  y{rh['y0']}..{rh['y1']}  "
          f"{rh['w']}x{rh['h']}  {rh['n']}px")
    print(f"HAT  synth  x{sx0}..{sx1}  y{sy0}..{sy1}  "
          f"{sh['w']}x{sh['h']}  {sh['n']}px  (farmer-aligned)\n")

    v_disp = rh["y0"] - sy0
    h_disp = ((rh["x0"] + rh["x1"]) / 2) - ((sx0 + sx1) / 2)
    scale = rh["w"] / sh["w"]

    # where does each put the hat relative to the head?
    head_top = rb["y0"]
    print(f"vertical displacement    {v_disp:+d} screen px "
          f"({v_disp/4:+.1f} sprite px)   <-- the composite put the hat "
          f"{'HIGHER' if v_disp > 0 else 'LOWER'} than the game does")
    print(f"horizontal displacement  {h_disp:+.1f} screen px ({h_disp/4:+.2f} sprite px)")
    print(f"apparent scale           real/synth = {scale:.3f} "
          f"({'same' if abs(scale-1) < 0.02 else 'DIFFERENT'})")
    print(f"hat top vs head top      real {rh['y0']-head_top:+d}px   "
          f"synth {sy0-head_top:+d}px")
    print(f"hat bottom vs head top   real {rh['y1']-head_top:+d}px   "
          f"synth {sy1-head_top:+d}px")

    # contact / intersection with the head
    real_cells = opaque(real_hat)
    bare_cells = opaque(real_bare)
    syn_cells = {(x + dx, y + dy) for (x, y) in colour_diff(syn_worn, syn_bare)}
    print(f"hat pixels overlapping the farmer  real {len(real_cells & bare_cells)}   "
          f"synth {len(syn_cells & bare_cells)}")
    print(f"IoU of the two hat footprints      "
          f"{len(real_cells & syn_cells)/max(1,len(real_cells | syn_cells)):.3f}")

    # picture
    S = 2
    tiles = [("real worn", real_worn), ("real hat only", real_hat),
             ("synthetic worn", syn_worn)]
    tw = 256 * S
    out = blank_image(len(tiles) * (tw + 8) + 8, tw + 30, (40, 40, 46, 255))
    draw_text(out, f"PART 5  seed {SEED} front — real Fashion Sense render vs the old synthetic composite", 8, 6)
    for i, (name, img) in enumerate(tiles):
        blit(out, nearest_scale(img, S), 8 + i * (tw + 8), 20)
        draw_text(out, name, 8 + i * (tw + 8), 22)
    write_rgba_png("output/v5_hat_reconstruction/part5.png", out)
    print("\nwrote output/v5_hat_reconstruction/part5.png")

    json.dump(dict(vertical_px=v_disp, horizontal_px=h_disp, scale=scale,
                   real=rh, synthetic_aligned=dict(x0=sx0, x1=sx1, y0=sy0, y1=sy1)),
              open("output/v5_hat_reconstruction/part5.json", "w"), indent=1)


if __name__ == "__main__":
    main()
