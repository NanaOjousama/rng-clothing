#!/usr/bin/env bash
# Publish one experiment's sheets + metrics + an UNREVIEWED notes stub to the private lora-reviews
# branch, directly from the pod, before the pod shuts down.
#
# Usage: publish_results.sh <folder-name> <tag...>
#   folder-name : the lora_reviews/<folder-name>/ directory this run gets on the review branch
#                 (must be unique per experiment -- the caller picks it, e.g. "phase5_pilot5_foo_2026-10-20")
#   tag...      : one or more eval tags (as passed to eval_phase5.py --tag) whose sheets/holdout/seed
#                 images and metrics rows get included. The shared compare_front/compare_fourview
#                 sheets (every checkpoint) are always included too.
#
# Publishes ONLY images + a metrics excerpt + NOTES.md. Never weights, never training data.
# Credential handling: reads $GITHUB_TOKEN from the environment (meant to come from a RunPod account
# secret via `{{ RUNPOD_SECRET_<name> }}` in the pod's env, never typed into this script or any file).
# The token is used only in-memory as a per-request Authorization header (`git -c http.extraHeader=...`)
# -- never written to .git-credentials, never placed in the remote URL, never echoed, and the work
# directory lives under /root (container-local, wiped with the pod) -- never under /workspace (the
# persistent network volume).
#
# Exit code 0 = verified push succeeded. Nonzero = publish failed after retries (caller must still
# proceed to the billing-safety shutdown regardless -- see run_pilotN.sh's use of this script).
set -uo pipefail

FOLDER="${1:?usage: publish_results.sh <folder-name> <tag...>}"; shift
TAGS=("$@")
[ "${#TAGS[@]}" -ge 1 ] || { echo "usage: publish_results.sh <folder-name> <tag...>"; exit 2; }

P=/workspace/phase5
SHEETS="$P/eval/sheets"
WORK=/root/lora_reviews_publish   # container-local only, never the network volume
REPO_SSH_HOST="github.com"
REPO="NanaOjousama/rng-clothing"
BRANCH="lora-reviews"
RETRIES=3
RETRY_DELAY=20

st() { echo "$(date -u +%FT%TZ) PUBLISH $*" | tee -a "$P/STATUS"; }

if [ -z "${GITHUB_TOKEN:-}" ]; then
    st "GITHUB_TOKEN not set in environment -- cannot publish (expected via a RunPod account secret, see publish_results.sh header)"
    exit 1
fi

rm -rf "$WORK"
mkdir -p "$WORK"

# Clone over HTTPS with the token supplied only as a per-request header, never in the URL or a
# credential file, so it never touches disk anywhere (not .git/config, not .git-credentials).
AUTH_HEADER="AUTHORIZATION: basic $(printf 'x-access-token:%s' "$GITHUB_TOKEN" | base64 -w0)"
git -c http.extraHeader="$AUTH_HEADER" clone --depth 1 --branch "$BRANCH" \
    "https://${REPO_SSH_HOST}/${REPO}.git" "$WORK" >>"$P/STATUS.publish_git.log" 2>&1
rc=$?
if [ "$rc" -ne 0 ]; then
    st "clone of $BRANCH failed (rc=$rc) -- see STATUS.publish_git.log (never contains the token)"
    rm -rf "$WORK"
    exit 1
fi

DEST="$WORK/lora_reviews/$FOLDER"
mkdir -p "$DEST"

# Always-present cross-checkpoint comparison sheets, if this eval run regenerated them.
for f in "$SHEETS"/compare_front_s101.png "$SHEETS"/compare_fourview_s101.png; do
    [ -f "$f" ] && cp "$f" "$DEST/"
done

# Per-tag images: holdout truth-vs-generation and seed-variety sheets, both layouts.
for tag in "${TAGS[@]}"; do
    for f in "$SHEETS/${tag}_front_holdout.png" "$SHEETS/${tag}_fourview_holdout.png" \
             "$SHEETS/${tag}_front_seeds.png" "$SHEETS/${tag}_fourview_seeds.png"; do
        [ -f "$f" ] && cp "$f" "$DEST/"
    done
done

# Metrics excerpt: just the rows for these tags out of summary.json (never the raw image tensors,
# never anything from the training run beyond these published numbers).
python3 - "$DEST/metrics_excerpt.json" "$SHEETS/summary.json" "${TAGS[@]}" <<'EOF'
import json, sys
out_path, summary_path, *tags = sys.argv[1:]
try:
    summary = json.load(open(summary_path))
except FileNotFoundError:
    summary = {}
excerpt = {t: summary[t] for t in tags if t in summary}
json.dump(excerpt, open(out_path, 'w'), indent=1)
EOF

cat > "$DEST/NOTES.md" <<EOF
# ${FOLDER}

**STATUS: UNREVIEWED** -- published automatically by the training pipeline right after this
experiment's eval + sheets finished, before the pod shut down. No verdict has been written yet;
this is raw material for review, not a conclusion.

Tags in this experiment: ${TAGS[*]}

Generated: $(date -u +%FT%TZ)

## Files
- \`compare_front_s101.png\`, \`compare_fourview_s101.png\` -- cross-checkpoint comparison, if present
- \`<tag>_front_holdout.png\`, \`<tag>_fourview_holdout.png\` -- held-out hats: ground truth vs generation
- \`<tag>_front_seeds.png\`, \`<tag>_fourview_seeds.png\` -- seed variety per family
- \`metrics_excerpt.json\` -- this experiment's rows from the eval summary (context only, never the
  basis for a verdict by itself -- see CLAUDE.md: a render always outranks a metric)

Images, metrics excerpt and this notes stub only -- no weights, no training data, no source art.
Checkpoints are backed up separately to the Steam Deck (sha256-verified), not published here.
EOF

cd "$WORK"
git config user.name "phase5-pod-pipeline"
git config user.email "noreply@anthropic.com"
git add "lora_reviews/$FOLDER"
git commit -m "LoRA reviews: ${FOLDER} (automated, unreviewed)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>" >>"$P/STATUS.publish_git.log" 2>&1

ok=0
for i in $(seq "$RETRIES"); do
    git -c http.extraHeader="$AUTH_HEADER" push origin "$BRANCH" >>"$P/STATUS.publish_git.log" 2>&1
    push_rc=$?
    if [ "$push_rc" -eq 0 ]; then
        # Verify: the branch's remote HEAD must now equal what we just pushed, not just a 0 exit code.
        LOCAL_HEAD=$(git rev-parse HEAD)
        REMOTE_HEAD=$(git -c http.extraHeader="$AUTH_HEADER" ls-remote "https://${REPO_SSH_HOST}/${REPO}.git" "refs/heads/$BRANCH" 2>>"$P/STATUS.publish_git.log" | cut -f1)
        if [ "$LOCAL_HEAD" = "$REMOTE_HEAD" ]; then
            ok=1
            st "push verified on attempt $i ($LOCAL_HEAD)"
            break
        else
            st "push attempt $i returned success but remote HEAD mismatch (local=$LOCAL_HEAD remote=$REMOTE_HEAD) -- retrying"
        fi
    else
        st "push attempt $i failed (rc=$push_rc) -- retrying in ${RETRY_DELAY}s"
    fi
    [ "$i" -lt "$RETRIES" ] && sleep "$RETRY_DELAY"
done

# Clean up the container-local clone regardless of outcome -- nothing here belongs on the volume,
# and nothing here should outlive this run even if the pod were somehow restarted before stopping.
rm -rf "$WORK"
unset GITHUB_TOKEN AUTH_HEADER

if [ "$ok" = 1 ]; then
    st "publish of $FOLDER succeeded"
    exit 0
else
    st "publish of $FOLDER FAILED after $RETRIES attempts -- results remain on the network volume (eval/sheets), safety shutdown proceeds regardless"
    exit 1
fi
