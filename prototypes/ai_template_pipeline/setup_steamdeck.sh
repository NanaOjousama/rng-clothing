#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="$HERE/.venv"
CACHE="/run/media/deck/USD00/ai-model-cache"

mkdir -p "$CACHE"
python3 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install torch --index-url https://download.pytorch.org/whl/cpu
"$VENV/bin/pip" install -r "$HERE/requirements.txt"

cat <<EOF
Ready.
Run preparation smoke test:
  HF_HOME="$CACHE" "$VENV/bin/python" "$HERE/run_pipeline.py" --prepare-only

Full model run will download SDXL + ControlNet + LoRA into:
  $CACHE
EOF
