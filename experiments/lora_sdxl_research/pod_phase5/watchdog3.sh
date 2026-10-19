#!/usr/bin/env bash
# Independent safety-net watchdog for pilot-3 (run_pilot3.sh already stops the pod itself on success
# or failure; this is the backstop in case that script or its SSH session hangs/dies without doing so).
set -uo pipefail
P=/workspace/phase5
SAFETY_MIN=130
st() { echo "$(date -u +%FT%TZ) WD3 $*" | tee -a "$P/STATUS"; }

MARKER=PILOT3_D_BALANCE_DONE
st "watching for the pilot-3 done-marker, backstop cap ${SAFETY_MIN}m"
ok=0
for i in $(seq $((SAFETY_MIN*2))); do
    if grep -qx "$MARKER" "$P/STATUS" 2>/dev/null; then ok=1; break; fi
    if ! pgrep -f "run_pilot3.sh" >/dev/null && [ "$i" -gt 4 ]; then
        st "run_pilot3.sh no longer running and no done-marker -- treating as failed, not hung"
        break
    fi
    sleep 30
done

if [ "$ok" = 1 ]; then
    st "done-marker observed by backstop -- pod should already be stopping, stopping again just in case"
else
    st "done-marker NOT observed (failure or ${SAFETY_MIN}m safety timeout) -- stopping pod anyway"
fi

for v in RUNPOD_POD_ID RUNPOD_API_KEY; do export "$(tr '\0' '\n' < /proc/1/environ | grep "^$v=")"; done
command -v runpodctl >/dev/null && runpodctl stop pod "$RUNPOD_POD_ID" | tee -a "$P/STATUS"
