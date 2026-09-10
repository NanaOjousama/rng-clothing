"""The authored value vocabulary of a source family, and our roles on top of it.

Fashion Sense recolours by exact RGB match against declared ColorMasks, so a
pack author encodes semantics in the pixel values themselves: a small set of
greys, each standing for a material or a shading level.  That set is the
family's own vocabulary, and it is the right space to reason in.

Working in raw RGB instead produces two errors, both observed in this library:

  false positives   "Beret (Dotted)" differs from "Beret" in 113 cells, but 85
                    of those move by <= 3 grey levels -- the author using 164
                    and 165 interchangeably.  In RGB that reads as a wholesale
                    re-shade; in vocabulary space it is 28 cells, the dots.

  false negatives   "Blouse (Button Up)" moves cells between the pack's five
                    DECLARED masks.  Those are real semantic edits and must not
                    be smoothed away by a tolerance that was tuned for noise.

So the vocabulary is taken from the pack's declaration when it makes one, and
clustered from the art when it does not.

ROLES.  Our own semantic system (outline / body shadow / mid / light /
highlight / trim / accent / hardware) is then mapped ONTO that vocabulary in
value order, rather than replacing it.  The authored value hierarchy is what
survives a recolour, so it is preserved exactly and only the hue moves.
"""
from __future__ import annotations

from collections import Counter

# Two greys this close are the same authored value used inconsistently, not a
# semantic distinction.  Above it, treat the difference as intentional.
NOISE_TOLERANCE = 3

# Value order, darkest first.  Deliberately not a fixed count: a family with
# three authored greys has three roles, and inventing more would be us adding
# structure the author did not draw.
ROLE_ORDER = ("outline", "shadow", "mid", "light", "highlight", "spec")


def greys_of(frames: dict) -> Counter:
    out = Counter()
    for frame in frames.values():
        for row in frame:
            for p in row:
                if p[3]:
                    out[tuple(p)[:3]] += 1
    return out


def build_vocabulary(frames_list: list, declared: list | None = None) -> list:
    """Ordered list of authored values, darkest first.

    `declared` is the pack's own ColorMasks when it has them: authoritative,
    because those are the exact values Fashion Sense keys its recolour on.
    """
    hist = Counter()
    for frames in frames_list:
        hist.update(greys_of(frames))
    if declared:
        vocab = sorted({tuple(c[:3]) for c in declared},
                       key=lambda c: sum(c) / 3)
        # keep any authored value the declaration omits, so nothing is lost
        for c in hist:
            if all(abs(sum(c) / 3 - sum(v) / 3) > NOISE_TOLERANCE for v in vocab):
                vocab.append(c)
        return sorted(vocab, key=lambda c: sum(c) / 3)

    vocab, current = [], []
    for c in sorted(hist, key=lambda c: sum(c) / 3):
        if current and sum(c) / 3 - sum(current[-1]) / 3 > NOISE_TOLERANCE:
            vocab.append(max(current, key=lambda v: hist[v]))
            current = []
        current.append(c)
    if current:
        vocab.append(max(current, key=lambda v: hist[v]))
    return vocab


def step_of(colour, vocab: list) -> int:
    """Which authored value a pixel belongs to: nearest by luminance."""
    lum = sum(colour[:3]) / 3
    return min(range(len(vocab)), key=lambda i: abs(sum(vocab[i]) / 3 - lum))


def roles_for(vocab: list) -> dict:
    """{step -> role name}, assigned in value order over what was drawn."""
    n = len(vocab)
    if n <= len(ROLE_ORDER):
        names = list(ROLE_ORDER[:n])
    else:
        names = [f"step{i}" for i in range(n)]
        for i, r in enumerate(ROLE_ORDER):
            names[min(i, n - 1)] = r
    return {i: names[i] for i in range(n)}


def to_steps(frames: dict, vocab: list) -> dict:
    """Frames as {direction: {(x, y): step}} — alpha becomes absence."""
    out = {}
    for d, frame in frames.items():
        cells = {}
        for y, row in enumerate(frame):
            for x, p in enumerate(row):
                if p[3]:
                    cells[(x, y)] = step_of(p, vocab)
        out[d] = cells
    return out


def tone_profile(vocab: list) -> dict:
    """The family's own value rhythm, as absolute luminance per step.

    Recolouring must preserve this: it is what makes the material read as the
    material the author drew, and flattening every family onto one shared ramp
    is exactly the mistake this records enough information to avoid.
    """
    lums = [round(sum(c) / 3, 1) for c in vocab]
    return {"levels": lums,
            "span": round(lums[-1] - lums[0], 1) if lums else 0.0,
            "steps": len(lums),
            "gaps": [round(b - a, 1) for a, b in zip(lums, lums[1:])]}
