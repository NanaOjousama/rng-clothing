#!/usr/bin/env bash
# Phase-5 pilot-2 driver (pod): C2 (rank32, 10ep) vs C3 (rank64, 10ep), both frozen-TE like winning arm C.
# Trains both -> evals final + midpoint (epoch 5) checkpoints of each, against pilot-1's base/C for context
# -> sheets -> DONE.  Same STATUS/PULLED safety-stop contract as run_pilot.sh.
set -uo pipefail
P=/workspace/phase5; cd "$P"; . venv/bin/activate
BASE=$(cat base_model.txt)
st() { echo "$(date -u +%FT%TZ) $*" | tee -a "$P/STATUS"; }

check_keys() {
python - "$@" <<'EOF'
import sys, toml
sys.path.insert(0, '/workspace/phase5/sd-scripts')
import sdxl_train_network as m
dests = {a.dest for a in m.setup_parser()._actions}
bad = {f: sorted(set(toml.load(f)) - dests) for f in sys.argv[1:]}
bad = {f: k for f, k in bad.items() if k}
print('config keys OK' if not bad else f'UNKNOWN KEYS {bad}'); sys.exit(1 if bad else 0)
EOF
}

train() {  # train <arm> <config>
    local arm=$1 cfg=$2
    st "train2 $arm start"
    accelerate launch --num_processes 1 --num_machines 1 --mixed_precision bf16 --dynamo_backend no \
        sd-scripts/sdxl_train_network.py --config_file "$cfg" --pretrained_model_name_or_path "$BASE" \
        > "$P/runs/train2_$arm.log" 2>&1
    local rc=$?
    nvidia-smi --query-gpu=memory.used --format=csv,noheader >> "$P/runs/train2_$arm.log"
    st "train2 $arm exit $rc"; return $rc
}

mkdir -p runs eval
check_keys configs/pilot_C2.toml configs/pilot_C3.toml || { st "pilot2 config key check FAILED"; exit 1; }

for arm in C2 C3; do
    train "$arm" "configs/pilot_$arm.toml" || { st "PILOT2 FAILED at $arm"; break; }
done

st "pilot2 eval start"
for arm in C2 C3; do
    f=runs/pilot2_$arm/sdvhat_p5_pilot2_$arm.safetensors
    [ -f "$f" ] && python eval_phase5.py --tag "p2_$arm" --lora "$P/$f" > "eval/p2_$arm.log" 2>&1
    mid=runs/pilot2_$arm/sdvhat_p5_pilot2_$arm-000005.safetensors
    [ -f "$mid" ] && python eval_phase5.py --tag "p2_${arm}_e5" --lora "$P/$mid" --seeds 2 --no-holdout > "eval/p2_${arm}_e5.log" 2>&1
done
python eval_phase5.py --sheets > eval/sheets2.log 2>&1
st "PILOT2 DONE"
for i in $(seq 60); do [ -f "$P/PULLED2" ] && exit 0; sleep 60; done
st "pilot2 results not pulled in 60 min: stopping pod"
for v in RUNPOD_POD_ID RUNPOD_API_KEY; do export "$(tr '\0' '\n' < /proc/1/environ | grep "^$v=")"; done
command -v runpodctl >/dev/null && runpodctl stop pod "$RUNPOD_POD_ID"
