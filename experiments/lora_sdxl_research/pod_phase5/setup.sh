#!/usr/bin/env bash
# Phase-5 pod setup (RunPod A40, volume at /workspace).  Idempotent: re-running skips what exists.
#   sd-scripts pinned to v0.12.0 (released 2026-09-24; v0.12.1 was same-day new, not used)
#   venv /workspace/phase5/venv with --system-site-packages, so the image's torch 2.8 / CUDA 12.8 is reused, not replaced
#   SDXL Base 1.0 (official single file): reused from the volume if present, else downloaded once
set -euo pipefail
P=/workspace/phase5; SDS_TAG=v0.12.0
mkdir -p "$P" "$P/models"
cd "$P"
if [ ! -d sd-scripts/.git ]; then
    git clone --depth 1 --branch "$SDS_TAG" https://github.com/kohya-ss/sd-scripts.git sd-scripts
fi
git -C sd-scripts describe --tags --exact-match
if [ ! -x venv/bin/python ]; then
    python3 -m venv --system-site-packages venv
fi
. venv/bin/activate
TORCH_BEFORE=$(python -c 'import torch; print(torch.__version__)')
if [ ! -f venv/.sds_installed ]; then
    # requirements.txt has no torch pin; constrain to the image's torch so pip cannot swap it
    echo "torch==$TORCH_BEFORE" > /tmp/torch_constraint.txt
    # requirements.txt ends with '-e .' (the sd-scripts package itself): pip must run from inside the checkout
    (cd sd-scripts && pip install -q -c /tmp/torch_constraint.txt -r requirements.txt)
    pip install -q -c /tmp/torch_constraint.txt peft tensorboard
    touch venv/.sds_installed
fi
python - <<'EOF'
import torch, diffusers, transformers, accelerate, bitsandbytes, peft
print('torch', torch.__version__, 'cuda', torch.version.cuda, 'gpu', torch.cuda.get_device_name(0),
      'bf16', torch.cuda.is_bf16_supported())
print('diffusers', diffusers.__version__, 'transformers', transformers.__version__, 'accelerate', accelerate.__version__,
      'bitsandbytes', bitsandbytes.__version__, 'peft', peft.__version__)
EOF
[ "$(python -c 'import torch; print(torch.__version__)')" = "$TORCH_BEFORE" ] || { echo "torch changed!"; exit 1; }
BASE=$(find /workspace -maxdepth 6 -name 'sd_xl_base_1.0.safetensors' -size +6G 2>/dev/null | head -1 || true)
if [ -z "$BASE" ]; then
    python - <<'EOF'
from huggingface_hub import hf_hub_download
print(hf_hub_download('stabilityai/stable-diffusion-xl-base-1.0', 'sd_xl_base_1.0.safetensors', local_dir='/workspace/phase5/models'))
EOF
    BASE=$P/models/sd_xl_base_1.0.safetensors
fi
sha256sum "$BASE" | tee "$P/base_model.sha256"
echo "$BASE" > "$P/base_model.txt"
echo "base model: $BASE"
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv
df -h /workspace | tail -1
