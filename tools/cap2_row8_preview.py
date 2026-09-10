"""How broken does the front crown look if row 8 joins the motif safe mask?

Row 8 is the last row of crown fabric before the visor at row 9. Admitting it
roughly doubles every motif's freedom (`ring` goes from 1 legal position to 6),
but it also lets a mark sit directly against the peak. This renders both so the
question is answered by looking, not by argument.

Left column  = the approved 16-cell mask, motif at its current placement.
Right column = the extended 24-cell mask, motif pushed to its lowest legal row.
"""
from __future__ import annotations
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v5 import authored, pngio
from v5.grammar import luminance
from v5.source.cap2_gen import Cap2Generator, build_ramp

OUT = "output/cap2_row8"
BASE = "authored/source_bases/cap2"
SCALES = [1, 2, 4]


def place_in(mask, cells):
    """Lowest legal placement of `cells` inside `mask`."""
    drop = 0
    while all((x, y + drop + 1) in mask for (x, y) in cells):
        drop += 1
    return [(x, y + drop) for (x, y) in cells], drop


def main():
    os.makedirs(OUT, exist_ok=True)
    gen = Cap2Generator(authored.load())
    approved = gen.safe
    ext = {tuple(c) for c in
           json.load(open(f"{BASE}/motif_safe_mask_ext8.json"))["safe_cells"]}
    marks = gen.marks

    # one palette for all of them, so only placement differs
    pal = next(p for p in gen.palettes if p.id == "WORKWEAR_DENIM_RUST")
    ramp, _ = build_ramp(pal.ramps["body"][3], gen.levels)
    colour = gen.motif_colour(ramp, pal, 0)
    src = gen.frames["Front"]

    def frame(cells):
        rows = []
        for y in range(20):
            row = []
            for x in range(20):
                p = src[y][x]
                if not p[3]:
                    row.append((0, 0, 0, 0)); continue
                step = min(range(len(gen.vocab)),
                           key=lambda i: abs(gen.levels[i] - luminance(p[:3])))
                row.append((*ramp[step], 255))
            rows.append(row)
        for (x, y) in cells:
            rows[y][x] = (*colour, 255)
        return rows

    report = []
    tiles = []
    for mid in sorted(marks):
        base = [tuple(c) for c in marks[mid]["cells"]]
        a_cells, a_drop = place_in(approved, base)
        b_cells, b_drop = place_in(ext, base)
        touches_visor_row = any(y == 8 for (x, y) in b_cells)
        report.append({"motif": mid, "approved_row": max(y for _, y in a_cells),
                       "extended_row": max(y for _, y in b_cells),
                       "dropped_extra_rows": b_drop - a_drop,
                       "reaches_row_8": touches_visor_row})
        tiles.append((mid, frame(a_cells), frame(b_cells)))
        print(f"{mid:10s} approved bottom row {max(y for _,y in a_cells)}"
              f" -> extended bottom row {max(y for _,y in b_cells)}"
              f"  (drops {b_drop - a_drop} extra)"
              f"{'   REACHES ROW 8' if touches_visor_row else ''}")

    # contact sheet: per motif, approved | extended, at each scale
    gap, label_h = 8, 0
    for scale in SCALES:
        cell = 20 * scale
        w = 2 * cell + gap * 3
        h = len(tiles) * (cell + gap) + gap
        sheet = [[(24, 24, 28, 255)] * w for _ in range(h)]
        for i, (mid, a, b) in enumerate(tiles):
            oy = gap + i * (cell + gap)
            for j, fr in enumerate((a, b)):
                ox = gap + j * (cell + gap)
                for y in range(20):
                    for x in range(20):
                        p = fr[y][x]
                        if not p[3]:
                            continue
                        for dy in range(scale):
                            for dx in range(scale):
                                sheet[oy + y * scale + dy][ox + x * scale + dx] = p
        path = f"{OUT}/row8_compare_{scale}x.png"
        pngio.write_rgba_png(path, sheet)
        print("wrote", path)

    json.dump(report, open(f"{OUT}/report.json", "w"), indent=1)


if __name__ == "__main__":
    main()
