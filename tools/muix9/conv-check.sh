#!/usr/bin/env bash
# Adaptable-code convention check for muix files: conv-check.sh <worktree> <spec list file>
# One line per spec; a compliant file shows roles>=1 plot=1 col=0 DATA=0 sans=0.
set -uo pipefail
W=${1:?worktree} LIST=${2:?spec list}
fail=0
for s in $(sed '/^$/d' "$LIST"); do
  f="$W/plots/$s/implementations/javascript/muix.tsx"
  [ -f "$f" ] || { echo "$s MISSING"; fail=$((fail + 1)); continue; }
  roles=$(grep -c '// role:' "$f"); plot=$(grep -cE '^// Plot' "$f")
  col=$(grep -cE '\b[A-Z_]+_COL\b' "$f"); DATA=$(grep -cE 'const DATA\b' "$f")
  sans=$(grep -cE 't\.(sans|mono)\b' "$f"); hdr=$(head -5 "$f" | grep -c '^// anyplot.ai')
  ok=yes; { [ "$roles" -ge 1 ] && [ "$plot" -eq 1 ] && [ "$col" -eq 0 ] && [ "$DATA" -eq 0 ] && [ "$sans" -eq 0 ] && [ "$hdr" -eq 1 ]; } || { ok=NO; fail=$((fail + 1)); }
  echo "$s roles=$roles plot=$plot col=$col DATA=$DATA sans=$sans headers=$hdr $ok"
done
echo "failing: $fail"
[ "$fail" -eq 0 ]
