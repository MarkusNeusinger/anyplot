#!/usr/bin/env bash
# Run one part of the local agent stack against the real models and the deployed renderer:
#
#   scripts/agents-dev.sh agents   the agents service on :8001
#   scripts/agents-dev.sh adk      ADK's development UI on :8002 with a fixture session
#   scripts/agents-dev.sh api      the API on :8000 with the agent routes switched on
#   scripts/agents-dev.sh app      the app on :3000 with the chat page built in
#
# Start each in its own terminal (or background task), from the checkout you want to run;
# agents/README.md, "Run the whole stack", walks through it. Every part runs in the
# foreground and writes its log to $ANYPLOT_DEV_LOGS (default ~/.cache/anyplot-dev).
#
# `agents` and `adk` render through the deployed `anyplot-renderer` with a gcloud identity
# token (`AGENT_RENDER_TOKEN`), which lives one hour, so they restart every 55 minutes with
# a fresh one. `AGENT_RENDER_URL` overrides the renderer, `AGENT_DEV_FIXTURE` the fixture
# `adk` opens (default scatter-basic-matplotlib).
#
# `api` needs ADMIN_TOKEN (the token you enter on /debug) and AGENT_USER_ID_KEY (any value
# for local use): from the environment, or else from the files of the same name in
# $ANYPLOT_DEV_SECRETS (default ~/.config/anyplot-dev, one value per file, mode 600). The
# script never prints them.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
LOGS=${ANYPLOT_DEV_LOGS:-$HOME/.cache/anyplot-dev}
SECRETS=${ANYPLOT_DEV_SECRETS:-$HOME/.config/anyplot-dev}
mkdir -p "$LOGS"
cd "$ROOT"
# A worktree's load_dotenv() would read the main checkout's production .env.
export PYTHON_DOTENV_DISABLED=1

model_env() {
  export ENVIRONMENT=development GOOGLE_CLOUD_PROJECT=anyplot GOOGLE_GENAI_USE_ENTERPRISE=TRUE \
    GOOGLE_CLOUD_LOCATION=eu AGENT_LOCATION=eu AGENT_RENDERER=remote
  if [ -z "${AGENT_RENDER_URL:-}" ]; then
    AGENT_RENDER_URL=$(gcloud run services describe anyplot-renderer --region=europe-west4 \
      --format='value(status.url)')
  fi
  export AGENT_RENDER_URL
}

# Run "$@" again and again with a fresh identity token, each run for at most 55 minutes.
with_fresh_token() {
  local name=$1
  shift
  while :; do
    if ! AGENT_RENDER_TOKEN=$(gcloud auth print-identity-token); then
      echo "$name: no identity token (gcloud auth login?), retrying in 60 s" >&2
      sleep 60
      continue
    fi
    export AGENT_RENDER_TOKEN
    echo "=== $name start $(date -u +%H:%M:%S)" >>"$LOGS/$name.log"
    local rc=0
    timeout 3300 "$@" >>"$LOGS/$name.log" 2>&1 || rc=$?
    echo "=== $name stop $(date -u +%H:%M:%S) rc=$rc" >>"$LOGS/$name.log"
    sleep 2
  done
}

# The value of the variable $1, or the content of the file $SECRETS/$1.
secret() {
  if [ -n "${!1:-}" ]; then
    printf '%s' "${!1}"
  elif [ -r "$SECRETS/$1" ]; then
    tr -d '\n' <"$SECRETS/$1"
  else
    echo "set $1 or put it in $SECRETS/$1" >&2
    exit 1
  fi
}

case "${1:-}" in
  agents)
    model_env
    with_fresh_token agents uv run --extra agents uvicorn agents.main:app --port 8001
    ;;
  adk)
    model_env
    export ADK_DISABLE_LOAD_DOTENV=1 AGENT_DEV_FIXTURE=${AGENT_DEV_FIXTURE:-scatter-basic-matplotlib}
    with_fresh_token adk uv run --extra agents adk web agents --port 8002 \
      --session_service_uri memory:// --artifact_service_uri memory://
    ;;
  api)
    ADMIN_TOKEN=$(secret ADMIN_TOKEN)
    AGENT_USER_ID_KEY=$(secret AGENT_USER_ID_KEY)
    export ADMIN_TOKEN AGENT_USER_ID_KEY AGENT_ENABLED=true AGENT_SERVICE_URL=http://localhost:8001
    uv run uvicorn api.main:app --port 8000 >>"$LOGS/api.log" 2>&1
    ;;
  app)
    # CI builds on Node 24; nvm picks it when it is installed.
    if [ -s "$HOME/.nvm/nvm.sh" ]; then
      . "$HOME/.nvm/nvm.sh" && nvm use 24 >/dev/null
    fi
    cd app
    VITE_ENABLE_AGENT_CHAT=true yarn dev --port 3000 --strictPort >>"$LOGS/app.log" 2>&1
    ;;
  *)
    echo "usage: $0 agents|adk|api|app" >&2
    exit 2
    ;;
esac
