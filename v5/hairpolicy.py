"""How a hat treats the hairstyle underneath it.

Fashion Sense offers three behaviours, all per-direction, and choosing between
them is an authoring decision about the construction -- not a global setting:

    KEEP   draw the hairstyle normally.
    HIDE   `HideHair: true`.  The hairstyle is not drawn at all.
    BALD   `UseBaldHead: true`.  The farmer is drawn with the game's bald
           sprite, so the HEAD SILHOUETTE ITSELF shrinks; hair does not merely
           disappear, the skull under the hat gets smaller.

Evidence for the default, measured over the source library's 116 hats
(`source_catalog/catalog.json`):

    114  declare nothing            -> KEEP
      2  declare HideHair: true     -> Headscarf 1, Plague Doctor Mask
      0  declare UseBaldHead

So KEEP is what real authors overwhelmingly ship, and the two exceptions are
both pieces that enclose the whole head.  An earlier note in this project
suggested close-fitting caps "usually" use hair hiding; the corpus does not
support that, and this module defaults accordingly.  HIDE and BALD are opt-in
per base, justified by construction, and never applied because a metric
improved.

Per-direction policies are supported because Fashion Sense evaluates
`HideHair` and `UseBaldHead` on each direction model independently -- a hood
that encloses the head from the front but shows hair at the back is expressible.
"""
from __future__ import annotations

import json
import os

KEEP = "KEEP"
HIDE = "HIDE"
BALD = "BALD"
POLICIES = (KEEP, HIDE, BALD)

CONFIG = "authored/hair_policy.json"
DIRECTIONS = ("front", "right", "left", "back")


def flags(policy: str) -> dict:
    """The Fashion Sense properties a policy maps to, for one direction."""
    if policy not in POLICIES:
        raise ValueError(f"unknown hair policy {policy!r}; expected {POLICIES}")
    return {
        KEEP: {"HideHair": False},
        HIDE: {"HideHair": True},
        # UseBaldHead replaces the farmer sprite; the hairstyle is still drawn
        # over the bald head unless it is also hidden, so BALD implies HideHair.
        BALD: {"HideHair": True, "UseBaldHead": True},
    }[policy]


def load(path: str = CONFIG) -> dict:
    if not os.path.isfile(path):
        return {"default": KEEP, "bases": {}}
    return json.load(open(path))


def for_base(name: str, cfg: dict | None = None) -> dict:
    """{direction: policy} for a base — a scalar entry applies to all four."""
    cfg = cfg if cfg is not None else load()
    entry = (cfg.get("bases") or {}).get(name, cfg.get("default", KEEP))
    if isinstance(entry, str):
        return {d: entry for d in DIRECTIONS}
    out = {d: entry.get(d, entry.get("default", KEEP)) for d in DIRECTIONS}
    return out


def from_source(app: dict) -> dict:
    """Preserve what the SOURCE author declared, per direction.

    Source fidelity outranks our defaults: if an artist hid the hair under
    their headscarf, an item generated from that art keeps doing so.
    """
    out = {}
    for d in DIRECTIONS:
        blk = None
        for key, val in (app.get("directions") or {}).items():
            if key.lower().startswith(d):
                blk = val
                break
        if blk is None:
            out[d] = KEEP
        elif blk.get("UseBaldHead"):
            out[d] = BALD
        elif blk.get("HideHair"):
            out[d] = HIDE
        else:
            out[d] = KEEP
    return out
