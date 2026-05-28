""" anyplot.ai
scatter-matrix: Scatter Plot Matrix
Library: highcharts unknown | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-09
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette for 3 categories
COLORS = ["#009E73", "#C475FD", "#4467A3"]

# Data - Iris dataset (classic multivariate example)
np.random.seed(42)

n_per_species = 50
species_names = ["Setosa", "Versicolor", "Virginica"]

# Setosa: small petals, medium sepals
setosa_sepal_length = np.random.normal(5.0, 0.35, n_per_species)
setosa_sepal_width = np.random.normal(3.4, 0.38, n_per_species)
setosa_petal_length = np.random.normal(1.5, 0.17, n_per_species)
setosa_petal_width = np.random.normal(0.25, 0.1, n_per_species)

# Versicolor: medium size
versicolor_sepal_length = np.random.normal(5.9, 0.52, n_per_species)
versicolor_sepal_width = np.random.normal(2.8, 0.31, n_per_species)
versicolor_petal_length = np.random.normal(4.3, 0.47, n_per_species)
versicolor_petal_width = np.random.normal(1.3, 0.2, n_per_species)

# Virginica: large
virginica_sepal_length = np.random.normal(6.6, 0.64, n_per_species)
virginica_sepal_width = np.random.normal(3.0, 0.32, n_per_species)
virginica_petal_length = np.random.normal(5.5, 0.55, n_per_species)
virginica_petal_width = np.random.normal(2.0, 0.27, n_per_species)

# Combine data
sepal_length = np.concatenate([setosa_sepal_length, versicolor_sepal_length, virginica_sepal_length])
sepal_width = np.concatenate([setosa_sepal_width, versicolor_sepal_width, virginica_sepal_width])
petal_length = np.concatenate([setosa_petal_length, versicolor_petal_length, virginica_petal_length])
petal_width = np.concatenate([setosa_petal_width, versicolor_petal_width, virginica_petal_width])
species = [0] * n_per_species + [1] * n_per_species + [2] * n_per_species

variables = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]
data = [sepal_length, sepal_width, petal_length, petal_width]
n_vars = len(variables)

# Calculate chart dimensions
canvas_size = 3600  # Square for symmetric matrix
chart_width = canvas_size // n_vars
chart_height = canvas_size // n_vars

# Download Highcharts JS with retry
highcharts_js = None
urls_to_try = ["https://code.highcharts.com/highcharts.js", "https://unpkg.com/highcharts@latest/highcharts.js"]
for url in urls_to_try:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        continue
if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS from any CDN")

# Build HTML with multiple charts
charts_html = ""
charts_js = ""

for row in range(n_vars):
    for col in range(n_vars):
        container_id = f"chart_{row}_{col}"
        left = col * chart_width
        top = row * chart_height

        # Add container div
        charts_html += f'<div id="{container_id}" style="position:absolute; left:{left}px; top:{top}px; width:{chart_width}px; height:{chart_height}px;"></div>\n'

        if row == col:
            # Diagonal: histogram for this variable
            var_data = data[row]
            bins = 15
            hist_counts, bin_edges = np.histogram(var_data, bins=bins)
            categories = [f"{bin_edges[i]:.1f}" for i in range(len(bin_edges) - 1)]

            # Create histogram data split by species for color coding
            hist_series_data = []
            for sp_idx in range(3):
                sp_mask = [i for i, s in enumerate(species) if s == sp_idx]
                sp_data = var_data[sp_mask]
                sp_counts, _ = np.histogram(sp_data, bins=bin_edges)
                hist_series_data.append(sp_counts.tolist())

            # Build chart config
            chart_config = {
                "chart": {
                    "type": "column",
                    "backgroundColor": PAGE_BG,
                    "marginTop": 80 if row == 0 else 15,
                    "marginBottom": 120 if row == n_vars - 1 else 15,
                    "marginLeft": 140 if col == 0 else 15,
                    "marginRight": 15,
                },
                "title": {"text": variables[row] if row == 0 else "", "style": {"fontSize": "32px", "color": INK}},
                "xAxis": {
                    "categories": categories,
                    "labels": {
                        "enabled": row == n_vars - 1,
                        "style": {"fontSize": "18px", "color": INK_SOFT},
                        "rotation": -45,
                        "step": 2,
                    },
                    "title": {"text": ""},
                    "lineColor": INK_SOFT,
                    "tickColor": INK_SOFT,
                    "gridLineColor": GRID,
                },
                "yAxis": {
                    "title": {"text": variables[row] if col == 0 else "", "style": {"fontSize": "26px", "color": INK}},
                    "labels": {"enabled": col == 0, "style": {"fontSize": "22px", "color": INK_SOFT}},
                    "gridLineWidth": 1,
                    "gridLineColor": GRID,
                    "lineColor": INK_SOFT,
                    "tickColor": INK_SOFT,
                },
                "legend": {"enabled": False},
                "credits": {"enabled": False},
                "plotOptions": {
                    "column": {"grouping": True, "borderWidth": 0, "pointPadding": 0.05, "groupPadding": 0.1}
                },
                "series": [
                    {"name": species_names[i], "data": hist_series_data[i], "color": COLORS[i]} for i in range(3)
                ],
            }
        else:
            # Off-diagonal: scatter plot
            x_data = data[col]
            y_data = data[row]

            # Build scatter series by species
            scatter_series = []
            for sp_idx in range(3):
                sp_mask = [i for i, s in enumerate(species) if s == sp_idx]
                sp_points = [[float(x_data[i]), float(y_data[i])] for i in sp_mask]
                scatter_series.append(
                    {
                        "name": species_names[sp_idx],
                        "data": sp_points,
                        "color": COLORS[sp_idx],
                        "marker": {"radius": 8, "symbol": "circle"},
                        "opacity": 0.75,
                    }
                )

            chart_config = {
                "chart": {
                    "type": "scatter",
                    "backgroundColor": PAGE_BG,
                    "marginTop": 80 if row == 0 else 15,
                    "marginBottom": 120 if row == n_vars - 1 else 15,
                    "marginLeft": 140 if col == 0 else 15,
                    "marginRight": 15,
                },
                "title": {"text": variables[col] if row == 0 else "", "style": {"fontSize": "32px", "color": INK}},
                "xAxis": {
                    "labels": {"enabled": row == n_vars - 1, "style": {"fontSize": "20px", "color": INK_SOFT}},
                    "title": {"text": ""},
                    "gridLineWidth": 1,
                    "gridLineColor": GRID,
                    "lineColor": INK_SOFT,
                    "tickColor": INK_SOFT,
                },
                "yAxis": {
                    "title": {"text": variables[row] if col == 0 else "", "style": {"fontSize": "26px", "color": INK}},
                    "labels": {"enabled": col == 0, "style": {"fontSize": "22px", "color": INK_SOFT}},
                    "gridLineWidth": 1,
                    "gridLineColor": GRID,
                    "lineColor": INK_SOFT,
                    "tickColor": INK_SOFT,
                },
                "legend": {"enabled": False},
                "credits": {"enabled": False},
                "plotOptions": {"scatter": {"marker": {"radius": 10}, "states": {"hover": {"lineWidthPlus": 0}}}},
                "series": scatter_series,
            }

        # Convert config to JS
        config_js = json.dumps(chart_config)
        charts_js += f"Highcharts.chart('{container_id}', {config_js});\n"

# Create legend HTML positioned closer to matrix with larger text
legend_html = (
    """
<div style="position:absolute; left:50%; transform:translateX(-50%); bottom:60px; display:flex; gap:100px; font-size:52px; font-family:Arial,sans-serif; font-weight:500; color:"""
    + INK
    + """;">
"""
)
for i, name in enumerate(species_names):
    legend_html += f'<div style="display:flex; align-items:center; gap:24px;"><div style="width:44px; height:44px; background:{COLORS[i]}; border-radius:50%;"></div><span>{name}</span></div>'
legend_html += "</div>"

# Title with larger font for 3600x3600 canvas
title_html = f'<div style="position:absolute; top:15px; left:50%; transform:translateX(-50%); font-size:60px; font-family:Arial,sans-serif; font-weight:bold; color:{INK};">scatter-matrix · highcharts · anyplot.ai</div>'

# Full HTML - with title at top, matrix in middle, legend close to matrix
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    {title_html}
    <div style="position:relative; width:{canvas_size}px; height:{canvas_size}px; margin-top:90px;">
        {charts_html}
    </div>
    {legend_html}
    <script>
        {charts_js}
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save as plot-{THEME}.html for interactive viewing
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3850")  # Extra height for title and legend

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)  # Wait for all charts to render
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
