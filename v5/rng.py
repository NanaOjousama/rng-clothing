"""Deterministic named seed streams.

Every resolution pass draws from its own named stream so that adding a
variable to one pass cannot shift the values drawn by another.  Streams are
derived by hashing, not by sequential PRNG advance, so a stream's Nth draw is
a pure function of (seed, stream name, N).
"""

from __future__ import annotations

import hashlib
import struct

_U64 = 1 << 64


class Stream:
    """One deterministic draw sequence."""

    def __init__(self, seed: int, name: str) -> None:
        self.seed = seed
        self.name = name
        self._n = 0
        self.frozen = False          # set once the Garment Spec is final
        self.draws = 0

    def _raw(self) -> float:
        if self.frozen:
            raise RuntimeError(
                f"stream {self.name!r} drawn after Garment Spec finalization "
                "(INV-11: projection contains zero design entropy)"
            )
        digest = hashlib.blake2b(
            f"{self.seed}:{self.name}:{self._n}".encode(), digest_size=8
        ).digest()
        self._n += 1
        self.draws += 1
        return struct.unpack(">Q", digest)[0] / _U64

    # -- primitives ---------------------------------------------------------

    def unit(self) -> float:
        return self._raw()

    def chance(self, p: float) -> bool:
        return self._raw() < p

    def randint(self, lo: int, hi: int) -> int:
        return lo + min(hi - lo, int(self._raw() * (hi - lo + 1)))

    def choice(self, options):
        options = list(options)
        return options[self.randint(0, len(options) - 1)]

    def weighted(self, weights: dict) -> object:
        """Pick a key with probability proportional to its (non-negative) weight."""
        items = [(k, float(w)) for k, w in weights.items() if w > 0]
        if not items:
            raise ValueError(f"stream {self.name!r}: no option has positive weight")
        total = sum(w for _, w in items)
        target = self._raw() * total
        acc = 0.0
        for key, w in items:
            acc += w
            if target < acc:
                return key
        return items[-1][0]


class StreamBank:
    """Lazily-created named streams for one roll."""

    def __init__(self, seed: int) -> None:
        self.seed = seed
        self._streams: dict[str, Stream] = {}

    def __call__(self, name: str) -> Stream:
        if name not in self._streams:
            self._streams[name] = Stream(self.seed, name)
        return self._streams[name]

    def freeze(self) -> None:
        for s in self._streams.values():
            s.frozen = True

    @property
    def total_draws(self) -> int:
        return sum(s.draws for s in self._streams.values())
