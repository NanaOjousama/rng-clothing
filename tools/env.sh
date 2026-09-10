#!/usr/bin/env bash
# Activate the project-local Python environment.
#
#   source tools/env.sh
#
# The GENERATOR is deliberately dependency-free: generator/png_utils.py builds
# RGBA8 PNGs from zlib+struct, and nothing under generator/ or tools/ imports
# PIL, NumPy or SciPy.  Every validate_*.py therefore runs on a bare system
# python3 -- do not add a dependency to that path.
#
# The venv exists for ANALYSIS tools only (tools/palette.py reads arbitrary
# reference JPG/PNG source art and does perceptual colour maths).  Keeping the
# two apart is what stops a missing wheel from breaking generation.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ ! -x "$ROOT/.venv/bin/python" ]; then
    echo "no .venv at $ROOT/.venv -- python3 -m venv .venv && .venv/bin/pip install pillow numpy" >&2
    return 1 2>/dev/null || exit 1
fi
# shellcheck disable=SC1091
. "$ROOT/.venv/bin/activate"
export QC_BRIDGE="$ROOT/qc_bridge"
export STARDEW_DIR="/run/media/deck/USD00/steamapps/common/Stardew Valley"
export SMAPI_LOG="$HOME/.config/StardewValley/ErrorLogs/SMAPI-latest.txt"
echo "venv: $(python -V), pillow+numpy for analysis tools"
echo "generator/validators need no venv -- plain python3 is correct there"
