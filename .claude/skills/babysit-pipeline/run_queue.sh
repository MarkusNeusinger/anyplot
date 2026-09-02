#!/usr/bin/env bash
# Queue scheduler for the gap backfill (SKILL.md §5): keep up to $SLOTS
# run_spec.sh drivers in flight over a queue file, skipping libraries that are
# already on origin/main and pairs recorded as CONFIRMED GAP in deferred.log.
# Refills a slot as soon as a driver exits and harvests each driver's RESULT line
# into done.log / deferred.log. Before every launch it checks for throttle signs
# (GitHub API quota, a cluster of generate failures, rate-limit signatures in
# failed impl-* logs) and waits instead of launching while any is present.
#
# Usage: run_queue.sh <queue-dir> [slots]
#   <queue-dir>  holds full_queue.txt (`<n-missing> <spec> <lib...>`, one spec
#                per line) and receives the ledger: done.log, deferred.log,
#                queue.log, results/, and an optional rescue_specs.txt
#   [slots]      drivers in flight at once (default 2; 4 only with the user's OK)
# Env: MODEL (default sonnet), DEADLINE (epoch seconds; no launches after it),
#      STAGGER (s between launches, 90), THROTTLE_WAIT (s, 900), ANYPLOT_REPO.
# Run it detached so it survives the session, with both streams captured
# (the second positional argument is the slot count, not a redirect):
#   setsid nohup run_queue.sh agentic/runs/<run> 2 > agentic/runs/<run>/queue.out 2>&1 &
# Stop it with `pkill -f run_queue.sh`; drivers keep running (after their
# dispatches they only watch).
set -uo pipefail

usage() {
  echo "usage: $(basename "$0") <queue-dir> [slots]" >&2
  exit 2
}
[ "$#" -ge 1 ] || usage
Q="$(cd "$1" && pwd)" || usage
[ -f "$Q/full_queue.txt" ] || { echo "error: $Q/full_queue.txt not found" >&2; exit 2; }
SLOTS="${2:-2}"

# run_spec.sh lives next to this script; the repo is resolved the same way the
# driver does it (ANYPLOT_REPO wins, then git from the script's location).
R="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${ANYPLOT_REPO:-$(git -C "$R" rev-parse --show-toplevel 2>/dev/null || true)}"
if [ -z "$REPO" ] || [ ! -d "$REPO/plots" ]; then
  echo "error: could not resolve the anyplot repo root (tried \$ANYPLOT_REPO, then git from $R)." >&2
  exit 2
fi
MODEL="${MODEL:-sonnet}"
DEADLINE="${DEADLINE:-}"        # epoch seconds; no new launches at or after this
STAGGER="${STAGGER:-90}"        # seconds between two launches
THROTTLE_WAIT="${THROTTLE_WAIT:-900}"
OUT="$Q/results"; mkdir -p "$OUT"
LOG="$Q/queue.log"
SEEN="$Q/queue_seen_runs.txt"; touch "$SEEN"
HARVESTED="$Q/harvested.txt"; touch "$HARVESTED"
# Specs to (re)generate ahead of the queue — lines of `<spec> <lib...>`. Used for
# specs whose first pass was cut short (an outage, a lost dispatch). A rescue
# launches only once nothing for that spec is in flight any more, so PRs that
# are still being reviewed or repaired are never auto-closed by a re-dispatch.
RESCUE="$Q/rescue_specs.txt"

say() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }

lang_of() {
  case "$1" in
    ggplot2) echo r ;;
    makie) echo julia ;;
    chartjs|d3|echarts|highcharts|muix) echo javascript ;;
    *) echo python ;;
  esac
}

fetch_main() {
  local i
  for i in 1 2 3; do
    git -C "$REPO" fetch origin main --quiet 2>/dev/null && return 0
    sleep $(( i * 3 ))
  done
  say "WARN: git fetch origin main failed 3x; using possibly stale origin/main"
  return 1
}

# Libraries of a spec that are neither on main nor a confirmed gap.
missing_libs() {
  local spec=$1; shift
  local l m=""
  for l in "$@"; do
    git -C "$REPO" ls-tree --name-only origin/main -- \
      "plots/$spec/metadata/$(lang_of "$l")/$l.yaml" 2>/dev/null | grep -q . && continue
    grep -qE "^$spec $l CONFIRMED GAP" "$Q/deferred.log" 2>/dev/null && continue
    m="$m $l"
  done
  echo "${m# }"
}

# Distinct specs with a driver process (the `bash -c "sleep N; ... run_spec.sh"`
# wrapper and the script itself both match, so count spec names, not PIDs).
# The scheduler's own command line never contains `run_spec.sh `, so no
# self-exclusion is needed — and a PID-substring filter would drop unrelated
# lines.
running() {
  pgrep -af 'run_spec\.sh ' | grep -oE 'run_spec\.sh [a-z0-9-]+' | sort -u | wc -l
}
driver_for() { pgrep -f "run_spec\.sh $1 " >/dev/null; }

# A spec whose generate runs or implementation PRs are still in flight must not
# be re-dispatched: a new impl-generate run auto-closes the open PR for the pair.
spec_in_flight() {
  local spec=$1 st out
  for st in in_progress queued waiting; do
    out=$(gh run list --workflow=impl-generate.yml --status "$st" --limit 100 --json displayTitle \
      --jq ".[] | select(.displayTitle | test(\" for ${spec}\$\")) | .displayTitle" 2>/dev/null) || return 0
    [ -n "$out" ] && return 0
  done
  out=$(gh pr list --state open --limit 100 --json headRefName \
    --jq ".[] | select(.headRefName | startswith(\"implementation/${spec}/\")) | .headRefName" 2>/dev/null) || return 0
  [ -n "$out" ] && return 0
  return 1
}

# Prints a reason to hold new launches, or nothing when the coast is clear.
throttle_reason() {
  local rem fails since id wf sig
  rem=$(gh api rate_limit --jq .resources.core.remaining 2>/dev/null) || { echo "gh api rate_limit failed"; return; }
  if [ "${rem:-0}" -lt 800 ]; then echo "GitHub core quota low ($rem remaining)"; return; fi
  fails=$(gh run list --workflow=impl-generate.yml --limit 100 --json conclusion,updatedAt,displayTitle \
    --jq '[.[] | select(.conclusion=="failure" and (.updatedAt > (now - 1500 | todate))) | .displayTitle] | unique | length' 2>/dev/null) \
    || { echo "gh run list failed"; return; }
  if [ "${fails:-0}" -ge 3 ]; then echo "$fails distinct generate pairs failed in the last 25 min"; return; fi
  since=$(date -u -d '30 min ago' +%Y-%m-%dT%H:%M:%SZ)
  for wf in impl-generate impl-review impl-repair impl-merge; do
    while read -r id; do
      [ -z "$id" ] && continue
      grep -qx "$id" "$SEEN" && continue
      echo "$id" >> "$SEEN"
      # POSIX ERE has no `\b`; the digit-boundary groups keep 429/529 from
      # matching inside run ids or timestamps.
      sig=$(gh run view "$id" --log-failed 2>/dev/null \
        | grep -iEo 'rate.?limit[^"]{0,60}|(^|[^0-9])(429|529)([^0-9]|$)|overloaded[^"]{0,40}|too many requests|usage limit[^"]{0,40}' \
        | head -1)
      if [ -n "$sig" ]; then echo "rate-limit signature in $wf run $id: $sig"; return; fi
    done < <(gh run list --workflow=$wf.yml --limit 100 --json databaseId,conclusion,updatedAt \
      --jq ".[] | select(.conclusion==\"failure\" and .updatedAt > \"$since\") | .databaseId" 2>/dev/null)
  done
}

# Copy each finished driver's RESULT line into the ledger, once. Rescue
# launches write `<spec>.rescue.out`, so a spec harvested as PARTIAL on its
# first pass is harvested again after the rescue (the key is the file name).
harvest() {
  local f key spec line
  for f in "$OUT"/*.out; do
    [ -e "$f" ] || continue
    key=$(basename "$f" .out); spec=${key%.rescue}
    grep -qx "$key" "$HARVESTED" && continue
    line=$(grep -m1 '^RESULT=' "$f") || continue
    echo "$key" >> "$HARVESTED"
    case "$line" in
      RESULT=COMPLETE*)
        echo "$spec COMPLETE ($(echo "$line" | sed -E 's/^RESULT=COMPLETE spec=[^ ]+ libs=//'), queue-runner) $(date -u +%F_%H:%M)" >> "$Q/done.log"
        say "DONE  $spec" ;;
      *)
        echo "$spec $(echo "$line" | sed 's/^RESULT=//') (queue-runner; retry pending) $(date -u +%F_%H:%M)" >> "$Q/deferred.log"
        say "DEFER $spec: ${line#RESULT=}" ;;
    esac
  done
}

wait_for_slot() {
  while [ "$(running)" -ge "$SLOTS" ]; do sleep 60; harvest; done
}
hold_while_throttled() {
  local reason
  while reason=$(throttle_reason); [ -n "$reason" ]; do
    say "THROTTLE: $reason; holding new launches for $((THROTTLE_WAIT/60)) min"
    sleep "$THROTTLE_WAIT"; harvest
  done
}

# One pass over the rescue list. Cheap checks first (git + pgrep); the API is
# only consulted for a spec that actually has missing libs and no driver.
rescue_pass() {
  [ -s "$RESCUE" ] || return 0
  local spec libs miss
  while read -r spec libs; do
    [ -z "${spec:-}" ] && continue
    miss=$(missing_libs "$spec" $libs); [ -z "$miss" ] && continue
    driver_for "$spec" && continue
    spec_in_flight "$spec" && continue
    wait_for_slot
    hold_while_throttled
    fetch_main
    miss=$(missing_libs "$spec" $libs); [ -z "$miss" ] && continue
    spec_in_flight "$spec" && continue
    say "rescue $spec [$miss] (running=$(running))"
    nohup env ANYPLOT_REPO="$REPO" "$R/run_spec.sh" "$spec" "$MODEL" $miss > "$OUT/$spec.rescue.out" 2>&1 &
    sleep "$STAGGER"
  done < "$RESCUE"
}

# `RUN_QUEUE_LIB=1 source run_queue.sh` loads the functions for testing without
# starting the scheduler loop.
if [ "${RUN_QUEUE_LIB:-}" = 1 ]; then return 0 2>/dev/null || exit 0; fi

say "scheduler start: slots=$SLOTS model=$MODEL deadline=$([ -n "$DEADLINE" ] && date -u -d @"$DEADLINE" +%H:%M || echo none) UTC"
while read -r n spec libs; do
  [ -z "${spec:-}" ] && continue
  if [ -n "$DEADLINE" ] && [ "$(date +%s)" -ge "$DEADLINE" ]; then
    say "deadline reached; no new launches"; break
  fi
  harvest
  rescue_pass
  fetch_main
  miss=$(missing_libs "$spec" $libs)
  [ -z "$miss" ] && continue
  if driver_for "$spec"; then say "skip  $spec: driver already running"; continue; fi
  # Rescue candidates get first pick of a freed slot: re-check them every
  # ~5 min while waiting.
  i=0
  while [ "$(running)" -ge "$SLOTS" ]; do
    sleep 60; harvest
    i=$((i+1)); [ $((i % 5)) -eq 0 ] && rescue_pass
  done
  if [ -n "$DEADLINE" ] && [ "$(date +%s)" -ge "$DEADLINE" ]; then
    say "deadline reached while waiting for a slot; no new launches"; break
  fi
  hold_while_throttled
  fetch_main
  miss=$(missing_libs "$spec" $libs)
  [ -z "$miss" ] && continue
  if spec_in_flight "$spec"; then say "skip  $spec: generate run or PR still in flight (needs a look)"; continue; fi
  say "launch $spec [$miss] (running=$(running))"
  nohup env ANYPLOT_REPO="$REPO" "$R/run_spec.sh" "$spec" "$MODEL" $miss > "$OUT/$spec.out" 2>&1 &
  sleep "$STAGGER"
done < "$Q/full_queue.txt"

say "queue pass finished; waiting for in-flight drivers"
while [ "$(running)" -gt 0 ]; do sleep 60; harvest; done
harvest
say "scheduler exit"
