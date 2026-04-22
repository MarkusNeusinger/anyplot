""" pyplots.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Simulated differential gene expression results
np.random.seed(42)
n_genes = 500

# Generate log2 fold changes (normally distributed around 0)
log2_fc = np.random.normal(0, 1.5, n_genes)

# Generate p-values (most non-significant, some significant)
# Use beta distribution to get realistic p-value distribution
pvalues = np.random.beta(0.5, 5, n_genes)

# Add some truly significant genes with large fold changes
n_sig_up = 30
n_sig_down = 25

# Significant upregulated genes
log2_fc[:n_sig_up] = np.random.uniform(1.5, 4, n_sig_up)
pvalues[:n_sig_up] = np.random.uniform(1e-10, 0.001, n_sig_up)

# Significant downregulated genes
log2_fc[n_sig_up : n_sig_up + n_sig_down] = np.random.uniform(-4, -1.5, n_sig_down)
pvalues[n_sig_up : n_sig_up + n_sig_down] = np.random.uniform(1e-10, 0.001, n_sig_down)

# Calculate -log10(p-value)
neg_log10_p = -np.log10(pvalues)

# Classify points
# Significant: p-value < 0.05 AND |log2FC| > 1
p_threshold = 0.05  # -log10(0.05) ≈ 1.3
fc_threshold = 1.0  # |log2FC| > 1 means 2-fold change

sig_up = (pvalues < p_threshold) & (log2_fc > fc_threshold)
sig_down = (pvalues < p_threshold) & (log2_fc < -fc_threshold)
not_sig = ~(sig_up | sig_down)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 200,
    "marginLeft": 220,
    "marginRight": 280,
    "marginTop": 150,
}

# Title
chart.options.title = {
    "text": "volcano-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Differential Gene Expression Analysis", "style": {"fontSize": "32px"}}

# X-axis
chart.options.x_axis = {
    "title": {"text": "log₂(Fold Change)", "style": {"fontSize": "36px", "fontWeight": "bold"}, "margin": 25},
    "labels": {"style": {"fontSize": "26px"}, "y": 40},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "tickLength": 15,
    "plotLines": [
        {"value": -fc_threshold, "color": "#555555", "dashStyle": "Dash", "width": 4, "zIndex": 3},
        {"value": fc_threshold, "color": "#555555", "dashStyle": "Dash", "width": 4, "zIndex": 3},
    ],
}

# Y-axis
neg_log10_threshold = -np.log10(p_threshold)
chart.options.y_axis = {
    "title": {"text": "-log₁₀(p-value)", "style": {"fontSize": "36px", "fontWeight": "bold"}, "margin": 25},
    "labels": {"style": {"fontSize": "26px"}, "x": -15},
    "min": 0,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "tickLength": 15,
    "plotLines": [{"value": neg_log10_threshold, "color": "#555555", "dashStyle": "Dash", "width": 4, "zIndex": 3}],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 80,
    "itemStyle": {"fontSize": "28px"},
}

# Plot options for scatter
chart.options.plot_options = {
    "scatter": {
        "marker": {"radius": 10, "states": {"hover": {"enabled": True, "lineColor": "#000000"}}},
        "states": {"inactive": {"opacity": 1}},
    }
}

# Create series for each category
# Non-significant points (gray)
series_ns = ScatterSeries()
series_ns.name = f"Not Significant ({np.sum(not_sig)})"
series_ns.data = [[float(x), float(y)] for x, y in zip(log2_fc[not_sig], neg_log10_p[not_sig], strict=True)]
series_ns.color = "#999999"
series_ns.marker = {"radius": 8, "symbol": "circle"}
chart.add_series(series_ns)

# Significant downregulated (blue - Python Blue)
series_down = ScatterSeries()
series_down.name = f"Down-regulated ({np.sum(sig_down)})"
series_down.data = [[float(x), float(y)] for x, y in zip(log2_fc[sig_down], neg_log10_p[sig_down], strict=True)]
series_down.color = "#306998"
series_down.marker = {"radius": 12, "symbol": "circle"}
chart.add_series(series_down)

# Significant upregulated (using a distinct color - orange/gold for contrast)
series_up = ScatterSeries()
series_up.name = f"Up-regulated ({np.sum(sig_up)})"
series_up.data = [[float(x), float(y)] for x, y in zip(log2_fc[sig_up], neg_log10_p[sig_up], strict=True)]
series_up.color = "#E07B00"
series_up.marker = {"radius": 12, "symbol": "circle"}
chart.add_series(series_up)

# Credits
chart.options.credits = {"enabled": False}

# Annotations for threshold labels
# Get max y value for positioning
y_max = float(np.max(neg_log10_p)) + 0.3

chart.options.annotations = [
    {
        "labels": [
            {
                "point": {"x": -fc_threshold, "y": y_max, "xAxis": 0, "yAxis": 0},
                "text": "FC = -1",
                "style": {"fontSize": "28px", "color": "#555555", "fontWeight": "bold"},
                "backgroundColor": "rgba(255, 255, 255, 0.9)",
                "borderWidth": 0,
                "y": -15,
            },
            {
                "point": {"x": fc_threshold, "y": y_max, "xAxis": 0, "yAxis": 0},
                "text": "FC = +1",
                "style": {"fontSize": "28px", "color": "#555555", "fontWeight": "bold"},
                "backgroundColor": "rgba(255, 255, 255, 0.9)",
                "borderWidth": 0,
                "y": -15,
            },
            {
                "point": {"x": 4.5, "y": neg_log10_threshold, "xAxis": 0, "yAxis": 0},
                "text": "p = 0.05",
                "style": {"fontSize": "28px", "color": "#555555", "fontWeight": "bold"},
                "backgroundColor": "rgba(255, 255, 255, 0.9)",
                "borderWidth": 0,
                "y": -25,
            },
        ],
        "labelOptions": {"shape": "rect"},
    }
]

# Download Highcharts JS and annotations module
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

annotations_url = "https://code.highcharts.com/modules/annotations.js"
with urllib.request.urlopen(annotations_url, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; padding:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save as plot.html for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    # Use CDN for the HTML file since it will be viewed in a browser
    html_interactive = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/annotations.js"></script>
</head>
<body style="margin:0; padding:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(html_interactive)

# Setup Chrome for headless screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
