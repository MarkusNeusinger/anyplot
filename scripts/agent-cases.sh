#!/usr/bin/env bash
# Read the production agent feedback cases (read-only): the list, or one case with its
# manifest. The same data as the "Agent cases" section of /debug.
#
#   scripts/agent-cases.sh            the newest cases, as JSON
#   scripts/agent-cases.sh <case-id>  one case, such as 20261012T160901Z-c1ddf295
#
# The API's admin gate needs ADMIN_TOKEN, and the API refuses a request without the origin
# secret that Cloudflare adds: both come from Secret Manager (`ADMIN_TOKEN`,
# `ORIGIN_SECRET`) through your gcloud account, so running this reads two production
# secrets. Neither is printed. `ANYPLOT_API_URL` overrides the service URL.
set -euo pipefail

URL=${ANYPLOT_API_URL:-$(gcloud run services describe anyplot-api --region=europe-west4 \
  --format='value(status.url)')}
ADMIN=$(gcloud secrets versions access latest --secret=ADMIN_TOKEN) || {
  echo "could not read the ADMIN_TOKEN secret" >&2
  exit 1
}
ORIGIN=$(gcloud secrets versions access latest --secret=ORIGIN_SECRET 2>/dev/null || true)
HEADERS=(-H "X-Admin-Token: $ADMIN" -H "X-Anyplot-Client: agent-chat/1")
[ -n "$ORIGIN" ] && HEADERS+=(-H "X-Origin-Secret: $ORIGIN")
curl -fsS --max-time 30 "${HEADERS[@]}" "$URL/debug/agent/cases${1:+/$1}"
echo
