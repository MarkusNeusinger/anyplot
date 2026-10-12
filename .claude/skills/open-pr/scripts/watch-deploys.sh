#!/usr/bin/env bash
# Watch the Cloud Build deploys of one merge commit (§4): every regional build whose
# SHORT_SHA matches. Prints each build once it finishes; exits 0 when at least one build
# was seen and none has been queued or working for two polls in a row (a merge triggers
# one to four deploys, depending on the paths it touched), 1 after ~30 minutes.
#
# Usage: watch-deploys.sh <merge-sha>   (the full SHA or its first 7 characters, Cloud Build's SHORT_SHA)
set -uo pipefail
SHA=${1:?usage: watch-deploys.sh <merge-sha>}
SHA=${SHA:0:7}
seen=""
quiet=0
for _ in $(seq 1 60); do
  rows=$(gcloud builds list --region=europe-west4 --limit 20 \
    --format='value(id,status,substitutions.TRIGGER_NAME,substitutions.SHORT_SHA)' 2>/dev/null |
    awk -v sha="$SHA" '$4 == sha {print $3": "$2" ("$1")"}' | sort)
  finished=$(grep -E "SUCCESS|FAILURE|CANCELLED|TIMEOUT|INTERNAL_ERROR|EXPIRED" <<<"$rows")
  fresh=$(comm -13 <(echo "$seen") <(echo "$finished"))
  [ -n "$fresh" ] && echo "$fresh"
  seen=$finished
  if [ -n "$rows" ] && ! grep -qE "QUEUED|PENDING|WORKING" <<<"$rows"; then
    quiet=$((quiet + 1))
    if [ "$quiet" -ge 2 ]; then
      failed=$(grep -vc "SUCCESS" <<<"$rows")
      echo "ALL DEPLOYS FINISHED for $SHA, $failed not SUCCESS"
      exit 0
    fi
  else
    quiet=0
  fi
  sleep 30
done
echo "TIMEOUT for $SHA:"
echo "$rows"
exit 1
