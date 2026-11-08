#!/usr/bin/env bash
# The pipeline state of an audit round's dispatched packages: one line per spec, a summary line per package.
#
# Usage: pkg_status.sh <round-dir> [<line key> ...]
#
# Reads <round-dir>/dispatch.state (written by dispatch.sh). For every dispatched line, or only the keys given,
# it finds each spec's newest PR titled "feat(<library>): implement <spec>" created since the dispatch, and prints
#   <spec> <library> #<pr> <state> <labels: quality:*, ai-*, regen:*>   or   <spec> <library> none
# then "SUMMARY <key> <kind> <library> merged=N open=N closed=N none=N". Read-only. A PR opens minutes after its
# dispatch and the search index lags a few minutes more, so "none" right after a dispatch is normal.
set -uo pipefail

ROUND=${1:?usage: pkg_status.sh <round-dir> [<line key> ...]}
shift
KEYS=("$@")
GH_REPO=MarkusNeusinger/anyplot
STATE=$ROUND/dispatch.state
[ -s "$STATE" ] || { echo "pkg_status: nothing dispatched yet ($STATE is empty)"; exit 0; }

selected() {
  local k
  [ "${#KEYS[@]}" -eq 0 ] && return 0
  for k in "${KEYS[@]}"; do [ "$k" = "$1" ] && return 0; done
  return 1
}

# The state comes in on fd 3, so gh and jq cannot read from it.
while read -r key kind lib _sha when count specs <&3; do
  [ "$kind" = refused ] && continue
  [ "${count:-0}" -gt 0 ] || continue
  selected "$key" || continue
  json=$(gh -R "$GH_REPO" pr list --state all --limit 500 --search "$lib in:title created:>=${when%%T*}" \
           --json number,title,state,labels,createdAt 2>/dev/null) || { echo "$key: gh pr list failed"; continue; }
  merged=0; open=0; closed=0; none=0
  for s in $specs; do
    row=$(jq -r --arg t "feat($lib): implement $s" --arg since "$when" '
      [.[] | select(.title == $t and .createdAt >= $since)] | sort_by(.number) | last
      | if . == null then "none"
        else "#\(.number) \(.state) \([.labels[].name | select(test("^(quality:|ai-|regen:)"))] | join(","))" end' <<< "$json")
    echo "$s $lib $row"
    case "$row" in
      none) none=$((none + 1)) ;;
      *" MERGED"*) merged=$((merged + 1)) ;;
      *" OPEN"*) open=$((open + 1)) ;;
      *) closed=$((closed + 1)) ;;
    esac
  done
  echo "SUMMARY $key $kind $lib merged=$merged open=$open closed=$closed none=$none (dispatched $when)"
done 3< "$STATE"
