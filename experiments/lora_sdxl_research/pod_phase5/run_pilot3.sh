#!/usr/bin/env bash
# Pilot-3 driver: build the front/fourview symlink split (additive, original dataset untouched),
# train D_balance (rank32/alpha16, frozen TE, cached TE outputs, fourview upweighted 2x, 7 epochs),
# eval with the corrected UNet-merge loader using the same fixed prompts/seeds/holdout as every other
# arm, regenerate comparison sheets, mark done, auto-stop the pod (success or failure/timeout).
set -uo pipefail
P=/workspace/phase5; cd "$P"; . venv/bin/activate
BASE=$(cat base_model.txt)
MARKER=PILOT3_D_BALANCE_DONE
SAFETY_MIN=120
st() { echo "$(date -u +%FT%TZ) $*" | tee -a "$P/STATUS"; }

st "pilot3 D_balance: building symlink split"
python3 build_split.py | tee -a "$P/STATUS" || { st "PILOT3 FAILED at split build"; echo "$MARKER" >> "$P/STATUS"; exit 1; }

st "pilot3 D_balance: train start"
accelerate launch --num_processes 1 --num_machines 1 --mixed_precision bf16 --dynamo_backend no \
    sd-scripts/sdxl_train_network.py --config_file configs/pilot_D_balance.toml \
    --pretrained_model_name_or_path "$BASE" > "$P/runs/train3_D_balance.log" 2>&1
rc=$?
nvidia-smi --query-gpu=memory.used --format=csv,noheader >> "$P/runs/train3_D_balance.log"
st "pilot3 D_balance: train exit $rc"
if [ "$rc" -ne 0 ]; then
    st "PILOT3 FAILED at training"
    echo "$MARKER" >> "$P/STATUS"
    for v in RUNPOD_POD_ID RUNPOD_API_KEY; do export "$(tr '\0' '\n' < /proc/1/environ | grep "^$v=")"; done
    command -v runpodctl >/dev/null && runpodctl stop pod "$RUNPOD_POD_ID" | tee -a "$P/STATUS"
    exit 1
fi

st "pilot3 D_balance: eval start"
f=runs/pilot3_D_balance/sdvhat_p5_pilot3_D_balance.safetensors
[ -f "$f" ] && python eval_phase5.py --tag p3_D_balance --lora "$P/$f" > eval/p3_D_balance.log 2>&1
python eval_phase5.py --sheets > eval/sheets4.log 2>&1
st "pilot3 D_balance: sheets regenerated"

echo "$MARKER" >> "$P/STATUS"
st "pilot3 D_balance: stopping pod"
for v in RUNPOD_POD_ID RUNPOD_API_KEY; do export "$(tr '\0' '\n' < /proc/1/environ | grep "^$v=")"; done
command -v runpodctl >/dev/null && runpodctl stop pod "$RUNPOD_POD_ID" | tee -a "$P/STATUS"
