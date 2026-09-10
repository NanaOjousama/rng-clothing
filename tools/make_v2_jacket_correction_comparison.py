#!/usr/bin/env python3
"""Compose the V2 jacket shoulder/collar before-after review sheet without scaling."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generator.png_utils import (  # noqa: E402
    blank_image,
    blit,
    draw_rect,
    draw_text,
    read_rgba_png,
    text_width,
    write_rgba_png,
)


FILENAMES = (
    "stonefield_layer_jacket-directions-8x.png",
    "mistral_lapel_layer_jacket-directions-8x.png",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before_dir", type=Path)
    parser.add_argument("after_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--title",
        default="V2 JACKET SHOULDER / COLLAR CORRECTION",
    )
    parser.add_argument(
        "--footer",
        default="8X NEAREST-NEIGHBOR CONTACTS - NO PREVIEW RESAMPLING",
    )
    parser.add_argument("--show-sleeve-samples", action="store_true")
    args = parser.parse_args()

    before = [read_rgba_png(args.before_dir / name) for name in FILENAMES]
    after = [read_rgba_png(args.after_dir / name) for name in FILENAMES]
    for index, (old, new) in enumerate(zip(before, after, strict=True)):
        if (old["width"], old["height"]) != (352, 128):
            raise ValueError(f"unexpected before contact dimensions for {FILENAMES[index]}")
        if (new["width"], new["height"]) != (352, 128):
            raise ValueError(f"unexpected after contact dimensions for {FILENAMES[index]}")

    width = 740
    height = 389 if args.show_sleeve_samples else 337
    canvas = blank_image(width, height, (235, 226, 214, 255))
    title = args.title.upper()
    draw_text(canvas, title, (width - text_width(title)) // 2, 6)
    draw_text(canvas, "BEFORE", 12 + (352 - text_width("BEFORE")) // 2, 23)
    draw_text(canvas, "AFTER", 376 + (352 - text_width("AFTER")) // 2, 23)
    for row, (old, new) in enumerate(zip(before, after, strict=True)):
        y = 39 + row * 140
        blit(canvas, old["pixels"], 12, y)
        blit(canvas, new["pixels"], 376, y)
    footer_y = 372 if args.show_sleeve_samples else 320
    if args.show_sleeve_samples:
        sample_title = "VANILLA SLEEVE SAMPLES: LIGHT   MID   CUFF / END"
        draw_text(canvas, sample_title, (width - text_width(sample_title)) // 2, 314)
        for column_x, contact in ((12, before[0]), (376, after[0])):
            # The contact's front tile begins at (12, 52), at exact 8x scale.
            samples = [contact["pixels"][52 + y * 8][12] for y in (2, 3, 4)]
            start_x = column_x + 126
            for index, color in enumerate(samples):
                x = start_x + index * 32
                draw_rect(canvas, x - 1, 337, 10, 10, (101, 86, 73, 255))
                draw_rect(canvas, x, 338, 8, 8, color)
            draw_text(canvas, "Y2       Y3       Y4", column_x + 112, 352)
    footer = args.footer.upper()
    draw_text(canvas, footer, (width - text_width(footer)) // 2, footer_y)
    write_rgba_png(args.output, canvas)
    print(args.output)


if __name__ == "__main__":
    main()
