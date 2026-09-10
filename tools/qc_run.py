"""PART 13 — drive a whole validation set through the running game.

    python3 tools/qc_run.py                     # every hat in the V5 pack
    python3 tools/qc_run.py --pack RNGClothing.FashionSense.V5HatValidation
    python3 tools/qc_run.py --vanilla           # the vanilla calibration group
    python3 tools/qc_run.py --good              # the four chosen reference hats
    python3 tools/qc_run.py --sheet <session>   # contact sheet from real captures

Produces, per hat, under qc_bridge/captures/<session>/<label>/:

    front_screen.png / front_head.png     what the player actually sees
    front_worn.png / front_nohat.png      the same renderer, isolated
    front_hatonly.png                     the hat's real drawn footprint
    ... and the same for right / back / left
    render_state.json                     every value the renderer used

Then `tools/qc_metrics.py <session dir>` turns those into fit numbers.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing")

from qc import (BridgeDown, CAPTURES, alive, refresh, require,      # noqa: E402
                send)

V5_PACK = "RNGClothing.FashionSense.V5HatValidation"


def preflight() -> None:
    if not alive():
        raise SystemExit(
            "The QC bridge is not answering.\n"
            "  1. launch Stardew Valley through SMAPI\n"
            "  2. load a save\n"
            "  3. check the SMAPI console for 'QC Bridge ready'\n"
            "Nothing below this point can be faked with a synthetic composite.")


def controlled_scene(hairstyle: int, direction: str = "front") -> dict:
    """One farmer, one hairstyle, one idle frame, one location — so that the only
    thing that differs between two captures is the hat."""
    return require("set_scene", hairstyle=hairstyle, direction=direction, freeze="true")


def hats_in_pack(pack_id: str | None) -> list[dict]:
    rows = require("list_hats")["hats"]
    if pack_id:
        rows = [h for h in rows if h["pack_id"] == pack_id]
    return rows


def capture_set(rows: list[dict], hairstyle: int) -> list[str]:
    labels = []
    controlled_scene(hairstyle)
    for i, hat in enumerate(rows, 1):
        label = hat["folder"] or hat["name"]
        print(f"[{i}/{len(rows)}] {hat['appearance_id']}")
        try:
            require("equip_hat", id=hat["appearance_id"])
            out = require("capture_all_directions", label=label)
            labels.append(out.get("directory", label))
        except (RuntimeError, BridgeDown) as exc:
            print(f"    SKIPPED: {exc}")
    return labels


def contact_sheet(session_dir: str, out_path: str, which: str = "head") -> str:
    """A contact sheet built from ACTUAL game captures — no compositing."""
    from v5.pngio import (blank_image, blit, draw_text, read_rgba_png,
                          write_rgba_png)

    folders = [os.path.join(session_dir, n) for n in sorted(os.listdir(session_dir))
               if os.path.isdir(os.path.join(session_dir, n))]
    tiles = []
    for folder in folders:
        row = []
        for d in ("front", "right", "back", "left"):
            p = os.path.join(folder, f"{d}_{which}.png")
            if os.path.exists(p):
                row.append(read_rgba_png(p))
        if row:
            tiles.append((os.path.basename(folder), row))
    if not tiles:
        raise SystemExit(f"no {which} captures under {session_dir}")

    th = max(len(img) for _, row in tiles for img in row)
    tw = max(len(img[0]) for _, row in tiles for img in row)
    cols = max(len(row) for _, row in tiles)
    pad, label_h = 6, 14
    out = blank_image(cols * (tw + pad) + pad + 150,
                      len(tiles) * (th + label_h + pad) + 24, (40, 40, 46, 255))
    draw_text(out, f"ACTUAL IN-GAME CAPTURES  ({which})  {os.path.basename(session_dir)}", 8, 6)
    y = 22
    for name, row in tiles:
        draw_text(out, name[:22], 6, y + th // 2)
        x = 150
        for img in row:
            blit(out, img, x, y)
            x += tw + pad
        y += th + label_h + pad
    write_rgba_png(out_path, out)
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", default=V5_PACK)
    ap.add_argument("--all-packs", action="store_true")
    ap.add_argument("--hairstyle", type=int, default=0)
    ap.add_argument("--sheet", help="session directory to build a contact sheet from")
    ap.add_argument("--which", default="head", choices=("head", "screen", "worn", "hatonly"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--reload", action="store_true",
                    help="reload Fashion Sense packs before capturing, so a "
                         "rebuilt pack is picked up without restarting the game")
    ap.add_argument("--expect", type=int, default=None,
                    help="with --reload, fail unless the pack lists this many "
                         "appearances after reloading")
    args = ap.parse_args()

    if args.sheet:
        session = args.sheet if os.path.isabs(args.sheet) else os.path.join(CAPTURES, args.sheet)
        out = os.path.join(session, f"contact_sheet_{args.which}.png")
        print("wrote", contact_sheet(session, out, args.which))
        return 0

    preflight()
    if args.reload:
        out = refresh(None if args.all_packs else args.pack, args.expect)
        print(f"fs_reload: {out.get('message')} "
              f"({out.get('hat_count')} appearances)")
    rows = hats_in_pack(None if args.all_packs else args.pack)
    if not rows:
        raise SystemExit(f"no hats found for pack {args.pack!r}. Run `qc list_hats`.")
    if args.limit:
        rows = rows[:args.limit]
    print(f"{len(rows)} hats, hairstyle {args.hairstyle}")
    capture_set(rows, args.hairstyle)

    sessions = sorted(os.listdir(CAPTURES)) if os.path.isdir(CAPTURES) else []
    if sessions:
        session = os.path.join(CAPTURES, sessions[-1])
        print("\ncaptures:", session)
        print("next:")
        print(f"  python3 tools/qc_metrics.py {session}")
        print(f"  python3 tools/qc_run.py --sheet {sessions[-1]} --which head")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
