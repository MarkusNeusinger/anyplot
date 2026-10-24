#!/usr/bin/env bash
# Costs per pipeline run and scores per spec for an adopt batch: START=<iso> collect.sh <out dir>
# Reads total_cost_usd from the job logs (the run log endpoint is empty for some runs).
set -uo pipefail
START=${START:?START=<iso timestamp of the dispatch>}
OUT=${1:?out dir}
mkdir -p "$OUT"
: > "$OUT/runs.tsv"
for wf in impl-review impl-repair; do
  gh run list --workflow=$wf.yml --limit 120 --created ">=$START" --json databaseId,conclusion,displayTitle \
    --jq '.[] | "\(.databaseId)\t\(.displayTitle)\t\(.conclusion)"' \
  | while IFS=$'\t' read -r id title concl; do
      jid=$(gh run view "$id" --json jobs --jq '.jobs[0].databaseId')
      c=$(gh api "repos/{owner}/{repo}/actions/jobs/$jid/logs" 2>/dev/null | grep -oE '"total_cost_usd":\s*[0-9.]+' | head -1 | grep -oE '[0-9.]+$')
      printf '%s\t%s\t%s\t%s\t%s\n' "$wf" "$id" "$title" "$concl" "${c:-na}" >> "$OUT/runs.tsv"
    done
done
: > "$OUT/specs.tsv"
for pr in $(gh pr list --state all --limit 200 --search "muix in:title created:>=$START" --json number --jq '.[].number'); do
  spec=$(gh pr view "$pr" --json title --jq '.title | sub("^.*implement ";"")')
  st=$(gh pr view "$pr" --json state --jq .state)
  sc=$(gh api "repos/{owner}/{repo}/issues/$pr/comments" --jq '.[] | .body' | grep -oE '^### Score: [0-9]+' | grep -oE '[0-9]+$' | tr '\n' ',')
  printf '%s\t%s\t%s\t%s\n' "$spec" "$pr" "$st" "${sc%,}" >> "$OUT/specs.tsv"
done
python3 - "$OUT" <<'EOF'
import sys, statistics as st
from pathlib import Path
E = Path(sys.argv[1]); tot = {}
for l in E.joinpath('runs.tsv').read_text().splitlines():
    wf, _id, _title, _concl, cost = l.split('\t')
    if cost != 'na':
        tot.setdefault(wf, []).append(float(cost))
s = 0
for wf, c in tot.items():
    print(f"{wf:12s} n={len(c)} sum=${sum(c):.2f} mean=${sum(c)/len(c):.2f}"); s += sum(c)
specs = [l.split('\t') for l in E.joinpath('specs.tsv').read_text().splitlines()]
first, final, norep = [], [], 0
for spec, pr, stt, sc in sorted(specs):
    v = [int(x) for x in sc.split(',') if x]
    if not v:
        print(f"{spec:28s} #{pr} {stt:7s} (no score)"); continue
    first.append(v[0]); final.append(v[-1]); norep += (len(v) == 1)
    print(f"{spec:28s} #{pr} {stt:7s} {sc}")
if first:
    print(f"pairs {len(first)} total ${s:.2f} per pair ${s/len(first):.2f}; first mean {st.mean(first):.1f} range {min(first)}-{max(first)}; final mean {st.mean(final):.1f}; no repair {norep}/{len(first)}")
EOF
