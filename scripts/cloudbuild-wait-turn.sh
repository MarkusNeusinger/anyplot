#!/usr/bin/env bash
# Hold a Cloud Build deploy until every OLDER build of the same Cloud Run service has
# finished, so the deploys of one service run one at a time, oldest build first. A step
# of app/, api/, agents/ and agents/renderer/cloudbuild.yaml, between push-image and
# deploy:
#
#   bash scripts/cloudbuild-wait-turn.sh <service> <region> <build-id>
#
# Why: each service has ONE `candidate` tag. Two merges a minute apart start two builds
# of the same service, the later deploy moves the tag to its own revision, and the other
# build's smoke then refuses to promote ("candidate tag moved"). Which build loses is
# luck; when it is the newer commit's, production stays on the older commit until
# someone reruns the trigger (deploy-app on 2026-10-16 and 2026-10-21, deploy-api and
# deploy-agents on 2026-10-12). The two deploys also race for the service's IAM policy,
# which gcloud reports as the warning "Setting IAM policy failed".
#
# "Same service" means the same `_SERVICE_NAME` substitution, so a push-triggered build,
# a trigger rerun and a hand-submitted build of one service queue together. Builds are
# ordered by create time, then by id; a build waits only for builds before it in that
# order, so two builds never wait for each other. Image build and push still run in
# parallel: they write build-unique tags.
#
# The queue is the list of builds in <region>. A build that list does not show runs
# somewhere else (`gcloud builds submit` without `--region` runs in `global`), where
# neither it nor the regional builds can see each other, so it fails and asks for
# `--region`. The wait is capped at MAX_WAIT_S (default 600 s of wall time; one build's
# serialized deploy, smoke and promote take about two minutes): a build still not clear
# to deploy after that fails with the ids it waited for rather than deploying alongside
# them. A listing may fail or hang (60 s) twice in a row; the third failure in a row
# fails the build.
set -euo pipefail

SERVICE=$1
REGION=$2
BUILD_ID=$3
MAX_WAIT_S=${MAX_WAIT_S:-600}
POLL_S=${POLL_S:-15}

# Reads `gcloud builds list --format=json` on stdin and prints the ids of the builds of
# SERVICE that come before BUILD_ID; exit code 3 when BUILD_ID itself is not listed.
# The order uses the full-precision create time: gcloud's own `createTime<` filter
# compares whole seconds only.
OLDER_BUILDS='
import json, sys

service, me = sys.argv[1], sys.argv[2]
builds = [b for b in json.load(sys.stdin) if b.get("substitutions", {}).get("_SERVICE_NAME") == service]


def order(build):
    stamp = build["createTime"].replace("+00:00", "").rstrip("Z")
    seconds, _, fraction = stamp.partition(".")
    return (seconds, fraction.ljust(9, "0"), build["id"])


mine = next((b for b in builds if b["id"] == me), None)
if mine is None:
    sys.exit(3)
print(" ".join(b["id"] for b in sorted(builds, key=order) if order(b) < order(mine)))
'

SECONDS=0
failures=0
older=""
while :; do
  list_rc=0
  pick_rc=0
  listed=""
  # `--limit=unlimited`: `gcloud builds list` stops at 50 builds by default, and the
  # service filter runs after the listing.
  json=$(timeout 60 gcloud builds list --region="$REGION" --ongoing --limit=unlimited --format=json) || list_rc=$?
  if [ "$list_rc" = 0 ]; then
    listed=$(python3 -c "$OLDER_BUILDS" "$SERVICE" "$BUILD_ID" <<< "$json") || pick_rc=$?
  fi
  if [ "$pick_rc" = 3 ]; then
    echo "build $BUILD_ID is not listed in $REGION, so it cannot queue with the other $SERVICE builds"
    echo "submit it with --region=$REGION"
    exit 1
  fi
  if [ "$list_rc" != 0 ] || [ "$pick_rc" != 0 ]; then
    failures=$((failures + 1))
    if [ "$failures" -ge 3 ]; then
      echo "could not list the running builds of $SERVICE in $REGION ($failures attempts in a row)"
      exit 1
    fi
    echo "listing the running builds of $SERVICE failed; retrying"
  else
    failures=0
    older=$listed
    if [ -z "$older" ]; then
      echo "no older $SERVICE build is running: deploying"
      exit 0
    fi
    echo "waiting for older $SERVICE build(s) to finish: $older"
  fi
  if [ "$SECONDS" -ge "$MAX_WAIT_S" ]; then
    echo "still not clear to deploy after $SECONDS s; older $SERVICE build(s) last seen running: ${older:-none listed}"
    echo "not deploying alongside them; rerun this trigger once they have finished"
    exit 1
  fi
  sleep "$POLL_S"
done
