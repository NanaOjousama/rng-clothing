#!/usr/bin/env bash
# Standalone watchdog for the corrected (post-UNet-merge-fix) eval+sheets run already in flight.
# Does NOT touch or restart that run -- only watches STATUS and stops the pod afterward, success or not.
# Never touches the network volume; only `pod-action stop` (keeps GPU billing off, keeps all data).
set -uo pipefail
P=/workspace/phase5
SAFETY_MIN=90   # hard cap: eval+sheets normally finishes in well under this; covers a hang or crash
st() { echo "$(date -u +%FT%TZ) WATCHDOG $*" | tee -a "$P/STATUS"; }

DONE_MARKER=FIXED_EVAL_DONE
st "watching for the done-marker (cap ${SAFETY_MIN}m)"
ok=0
for i in $(seq $((SAFETY_MIN*2))); do
    # exact full-line match only: the marker line in STATUS is the bare word with no timestamp/tag
    # prefix, unlike every watchdog log line (which is prefixed and must never self-match this check)
    if grep -qx "$DONE_MARKER" "$P/STATUS" 2>/dev/null; then ok=1; break; fi
    # also bail early if the eval process has died without writing the done-marker (crash, not a hang)
    if ! pgrep -f "eval_phase5.py" >/dev/null && [ "$i" -gt 4 ]; then
        st "eval_phase5.py no longer running and no FIXED_EVAL_DONE marker -- treating as failed, not hung"
        break
    fi
    sleep 30
done

if [ "$ok" = 1 ]; then
    st "FIXED_EVAL_DONE observed -- stopping pod"
else
    st "FIXED_EVAL_DONE NOT observed (failure or ${SAFETY_MIN}m safety timeout) -- stopping pod anyway"
fi

for v in RUNPOD_POD_ID RUNPOD_API_KEY; do export "$(tr '\0' '\n' < /proc/1/environ | grep "^$v=")"; done
if command -v runpodctl >/dev/null; then
    runpodctl stop pod "$RUNPOD_POD_ID" | tee -a "$P/STATUS"
else
    st "runpodctl not found -- could not stop pod automatically"
fi
