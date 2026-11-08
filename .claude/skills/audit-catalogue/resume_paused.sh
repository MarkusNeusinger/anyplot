#!/usr/bin/env bash
# Resume the reviews and repairs Claude paused at a usage limit, one dispatch every 150 s.
#
# Usage: resume_paused.sh <round-dir> [--library <lib>] [--repairs] [--all-open] [--execute]
#
# Lists the open PRs labelled ai-review-paused (and with --repairs ai-repair-paused) titled
# "feat(<library>): implement <spec>" for a pair this round dispatched (<round-dir>/dispatch.state); --all-open drops
# that filter and takes every paused PR, which needs the owner to name it. --library narrows the list further. For each
# PR still labelled, and only when neither a review run ("Review: PR #N") nor a repair run of its pair
# ("Repair: <library> for <spec> (attempt N)") is queued or in progress (two runs on one PR race their labels), it runs
# what the pause comment says:
#   review: gh workflow run impl-review.yml -f pr_number=N
#   repair: the `gh workflow run impl-repair.yml ...` line of the newest bot comment that carries one, checked against
#           a strict pattern and the PR's own number, spec and library, and run as an argument list, never through a
#           shell.
# Resume only after the limit has reset: a resume while the stop lasts pauses the PR again. Without --execute it
# prints what it would dispatch. The log is <round-dir>/resume.log.
set -uo pipefail
umask 077

ROUND=${1:?usage: resume_paused.sh <round-dir> [--library <lib>] [--repairs] [--all-open] [--execute]}
shift
LIB=""
REPAIRS=0
ALL_OPEN=0
EXECUTE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --library) LIB=${2:?--library needs a name}; shift ;;
    --repairs) REPAIRS=1 ;;
    --all-open) ALL_OPEN=1 ;;
    --execute) EXECUTE=1 ;;
    *) echo "resume_paused: unknown argument $1" >&2; exit 2 ;;
  esac
  shift
done
[[ -z "$LIB" || "$LIB" =~ ^[a-z0-9]+$ ]] || { echo "resume_paused: bad library $LIB" >&2; exit 2; }

GH_REPO=MarkusNeusinger/anyplot
LOG=$ROUND/resume.log
STATE=$ROUND/dispatch.state
REPAIR_LINE='^gh workflow run impl-repair\.yml -f pr_number=[0-9]+ -f specification_id=[a-z0-9-]+ -f library=[a-z0-9]+ -f attempt=[0-9]+ -f model=[A-Za-z0-9._-]+$'

# The round's pairs, as "library spec", from every dispatched line.
declare -A IN_ROUND=()
if [ "$ALL_OPEN" != 1 ]; then
  [ -s "$STATE" ] || { echo "resume_paused: $STATE lists nothing dispatched; --all-open takes every paused PR" >&2; exit 2; }
  while read -r _key kind lib _sha _when _count specs; do
    case "$kind" in
      adopt|rerender|regen) for s in $specs; do IN_ROUND["$lib $s"]=1; done ;;
    esac
  done < "$STATE"
fi
mkdir -p "$ROUND"
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }

# paused <label>: "<number> <library> <spec>" per open PR with the label and an implementation title.
paused() {
  gh -R "$GH_REPO" pr list --state open --label "$1" --limit 200 --json number,title \
    | jq -r '.[] | . as $pr | (.title | capture("^feat\\((?<lib>[a-z0-9]+)\\): implement (?<spec>[a-z0-9-]+)$"))
             | "\($pr.number) \(.lib) \(.spec)"' \
    | sort -n
}

# active <number> <library> <spec>: how many review or repair runs of the PR are queued or in progress (1 when gh fails).
active() {
  gh -R "$GH_REPO" run list --limit 200 --json displayTitle,status 2>/dev/null \
    | jq --arg review "Review: PR #$1" --arg repair "Repair: $2 for $3 " \
        '[.[] | select(.status != "completed" and (.displayTitle == $review or (.displayTitle | startswith($repair))))] | length' \
    || echo 1
}

still_labelled() {
  gh -R "$GH_REPO" pr view "$1" --json labels --jq '.labels[].name' 2>/dev/null | grep -qx "$2"
}

resume() {
  local kind=$1 n=$2 lib=$3 spec=$4 line args
  local label="ai-$kind-paused"
  if ! still_labelled "$n" "$label"; then log "#$n no longer carries $label, skipped"; return 1; fi
  if [ "$(active "$n" "$lib" "$spec")" != "0" ]; then log "#$n has a review or repair run active, skipped"; return 1; fi
  if [ "$kind" = review ]; then
    args=(workflow run impl-review.yml -f pr_number="$n")
  else
    line=$(gh api --paginate "repos/$GH_REPO/issues/$n/comments?per_page=100" 2>/dev/null \
           | jq -rs 'add // [] | [.[] | select(.user.type == "Bot" and ((.body // "") | contains("gh workflow run impl-repair.yml")))]
                     | last | .body // ""' \
           | grep -oE 'gh workflow run impl-repair\.yml [^`]*' | tail -1 | sed 's/[[:space:]]*$//')
    if ! [[ "$line" =~ $REPAIR_LINE ]] || [[ "$line" != *"pr_number=$n -f specification_id=$spec -f library=$lib "* ]]; then
      log "#$n: no valid resume command for $spec/$lib in the newest bot comment that carries one, skipped"; return 1
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
  taken=0
  for entry in "${prs[@]}"; do
    read -r n lib spec <<< "$entry"
    [ -n "$LIB" ] && [ "$lib" != "$LIB" ] && continue
    [ "$ALL_OPEN" = 1 ] || [ -n "${IN_ROUND["$lib $spec"]:-}" ] || continue
    taken=$((taken + 1))
    resume "$kind" "$n" "$lib" "$spec" && sleep 150
  done
  log "paused ${kind}s${LIB:+ of $LIB}$([ "$ALL_OPEN" = 1 ] || echo " in this round"): $taken of ${#prs[@]} open"
done
log "done"
