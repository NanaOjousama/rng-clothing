"""Client for the Stardew Visual QC Bridge.

The bridge is a directory of JSON files, so this is deliberately tiny: write a
request, wait for the response file, return it.  No daemon, no socket, no new
dependency, and everything it does is inspectable afterwards.

Use the SUBCOMMANDS.  They exist because the bridge has ordering traps that
cost real capture runs -- a reloaded pack that did not reload, a pack folder
created after the game started, a `world_ready` that says nothing about
textures.  The library functions that guard against those were previously
unreachable from the command line, so a hand-typed call could silently capture
stale art.  Now the safe path is the easy path:

    python3 tools/qc.py ping
    python3 tools/qc.py state
    python3 tools/qc.py packs
    python3 tools/qc.py refresh --pack <id> --expect <n>
    python3 tools/qc.py worn --pack <id>
    python3 tools/qc.py compare <session-dir>
    python3 tools/qc.py menu-probe --what state
    python3 tools/qc.py smapi-log --errors

`raw` still sends an arbitrary command for debugging, and says out loud that it
skips the guards:

    python3 tools/qc.py raw capture_all label=seed000
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


def pack_dir_for(pack_id: str) -> str | None:
    """The installed folder for a pack id, so pack_is_new() can be applied.

    Read from each manifest's UniqueID rather than guessed from the folder name:
    our pack folders are named RNG-Cap2Fit while the id is
    RNGClothing.FashionSense.Cap2Fit, and guessing gets that wrong every time.
    """
    if not os.path.isdir(MODS):
        return None
    for name in os.listdir(MODS):
        man = os.path.join(MODS, name, "manifest.json")
        if not os.path.isfile(man):
            continue
        try:
            with open(man, encoding="utf-8-sig") as fh:
                uid = json.load(fh).get("UniqueID")
        except (json.JSONDecodeError, OSError):
            continue
        if uid == pack_id:
            return os.path.join(MODS, name)
    return None


def current_session() -> str | None:
    """The running game's session stamp, which dates every capture folder."""
    try:
        return send("ping", timeout=10.0).get("session")
    except BridgeDown:
        return None


def latest_session() -> str | None:
    if not os.path.isdir(CAPTURES):
        return None
    rows = sorted(os.listdir(CAPTURES))
    return os.path.join(CAPTURES, rows[-1]) if rows else None


SMAPI_LOG = os.path.expanduser(
    os.environ.get("SMAPI_LOG",
                   "~/.config/StardewValley/ErrorLogs/SMAPI-latest.txt"))


def _preflight() -> None:
    if not alive():
        raise SystemExit(
            "The QC bridge is not answering.\n"
            "  1. launch Stardew Valley through SMAPI\n"
            "  2. load a save\n"
            "  3. check the SMAPI console for 'QC Bridge ready'\n"
            "Nothing below this point can be faked with a synthetic composite.")


def _dump(out: dict) -> int:
    print(json.dumps(out, indent=2)[:8000])
    return 0 if out.get("ok") else 1


def cmd_ping(args) -> int:
    # Short by default: ping is the command you run to find out whether the game
    # is up, so it must fail fast rather than block for the full timeout.
    return _dump(send("ping", timeout=args.ping_timeout))


def cmd_state(args) -> int:
    _preflight()
    return _dump(send("get_render_state", timeout=args.timeout))


def cmd_packs(args) -> int:
    """Every appearance the running game can see, grouped by pack."""
    _preflight()
    rows = require("list_hats")["hats"]
    groups: dict[str, list[dict]] = {}
    for h in rows:
        groups.setdefault(h.get("pack_id") or "?", []).append(h)
    for pack, hats in sorted(groups.items()):
        where = pack_dir_for(pack)
        print(f"{pack}   {len(hats)} appearance(s)"
              f"{'' if where else '   [no installed folder found]'}")
        if args.verbose:
            for h in hats:
                print(f"    {h.get('appearance_id')}")
    print(f"\n{len(rows)} appearance(s) in {len(groups)} pack(s)")
    return 0


def cmd_refresh(args) -> int:
    """Reload packs and PROVE the reload happened before anyone captures."""
    _preflight()
    out = refresh(pack=args.pack, expect=args.expect,
                  pack_dir=args.pack_dir or (pack_dir_for(args.pack) if args.pack else None),
                  session=current_session())
    got = [h for h in out.get("hats", []) if args.pack and h.startswith(args.pack)]
    print(f"reloaded; {len(got) if args.pack else len(out.get('hats', []))} "
          f"appearance(s) visible"
          + (f" for {args.pack}" if args.pack else ""))
    return 0 if out.get("ok") else 1


def cmd_worn(args) -> int:
    """Front/right/back/left worn captures for a pack, after a verified reload.

    The reload and the new-pack check run first and are not optional: that
    ordering is the whole reason this subcommand exists instead of a raw
    equip + capture_all_directions pair.
    """
    _preflight()
    session = current_session()
    refresh(pack=args.pack, expect=args.expect,
            pack_dir=args.pack_dir or (pack_dir_for(args.pack) if args.pack else None),
            session=session)
    rows = require("list_hats")["hats"]
    if args.pack:
        rows = [h for h in rows if h.get("pack_id") == args.pack]
    if args.name:
        rows = [h for h in rows if args.name.lower() in (h.get("appearance_id") or "").lower()]
    if not rows:
        raise SystemExit(f"no appearances matched (pack={args.pack!r} name={args.name!r}); "
                         "run `qc.py packs` to see what the game can actually see")
    # one farmer, one hairstyle, one frozen idle frame: the only thing that
    # differs between two captures must be the garment
    require("set_scene", hairstyle=args.hairstyle, direction="front", freeze="true")
    dirs = []
    for i, hat in enumerate(rows, 1):
        label = hat.get("folder") or hat.get("name") or f"item{i}"
        print(f"[{i}/{len(rows)}] {hat.get('appearance_id')}")
        try:
            require("equip_hat", id=hat["appearance_id"])
            out = require("capture_all_directions", label=label)
            dirs.append(out.get("directory", label))
        except (RuntimeError, BridgeDown) as exc:
            print(f"    SKIPPED: {exc}")
    print(f"\n{len(dirs)} capture set(s) under {CAPTURES}")
    for d in dirs:
        print(f"  {d}")
    print("\nMeasure with: python3 tools/qc_metrics.py <session dir>")
    return 0 if dirs else 1


def cmd_compare(args) -> int:
    """Delegate to the existing comparison tools rather than reimplement them."""
    import subprocess
    target = args.session or latest_session()
    if not target:
        raise SystemExit(f"no capture sessions under {CAPTURES}")
    print(f"comparing {target}")
    tool = "qc_compare.py" if args.groups else "qc_metrics.py"
    here = os.path.dirname(os.path.abspath(__file__))
    return subprocess.call([sys.executable, os.path.join(here, tool), target])


def cmd_menu_probe(args) -> int:
    """Probe the live fitting/sewing menu -- state, screen, ingredients, presses."""
    _preflight()
    extra = {}
    if args.key:
        extra["key"] = args.key
    return _dump(send("fitting_probe", timeout=args.timeout, action=args.what, **extra))


def cmd_smapi_log(args) -> int:
    """Read the real SMAPI log. A silent FS rejection only ever shows up here."""
    if not os.path.isfile(SMAPI_LOG):
        raise SystemExit(f"no SMAPI log at {SMAPI_LOG}")
    with open(SMAPI_LOG, errors="replace") as fh:
        lines = fh.readlines()
    if args.errors:
        want = ("ERROR", "WARN", "Exception", "failed", "rejected", "invalid")
        lines = [ln for ln in lines if any(w.lower() in ln.lower() for w in want)]
    if args.grep:
        lines = [ln for ln in lines if args.grep.lower() in ln.lower()]
    for ln in lines[-args.tail:]:
        print(ln.rstrip())
    print(f"\n-- {len(lines)} matching line(s) in {SMAPI_LOG}")
    return 0


def cmd_raw(args) -> int:
    kwargs = dict(t.split("=", 1) for t in args.args if "=" in t)
    print(f"raw {args.command}: this skips the reload and new-pack guards. "
          f"If a capture comes back empty, that is why.", file=sys.stderr)
    try:
        return _dump(send(args.command, timeout=args.timeout, **kwargs))
    except BridgeDown as exc:
        print(f"BRIDGE DOWN: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--timeout", type=float, default=60.0)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ping", help="is the bridge answering?")
    p.add_argument("--ping-timeout", type=float, default=5.0)
    sub.add_parser("state", help="everything the renderer is currently using")

    p = sub.add_parser("packs", help="appearances the running game can see, by pack")
    p.add_argument("-v", "--verbose", action="store_true")

    for name, helptext in (("refresh", "reload Fashion Sense packs and verify it happened"),
                           ("worn", "front/right/back/left worn captures, after a verified reload")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("--pack", help="pack id (see `qc.py packs`)")
        p.add_argument("--expect", type=int,
                       help="appearances the pack must list after reloading; "
                            "a mismatch fails loudly instead of capturing stale art")
        p.add_argument("--pack-dir", help="override the installed folder lookup")
        if name == "worn":
            p.add_argument("--name", help="only appearances matching this substring")
            p.add_argument("--hairstyle", type=int, default=38,
                           help="fixed hairstyle so captures stay comparable")

    p = sub.add_parser("compare", help="measure or compare a capture session")
    p.add_argument("session", nargs="?", help="defaults to the latest session")
    p.add_argument("--groups", action="store_true",
                   help="group-vs-group ranges (qc_compare) instead of raw metrics")

    p = sub.add_parser("menu-probe", help="probe the live fitting/sewing menu")
    p.add_argument("--what", default="state",
                   choices=["state", "screen", "ingredients", "press", "sew", "equip"])
    p.add_argument("--key", help="button/key for --what press")

    p = sub.add_parser("smapi-log", help="read the real SMAPI log")
    p.add_argument("--errors", action="store_true", help="errors and warnings only")
    p.add_argument("--grep")
    p.add_argument("--tail", type=int, default=60)

    p = sub.add_parser("raw", help="send an arbitrary command (skips the guards)")
    p.add_argument("command")
    p.add_argument("args", nargs="*", help="key=value pairs")

    args = ap.parse_args(argv)
    handler = {"ping": cmd_ping, "state": cmd_state, "packs": cmd_packs,
               "refresh": cmd_refresh, "worn": cmd_worn, "compare": cmd_compare,
               "menu-probe": cmd_menu_probe, "smapi-log": cmd_smapi_log,
               "raw": cmd_raw}[args.cmd]
    # A tripped guard is the expected outcome of a bad run, not a crash: print
    # what it found and exit non-zero, so a caller (or a script) reads the
    # diagnosis instead of a traceback.
    try:
        return handler(args)
    except BridgeDown as exc:
        print(f"\nQC GUARD / BRIDGE: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"\nQC COMMAND FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
