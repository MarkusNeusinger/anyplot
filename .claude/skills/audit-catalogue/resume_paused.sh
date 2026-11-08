#!/usr/bin/env bash
# Resume the reviews and repairs Claude paused at a usage limit, one dispatch every 150 s.
#
# Usage: resume_paused.sh <round-dir> [--library <lib>] [--repairs] [--execute]
#
# Lists the open PRs labelled ai-review-paused (and with --repairs ai-repair-paused), titled
# "feat(<library>): implement <spec>" when --library is given. For each one still labelled, and only when no
# "Review: PR #N" or "Repair: PR #N" run is queued or in progress (two re-reviews of one PR race their labels),
# it runs what the pause comment says:
#   review: gh workflow run impl-review.yml -f pr_number=N
#   repair: the `gh workflow run impl-repair.yml ...` line of the newest bot comment, checked against a strict
#           pattern and run as an argument list, never through a shell.
# Resume only after the limit has reset: a resume while the stop lasts pauses the PR again. Without --execute it
# prints what it would dispatch. The log is <round-dir>/resume.log.
set -uo pipefail

ROUND=${1:?usage: resume_paused.sh <round-dir> [--library <lib>] [--repairs] [--execute]}
shift
LIB=""
REPAIRS=0
EXECUTE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --library) LIB=${2:?--library needs a name}; shift ;;
    --repairs) REPAIRS=1 ;;
    --execute) EXECUTE=1 ;;
    *) echo "resume_paused: unknown argument $1" >&2; exit 2 ;;
  esac
  shift
done
[[ -z "$LIB" || "$LIB" =~ ^[a-z0-9]+$ ]] || { echo "resume_paused: bad library $LIB" >&2; exit 2; }

GH_REPO=MarkusNeusinger/anyplot
LOG=$ROUND/resume.log
REPAIR_LINE='^gh workflow run impl-repair\.yml -f pr_number=[0-9]+ -f specification_id=[a-z0-9-]+ -f library=[a-z0-9]+ -f attempt=[0-9]+ -f model=[A-Za-z0-9._-]+$'
mkdir -p "$ROUND"
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }

paused() {
  local label=$1 title='^feat\([a-z0-9]+\): implement '
  [ -n "$LIB" ] && title="^feat\\($LIB\\): implement "
  gh -R "$GH_REPO" pr list --state open --label "$label" --limit 200 --json number,title \
    | jq -r --arg re "$title" '.[] | select(.title | test($re)) | .number' | sort -n
}

active() {
  local n=$1
  gh -R "$GH_REPO" run list --limit 100 --json displayTitle,status \
    --jq "[.[] | select(.status != \"completed\" and (.displayTitle == \"Review: PR #$n\" or .displayTitle == \"Repair: PR #$n\"))] | length" \
    2>/dev/null || echo 1
}

still_labelled() {
  gh -R "$GH_REPO" pr view "$1" --json labels --jq '.labels[].name' 2>/dev/null | grep -qx "$2"
}

resume() {
  local kind=$1 n=$2 line args
  local label="ai-$kind-paused"
  if ! still_labelled "$n" "$label"; then log "#$n no longer carries $label, skipped"; return 1; fi
  if [ "$(active "$n")" != "0" ]; then log "#$n has a review or repair run active, skipped"; return 1; fi
  if [ "$kind" = review ]; then
    args=(workflow run impl-review.yml -f pr_number="$n")
  else
    line=$(gh api --paginate "repos/$GH_REPO/issues/$n/comments?per_page=100" 2>/dev/null \
           | jq -rs 'add // [] | [.[] | select(.user.type == "Bot")] | last | .body // ""' \
           | grep -oE 'gh workflow run impl-repair\.yml [^`]*' | head -1 | sed 's/[[:space:]]*$//')
    if ! [[ "$line" =~ $REPAIR_LINE ]] || [[ "$line" != *"pr_number=$n "* ]]; then
      log "#$n: no valid resume command in the newest bot comment, skipped"; return 1
    fi
    read -r -a args <<< "${line#gh }"
  fi
  if [ "$EXECUTE" != 1 ]; then echo "dry-run: #$n gh ${args[*]}"; return 1; fi
  if gh -R "$GH_REPO" "${args[@]}"; then log "#$n $kind re-dispatched"; return 0; fi
  log "#$n $kind dispatch FAILED"
  return 1
}

kinds=(review)
[ "$REPAIRS" = 1 ] && kinds+=(repair)
for kind in "${kinds[@]}"; do
  mapfile -t prs < <(paused "ai-$kind-paused")
  log "paused ${kind}s${LIB:+ of $LIB}: ${#prs[@]}"
  for n in "${prs[@]}"; do
    resume "$kind" "$n" && sleep 150
  done
done
log "done"
