#!/usr/bin/env bash
# Phase-5 pilot driver (pod).  usage: run_pilot.sh smoke | pilot
#   smoke  20 optimiser steps per arm into runs/smoke_<arm> (VRAM + s/it check; no eval)
#   pilot  arms B, A, C (4 epochs each, checkpoint every epoch) -> eval (base, A, B, C, B epoch 2) -> sheets -> DONE
# Status: /workspace/phase5/STATUS (one line per stage).  Safety: after DONE, if /workspace/phase5/PULLED does not appear
# within 60 min (results not fetched), the pod stops itself so GPU billing cannot run on idle.
set -uo pipefail
P=/workspace/phase5; cd "$P"; . venv/bin/activate
BASE=$(cat base_model.txt); MODE=${1:-pilot}
st() { echo "$(date -u +%FT%TZ) $*" | tee -a "$P/STATUS"; }

check_keys() {  # sd-scripts accepts unknown TOML keys silently: refuse to train on a typo
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
    st "train $arm start"
    accelerate launch --num_processes 1 --num_machines 1 --mixed_precision bf16 --dynamo_backend no \
        sd-scripts/sdxl_train_network.py --config_file "$cfg" --pretrained_model_name_or_path "$BASE" \
        > "$P/runs/train_$arm.log" 2>&1
    local rc=$?
    nvidia-smi --query-gpu=memory.used --format=csv,noheader >> "$P/runs/train_$arm.log"
    st "train $arm exit $rc"; return $rc
}

mkdir -p runs eval
check_keys configs/pilot_A.toml configs/pilot_B.toml configs/pilot_C.toml || { st "config key check FAILED"; exit 1; }

if [ "$MODE" = smoke ]; then
    for arm in B A C; do
        python - "$arm" <<'EOF'
import sys, toml
a = sys.argv[1]; c = toml.load(f'/workspace/phase5/configs/pilot_{a}.toml')
c.pop('max_train_epochs'); c.pop('save_every_n_epochs'); c['max_train_steps'] = 20
c['output_dir'] = c['logging_dir'] = f'/workspace/phase5/runs/smoke_{a}'
toml.dump(c, open(f'/workspace/phase5/configs/smoke_{a}.toml', 'w'))
EOF
        train "smoke_$arm" "configs/smoke_$arm.toml" || exit 1
        grep -E "steps:|it/s|s/it|CUDA out of memory|Error" "runs/train_smoke_$arm.log" | tail -3
    done
    st "SMOKE DONE"; exit 0
fi

for arm in B A C; do
    train "$arm" "configs/pilot_$arm.toml" || { st "PILOT FAILED at $arm"; break; }
done
st "eval start"
python eval_phase5.py --tag base --seeds 1 --no-holdout > eval/base.log 2>&1
for arm in A B C; do
    f=runs/pilot_$arm/sdvhat_p5_pilot_$arm.safetensors
    [ -f "$f" ] && python eval_phase5.py --tag "$arm" --lora "$P/$f" > "eval/$arm.log" 2>&1
done
f=runs/pilot_B/sdvhat_p5_pilot_B-000002.safetensors
[ -f "$f" ] && python eval_phase5.py --tag B_e2 --lora "$P/$f" --seeds 2 --no-holdout > eval/B_e2.log 2>&1
python eval_phase5.py --sheets > eval/sheets.log 2>&1
st "DONE"
for i in $(seq 60); do [ -f "$P/PULLED" ] && exit 0; sleep 60; done
st "results not pulled in 60 min: stopping pod"
# RUNPOD_* are set for the container's PID 1, not exported into SSH / nohup shells
for v in RUNPOD_POD_ID RUNPOD_API_KEY; do export "$(tr '\0' '\n' < /proc/1/environ | grep "^$v=")"; done
command -v runpodctl >/dev/null && runpodctl stop pod "$RUNPOD_POD_ID"
