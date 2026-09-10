"""Client for the Stardew Visual QC Bridge.

The bridge is a directory of JSON files, so this is deliberately tiny: write a
request, wait for the response file, return it.  No daemon, no socket, no new
dependency, and everything it does is inspectable afterwards.

    python3 tools/qc.py ping
    python3 tools/qc.py list_hats
    python3 tools/qc.py equip_hat id=RNGClothing.FashionSense.V5HatValidation/Hat/"V5 Hat 000 (Shallow)"
    python3 tools/qc.py set_direction direction=front
    python3 tools/qc.py capture_all label=seed000
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid

ROOT = os.environ.get("QC_BRIDGE", "/run/media/deck/USD00/RNG_clothing/qc_bridge")
REQUESTS = os.path.join(ROOT, "requests")
RESPONSES = os.path.join(ROOT, "responses")
CAPTURES = os.path.join(ROOT, "captures")


class BridgeDown(RuntimeError):
    """The game is not running, or the bridge mod did not load."""


def send(command: str, timeout: float = 60.0, **args) -> dict:
    """Write one request and block until the game answers."""
    os.makedirs(REQUESTS, exist_ok=True)
    os.makedirs(RESPONSES, exist_ok=True)
    rid = f"{int(time.time()*1000)}-{uuid.uuid4().hex[:6]}"
    body = {"id": rid, "command": command, "args": {k: str(v) for k, v in args.items()}}
    # write-then-move: the mod must never read a half-written request
    tmp = os.path.join(REQUESTS, rid + ".json.tmp")
    with open(tmp, "w") as fh:
        json.dump(body, fh)
    os.replace(tmp, os.path.join(REQUESTS, rid + ".json"))

    path = os.path.join(RESPONSES, rid + ".json")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(path):
            for _ in range(10):                     # tolerate a partial flush
                try:
                    with open(path) as fh:
                        out = json.load(fh)
                    os.remove(path)
                    return out
                except (json.JSONDecodeError, FileNotFoundError):
                    time.sleep(0.05)
        time.sleep(0.1)
    raise BridgeDown(
        f"no response to {command!r} within {timeout:.0f}s.\n"
        "  * is Stardew Valley running with a save loaded?\n"
        "  * does the SMAPI log show 'QC Bridge ready'?\n"
        f"  * bridge root: {ROOT}")


def alive(timeout: float = 5.0) -> bool:
    try:
        return bool(send("ping", timeout=timeout).get("ok"))
    except BridgeDown:
        return False


def require(command: str, **args) -> dict:
    out = send(command, **args)
    if not out.get("ok"):
        raise RuntimeError(f"{command} failed: {out.get('message')}")
    return out


def reload_packs(pack: str | None = None, timeout: float = 120.0) -> dict:
    """Reload Fashion Sense content packs in place, no game restart.

    Fashion Sense loads pack textures once at startup.  Before this existed the
    only way to see a rebuilt pack was to restart the game, and three capture
    runs were lost to that assumption -- including one that captured empty
    frames because the world was already loaded, so a `world_ready` check
    passed while Fashion Sense still held the old textures.

    Returns the bridge response, whose `hats` list is resolved AFTER the reload
    so a caller can never capture against a listing taken before it.
    """
    args = {"pack": pack} if pack else {}
    return send("fs_reload", timeout=timeout, **args)


# Fashion Sense mod folder, used to tell a REFRESHED pack from a NEW one.
MODS = "/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods"


def pack_is_new(pack_dir: str, session: str) -> bool:
    """Was this pack folder created after the running game started?

    fs_reload refreshes packs the game already knows about.  A pack FOLDER
    created after startup is not registered with SMAPI at all, so Fashion
    Sense lists its appearance names but never loads its textures -- the hats
    equip and draw nothing, which looks exactly like art that failed.
    Measured: every pack that existed before its session captured correctly;
    the one installed mid-session did not.
    """
    try:
        made = os.path.getmtime(pack_dir)
    except OSError:
        return False
    try:
        start = time.mktime(time.strptime(session, "%Y%m%d-%H%M%S"))
    except (ValueError, TypeError):
        return False
    return made > start


def refresh(pack: str | None = None, expect: int | None = None,
            pack_dir: str | None = None, session: str | None = None) -> dict:
    """Reload and verify, or say plainly that a restart is required.

    Never returns quietly on failure: a reload that did not happen looks
    exactly like a reload that did, right up until the captures come back
    empty.
    """
    if pack_dir and session and pack_is_new(pack_dir, session):
        raise BridgeDown(
            f"{pack_dir} was installed AFTER this game session started.\n"
            "  fs_reload refreshes packs the game already knows about; a new\n"
            "  pack folder is not registered with SMAPI, so Fashion Sense will\n"
            "  list its appearances but draw nothing. Restart the game.")
    out = reload_packs(pack)
    if not out.get("ok"):
        raise BridgeDown(
            f"fs_reload failed: {out.get('message')}\n"
            "  fall back to restarting the game so Fashion Sense reloads at startup")
    if expect is not None and pack:
        got = [h for h in out.get("hats", []) if h.startswith(pack)]
        if len(got) < expect:
            raise BridgeDown(
                f"reloaded, but {pack} lists {len(got)} appearances, expected {expect}.\n"
                "  the pack may be malformed; a float in any Position field makes "
                "Fashion Sense reject the whole model silently")
    return out


def latest_session() -> str | None:
    if not os.path.isdir(CAPTURES):
        return None
    rows = sorted(os.listdir(CAPTURES))
    return os.path.join(CAPTURES, rows[-1]) if rows else None


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    command, kwargs = argv[0], {}
    for token in argv[1:]:
        if "=" in token:
            k, v = token.split("=", 1)
            kwargs[k] = v
    try:
        out = send(command, **kwargs)
    except BridgeDown as exc:
        print(f"BRIDGE DOWN: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2)[:8000])
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
