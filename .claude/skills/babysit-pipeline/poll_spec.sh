#!/usr/bin/env bash
# Background poller: re-checks a spec until it completes, needs attention,
# or a max wall-clock cap is hit. Exits (re-invoking the agent) with the
# final status so the agent can decide the next action.
# Usage: poll_spec.sh <spec-id> <issue-number> [max_minutes]
set -uo pipefail
SPEC="$1"; ISSUE="$2"; MAXMIN="${3:-130}"
HERE="$(cd "$(dirname "$0")" && pwd)"
# Log OUTSIDE the repo — the script is checked in, its output must not dirty the tree.
LOGDIR="${POLL_LOG_DIR:-$HOME/.cache/anyplot-babysit}"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/poll_${SPEC}.log"
INTERVAL=180
iters=$(( MAXMIN * 60 / INTERVAL ))
# A "stall" is only real once the dispatcher has finished AND no impl runs for
# this spec are still active. Early 0/15 is normal: impl:done labels lag the
# whole generate->review->merge chain, and merges cluster near the end.
pipeline_active() {
  # NOTE: impl-review/impl-merge runs are titled "Review: PR #N" / "Merge: PR #N"
  # (no spec name), so we cannot filter those by $SPEC. Because specs are
  # processed strictly sequentially, ANY active impl-* run belongs to the
  # current spec — so an unfiltered in_progress/queued check is correct here.
  for wf in bulk-generate.yml impl-generate.yml impl-review.yml impl-repair.yml impl-merge.yml impl-review-retry.yml; do
    local out
    if ! out=$(gh run list --workflow="$wf" --limit 12 --json status \
        --jq '.[] | select(.status=="in_progress" or .status=="queued") | .status' 2>&1); then
      # gh failure means status is UNKNOWN — treat as "might be active" so a
      # rate-limit/auth hiccup can never manufacture a false STALL.
      printf 'WARN: gh run list --workflow=%s failed; assuming pipeline active: %s\n' "$wf" "$out" >> "$LOG"
      return 0
    fi
    if grep -q . <<<"$out"; then return 0; fi
  done
  return 1
}

last_done=-1; stale=0
for ((i=1; i<=iters; i++)); do
  out="$(bash "$HERE/monitor_spec.sh" "$SPEC" "$ISSUE")"
  ts="$(TZ=UTC date -u +%H:%M:%S 2>/dev/null || echo '')"
  printf '[%s iter %d/%d]\n%s\n\n' "$ts" "$i" "$iters" "$out" >> "$LOG"
  status="$(grep -o 'STATUS=[A-Z_]*' <<<"$out" | tail -1)"
  done_now="$(grep -oE 'done=[0-9]+' <<<"$out" | grep -oE '[0-9]+' | head -1)"

  if [ "$status" = "STATUS=COMPLETE" ] || [ "$status" = "STATUS=NEEDS_ATTENTION" ]; then
    echo "=== FINAL for $SPEC (#$ISSUE) after $i checks ==="
    echo "$out"
    exit 0
  fi

  # stall detection: no label progress for a while AND the pipeline has gone
  # idle (dispatcher done + no impl runs active for this spec). A non-numeric
  # done count means monitor_spec.sh errored — report, don't count as a stall.
  if ! [[ "$done_now" =~ ^[0-9]+$ ]]; then
    # no `continue` here — the sleep below must still run or errors spin hot
    printf 'WARN: non-numeric done count (%s) — monitor error, skipping stall accounting\n' "${done_now:-empty}" >> "$LOG"
  elif [ "$done_now" = "$last_done" ]; then stale=$((stale+1)); else stale=0; last_done="$done_now"; fi
  if [ "$stale" -ge 5 ] && ! pipeline_active; then
    echo "=== STALL for $SPEC (#$ISSUE): done stuck at $done_now/15 for ~$((stale*INTERVAL/60)) min, pipeline idle ==="
    echo "$out"
    exit 0
  fi
  sleep "$INTERVAL"
done

echo "=== TIMEOUT for $SPEC (#$ISSUE) after ${MAXMIN}min — last status: ==="
bash "$HERE/monitor_spec.sh" "$SPEC" "$ISSUE"
exit 0
