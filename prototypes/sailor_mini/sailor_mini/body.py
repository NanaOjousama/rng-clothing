"""The torso silhouette and its hand-authored shading.

Traced from the installed vanilla plain tee (sprite 1) at 2x. Light from screen
upper-left; deep only at silhouette turns and hem corners. The prototype does
not vary the silhouette by family — only FIT tapers the lower body.

Chars: b base, l light, s shadow, d deep, . transparent.
"""

from __future__ import annotations

W = 16
COVERAGE_ROWS = 4  # rows 0-3 must stay opaque: the Farmer's shoulder coverage

BLANK = {
    "front": [
        "dsssss....sssssd", "sllbbb....bbbbss", "sllbbbbbbbbbbbss", "slllbbbbbbbbbbss",
        "slllbbbbbbbbbbss", "slllbbbbbbbbbbss", "sllbbbbbbbbbbbss", "sbbbbbbbbbbbbbss",
        "sbbbbbbbbbbbbbss", "sbbbbbbbbbbbbbsd", "sbbbbbbbbbbbbbsd", "sbbbbbbbbbbbbbsd",
        "sbbbbbbbbbbbbssd", "sbbbbbbbbbbbsssd", "sbbbbbbbbbbbbbss", "ssssssssssssssss",
    ],
    "side": [
        "dsssss..ssss....", "sllbbs..bbbs....", "sllbbbbbbbbbss..", "slllbbbbbbbbss..",
        "slllbbbbbbbbss..", "sllbbbbbbbbbbs..", "slbbbbbbbbbbbbss", "sbbbbbbbbbbbbbss",
        "sbbbbbbbbbbbbbsd", "sbbbbbbbbbbbbbsd", "..sbbbbbbbbbbbsd", "..sbbbbbbbbbbbsd",
        "..sbbbbbbbbbbssd", "..sbbbbbbbbbsssd", "..sbbbbbbbbbbbss", "..ssssssssssssss",
    ],
    "back": [
        "ddssssssssssssdd", "sslbbbbbbbbbbsss", "sllbbbbbbbbbbbss", "slllbbbbbbbbbbss",
        "slllbbbbbbbbbbss", "sllbbbbbbbbbbbss", "slbbbbbbbbbbbbss", "sbbbbbbbbbbbbbss",
        "sbbbbbbbbbbbbbsd", "sbbbbbbbbbbbbbsd", "sbbbbbbbbbbbbbsd", "sbbbbbbbbbbbbbsd",
        "sbbbbbbbbbbbbssd", "sbbbbbbbbbbbsssd", ".sbbbbbbbbbbbbs.", ".ssssssssssssss.",
    ],
}

ROLE_CHARS = {"b": "base", "l": "light", "s": "shadow", "d": "deep"}
TAPER_ROWS = (12, 13, 14)


def silhouette(view: str, taper: int) -> list[list[str | None]]:
    """Return a 16x16 grid of role names (or None), with the FIT taper applied."""
    grid = [[ROLE_CHARS[c] if c != "." else None for c in row] for row in BLANK[view]]
    for _ in range(taper):
        for y in TAPER_ROWS:
            xs = [x for x, v in enumerate(grid[y]) if v is not None]
            if len(xs) > 8:
                grid[y][xs[0]] = None
                grid[y][xs[-1]] = None
    return grid
