from __future__ import annotations

from pathlib import Path
from typing import List

from v5.pngio import read_rgba_png, write_rgba_png


def mirror_right_to_left(right_path: str, left_path: str) -> str:
    """Create the left base by deterministically mirroring the approved right base."""
    image = read_rgba_png(Path(right_path))
    mirrored: List[list[tuple[int, int, int, int]]] = [
        list(reversed(row)) for row in image
    ]
    out = Path(left_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_rgba_png(out, mirrored)
    return str(out)


def localized_visibility_rule() -> str:
    return (
        "Localized motifs are applied after base cardinal construction by the "
        "generator using declared placement/visibility rules; do not ask AI to "
        "re-invent motif placement independently per direction."
    )
