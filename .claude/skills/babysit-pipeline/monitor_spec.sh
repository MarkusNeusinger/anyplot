#!/usr/bin/env bash
# Oneshot completion checker for a single spec's bulk-generate pipeline.
# Usage: monitor_spec.sh <spec-id> <issue-number>
# Prints per-library status and an overall verdict line:
#   STATUS=COMPLETE | STATUS=IN_PROGRESS | STATUS=NEEDS_ATTENTION
set -uo pipefail

SPEC="$1"
ISSUE="$2"

PY="matplotlib seaborn plotly bokeh altair plotnine pygal letsplot"
ALL_LIBS="$PY ggplot2 makie chartjs d3 echarts highcharts muix"

lang_of() {
  case "$1" in
    ggplot2) echo r ;;
    makie) echo julia ;;
    chartjs|d3|echarts|highcharts|muix) echo javascript ;;
    *) echo python ;;
  esac
}

# A gh failure must surface as such — silencing it would report a bogus
# done=0/15 and let the poller mis-diagnose a stall.
if ! LABELS=$(gh issue view "$ISSUE" --json labels --jq '.labels[].name' 2>&1); then
  echo "ERROR: gh issue view #$ISSUE failed (auth/network?): $LABELS"
  echo "STATUS=NEEDS_ATTENTION"
  exit 0
fi

done_count=0
failed_libs=""
pending_libs=""
for lib in $ALL_LIBS; do
  if grep -qx "impl:${lib}:done" <<<"$LABELS"; then
    done_count=$((done_count+1))
  elif grep -qx "impl:${lib}:failed" <<<"$LABELS"; then
    failed_libs="$failed_libs $lib"
  else
    pending_libs="$pending_libs $lib"
  fi
done

echo "spec=$SPEC issue=$ISSUE  done=$done_count/15"
[ -n "$pending_libs" ] && echo "  pending:$pending_libs"
[ -n "$failed_libs" ]  && echo "  failed:$failed_libs"

# Verdict
if [ "$done_count" -eq 15 ]; then
  # GCS spot-check: confirm production image for one python + one js lib
  gcs_ok=0
  gsutil -q stat "gs://anyplot-images/plots/${SPEC}/python/matplotlib/plot-light.png" 2>/dev/null && gcs_ok=$((gcs_ok+1))
  gsutil -q stat "gs://anyplot-images/plots/${SPEC}/javascript/muix/plot-light.png" 2>/dev/null && gcs_ok=$((gcs_ok+1))
  if [ "$gcs_ok" -eq 2 ]; then
    echo "STATUS=COMPLETE"
  else
    # impl-merge promotes to GCS atomically with the labels, so 15/15 labels
    # without the images is abnormal (broken gsutil auth or a failed
    # promotion), not a transient — surface it instead of waiting forever.
    echo "  GCS spot-check failed at 15/15 labels (matplotlib+muix present=$gcs_ok/2) — check gsutil auth, then the impl-merge promotion"
    echo "STATUS=NEEDS_ATTENTION"
  fi
elif [ -n "$failed_libs" ] && [ -z "$pending_libs" ]; then
  # nothing left running, only failures remain -> needs intervention
  echo "STATUS=NEEDS_ATTENTION"
else
  echo "STATUS=IN_PROGRESS"
fi
