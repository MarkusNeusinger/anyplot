#!/usr/bin/env bash
# One status line per cycle for the MUI X forced regeneration of a spec list.
# Usage: status.sh <spec-list-file> [cycle_seconds] [max_cycles]
# Exits 0 when every spec in the list has a muix metadata file on origin/main
# newer than START (an impl-merge landed), 1 after max_cycles.
set -uo pipefail
LIST=${1:?spec list file}
CYCLE=${2:-600}
MAX=${3:-18}
REPO=MarkusNeusinger/anyplot
START=${START:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}
cd "$(git rev-parse --show-toplevel)" || exit 2
mapfile -t SPECS < <(tr ' ' '\n' < "$LIST" | sed '/^$/d')
for ((c = 1; c <= MAX; c++)); do
  git fetch -q origin main 2>/dev/null
  done_n=0; done_list=""
  for s in "${SPECS[@]}"; do
    # merged = a merged implementation PR for spec/muix since START
    m=$(gh pr list --repo "$REPO" --state merged --search "head:implementation/$s/muix merged:>=$START" --json number --jq 'length' 2>/dev/null || echo 0)
    if [ "${m:-0}" -gt 0 ]; then done_n=$((done_n + 1)); done_list="$done_list $s"; fi
  done
  open=$(gh pr list --repo "$REPO" --state open --search "muix in:title created:>=$START" --json number,title,labels --jq '.[] | "#\(.number) \(.title | sub("^.*for ";"") | sub(" .*$";"")) [\([.labels[].name | select(startswith("ai-") or startswith("quality") or startswith("regen"))] | join(","))]"' 2>/dev/null | tr '\n' ' ')
  runs=$(gh run list --repo "$REPO" --limit 60 --json name,status,conclusion,createdAt,displayTitle --jq "[.[] | select(.createdAt >= \"$START\") | select(.displayTitle | test(\"^(Bulk|Generate|Review|Repair|Merge):\"))] | group_by(.status + \":\" + (.conclusion // \"\")) | map(\"\\(.[0].status)\\(if .[0].conclusion then \"/\" + .[0].conclusion else \"\" end)=\\(length)\") | join(\" \")" 2>&1)
  fails=$(gh run list --repo "$REPO" --limit 60 --json name,conclusion,createdAt,displayTitle --jq "[.[] | select(.createdAt >= \"$START\" and .conclusion == \"failure\") | select(.name | startswith(\"CI:\") | not)] | map(.displayTitle) | unique | join(\"; \")" 2>&1)
  echo "$(date -u +%H:%M) cycle $c/$MAX merged ${done_n}/${#SPECS[@]}${done_list:+ (${done_list# })} | runs: ${runs:-none} | open PRs: ${open:-none}${fails:+ | FAILED: $fails}"
  [ "$done_n" -ge "${#SPECS[@]}" ] && exit 0
  sleep "$CYCLE"
done
exit 1
