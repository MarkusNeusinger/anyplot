#!/usr/bin/env bash
# Dispatch an audit round's fixes to the pipeline, one line at a time, under the owner's OK for the queue.
#
# Usage: dispatch.sh <round-dir>                                     the dry run: plan, check, print the token
#        dispatch.sh <round-dir> --execute --approved <token> [--hours N]
#
# Reads <round-dir>/queue.txt, one package per line; blank lines and # comments are skipped:
#   adopt    <library> <claude/ref> <source_model> <spec> [<spec> ...]
#   rerender <library> <source_model> <spec>
#   regen    <library> <spec> <one-sentence change request>
# adopt: a pushed claude/* ref holding fixes for one Python or JavaScript library. bulk-generate.yml adopts it from
#   the SHA the dry run planned, for the specs check_fix.py passes there against the current main (an unchanged or
#   failing spec is skipped and logged).
# rerender: impl-generate.yml in adopt mode from main: a fresh render of the merged code, for a stale or missing
#   render or a pair verify_merged.py failed. Python and JavaScript only, like adopt.
# regen: impl-generate.yml with regen_gate=false and the change request: R and Julia, which adopt mode cannot render,
#   or a fix a one-sentence hint describes better than a patch.
#
# The OK is bound to what the owner saw. The dry run resolves every adopt ref to a SHA (origin's, else the local
# branch's, so it runs before the push), checks it, writes <round>/queue.plan and prints a token over queue.txt and
# the plan. --execute needs that token, stops (exit 1) when queue.txt or the plan changes, and refuses an adopt line
# whose ref on origin is not the planned SHA. A refused line stays refused: to retry it, push the re-cut fix to a new
# ref, change the line, run the dry run again and ask again.
#
# The single-run rule: a line goes out only while no bulk-generate run is queued or in progress. GitHub keeps one
# pending run per concurrency group and cancels the older pending one, daily-regen's spec-mode run included. A
# rerender or regen line also waits while an impl-generate run of its own pair is queued or in progress (that pair's
# group), and it waits behind bulk-generate too, so it never doubles a bulk run's pace. A failed `gh run list` counts
# as busy. One dispatch per pass, a pass every 120 s, until every line is out or --hours (default 14) have passed.
#
# State: <round>/dispatch.state, one line per dispatched, refused or failed attempt, keyed by a hash of the line's text:
#   <key> <adopt|rerender|regen|refused|failed> <library|-> <sha|-> <time> <count> [<spec> ...]
# A dispatch whose `gh workflow run` failed is looked up among the runs created since, before it is tried again, so a
# dispatch GitHub accepted despite the error never goes out twice. The log is <round>/dispatch.log. Env: PACE
# (bulk-generate pace_seconds, empty for its default), REGEN_PACE (seconds after each impl-generate dispatch, default
# 180), UV_PROJECT_ENVIRONMENT (a shared venv for check_fix.py; SKILL.md, step 6).
set -uo pipefail
umask 077

ROUND=${1:?usage: dispatch.sh <round-dir> [--execute --approved <token>] [--hours N]}
shift
EXECUTE=0
APPROVED=""
HOURS=14
while [ $# -gt 0 ]; do
  case "$1" in
    --execute) EXECUTE=1 ;;
    --approved) APPROVED=${2:?--approved needs the token of the dry run}; shift ;;
    --hours) HOURS=${2:?--hours needs a number}; shift ;;
    *) echo "dispatch: unknown argument $1" >&2; exit 2 ;;
  esac
  shift
done

GH_REPO=MarkusNeusinger/anyplot
S=$(cd "$(dirname "$0")" && pwd)
REPO=$(git -C "$S" rev-parse --show-toplevel)
QUEUE=$ROUND/queue.txt
PLAN=$ROUND/queue.plan
STATE=$ROUND/dispatch.state
LOG=$ROUND/dispatch.log
[ -f "$QUEUE" ] || { echo "dispatch: no $QUEUE" >&2; exit 2; }

token() { cat "$QUEUE" "$PLAN" 2>/dev/null | sha1sum | cut -c1-12; }

if [ "$EXECUTE" = 1 ]; then
  [ -n "$APPROVED" ] || { echo "dispatch: --execute needs --approved <token> from the dry run the owner approved" >&2; exit 2; }
  [ -f "$PLAN" ] || { echo "dispatch: no $PLAN; run the dry run first" >&2; exit 2; }
  if [ "$(token)" != "$APPROVED" ]; then
    echo "dispatch: queue.txt or queue.plan changed since the approved dry run (token $(token), approved $APPROVED);" \
      "run the dry run again and ask the owner" >&2
    exit 2
  fi
  exec 9> "$ROUND/dispatch.lock"
  flock -n 9 || { echo "dispatch: another dispatcher holds $ROUND/dispatch.lock" >&2; exit 2; }
fi

# The library registry, as library:language pairs (core.constants), so this script never restates it.
LIBS=$(cd "$REPO" && PYTHON_DOTENV_DISABLED=1 uv run --frozen -q python -c \
  'from core.constants import LIBRARY_LANGUAGES as L; print(" ".join(f"{k}:{v}" for k, v in sorted(L.items())))') \
  || { echo "dispatch: cannot read core.constants.LIBRARY_LANGUAGES" >&2; exit 2; }
touch "$STATE"
PLAN_LINES=("# dispatch.sh plan: <line key> <the adopt line's SHA>")

now() { date -u +%FT%TZ; }
log() { echo "$(now) $*" | tee -a "$LOG"; }
say() { if [ "$EXECUTE" = 1 ]; then log "$@"; else echo "dry-run: $*"; fi; }

busy() {
  local n
  n=$(gh -R "$GH_REPO" run list --workflow bulk-generate.yml --limit 20 --json status \
        --jq '[.[] | select(.status != "completed")] | length' 2>/dev/null) || return 0
  [ "$n" != "0" ]
}

# pair_busy <library> <spec>: an impl-generate run of the pair is queued or in progress (or gh failed).
pair_busy() {
  local n
  n=$(gh -R "$GH_REPO" run list --workflow impl-generate.yml --limit 100 --json displayTitle,status 2>/dev/null \
        | jq --arg t "Generate: $1 for $2" '[.[] | select(.status != "completed" and .displayTitle == $t)] | length') \
    || return 0
  [ "$n" != "0" ]
}

# landed <workflow> <title prefix> <since>: 0 when such a run was created since (60 s of clock slack), 1 when none
# was, 2 when gh cannot tell.
landed() {
  local n since
  since=$(date -u -d "@$(( $(date -u -d "$3" +%s) - 60 ))" +%FT%TZ)
  n=$(gh -R "$GH_REPO" run list --workflow "$1" --limit 30 --json displayTitle,createdAt 2>/dev/null \
        | jq --arg t "$2" --arg s "$since" '[.[] | select((.displayTitle | startswith($t)) and .createdAt >= $s)] | length') \
    || return 2
  [ -n "$n" ] || return 2
  [ "$n" != "0" ]
}

lang_of() {
  local entry
  for entry in $LIBS; do
    if [ "${entry%%:*}" = "$1" ]; then echo "${entry#*:}"; return 0; fi
  done
  return 1
}
is_spec() { [[ "$1" =~ ^[a-z0-9-]+$ ]]; }
is_model() { [[ "$1" =~ ^[A-Za-z0-9._-]{1,40}$ ]]; }

# Record a line the script will not send, so later passes skip it; returns 2.
refuse() {
  local key=$1; shift
  say "line $key refused: $*"
  [ "$EXECUTE" = 1 ] && echo "$key refused - - $(now) 0" >> "$STATE"
  return 2
}

# can_adopt <key> <library>: a registered Python or JavaScript library, else the line is refused.
can_adopt() {
  local lang
  lang=$(lang_of "$2") || { refuse "$1" "unknown library $2"; return 2; }
  case "$lang" in
    python|javascript) return 0 ;;
    *) refuse "$1" "adopt mode cannot render $2 ($lang); use a regen line"; return 2 ;;
  esac
}

# send <key> <workflow> <title prefix> <kind lib sha> <count specs> <gh args...>: dispatch once and record it;
# returns 0 sent, 1 not sent (the next pass tries again).
send() {
  local key=$1 workflow=$2 title=$3 head=$4 tail=$5; shift 5
  local since start rc
  since=$(awk -v k="$key" '$1 == k && $2 == "failed" { print $5; exit }' "$STATE")
  if [ -n "$since" ]; then
    landed "$workflow" "$title" "$since"; rc=$?
    if [ "$rc" = 0 ]; then
      echo "$key $head $since $tail" >> "$STATE"
      log "line $key: the attempt that reported a failure at $since did start a run; recorded, not sent again"
      return 0
    fi
    if [ "$rc" = 2 ]; then log "line $key: cannot tell whether the attempt at $since started a run, waiting"; return 1; fi
  fi
  start=$(now)
  if gh -R "$GH_REPO" workflow run "$workflow" "$@"; then
    echo "$key $head $start $tail" >> "$STATE"
    return 0
  fi
  sleep 20
  if landed "$workflow" "$title" "$start"; then
    echo "$key $head $start $tail" >> "$STATE"
    log "line $key: gh reported a failure, but the run started; recorded"
    return 0
  fi
  echo "$key failed - - $start 0" >> "$STATE"
  log "line $key: the dispatch of $workflow FAILED"
  return 1
}

fetch() {
  local refspecs=("+refs/heads/main:refs/remotes/origin/main")
  [ -n "$2" ] && refspecs+=("+refs/heads/$1:refs/remotes/origin/$1")
  git -C "$REPO" fetch -q origin "${refspecs[@]}"
}

# adopt <key> <library> <ref> <model> <spec>...; returns 0 dispatched or planned, 1 waiting, 2 refused.
adopt() {
  local key=$1 lib=$2 ref=$3 model=$4; shift 4
  local specs=("$@") sha local_sha remote_sha pairs=() ok=() skipped=() s check
  can_adopt "$key" "$lib" || return 2
  [[ "$ref" =~ ^claude/[A-Za-z0-9._/-]+$ ]] || { refuse "$key" "$ref is not a claude/* ref"; return; }
  is_model "$model" || { refuse "$key" "source_model $model is malformed"; return; }
  for s in "${specs[@]}"; do
    is_spec "$s" || { refuse "$key" "bad spec id $s"; return; }
    pairs+=("$s/$lib")
  done
  remote_sha=$(git -C "$REPO" ls-remote origin "refs/heads/$ref" | cut -f1)
  if [ "$EXECUTE" = 1 ]; then
    sha=$(awk -v k="$key" '$1 == k { print $2; exit }' "$PLAN")
    [[ "$sha" =~ ^[0-9a-f]{40}$ ]] || { refuse "$key" "the approved plan has no SHA for $ref"; return; }
    if [ -z "$remote_sha" ]; then log "line $key: $ref is not on origin yet, waiting"; return 1; fi
    [ "$remote_sha" = "$sha" ] || { refuse "$key" "$ref is at $remote_sha on origin, the approved plan has $sha"; return; }
  else
    local_sha=$(git -C "$REPO" rev-parse --verify -q "refs/heads/$ref^{commit}")
    if [ -n "$local_sha" ] && [ -n "$remote_sha" ] && [ "$local_sha" != "$remote_sha" ]; then
      refuse "$key" "the local $ref ($local_sha) and origin's ($remote_sha) differ; push it or reset it first"
      return
    fi
    sha=${local_sha:-$remote_sha}
    [ -n "$sha" ] || { refuse "$key" "$ref exists neither locally nor on origin"; return; }
  fi
  fetch "$ref" "$remote_sha" || { say "line $key: the fetch failed"; return 1; }
  git -C "$REPO" cat-file -e "$sha^{commit}" 2>/dev/null || { say "line $key: $sha is not in the local store"; return 1; }
  check=$ROUND/check-$key.json
  rm -f "$check"
  (cd "$REPO" && PYTHON_DOTENV_DISABLED=1 uv run --frozen -q --extra agents python "$S/check_fix.py" \
      --repo "$REPO" --ref "$sha" --base origin/main --json "$check" "${pairs[@]}") >> "$LOG" 2>&1
  if [ ! -s "$check" ]; then say "line $key: check_fix.py wrote no result, see $LOG"; return 1; fi
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
    PLAN_LINES+=("$key $sha")
    echo "dry-run: line $key would dispatch bulk-generate library=$lib source_ref=$sha source_model=$model specs: ${ok[*]}"
    if [ "${#skipped[@]}" -gt 0 ]; then echo "dry-run: line $key skips ${skipped[*]}"; fi
    return 0
  fi
  send "$key" bulk-generate.yml "Bulk: $lib for " "adopt $lib $sha" "${#ok[@]} ${ok[*]}" \
    -f specification_id="${ok[*]}" -f library="$lib" -f source_ref="$sha" -f source_model="$model" \
    -f regen_gate=false ${PACE:+-f pace_seconds="$PACE"} || return 1
  log "line $key: dispatched ${#ok[@]} spec(s) of $lib from $sha; skipped ${skipped[*]:-none}"
  sleep 30
  return 0
}

# rerender <key> <library> <model> <spec>; returns 0 dispatched or planned, 1 waiting, 2 refused.
rerender() {
  local key=$1 lib=$2 model=$3 spec=$4
  can_adopt "$key" "$lib" || return 2
  is_model "$model" || { refuse "$key" "source_model $model is malformed"; return; }
  is_spec "$spec" || { refuse "$key" "bad spec id $spec"; return; }
  if [ "$EXECUTE" != 1 ]; then
    echo "dry-run: line $key would dispatch impl-generate $spec/$lib source_ref=main source_model=$model"
    return 0
  fi
  if pair_busy "$lib" "$spec"; then log "line $key waits: an impl-generate run of $spec/$lib is active"; return 1; fi
  send "$key" impl-generate.yml "Generate: $lib for $spec" "rerender $lib -" "1 $spec" \
    -f specification_id="$spec" -f library="$lib" -f source_ref=main -f source_model="$model" || return 1
  log "line $key: dispatched a re-render of $spec/$lib from main"
  sleep "${REGEN_PACE:-180}"
  return 0
}

# regen <key> <library> <spec> <request...>; returns 0 dispatched or planned, 1 waiting, 2 refused.
regen() {
  local key=$1 lib=$2 spec=$3; shift 3
  local request="$*"
  if ! lang_of "$lib" > /dev/null || ! is_spec "$spec"; then refuse "$key" "bad library or spec ($lib, $spec)"; return; fi
  if [ -z "$request" ] || [ "${#request}" -gt 300 ]; then
    refuse "$key" "the change request is empty or longer than 300 characters"
    return
  fi
  if [ "$EXECUTE" != 1 ]; then
    echo "dry-run: line $key would dispatch impl-generate $spec/$lib regen_gate=false change_request=\"$request\""
    return 0
  fi
  if pair_busy "$lib" "$spec"; then log "line $key waits: an impl-generate run of $spec/$lib is active"; return 1; fi
  send "$key" impl-generate.yml "Generate: $lib for $spec" "regen $lib -" "1 $spec" \
    -f specification_id="$spec" -f library="$lib" -f regen_gate=false -f change_request="$request" || return 1
  log "line $key: dispatched a forced regeneration of $spec/$lib"
  sleep "${REGEN_PACE:-180}"
  return 0
}

if [ "$EXECUTE" != 1 ] && busy; then echo "dry-run: a bulk-generate run is queued or in progress right now"; fi
end=$(( $(date +%s) + HOURS * 3600 ))
while :; do
  if [ "$EXECUTE" = 1 ] && [ "$(token)" != "$APPROVED" ]; then
    log "queue.txt or queue.plan changed after the approved dry run; stopped. Run the dry run again and ask the owner"
    exit 1
  fi
  pending=0
  # The queue comes in on fd 3, so no command in the loop can read from it.
  while IFS= read -r line <&3 || [ -n "$line" ]; do
    line=${line%%#*}
    read -r -a f <<< "$line"
    [ "${#f[@]}" -eq 0 ] && continue
    key=$(printf '%s' "${f[*]}" | sha1sum | cut -c1-12)
    if grep -qE "^$key (adopt|rerender|regen|refused) " "$STATE"; then
      [ "$EXECUTE" = 1 ] || echo "dry-run: line $key is already dispatched or refused"
      continue
    fi
    pending=$((pending + 1))
    if [ "$EXECUTE" = 1 ] && busy; then log "line $key waits: a bulk-generate run is queued or in progress"; break; fi
    rc=2
    case "${f[0]}" in
      adopt) if [ "${#f[@]}" -ge 5 ]; then adopt "$key" "${f[@]:1}"; rc=$?
             else refuse "$key" "adopt needs <library> <ref> <model> <spec>..."; fi ;;
      rerender) if [ "${#f[@]}" -eq 4 ]; then rerender "$key" "${f[@]:1}"; rc=$?
                else refuse "$key" "rerender needs <library> <source_model> <spec>"; fi ;;
      regen) if [ "${#f[@]}" -ge 4 ]; then regen "$key" "${f[@]:1}"; rc=$?
             else refuse "$key" "regen needs <library> <spec> <request>"; fi ;;
      *) refuse "$key" "unknown kind ${f[0]}" ;;
    esac
    [ "$rc" = 2 ] && pending=$((pending - 1))
    # One dispatch per pass: the next line waits until bulk-generate is idle again.
    if [ "$EXECUTE" = 1 ] && [ "$rc" = 0 ]; then break; fi
  done 3< "$QUEUE"
  if [ "$EXECUTE" != 1 ]; then
    (umask 077 && printf '%s\n' "${PLAN_LINES[@]}" > "$PLAN")
    echo "dry-run: wrote $PLAN; approval token $(token) (covers queue.txt and the planned SHAs)"
    exit 0
  fi
  if [ "$pending" -eq 0 ]; then log "every line of $QUEUE is dispatched or refused"; exit 0; fi
  if [ "$(date +%s)" -ge "$end" ]; then
    log "time limit reached; $pending line(s) were open at the last pass (dispatch.state shows what went out)"
    exit 1
  fi
  sleep 120
done
