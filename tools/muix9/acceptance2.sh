#!/usr/bin/env bash
# Acceptance run for a Gemini chunk: W=worktree LIST=spec list (one per line) OUT=dir
set -uo pipefail
source ~/.nvm/nvm.sh >/dev/null && nvm use 24 >/dev/null
W=${W:?} LIST=${LIST:?} OUT=${OUT:?}
MAIN=$(cd "$W" && git rev-parse --git-common-dir | xargs dirname)
mkdir -p "$OUT/renders"; cd "$W" || exit 2
echo "node $(node --version) wt $(git rev-parse --short HEAD)"
if [ ! -d node_modules ]; then npm ci --no-audit --no-fund > "$OUT/npm-ci.log" 2>&1 || { echo "npm ci FAILED"; tail -20 "$OUT/npm-ci.log"; exit 2; }; fi
node -p "require('@mui/x-charts/package.json').version" | sed 's/^/x-charts /'
GREP='ResponsiveChartContainer|[^s]ChartContainer|DefaultChartsLegend|Unstable_|hidden: *true|labelFontSize|tickFontSize|\b(top|left|bottom|right)Axis\b|MuiAreaElement-root|MuiLineElement-series-|MuiBarElement-root|MuiMarkElement-root|MuiScatterElement-root|MuiPieArc-root|lineElementClasses|areaElementClasses|barElementClasses|markElementClasses|pieArcClasses|pieArcLabelClasses|itemMarkWidth|itemMarkHeight|markGap|itemGap|t\.muted'
for s in $(sed '/^$/d' "$LIST"); do
  f=plots/$s/implementations/javascript/muix.tsx; R="$OUT/renders/$s"; mkdir -p "$R"
  ANYPLOT_THEME=light node automation/js-render/render.mjs "$f" >"$R/light.log" 2>&1; le=$?; mv -f plot-light.png "$R/plot-light.png" 2>/dev/null; rm -f plot-light.html
  ANYPLOT_THEME=dark  node automation/js-render/render.mjs "$f" >"$R/dark.log" 2>&1; de=$?; mv -f plot-dark.png "$R/plot-dark.png" 2>/dev/null; rm -f plot-dark.html
  chk=$(cd "$MAIN" && PYTHON_DOTENV_DISABLED=1 uv run -q python -c "
from pathlib import Path
from core.canvas import check_png
d=Path('$R')
for t in ('light','dark'):
    p=d/f'plot-{t}.png'
    v=check_png(p,'muix') if p.exists() else None
    print('MISSING' if v is None else f'{v.width}x{v.height}/{v.target[0]}x{v.target[1]}', end=' ')
" 2>&1 | tr -d '\n')
  v7=$(grep -cE "$GREP" "$f"); hdr=$(head -5 "$f" | grep -c '^// anyplot.ai'); l1=$(head -1 "$f" | cut -c1-30)
  echo "$(date -u +%H:%M:%S) $s light=$le dark=$de v7=$v7 headers=$hdr line1='$l1' :: $chk"
done
echo DONE
