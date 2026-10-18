#!/usr/bin/env bash
set -euo pipefail
ROOT=/workspace/stardew-lora-lab
for h in hat_0104 hat_0172 hat_0197 hat_0199; do
  echo "BEGIN_$h"
  /tmp/stardew-env/bin/python "$ROOT/runpod_prep/compare_lineart.py" --root "$ROOT" --holdout "$h"
done
echo ALL_FIVE_COMPLETE

[executed on device: LAPTOP-GGEDSK3A (11c475b4-4eca-400d-8353-a8393d5d126f)]