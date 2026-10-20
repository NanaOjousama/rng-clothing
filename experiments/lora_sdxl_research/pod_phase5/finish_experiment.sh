#!/usr/bin/env bash
# Shared "finish" step for every pilot driver from here on:
#   1. checksum the checkpoint dir and wait (bounded) for a human-confirmed pull of those
#      checkpoints to the Steam Deck
#   2. publish results to lora-reviews (bounded retries, in publish_results.sh)
#   3. ALWAYS proceed to the billing-safety pod stop, no matter how 1 or 2 went
#
# Source this (not execute) from a driver script after sheets regeneration:
#
#   . finish_experiment.sh "$FOLDER" "$CKPT_DIR" tag1 tag2 ...
#
# Never blocks indefinitely: the pull-wait has its own cap (PULL_WAIT_MIN) and publish_results.sh has
# its own bounded retry count; this wrapper adds no further retry layer around either. Nothing here
# depends on GitHub or on a human to avoid runaway billing -- the network volume already holds every
# checkpoint and eval output regardless of whether the pull was confirmed or publishing succeeded, so
# a timeout on either step only means a manual recovery pull afterward, never data loss.
set -uo pipefail
P=/workspace/phase5
PULL_WAIT_MIN=45
st() { echo "$(date -u +%FT%TZ) $*" | tee -a "$P/STATUS"; }

FOLDER="${1:?finish_experiment.sh: missing folder name}"; shift
CKPT_DIR="${1:?finish_experiment.sh: missing checkpoint dir}"; shift

if [ -d "$CKPT_DIR" ]; then
    (cd "$CKPT_DIR" && sha256sum *.safetensors > CHECKSUMS.sha256 2>/dev/null)
    st "finish: checksums written to $CKPT_DIR/CHECKSUMS.sha256"
    PULL_MARKER="$CKPT_DIR/PULLED"
    rm -f "$PULL_MARKER"
    st "finish: waiting up to ${PULL_WAIT_MIN}m for checkpoint pull confirmation ($PULL_MARKER)"
    pulled=0
    for i in $(seq $((PULL_WAIT_MIN*2))); do
        [ -f "$PULL_MARKER" ] && { pulled=1; break; }
        sleep 30
    done
    if [ "$pulled" = 1 ]; then
        st "finish: checkpoint pull confirmed"
    else
        st "finish: checkpoint pull NOT confirmed after ${PULL_WAIT_MIN}m -- proceeding anyway (checksummed checkpoints remain on the network volume for a later pull)"
    fi
else
    st "finish: checkpoint dir $CKPT_DIR not found -- skipping checksum/pull-wait step"
fi

if [ -z "${GITHUB_TOKEN:-}" ]; then
    st "finish: GITHUB_TOKEN not set -- skipping publish (results remain on the volume), proceeding to shutdown"
    publish_rc=1
else
    "$P/publish_results.sh" "$FOLDER" "$@"
    publish_rc=$?
fi
[ "$publish_rc" -eq 0 ] && st "finish: publish OK, proceeding to shutdown" || st "finish: publish did not succeed, proceeding to shutdown anyway (billing safety is never gated on GitHub)"

for v in RUNPOD_POD_ID RUNPOD_API_KEY; do export "$(tr '\0' '\n' < /proc/1/environ | grep "^$v=")"; done
command -v runpodctl >/dev/null && runpodctl stop pod "$RUNPOD_POD_ID" | tee -a "$P/STATUS"
