#!/usr/bin/env bash
# Wait for the Copilot reviewer (§3b) until the PR carries at least <count> of its reviews,
# at most ~15 minutes, then print the latest review's summary, every inline comment and
# the ids of the unresolved threads (§3c), which the resolve mutation (§3d) takes.
#
# Usage: watch-copilot.sh <pr> [count, default 1]
#   count 2 waits for the one extra round requested after fixing the first round's findings.
set -uo pipefail
PR=${1:?usage: watch-copilot.sh <pr> [count]}
WANT=${2:-1}
REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
BOT='copilot-pull-request-reviewer[bot]'
n=0
for _ in $(seq 1 30); do
  n=$(gh api "repos/$REPO/pulls/$PR/reviews" --jq "[.[] | select(.user.login==\"$BOT\")] | length")
  [ "${n:-0}" -ge "$WANT" ] && break
  sleep 30
done
echo "copilot reviews: $n (waited for $WANT)"
echo "== latest review"
gh api "repos/$REPO/pulls/$PR/reviews" \
  --jq "[.[] | select(.user.login==\"$BOT\")] | last | \"\(.state) on \(.commit_id[0:9]):\n\(.body)\"" | head -40
echo "== inline comments"
gh api "repos/$REPO/pulls/$PR/comments" --jq '.[] | "--- \(.path):\(.line // .original_line) [\(.id)]\n\(.body)"'
echo "== unresolved threads"
gh api graphql -F owner="${REPO%/*}" -F repo="${REPO#*/}" -F pr="$PR" -f query='
  query($owner: String!, $repo: String!, $pr: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $pr) { reviewThreads(first: 100) { nodes { id isResolved isOutdated path } } }
    }
  }' --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved | not)
           | "\(.id) \(.path) outdated=\(.isOutdated)"'
