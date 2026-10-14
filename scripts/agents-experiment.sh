#!/usr/bin/env bash
# Run an agent experiment on the live code, with the Claude calls on your Claude subscription:
#
#   scripts/agents-experiment.sh NAME [matrix options...]
#
# Runs the regression harness (`agents.evals.matrix`, every case through the real `/v1`
# flow, the deployed renderer, every attempt's render kept) with AGENT_TRANSPORT=claude-cli,
# then scores the first and shipped render of each run with the catalogue rubric
# (`agents.evals.score --transport claude-cli`, Opus). Everything lands in
# $ANYPLOT_DEV_EXPERIMENTS/NAME (default ~/.cache/anyplot-dev/experiments/NAME), outside
# the checkout, so a removed worktree takes nothing with it.
#
# The experiment is what you change: the code of the checkout you run this from (a branch
# with another prompt or pipeline step), and these variables:
#
#   AGENT_ADAPTER_MODEL=claude-sonnet-5-5   the adapter's model (any of cli_transport.CLI_MODELS)
#   AGENT_REVIEWER_MODEL=claude-opus-5-5    the reviewer's model
#   AGENT_MAX_ATTEMPTS=3                    or `--max-attempts 3`; any other AGENT_* setting
#   SCORE=0                                 skip the scoring step
#
# The root (chat with tools) is the one agent the CLI cannot run; its calls go to Claude
# Haiku on Vertex AI, about $0.002 a run. Matrix options pass through, for example
# `--cases smoke`, `--cases 'scatter-basic-*'` or `--repeats 2`. Compare two experiments
# by their `*-scores.md`, or the harness reports with `--compare`.
set -euo pipefail

if [ $# -lt 1 ] || [[ $1 == -* ]]; then
  sed -n '2,26p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
fi
NAME=$1
shift

ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=${ANYPLOT_DEV_EXPERIMENTS:-$HOME/.cache/anyplot-dev/experiments}/$NAME
mkdir -p "$OUT"
cd "$ROOT"

# A worktree's load_dotenv() would read the main checkout's production .env.
export PYTHON_DOTENV_DISABLED=1
export ENVIRONMENT=development GOOGLE_CLOUD_PROJECT=anyplot AGENT_LOCATION=eu \
  AGENT_TRANSPORT=claude-cli AGENT_CLI_CALL_LOG="$OUT/cli-calls.jsonl"
# The token budgets guard Vertex AI spend. On the subscription they only distort the experiment:
# the CLI's own thinking writes more output tokens than the live thinking budget allows, and the
# Budget plugin would end runs before their review (7 of the first 15 runs of 2026-10-13).
export AGENT_REQUEST_TOKEN_BUDGET=${AGENT_REQUEST_TOKEN_BUDGET:-10000000} \
  AGENT_DAILY_TOKEN_BUDGET=${AGENT_DAILY_TOKEN_BUDGET:-1000000000} \
  AGENT_GLOBAL_DAILY_TOKEN_BUDGET=${AGENT_GLOBAL_DAILY_TOKEN_BUDGET:-1000000000} \
  AGENT_DAILY_PIPELINE_RUNS=${AGENT_DAILY_PIPELINE_RUNS:-100000}
if [ -z "${AGENT_RENDER_URL:-}" ]; then
  AGENT_RENDER_URL=$(gcloud run services describe anyplot-renderer --region=europe-west4 \
    --format='value(status.url)')
fi

echo "experiment $NAME: adapter ${AGENT_ADAPTER_MODEL:-default}, reviewer ${AGENT_REVIEWER_MODEL:-default}," \
  "commit $(git rev-parse --short HEAD), out $OUT"
# The fixed options come last, so a pass-through option cannot override the renderer or the output.
uv run --extra agents python -m agents.evals.matrix "$@" --keep-attempts --no-baseline \
  --renderer remote --render-url "$AGENT_RENDER_URL" --gcloud-token --out "$OUT"

if [ "${SCORE:-1}" != 0 ]; then
  report=$(ls -t "$OUT"/*.json | grep -v -e '-scores[-.]' -e 'cli-calls' | head -1)
  uv run --extra agents python -m agents.evals.score "$report" --transport claude-cli
fi
