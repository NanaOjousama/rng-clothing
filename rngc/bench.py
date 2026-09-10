"""Vanilla benchmark helpers: read installed 1.6.15 shirt tiles, measure their identity salience,
and produce the 2x2 majority reduction used ONLY for diagnostics and the resolution experiment."""

from __future__ import annotations

import json
from pathlib import Path

from .pngio import RGBA, blank_image
from .preview import CONTENT
from .pngio import read_rgba_png
from .roleimage import DIRECTIONS, SIZE, SLOTS
from .validate import luminance

DIRY = {"front": 0, "right": 8, "left": 16, "back": 24}


class Vanilla:
    def __init__(self, content: Path = CONTENT):
        sheet = content / "Characters/Farmer/shirts.png"; data = content / "Data/Shirts.json"
        self.available = sheet.exists() and data.exists()
        if not self.available: return
        self.sheet = read_rgba_png(sheet)
        raw = json.loads(data.read_text(encoding="utf-8-sig"))
        self.meta = {}
        for k, v in raw.items(): self.meta.setdefault(v["SpriteIndex"], {**v, "Key": k})

    def name(self, i): return self.meta[i].get("Name") or self.meta[i]["Key"]

    def _tile(self, i, d, mask=False):
        x0 = (i * 8) % 128 + (128 if mask else 0); y0 = (i * 8 // 128) * 32 + DIRY[d]
        return [list(self.sheet[y0 + y][x0:x0 + 8]) for y in range(8)]

    def dye(self, i):
        c = self.meta[i].get("DefaultColor")
        return tuple(int(v) for v in c.split()) if c else (255, 255, 255)

    def layers(self, i, d):
        """Return (rendered 8x8 RGBA, layer grid: 'base'|'dye'|None)."""
        b, m, D = self._tile(i, d), self._tile(i, d, True), self.dye(i)
        out = blank_image(8, 8); layer = [[None] * 8 for _ in range(8)]
        for y in range(8):
            for x in range(8):
                if b[y][x][3]: out[y][x] = b[y][x][:3] + (255,); layer[y][x] = "base"
                if m[y][x][3]:
                    p = m[y][x]; out[y][x] = (p[0] * D[0] // 255, p[1] * D[1] // 255, p[2] * D[2] // 255, 255); layer[y][x] = "dye"
        return out, layer

    def frames(self, i) -> dict[str, list[list[RGBA]]]:
        return {d: self.layers(i, d)[0] for d in DIRECTIONS}

    def identity_salience(self, i) -> dict:
        """Identity region = the minority layer (dye vs fixed) per garment; contrast against the majority layer."""
        report = {}
        for d in DIRECTIONS:
            frame, layer = self.layers(i, d)
            counts = {"base": 0, "dye": 0}
            for r in layer:
                for v in r:
                    if v: counts[v] += 1
            if not counts["base"] or not counts["dye"]:
                report[d] = {"cells": 0, "max_contrast": 0.0, "note": "single layer, no separable identity region"}; continue
            minority = min(counts, key=counts.get)
            best = 0.0; n = 0
            for y in range(8):
                for x in range(8):
                    if layer[y][x] != minority: continue
                    n += 1
                    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                        if 0 <= nx < 8 and 0 <= ny < 8 and layer[ny][nx] and layer[ny][nx] != minority:
                            best = max(best, abs(luminance(frame[y][x]) - luminance(frame[ny][nx])))
            report[d] = {"cells": n, "max_contrast": round(best, 1), "region": minority}
        return report


def reduce_2x2(img, frame) -> list[list[RGBA]]:
    """DIAGNOSTIC ONLY. 2x2 majority of (slot, role); ties prefer non-primary slot, then darker role.
    Alpha: opaque when at least two of four cells are opaque."""
    out = blank_image(8, 8)
    for Y in range(8):
        for X in range(8):
            cells = [(2 * X + dx, 2 * Y + dy) for dy in (0, 1) for dx in (0, 1)]
            op = [(x, y) for x, y in cells if img.role[y][x]]
            if len(op) < 2: continue
            votes = {}
            for x, y in op:
                key = (img.slot[y][x], img.role[y][x]); votes[key] = votes.get(key, 0) + 1
            best = max(votes.items(), key=lambda kv: (kv[1], kv[0][0] != 0, kv[0][1]))[0]
            for x, y in op:
                if (img.slot[y][x], img.role[y][x]) == best: out[Y][X] = frame[y][x]; break
    return out
