#!/usr/bin/env bash
# Dispatch an audit round's fixes to the pipeline, one bulk-generate run at a time.
#
# Usage: dispatch.sh <round-dir> [--execute] [--hours N]
#
# Reads <round-dir>/queue.txt, one package per line; blank lines and # comments are skipped:
#   adopt <library> <claude/ref> <source_model> <spec> [<spec> ...]
#   regen <library> <spec> <one-sentence change request>
# An adopt line names one pushed claude/* ref holding fixes for one library. The script resolves the ref to its
# full SHA on origin, runs check_fix.py over the specs at that SHA, and dispatches bulk-generate.yml in adopt mode
# from the SHA for the specs that pass (an unchanged or failing spec is skipped and logged). Python and JavaScript
# only: adopt mode has no R or Julia render. A regen line dispatches impl-generate.yml with regen_gate=false and
# the change request, for R and Julia, or for a fix a one-sentence hint describes better than a patch.
#
# The single-run rule: a line goes out only while no bulk-generate run is queued or in progress. GitHub keeps one
# pending run per concurrency group and cancels the older pending one, daily-regen's spec-mode run included. A
# failed `gh run list` counts as busy.
#
# Without --execute it makes one pass that prints what it would dispatch and dispatches nothing. With --execute it
# loops every 120 s until every line is out or --hours (default 14) have passed. The state file
# <round>/dispatch.state keys each line by a hash of its text, so a line is never dispatched twice, and a line it
# refused (a bad library, spec or ref, files outside the named pairs) is recorded there too; the log is
# <round>/dispatch.log. Env: PACE (bulk-generate pace_seconds, empty for its default), REGEN_PACE (seconds after
# each regen dispatch, default 180).
set -uo pipefail

ROUND=${1:?usage: dispatch.sh <round-dir> [--execute] [--hours N]}
shift
EXECUTE=0
HOURS=14
while [ $# -gt 0 ]; do
  case "$1" in
    --execute) EXECUTE=1 ;;
    --hours) HOURS=${2:?--hours needs a number}; shift ;;
    *) echo "dispatch: unknown argument $1" >&2; exit 2 ;;
  esac
  shift
done

GH_REPO=MarkusNeusinger/anyplot
S=$(cd "$(dirname "$0")" && pwd)
REPO=$(git -C "$S" rev-parse --show-toplevel)
QUEUE=$ROUND/queue.txt
STATE=$ROUND/dispatch.state
LOG=$ROUND/dispatch.log
LIBS="matplotlib seaborn plotly bokeh altair plotnine pygal highcharts letsplot ggplot2 makie chartjs d3 echarts muix"
[ -f "$QUEUE" ] || { echo "dispatch: no $QUEUE" >&2; exit 2; }
touch "$STATE"

now() { date -u +%FT%TZ; }
log() { echo "$(now) $*" | tee -a "$LOG"; }
say() { if [ "$EXECUTE" = 1 ]; then log "$@"; else echo "dry-run: $*"; fi; }

busy() {
  local n
  n=$(gh -R "$GH_REPO" run list --workflow bulk-generate.yml --limit 20 --json status \
        --jq '[.[] | select(.status != "completed")] | length' 2>/dev/null) || return 0
  [ "$n" != "0" ]
}

known_lib() { [[ " $LIBS " == *" $1 "* ]]; }
is_spec() { [[ "$1" =~ ^[a-z0-9-]+$ ]]; }

# Record a line the script will not send, so later passes skip it; returns 2.
refuse() {
  local key=$1; shift
  say "line $key refused: $*"
  [ "$EXECUTE" = 1 ] && echo "$key refused - - $(now) 0" >> "$STATE"
  return 2
}

# adopt <key> <library> <ref> <model> <spec>...; returns 0 dispatched, 1 waiting, 2 refused or nothing to send.
adopt() {
  local key=$1 lib=$2 ref=$3 model=$4; shift 4
  local specs=("$@") sha pairs=() ok=() skipped=() s check
  known_lib "$lib" || { refuse "$key" "unknown library $lib"; return; }
  case "$lib" in ggplot2|makie) refuse "$key" "adopt mode cannot render $lib; use a regen line"; return ;; esac
  [[ "$ref" =~ ^claude/[A-Za-z0-9._/-]+$ ]] || { refuse "$key" "$ref is not a claude/* ref"; return; }
  [[ "$model" =~ ^[A-Za-z0-9._-]{1,40}$ ]] || { refuse "$key" "source_model $model is malformed"; return; }
  for s in "${specs[@]}"; do
    is_spec "$s" || { refuse "$key" "bad spec id $s"; return; }
    pairs+=("$s/$lib")
  done
  sha=$(git -C "$REPO" ls-remote origin "refs/heads/$ref" | cut -f1)
  if [ -z "$sha" ]; then say "line $key: $ref is not on origin yet, waiting"; return 1; fi
  git -C "$REPO" fetch -q origin "$ref" main || { log "line $key: fetch failed"; return 1; }
  check=$ROUND/check-$key.json
  rm -f "$check"
  (cd "$REPO" && PYTHON_DOTENV_DISABLED=1 uv run --frozen -q --extra agents python "$S/check_fix.py" \
      --repo "$REPO" --ref "$sha" --base origin/main --json "$check" "${pairs[@]}") >> "$LOG" 2>&1
  if [ ! -s "$check" ]; then log "line $key: check_fix.py wrote no result, see the log"; return 1; fi
  if [ "$(jq '.scope | length' "$check")" != "0" ]; then
    refuse "$key" "$ref ($sha) changes files outside the named pairs: $(jq -r '.scope | join("; ")' "$check")"
    return
  fi
  mapfile -t ok < <(jq -r '.results[] | select(.changed and (.problems | length) == 0) | .pair | split("/")[0]' "$check")
  mapfile -t skipped < <(jq -r '.results[] | select((.changed | not) or (.problems | length) > 0)
      | "\(.pair | split("/")[0]):\(if .changed then (.problems | join(" / ")) else "unchanged" end)"' "$check")
  if [ "${#ok[@]}" -eq 0 ]; then
    refuse "$key" "nothing to dispatch from $sha; skipped ${skipped[*]:-none}"
    return
  fi
  if [ "$EXECUTE" != 1 ]; then
    echo "dry-run: line $key would dispatch bulk-generate library=$lib source_ref=$sha source_model=$model specs: ${ok[*]}"
    if [ "${#skipped[@]}" -gt 0 ]; then echo "dry-run: line $key skips ${skipped[*]}"; fi
    return 0
  fi
  if gh -R "$GH_REPO" workflow run bulk-generate.yml -f specification_id="${ok[*]}" -f library="$lib" \
       -f source_ref="$sha" -f source_model="$model" -f regen_gate=false ${PACE:+-f pace_seconds="$PACE"}; then
    echo "$key adopt $lib $sha $(now) ${#ok[@]} ${ok[*]}" >> "$STATE"
    log "line $key: dispatched ${#ok[@]} spec(s) of $lib from $sha; skipped ${skipped[*]:-none}"
    sleep 30
    return 0
  fi
  log "line $key: the dispatch FAILED for $sha"
  return 1
}

# regen <key> <library> <spec> <request...>; returns 0 dispatched, 1 failed, 2 refused.
regen() {
  local key=$1 lib=$2 spec=$3; shift 3
  local request="$*"
  if ! known_lib "$lib" || ! is_spec "$spec"; then refuse "$key" "bad library or spec ($lib, $spec)"; return; fi
  if [ -z "$request" ] || [ "${#request}" -gt 300 ]; then
    refuse "$key" "the change request is empty or longer than 300 characters"
    return
  fi
  if [ "$EXECUTE" != 1 ]; then
    echo "dry-run: line $key would dispatch impl-generate $spec/$lib regen_gate=false change_request=\"$request\""
    return 0
  fi
  if gh -R "$GH_REPO" workflow run impl-generate.yml -f specification_id="$spec" -f library="$lib" \
       -f regen_gate=false -f change_request="$request"; then
    echo "$key regen $lib - $(now) 1 $spec" >> "$STATE"
    log "line $key: dispatched a forced regeneration of $spec/$lib"
    sleep "${REGEN_PACE:-180}"
    return 0
  fi
  log "line $key: the dispatch FAILED for $spec/$lib"
  return 1
}

if [ "$EXECUTE" != 1 ] && busy; then echo "dry-run: a bulk-generate run is queued or in progress right now"; fi
end=$(( $(date +%s) + HOURS * 3600 ))
while :; do
  pending=0
  # The queue comes in on fd 3, so no command in the loop can read from it.
  while IFS= read -r line <&3 || [ -n "$line" ]; do
    line=${line%%#*}
    read -r -a f <<< "$line"
    [ "${#f[@]}" -eq 0 ] && continue
    key=$(printf '%s' "${f[*]}" | sha1sum | cut -c1-12)
    grep -q "^$key " "$STATE" && continue
    pending=$((pending + 1))
    if [ "$EXECUTE" = 1 ] && busy; then log "line $key waits: a bulk-generate run is queued or in progress"; break; fi
    rc=2
    case "${f[0]}" in
      adopt) if [ "${#f[@]}" -ge 5 ]; then adopt "$key" "${f[@]:1}"; rc=$?
             else refuse "$key" "adopt needs <library> <ref> <model> <spec>..."; fi ;;
      regen) if [ "${#f[@]}" -ge 4 ]; then regen "$key" "${f[@]:1}"; rc=$?
             else refuse "$key" "regen needs <library> <spec> <request>"; fi ;;
      *) refuse "$key" "unknown kind ${f[0]}" ;;
    esac
    [ "$rc" = 2 ] && pending=$((pending - 1))
    # One dispatch per pass: the next line waits until bulk-generate is idle again.
    if [ "$EXECUTE" = 1 ] && [ "$rc" = 0 ]; then break; fi
  done 3< "$QUEUE"
  [ "$EXECUTE" = 1 ] || exit 0
  if [ "$pending" -eq 0 ]; then log "every line of $QUEUE is dispatched or refused"; exit 0; fi
  if [ "$(date +%s)" -ge "$end" ]; then log "time limit reached; $pending line(s) not dispatched"; exit 1; fi
  sleep 120
done
