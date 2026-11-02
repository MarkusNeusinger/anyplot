#!/bin/bash
# The renderer deploy's render probes against the CANDIDATE revision (agents/renderer/cloudbuild.yaml,
# step "smoke", with _SMOKE_RENDER=true, after its IAM and /status checks). Each probe gates the
# promotion: a failure exits non-zero, and the revision serving now keeps serving.
#
# They live in this file because Cloud Build refuses a step argument longer than 10,000 characters
# ("invalid build: invalid .steps field: build step 7 arg 1 too long (max: 10000)"; build dc1cf3ae of
# 2026-11-01, when the plotly probe took the inline step to 11,347 characters and PB-2a's renderer never
# deployed). tests/unit/test_cloudbuild_configs.py holds every config's arguments under that limit.
#
# Usage, from the repository root (Cloud Build's /workspace):
#   SMOKE_TOKEN=<ID token for the service URL> bash agents/renderer/deploy_smoke.sh <candidate URL>
# The token comes through the environment, never as an argument. The probes write their request and
# response files into the working directory.
set -eu
URL="$1"
TOKEN="$SMOKE_TOKEN"

# 2a. A matplotlib render: the launcher, the in-memory volume, the harness and the caller check, end to end.
python3 - <<'EOF'
import json
source = "\n".join([
    "import matplotlib.pyplot as plt",
    "fig, ax = plt.subplots(figsize=(16, 9), dpi=200)",
    "ax.plot([1, 2, 3, 4], [3, 1, 4, 2], linewidth=6)",
    "fig.savefig('plot-light.png')",
])
job = {"job_id": "smoke", "language": "python", "library": "matplotlib", "source": source,
       "data_csv": "x\n1\n", "themes": ["light"], "timeout_s": 60}
json.dump(job, open("job.json", "w"))
EOF
curl -fsS --retry 3 --retry-delay 10 --retry-all-errors --max-time 200 -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" --data @job.json -o render.json "$URL/render" \
  || { echo "the smoke render request failed"; exit 1; }
python3 -c "import json; r=json.load(open('render.json')); o=r['outputs']['light']; assert o['exit_code']==0 and o['png_base64'], {k: o[k] for k in ('exit_code','reason','attempts','wall_s')}; print('OK: smoke render', o['wall_s'], 's,', o['attempts'], 'attempt(s)')"

# 2b. A Makie render through the Julia row (step 5 of agentic/specs/261024-agent-all-libraries.md): the
#     depot's package images load under gVisor with --compiled-modules=strict and the preloaded exec filter,
#     or the render fails within seconds and nothing is promoted. The first Julia render of a fresh
#     instance, so its wall time is the cold one.
python3 - <<'EOF'
import json
source = "\n".join([
    "using CairoMakie",
    "THEME = get(ENV, \"ANYPLOT_THEME\", \"light\")",
    "fig = Figure(size = (1600, 900))",
    "ax = Axis(fig[1, 1], title = \"Größe – smoke\")",
    "lines!(ax, [1, 2, 3, 4], [3, 1, 4, 2], linewidth = 6)",
    "save(\"plot-$(THEME).png\", fig; px_per_unit = 2)",
])
job = {"job_id": "smoke-makie", "language": "julia", "library": "makie", "source": source,
       "data_csv": "x\n1\n", "themes": ["light"], "timeout_s": 90}
json.dump(job, open("makie_job.json", "w"))
EOF
curl -fsS --retry 3 --retry-delay 10 --retry-all-errors --max-time 240 -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" --data @makie_job.json -o makie.json "$URL/render" \
  || { echo "the Makie smoke render request failed"; exit 1; }
python3 -c "import json; r=json.load(open('makie.json')); o=r['outputs']['light']; assert o['exit_code']==0 and o['png_base64'], {k: o[k] for k in ('exit_code','reason','attempts','wall_s','stderr_tail')}; print('OK: Makie smoke render', o['wall_s'], 's wall,', o['cpu_s'], 's CPU,', o['max_rss_mb'], 'MiB,', o['attempts'], 'attempt(s)')"

# 2c. A Chart.js render through the JavaScript row (JS-1 of step 3): Node by its path starts Chromium's
#     headless shell under gVisor, which no local run can, and the page reads the job's typed table
#     (`data_json`, `window.ANYPLOT_DATA`), as every agent job does. A gate like the Makie render since JS-4a
#     served JavaScript. curl's retries cover the transport only, and a render that fails answers 200, so
#     the render gets a second try 30 s later; each failure prints the exit code, the reason, the attempts
#     and the stderr tail (JS renders failed on Cloud Run for about 40 minutes after a fresh toolchain build
#     on 2026-10-30, cause unproven).
python3 - <<'EOF'
import json
source = "\n".join([
    "const t = window.ANYPLOT_TOKENS;",
    "const data = window.ANYPLOT_DATA;",
    "const canvas = document.createElement('canvas');",
    "document.getElementById('container').appendChild(canvas);",
    "new Chart(canvas, {",
    "  type: 'bar',",
    "  data: {labels: data.map((d) => d.Gruppe), datasets: [{data: data.map((d) => d.Wert), backgroundColor: t.palette[0]}]},",
    "  options: {responsive: true, maintainAspectRatio: false, animation: false,",
    "    plugins: {title: {display: true, text: 'Größe – smoke', color: t.ink}}},",
    "});",
])
table = {"columns": ["Gruppe", "Wert"], "data": [["a", 3], ["b", 1], ["c", 2]]}
job = {"job_id": "smoke-chartjs", "language": "javascript", "library": "chartjs", "source": source,
       "data_csv": "Gruppe,Wert\na,3\nb,1\nc,2\n", "data_json": json.dumps(table),
       "themes": ["light"], "timeout_s": 60}
json.dump(job, open("chartjs_job.json", "w"))
EOF
chartjs_ok=""
for try in 1 2; do
  if curl -fsS --retry 3 --retry-delay 10 --retry-all-errors --max-time 200 -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" --data @chartjs_job.json -o chartjs.json "$URL/render" \
    && python3 -c "import json; r=json.load(open('chartjs.json')); o=r['outputs']['light']; assert o['exit_code']==0 and o['png_base64'], {k: o[k] for k in ('exit_code','reason','attempts','wall_s','stderr_tail')}; print('OK: Chart.js smoke render', o['wall_s'], 's wall,', o['cpu_s'], 's CPU,', o['max_rss_mb'], 'MiB,', o['attempts'], 'attempt(s)')"; then
    chartjs_ok=1
    break
  fi
  echo "the Chart.js smoke render failed (try $try of 2)"
  if [ "$try" = 1 ]; then sleep 30; fi
done
[ -n "$chartjs_ok" ] || { echo "the Chart.js smoke render failed twice"; exit 1; }

# 2d. A plotly render through the two-step figure mode (PB-1, a gate since PB-2a served plotly and bokeh):
#     the harness forks the plot under its guard and the exec filter, the plot reads data.csv and writes its
#     figure as JSON through the pinned save (an axis range included, which runs plotly's `build_validator`
#     under the guard), and the JavaScript row's harness draws it in Chromium under gVisor, which no local
#     run can. The same two tries as the Chart.js render; a failure refuses the promotion.
python3 - <<'EOF'
import json
source = "\n".join([
    "import os",
    "",
    "import pandas as pd",
    "import plotly.graph_objects as go",
    "",
    "THEME = os.getenv('ANYPLOT_THEME', 'light')",
    "df = pd.read_csv('data.csv')",
    "fig = go.Figure(go.Bar(x=df['Gruppe'], y=df['Wert'], marker_color='#009E73'))",
    "fig.update_layout(title={'text': 'Größe – smoke'}, yaxis={'range': [0, 3.5]})",
    "fig.update_layout(width=800, height=450).write_json(f'plot-{THEME}.json')",
])
job = {"job_id": "smoke-plotly", "language": "python", "library": "plotly", "source": source,
       "data_csv": "Gruppe,Wert\na,3\nb,1\nc,2\n", "themes": ["light"], "timeout_s": 60}
json.dump(job, open("plotly_job.json", "w"))
EOF
plotly_ok=""
for try in 1 2; do
  if curl -fsS --retry 3 --retry-delay 10 --retry-all-errors --max-time 200 -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" --data @plotly_job.json -o plotly.json "$URL/render" \
    && python3 -c "import json; r=json.load(open('plotly.json')); o=r['outputs']['light']; assert o['exit_code']==0 and o['png_base64'], {k: o[k] for k in ('exit_code','reason','attempts','wall_s','stderr_tail')}; print('OK: plotly figure smoke render', o['wall_s'], 's wall,', o['cpu_s'], 's CPU,', o['max_rss_mb'], 'MiB,', o['attempts'], 'attempt(s)')"; then
    plotly_ok=1
    break
  fi
  echo "the plotly figure smoke render failed (try $try of 2)"
  if [ "$try" = 1 ]; then sleep 30; fi
done
[ -n "$plotly_ok" ] || { echo "the plotly figure smoke render failed twice"; exit 1; }

# 3. A real data run (POST /run-data, run_data_code): the harness in data mode with its audit-hook guard
#    armed returns a 2-row table.
python3 - <<'EOF'
import json
source = "import pandas as pd\ndf = pd.DataFrame({'x': [1, 2], 'y': [3, 4]})\n"
json.dump({"job_id": "smoke-data", "source": source, "timeout_s": 30}, open("data_job.json", "w"))
EOF
curl -fsS --retry 3 --retry-delay 10 --retry-all-errors --max-time 120 -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" --data @data_job.json -o data.json "$URL/run-data" \
  || { echo "the smoke data run request failed"; exit 1; }
python3 -c "import json; r=json.load(open('data.json')); assert r['exit_code']==0 and (r['csv_text'] or '').splitlines()==['x,y','1,3','2,4'], {k: r[k] for k in ('exit_code','reason','attempts','wall_s')}; print('OK: smoke data run', r['wall_s'], 's,', r['attempts'], 'attempt(s)')"
