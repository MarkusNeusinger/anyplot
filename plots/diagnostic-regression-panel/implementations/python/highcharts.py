""" anyplot.ai
diagnostic-regression-panel: Regression Diagnostic Panel (Four-Plot Display)
Library: highcharts unknown | Python 3.13.13
Quality: 80/100 | Created: 2026-05-13
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from scipy import stats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from statsmodels.nonparametric.smoothers_lowess import lowess


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"
SMOOTHER = "#C475FD"
COOK_COLOR = "#BD8233"

# Data — OLS regression with injected influential observations
np.random.seed(42)
n = 120
x1 = np.random.normal(0, 1, n)
x2 = np.random.normal(0, 1, n)
y = 2.0 * x1 + 0.5 * x2 + np.random.normal(0, 1.2, n)

x1[5], x2[5], y[5] = 4.2, 0.5, 15.0
x1[15], x2[15], y[15] = -4.0, 1.0, -8.0
x1[30], x2[30], y[30] = 3.5, -2.5, 2.0

X_mat = np.column_stack([np.ones(n), x1, x2])
beta = np.linalg.lstsq(X_mat, y, rcond=None)[0]
fitted = X_mat @ beta
resid = y - fitted

H_mat = X_mat @ np.linalg.inv(X_mat.T @ X_mat) @ X_mat.T
hat = np.diag(H_mat)
p = 3
sigma2 = np.sum(resid**2) / (n - p)
std_r = resid / np.sqrt(sigma2 * np.maximum(1.0 - hat, 1e-10))
cooks = std_r**2 * hat / (p * np.maximum(1.0 - hat, 1e-10))

top3 = {int(i) for i in np.argsort(cooks)[-3:]}

# LOWESS smoothers for subplots 1 and 3
ord_i = np.argsort(fitted)
lw_resid = lowess(resid[ord_i], fitted[ord_i], frac=0.6, return_sorted=True)
lw_scale = lowess(np.sqrt(np.abs(std_r[ord_i])), fitted[ord_i], frac=0.6, return_sorted=True)

# Q-Q data: sorted std residuals vs theoretical normal quantiles
sort_r = np.argsort(std_r)
qq_x = stats.norm.ppf(np.linspace(1 / (n + 1), n / (n + 1), n))
qq_y = std_r[sort_r]
q25_x, q75_x = np.percentile(qq_x, [25, 75])
q25_y, q75_y = np.percentile(qq_y, [25, 75])
qq_slope = (q75_y - q25_y) / max(q75_x - q25_x, 1e-10)
qq_inter = q25_y - qq_slope * q25_x

# Cook's D = 0.5 contour curves for subplot 4
lev_grid = np.linspace(0.005, min(float(hat.max()) * 1.5, 0.95), 300)
valid_h = lev_grid[lev_grid < 1.0]
c05_pos = [[round(float(h), 6), round(float(np.sqrt(0.5 * p * (1 - h) / h)), 4)] for h in valid_h]
c05_neg = [[round(float(h), 6), round(float(-np.sqrt(0.5 * p * (1 - h) / h)), 4)] for h in valid_h]


def make_pts(xs, ys, obs_indices):
    pts = []
    for j, (xv, yv) in enumerate(zip(xs, ys, strict=False)):
        idx = int(obs_indices[j])
        pt = {"x": round(float(xv), 5), "y": round(float(yv), 5)}
        if idx in top3:
            pt["dataLabels"] = {
                "enabled": True,
                "format": str(idx),
                "style": {"fontSize": "22px", "color": INK_SOFT, "fontWeight": "normal", "textOutline": "none"},
                "allowOverlap": True,
                "crop": False,
            }
        pts.append(pt)
    return pts


# Build per-subplot data arrays
obs_idx = list(range(n))
data_c1 = make_pts(fitted, resid, obs_idx)
data_lw1 = [[round(float(r[0]), 5), round(float(r[1]), 5)] for r in lw_resid]

data_c2 = make_pts(qq_x, qq_y, [int(sort_r[j]) for j in range(n)])
data_qq_ref = [
    {"x": round(float(qq_x.min()), 4), "y": round(float(qq_slope * float(qq_x.min()) + qq_inter), 4)},
    {"x": round(float(qq_x.max()), 4), "y": round(float(qq_slope * float(qq_x.max()) + qq_inter), 4)},
]

sqrt_abs_r = np.sqrt(np.abs(std_r))
data_c3 = make_pts(fitted, sqrt_abs_r, obs_idx)
data_lw3 = [[round(float(r[0]), 5), round(float(r[1]), 5)] for r in lw_scale]

data_c4 = make_pts(hat, std_r, obs_idx)

# Serialize to JSON for embedding in JavaScript
js_c1 = json.dumps(data_c1)
js_lw1 = json.dumps(data_lw1)
js_c2 = json.dumps(data_c2)
js_qqr = json.dumps(data_qq_ref)
js_c3 = json.dumps(data_c3)
js_lw3 = json.dumps(data_lw3)
js_c4 = json.dumps(data_c4)
js_cp = json.dumps(c05_pos)
js_cn = json.dumps(c05_neg)

# Download Highcharts JS inline (headless Chrome cannot load CDN from file://)
hc_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
req = urllib.request.Request(hc_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    hc_js = resp.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <script>{hc_js}</script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: {PAGE_BG}; width: 4800px; height: 2700px; overflow: hidden; }}
    #hdr {{
      width: 4800px; height: 100px;
      display: flex; align-items: center; justify-content: center;
      font-family: system-ui, sans-serif;
      font-size: 34px; font-weight: 700; color: {INK};
      letter-spacing: 0.02em;
    }}
    #grid {{
      display: grid;
      grid-template-columns: 2400px 2400px;
      grid-template-rows: 1300px 1300px;
    }}
  </style>
</head>
<body>
  <div id="hdr">diagnostic-regression-panel · highcharts · anyplot.ai</div>
  <div id="grid">
    <div id="c1"></div>
    <div id="c2"></div>
    <div id="c3"></div>
    <div id="c4"></div>
  </div>
  <script>
  var D = {{
    c1: {js_c1}, lw1: {js_lw1},
    c2: {js_c2}, qqr: {js_qqr},
    c3: {js_c3}, lw3: {js_lw3},
    c4: {js_c4}, cp: {js_cp}, cn: {js_cn}
  }};

  var titleStyle = {{fontSize: '24px', color: '{INK}', fontWeight: '700', fontFamily: 'system-ui, sans-serif'}};
  var axTitle   = function(t) {{ return {{text: t, style: {{fontSize: '20px', color: '{INK}', fontFamily: 'system-ui, sans-serif'}}}}; }};
  var axLabels  = {{style: {{fontSize: '16px', color: '{INK_SOFT}', fontFamily: 'system-ui, sans-serif'}}}};
  var axBase    = {{labels: axLabels, lineColor: '{INK_SOFT}', tickColor: '{INK_SOFT}', gridLineColor: '{GRID}'}};

  function mkScatter(data) {{
    return {{
      type: 'scatter', color: '{BRAND}',
      marker: {{radius: 5, symbol: 'circle', lineWidth: 1, lineColor: '{PAGE_BG}'}},
      data: data, enableMouseTracking: false
    }};
  }}
  function mkLine(data, color, dash, width) {{
    var s = {{
      type: 'line', color: color, lineWidth: width || 3,
      marker: {{enabled: false}}, data: data, enableMouseTracking: false
    }};
    if (dash) s.dashStyle = dash;
    return s;
  }}
  function zeroLine() {{
    return {{plotLines: [{{value: 0, color: '{INK_SOFT}', dashStyle: 'Dash', width: 2, zIndex: 3}}]}};
  }}

  function mkChart(id, title, xLabel, yLabel, series, extraY, extraX) {{
    var xAxis = Object.assign({{}}, axBase, {{title: axTitle(xLabel), gridLineWidth: 0}});
    var yAxis = Object.assign({{}}, axBase, {{title: axTitle(yLabel), gridLineWidth: 1}});
    if (extraY) Object.assign(yAxis, extraY);
    if (extraX) Object.assign(xAxis, extraX);
    Highcharts.chart(id, {{
      chart: {{
        type: 'scatter', width: 2400, height: 1300,
        backgroundColor: '{PAGE_BG}',
        style: {{fontFamily: 'system-ui, sans-serif'}},
        marginLeft: 130, marginBottom: 100, marginTop: 90, marginRight: 50
      }},
      title: {{text: title, style: titleStyle}},
      xAxis: xAxis,
      yAxis: yAxis,
      legend: {{enabled: false}},
      credits: {{enabled: false}},
      tooltip: {{enabled: false}},
      series: series
    }});
  }}

  // Subplot 1: Residuals vs Fitted
  mkChart('c1', 'Residuals vs Fitted', 'Fitted Values', 'Residuals',
    [mkScatter(D.c1), mkLine(D.lw1, '{SMOOTHER}')],
    zeroLine(), null);

  // Subplot 2: Normal Q-Q
  mkChart('c2', 'Normal Q-Q', 'Theoretical Quantiles', 'Std. Residuals',
    [mkScatter(D.c2), mkLine(D.qqr, '{INK_SOFT}', 'ShortDash', 2)],
    null, null);

  // Subplot 3: Scale-Location
  mkChart('c3', 'Scale-Location', 'Fitted Values', '√|Std. Residuals|',
    [mkScatter(D.c3), mkLine(D.lw3, '{SMOOTHER}')],
    null, null);

  // Subplot 4: Residuals vs Leverage
  mkChart('c4', 'Residuals vs Leverage', 'Leverage', 'Std. Residuals',
    [
      mkScatter(D.c4),
      mkLine(D.cp, '{COOK_COLOR}', 'ShortDash', 2),
      mkLine(D.cn, '{COOK_COLOR}', 'ShortDash', 2)
    ],
    zeroLine(), {{min: 0}});
  </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_opts = Options()
chrome_opts.add_argument("--headless")
chrome_opts.add_argument("--no-sandbox")
chrome_opts.add_argument("--disable-dev-shm-usage")
chrome_opts.add_argument("--disable-gpu")
chrome_opts.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_opts)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
