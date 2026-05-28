""" anyplot.ai
ice-basic: Individual Conditional Expectation (ICE) Plot
Library: highcharts unknown | Python 3.13.13
Quality: 86/100 | Created: 2026-05-07
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.ensemble import GradientBoostingRegressor


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BRAND = "#009E73"  # Okabe-Ito position 1 — ICE lines
PDP_COLOR = "#C475FD"  # Okabe-Ito position 2 — PDP overlay
ICE_COLOR = "rgba(0,158,115,0.20)"  # BRAND at 20% opacity

# Data
np.random.seed(42)
n_samples = 400

sqft = np.random.uniform(800, 3500, n_samples)
bedrooms = np.random.randint(1, 6, n_samples).astype(float)
age = np.random.uniform(0, 50, n_samples)
location = np.random.uniform(1, 10, n_samples)  # 1=poor area, 10=premium area

# Price scales sqft by location quality — creates strong heterogeneous ICE fan-out
price = (
    sqft * (80 + 15 * location)  # per-sqft rate rises sharply with location
    + 25000 * bedrooms
    - 1500 * age
    + np.random.normal(0, 25000, n_samples)
)
price = np.clip(price, 50000, None)

X = np.column_stack([sqft, bedrooms, age, location])

model = GradientBoostingRegressor(n_estimators=150, max_depth=4, learning_rate=0.1, random_state=42)
model.fit(X, price)

# ICE curves: vary sqft across its range for each sampled observation
n_ice = 80
n_grid = 60
sample_idx = np.random.choice(n_samples, n_ice, replace=False)
X_sample = X[sample_idx]

sqft_grid = np.linspace(sqft.min(), sqft.max(), n_grid)
ice_matrix = np.zeros((n_ice, n_grid))

for j, sq in enumerate(sqft_grid):
    X_mod = X_sample.copy()
    X_mod[:, 0] = sq
    ice_matrix[:, j] = model.predict(X_mod)

# Scale to $k for cleaner axis labels
ice_matrix /= 1000
pdp = ice_matrix.mean(axis=0)

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK},
    "marginTop": 110,
    "marginBottom": 160,
    "marginLeft": 180,
    "marginRight": 80,
}

chart.options.title = {
    "text": "ice-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "600"},
    "margin": 30,
}

chart.options.subtitle = {
    "text": (
        f"House Price Predictions — GradientBoostingRegressor · {n_ice} observations · "
        "How predicted price varies with square footage"
    ),
    "style": {"fontSize": "20px", "color": INK_SOFT},
    "margin": 20,
}

chart.options.x_axis = {
    "title": {"text": "Square Footage (sq ft)", "style": {"fontSize": "22px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineWidth": 0,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
}

chart.options.y_axis = {
    "title": {"text": "Predicted Price ($k)", "style": {"fontSize": "22px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineWidth": 0,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"color": INK_SOFT, "fontSize": "20px", "fontWeight": "400"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "borderRadius": 4,
    "padding": 20,
    "symbolWidth": 50,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -20,
    "y": 60,
}

chart.options.tooltip = {"enabled": False}

chart.options.plot_options = {
    "line": {"marker": {"enabled": False}, "states": {"hover": {"enabled": False}}, "animation": False}
}

# ICE series (individual prediction curves)
grid_x = [float(v) for v in sqft_grid]

for i in range(n_ice):
    s = LineSeries()
    s.data = [[grid_x[j], float(ice_matrix[i, j])] for j in range(n_grid)]
    s.color = ICE_COLOR
    s.line_width = 2
    s.show_in_legend = i == 0
    s.name = f"ICE Curves (n={n_ice})" if i == 0 else "ice"
    s.enable_mouse_tracking = False
    chart.add_series(s)

# PDP series (bold average line)
pdp_s = LineSeries()
pdp_s.data = [[grid_x[j], float(pdp[j])] for j in range(n_grid)]
pdp_s.name = "Partial Dependence (PDP)"
pdp_s.color = PDP_COLOR
pdp_s.line_width = 6
pdp_s.z_index = 10
pdp_s.show_in_legend = True
chart.add_series(pdp_s)

# Download Highcharts JS (inline embedding required for headless Chrome)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as resp:
    highcharts_js = resp.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
