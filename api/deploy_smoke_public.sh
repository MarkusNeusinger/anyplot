#!/bin/bash
# The API deploy's probes of the public agent chat (`/agent/*`, api/routers/agent_public.py) against the
# CANDIDATE revision (api/cloudbuild.yaml, step "smoke", after its admin-gate probes). Each probe gates the
# promotion: a failure exits non-zero, and the revision serving now keeps serving.
#
# They live in this file because Cloud Build refuses a step argument longer than 10,000 characters;
# tests/unit/test_cloudbuild_configs.py holds every config's arguments under that limit.
#
# Usage, from the repository root (Cloud Build's /workspace):
#   ORIGIN_SECRET=<secret or empty> bash api/deploy_smoke_public.sh <candidate URL> <_AGENT_ENABLED> <_AGENT_PUBLIC_ENABLED>
# The secret comes through the environment, never as an argument, and is never echoed. The probes write their
# response into body.out in the working directory.
set -eu
URL="$1"
AGENT_ENABLED="$2"
PUBLIC_ENABLED="$3"
# Every probe retries: a freshly deployed candidate starts cold.
RETRY=(--retry 5 --retry-delay 5 --retry-all-errors)
HDR=()
if [ -n "${ORIGIN_SECRET:-}" ]; then HDR=(-H "X-Origin-Secret: $ORIGIN_SECRET"); fi
# A fixed smoke value, never a real visitor's tab id.
ANON="X-Anyplot-Anon: deploy-smoke-0000000000000000"

# The public door answers exactly as the trigger set it: 404 while closed, so a revision never opens it by
# accident, and while open `{"open": true}`.
code=$(curl -s "${RETRY[@]}" "${HDR[@]}" -o body.out -w '%{http_code}' "$URL/agent/lane")
if [ "$AGENT_ENABLED" != "true" ] || [ "$PUBLIC_ENABLED" != "true" ]; then
  test "$code" = "404" || { echo "public agent lane expected closed (404), got $code"; exit 1; }
  echo "OK: /agent/* is closed"
  exit 0
fi
test "$code" = "200" && grep -qF '"open":true' body.out \
  || { echo "public agent lane expected open (200), got $code (in production it opens only while ORIGIN_SECRET arms the origin gate and TURNSTILE_SECRET_KEY is bound)"; exit 1; }

# A public status call that reaches the agents service as an anonymous caller: it books nothing, and no login is
# involved.
code=$(curl -s "${RETRY[@]}" "${HDR[@]}" -H "$ANON" -o body.out -w '%{http_code}' "$URL/agent/status")
test "$code" = "200" || { echo "public agent status expected 200, got $code"; exit 1; }
grep -qF '"libraries"' body.out || { echo "public agent status did not relay the agents service's status"; exit 1; }
echo "OK: /agent/* is open and reaches anyplot-agents"

# The bot check (api/turnstile.py), end to end: Cloudflare's dummy token, which every production secret refuses,
# must read 403 bot_check_failed. That proves the secret arrived, Cloudflare accepted it and siteverify is
# reachable from the service. A 503 bot_check_unavailable is a wrong or test secret or no route to Cloudflare; a
# 200 means a session opened unchecked. The token is checked before the agents service is asked, so on the 403
# path no session opens and nothing is booked.
code=$(curl -s "${RETRY[@]}" "${HDR[@]}" -X POST -H "X-Anyplot-Client: agent-chat/1" \
  -H "Content-Type: application/json" -H "$ANON" -H "X-Turnstile-Token: XXXX.DUMMY.TOKEN.XXXX" \
  -d '{"spec_id":"scatter-basic","library":"matplotlib","locale":"en"}' -o body.out -w '%{http_code}' "$URL/agent/sessions")
test "$code" = "403" && grep -qF '"bot_check_failed"' body.out \
  || { echo "the bot check expected 403 bot_check_failed for a dummy token, got $code: $(head -c 200 body.out)"; exit 1; }
echo "OK: /agent/sessions refuses a dummy Turnstile token"
