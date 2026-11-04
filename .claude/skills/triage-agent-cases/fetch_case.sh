#!/usr/bin/env bash
# Copy feedback cases from the private case bucket into a private directory, read-only on GCS.
#
#   .claude/skills/triage-agent-cases/fetch_case.sh [--dest DIR] CASE_ID...
#
# Each case lands in DIR/<case id>/ (manifest.json, and data.csv, plot-light.png,
# plot-dark.png and the code file when the case holds them). Without --dest, DIR is a new
# `mktemp -d` directory. DIR must lie outside every git checkout, because a case holds a
# user's data; it is created with mode 0700. The last line of output is DIR. Delete it
# when the round is done.
#
# Exit codes: 0 every case copied, 1 a copy failed, 2 bad arguments.
set -euo pipefail

bucket="${AGENT_CASES_BUCKET:-anyplot-agent-cases}"
# CASE_ID_PATTERN in core/agent_cases.py.
case_id_re='^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$'
dest=""

if [[ ${1:-} == "--dest" ]]; then
  if [[ -z ${2:-} ]]; then
    echo "fetch_case: --dest needs a directory" >&2
    exit 2
  fi
  dest="$2"
  shift 2
fi
if [[ $# -eq 0 ]]; then
  echo "usage: fetch_case.sh [--dest DIR] CASE_ID..." >&2
  exit 2
fi
for id in "$@"; do
  if [[ ! $id =~ $case_id_re ]]; then
    echo "fetch_case: '$id' is not a case id" >&2
    exit 2
  fi
done

# The directory, given or `mktemp`'s (which follows TMPDIR), must lie outside every
# checkout; the nearest existing ancestor is checked before anything is created.
target="${dest:-${TMPDIR:-/tmp}}"
probe="$(realpath -m "$target")"
while [[ ! -d $probe ]]; do probe="$(dirname "$probe")"; done
if git -C "$probe" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "fetch_case: $target is inside a git checkout; a case holds a user's data" >&2
  exit 2
fi
if [[ -z $dest ]]; then
  dest="$(mktemp -d -t anyplot-cases-XXXXXX)"
else
  mkdir -p -m 700 "$dest"
fi
chmod 700 "$dest"

failed=0
for id in "$@"; do
  if gcloud storage cp --recursive --no-user-output-enabled "gs://$bucket/cases/$id" "$dest/"; then
    echo "$id: $(cd "$dest/$id" && ls | tr '\n' ' ')"
  else
    echo "fetch_case: copying $id failed" >&2
    failed=1
  fi
done
echo "$dest"
exit "$failed"
