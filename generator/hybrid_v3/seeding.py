"""Call-order-independent deterministic seed derivation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


def derive_seed(root_seed: int, *path: str) -> int:
    payload = json.dumps(
        {"root": int(root_seed), "path": list(path)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


@dataclass
class SeedBook:
    root_seed: int
    values: dict[str, int] = field(default_factory=dict)

    def for_stage(self, stage: str, *parts: str) -> int:
        key = "/".join((stage, *parts))
        value = derive_seed(self.root_seed, stage, *parts)
        self.values[key] = value
        return value

    def provenance(self) -> dict[str, object]:
        return {"rootSeed": self.root_seed, "stageSeeds": dict(sorted(self.values.items()))}
