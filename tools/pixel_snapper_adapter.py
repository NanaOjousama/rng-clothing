#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v5.pngio import blank_image, blit, read_rgba_png, write_rgba_png

DEFAULT_BIN = ROOT / "tools" / "bin" / "spritefusion-pixel-snapper"


def dims(p):
    return (len(p[0]), len(p))


def alpha_cells(p):
    return {(x, y) for y, row in enumerate(p) for x, px in enumerate(row) if px[3] > 0}


def bbox(cells):
    if not cells:
        return None
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    return (min(xs), min(ys), max(xs), max(ys))


def alpha_hash(cells):
    payload = ";".join(f"{x},{y}" for x, y in sorted(cells)).encode()
    return hashlib.sha256(payload).hexdigest()


def crop_to_alpha(p):
    cells = alpha_cells(p)
    b = bbox(cells)
    if b is None:
        return [[]], None
    x0, y0, x1, y1 = b
    return [row[x0:x1 + 1] for row in p[y0:y1 + 1]], b


def restore_canvas(processed, original, anchor):
    ow, oh = dims(original)
    original_bbox = bbox(alpha_cells(original))
    cropped, _ = crop_to_alpha(processed)
    if original_bbox is None or not cropped or not cropped[0]:
        return blank_image(ow, oh)

    cw, ch = dims(cropped)
    x0, y0, x1, y1 = original_bbox
    if anchor == "top-left":
        dx, dy = x0, y0
    elif anchor == "center":
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        dx = round(cx - (cw - 1) / 2.0)
        dy = round(cy - (ch - 1) / 2.0)
    else:  # center-bottom
        cx = (x0 + x1) / 2.0
        dx = round(cx - (cw - 1) / 2.0)
        dy = y1 - ch + 1

    if dx < 0 or dy < 0 or dx + cw > ow or dy + ch > oh:
        raise ValueError(
            f"processed sprite {cw}x{ch} cannot be reseated on {ow}x{oh} canvas "
            f"with anchor={anchor}"
        )
    out = blank_image(ow, oh)
    blit(out, cropped, dx, dy)
    return out


def run():
    ap = argparse.ArgumentParser(
        description="Safe Sprite Fusion Pixel Snapper adapter with silhouette approval gating."
    )
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--colors", type=int, default=16)
    ap.add_argument("--pixel-size", type=int)
    ap.add_argument("--palette")
    ap.add_argument("--binary", type=Path, default=DEFAULT_BIN)
    ap.add_argument(
        "--anchor",
        choices=("center-bottom", "center", "top-left"),
        default="center-bottom",
        help="How cropped Pixel Snapper output is reseated onto the original canvas.",
    )
    ap.add_argument(
        "--approve-silhouette-change",
        action="store_true",
        help="Explicit human approval allowing alpha geometry to differ from the input.",
    )
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()

    if not args.binary.exists():
        raise SystemExit(f"Pixel Snapper binary not found: {args.binary}")
    original = read_rgba_png(args.input)

    with tempfile.TemporaryDirectory(prefix="pixel-snapper-") as td:
        raw = Path(td) / "snap.png"
        cmd = [str(args.binary), str(args.input), str(raw), str(args.colors)]
        if args.pixel_size is not None:
            cmd += ["--pixel-size", str(args.pixel_size)]
        if args.palette:
            cmd += ["--palette", args.palette]
        proc = subprocess.run(cmd, text=True, capture_output=True)
        if proc.returncode:
            sys.stderr.write(proc.stdout)
            sys.stderr.write(proc.stderr)
            raise SystemExit(proc.returncode)

        processed = read_rgba_png(raw)
        restored = restore_canvas(processed, original, args.anchor)

    before = alpha_cells(original)
    after = alpha_cells(restored)
    changed = before != after
    report = {
        "tool": "Sprite Fusion Pixel Snapper",
        "input": str(args.input),
        "output": str(args.output),
        "inputCanvas": list(dims(original)),
        "rawSnapperCanvas": list(dims(processed)),
        "restoredCanvas": list(dims(restored)),
        "anchor": args.anchor,
        "inputAlphaSha256": alpha_hash(before),
        "outputAlphaSha256": alpha_hash(after),
        "alphaCellsBefore": len(before),
        "alphaCellsAfter": len(after),
        "alphaCellsChanged": len(before ^ after),
        "silhouetteChanged": changed,
        "approvalRequired": bool(changed and not args.approve_silhouette_change),
        "silhouetteChangeApproved": bool(changed and args.approve_silhouette_change),
        "accepted": bool(not changed or args.approve_silhouette_change),
    }

    report_path = args.report or args.output.with_suffix(args.output.suffix + ".pixel-snapper.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")

    if changed and not args.approve_silhouette_change:
        print(
            "REJECTED: Pixel Snapper changed silhouette geometry. "
            "Human approval is required before accepting this output."
        )
        print(f"Report: {report_path}")
        raise SystemExit(3)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_rgba_png(args.output, restored)
    print("ACCEPTED")
    if changed:
        print("Silhouette change accepted via explicit --approve-silhouette-change.")
    else:
        print("Silhouette unchanged.")
    print(f"Output: {args.output}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    run()
