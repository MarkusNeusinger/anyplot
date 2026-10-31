#!/usr/bin/env bash
# Watch a PR's checks on its current head (§3a): print each check once it finishes, exit 0
# when every check has finished, 1 after ~45 minutes (90 polls; a PR that builds the
# renderer image takes 30 to 40 minutes) with the names of the checks still pending.
# Reads the check-runs API, deduped by name with the newest id winning (§3e), and re-reads
# the head on every poll, so a push during the watch is followed. A check that has not
# registered yet cannot be told from one that never comes, so the watch also waits until
# at least MIN_CHECKS runs exist.
#
# Usage: watch-checks.sh <pr> [min-checks, default 10]
set -uo pipefail
PR=${1:?usage: watch-checks.sh <pr> [min-checks]}
MIN_CHECKS=${2:-10}
REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
seen=""
for _ in $(seq 1 90); do
  head=$(gh pr view "$PR" -R "$REPO" --json headRefOid --jq .headRefOid)
  runs=$(gh api "repos/$REPO/commits/$head/check-runs?per_page=100" --jq \
    '[.check_runs[]] | group_by(.name) | map(max_by(.id)) | .[] | "\(.name): \(.status) \(.conclusion // "")"')
  finished=$(grep ": completed" <<<"$runs" | sort)
  fresh=$(comm -13 <(echo "$seen") <(echo "$finished"))
  [ -n "$fresh" ] && echo "$fresh"
  seen=$finished
  total=$(grep -c . <<<"$runs")
  pending=$(grep -vc ": completed" <<<"$runs")
  if [ "$total" -ge "$MIN_CHECKS" ] && [ "$pending" -eq 0 ]; then
    failed=$(grep ": completed" <<<"$runs" | grep -Evc "success|skipped|neutral$")
    echo "ALL $total CHECKS FINISHED on ${head:0:9}, $failed not green"
    exit 0
  fi
  sleep 30
done
names=$(grep . <<<"$runs" | grep -v ": completed" | sed -E 's/: [a-z_]+ ?$//' | paste -sd ',' - | sed 's/,/, /g')
if [ -n "$names" ]; then
  echo "TIMEOUT: $pending of $total checks still pending on ${head:0:9}: $names"
else
  echo "TIMEOUT: only $total checks registered on ${head:0:9}, none pending (waited for $MIN_CHECKS)"
fi
exit 1
