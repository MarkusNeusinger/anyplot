#!/usr/bin/env bash
# Per-SPEC driver: dispatch impl-generate for every missing library of one
# spec, staggered so the pipeline overlaps generate/review/merge across libs
# (the bulk-generate pacing pattern), then poll origin/main until each lib's
# metadata file exists. Repo metadata is the completion signal — works for
# specs whose issues closed long ago. Exits per spec so the agent can report
# and start the next queue entry.
# Usage: run_spec.sh <spec-id> <model> <lib1> [lib2 ...]
set -uo pipefail

usage() {
  echo "usage: $(basename "$0") <spec-id> <model> <lib1> [lib2 ...]" >&2
  echo "  e.g. $(basename "$0") line-basic sonnet highcharts muix" >&2
  exit 2
}
# Explicit guard: with `set -u` a missing argument would otherwise surface as an
# unbound-variable error from somewhere deep in the polling loop.
[ "$#" -ge 3 ] || usage
SPEC="$1"; MODEL="$2"; shift 2; LIBS=("$@")

# Resolve the repo from this script's location (.claude/skills/<name>/), so the
# driver works from any checkout and any working directory. ANYPLOT_REPO wins
# when the script is copied elsewhere (e.g. a scratch queue under agentic/runs/).
# Fail fast rather than falling back to $PWD: an unvalidated repo makes every
# `meta_present` check return false, which reads as "nothing ever landed" and
# burns the full polling timeout before anyone notices.
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="${ANYPLOT_REPO:-$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null || true)}"
if [ -z "$REPO" ] || [ ! -d "$REPO/plots" ]; then
  echo "error: could not resolve the anyplot repo root (tried \$ANYPLOT_REPO, then git from $HERE)." >&2
  echo "       set ANYPLOT_REPO=/path/to/anyplot and re-run." >&2
  exit 2
fi
STAGGER=150      # seconds between dispatches
INTERVAL=180     # poll interval
LOGDIR="${POLL_LOG_DIR:-$HOME/.cache/anyplot-babysit}"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/spec_${SPEC}.log"

lang_of() {
  case "$1" in
    ggplot2) echo r ;;
    makie) echo julia ;;
    chartjs|d3|echarts|highcharts|muix) echo javascript ;;
    *) echo python ;;
  esac
}

meta_present() {  # assumes a fresh `git fetch` already ran this iteration
  local lang; lang=$(lang_of "$1")
  [ -n "$(git -C "$REPO" ls-tree --name-only origin/main -- "plots/${SPEC}/metadata/${lang}/$1.yaml" 2>/dev/null)" ]
}

pipeline_active() {
  for wf in impl-generate.yml impl-review.yml impl-repair.yml impl-merge.yml impl-review-retry.yml; do
    local out
    if ! out=$(gh run list --workflow="$wf" --limit 12 --json status \
        --jq '.[] | select(.status=="in_progress" or .status=="queued") | .status' 2>&1); then
      printf 'WARN: gh run list %s failed; assuming active: %s\n' "$wf" "$out" >> "$LOG"
      return 0
    fi
    grep -q . <<<"$out" && return 0
  done
  return 1
}

# Rough health signal for the report line: how many generate runs failed in the
# last 25 min. The limit must cover the whole window — two specs in flight can
# put 10+ runs in it, and a short limit silently reports "0 failures" because
# the failures fell off the end of the list rather than because there were none.
# `?` on error, never 0: a masked API failure reading as "all healthy" is how a
# quota outage gets mistaken for a slow queue.
recent_generate_failures() {
  gh run list --workflow=impl-generate.yml --limit 60 \
    --json conclusion,updatedAt \
    --jq "[.[] | select(.conclusion==\"failure\" and (.updatedAt > (now - 1500 | todate)))] | length" 2>/dev/null \
    || echo "?"
}

git -C "$REPO" fetch origin main --quiet
TODO=()
for lib in "${LIBS[@]}"; do
  if meta_present "$lib"; then
    echo "[skip] $SPEC/$lib already on main" | tee -a "$LOG"
  else
    TODO+=("$lib")
  fi
done
if [ ${#TODO[@]} -eq 0 ]; then
  echo "RESULT=COMPLETE spec=$SPEC (all libs already present)"
  exit 0
fi

for i in "${!TODO[@]}"; do
  lib="${TODO[$i]}"
  echo "[$(TZ=UTC date -u +%H:%M:%S)] dispatch $SPEC/$lib model=$MODEL" | tee -a "$LOG"
  if ! gh workflow run impl-generate.yml \
      -f "specification_id=$SPEC" -f "library=$lib" -f "model=$MODEL" >> "$LOG" 2>&1; then
    echo "WARN: dispatch failed for $SPEC/$lib" | tee -a "$LOG"
  fi
  [ "$i" -lt $(( ${#TODO[@]} - 1 )) ] && sleep "$STAGGER"
done

MAXMIN=$(( 30 + 15 * ${#TODO[@]} )); [ "$MAXMIN" -gt 150 ] && MAXMIN=150
iters=$(( MAXMIN * 60 / INTERVAL ))
idle=0; last_done=-1
for ((i=1; i<=iters; i++)); do
  sleep "$INTERVAL"
  git -C "$REPO" fetch origin main --quiet
  missing=(); done_n=0
  for lib in "${TODO[@]}"; do
    if meta_present "$lib"; then done_n=$((done_n+1)); else missing+=("$lib"); fi
  done
  if [ ${#missing[@]} -eq 0 ]; then
    echo "RESULT=COMPLETE spec=$SPEC libs=${TODO[*]} after ~$(( (i*INTERVAL)/60 + (${#TODO[@]}-1)*STAGGER/60 )) min"
    exit 0
  fi
  if [ "$done_n" -gt "$last_done" ]; then idle=0; last_done=$done_n
  elif pipeline_active; then idle=0
  else idle=$((idle+1)); fi
  printf '[%s iter %d/%d] %d/%d done, missing: %s (idle=%d)\n' \
    "$(TZ=UTC date -u +%H:%M:%S)" "$i" "$iters" "$done_n" "${#TODO[@]}" "${missing[*]}" "$idle" >> "$LOG"
  if [ "$idle" -ge 3 ]; then
    echo "RESULT=PARTIAL spec=$SPEC done=$done_n/${#TODO[@]} still-missing: ${missing[*]} — pipeline idle ~$((3*INTERVAL/60)) min"
    echo "recent generate failures (25 min): $(recent_generate_failures)"
    exit 0
  fi
done
echo "RESULT=TIMEOUT spec=$SPEC done=$last_done/${#TODO[@]} still-missing: ${missing[*]} after ${MAXMIN} min"
echo "recent generate failures (25 min): $(recent_generate_failures)"
exit 0
