""" pyplots.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Simulated fatigue test results for steel specimens
np.random.seed(42)

# Generate realistic S-N curve data points with scatter
stress_levels = np.array([450, 400, 350, 320, 300, 280, 260, 250, 240, 230, 220, 210])

# Generate multiple test points per stress level with realistic scatter
cycles_data = []
stress_data = []

for stress in stress_levels:
    # Basquin equation: N = (S/A)^(-1/b)
    A = 1200  # Material constant
    b = 0.12  # Fatigue strength exponent
    N_mean = (stress / A) ** (-1 / b)

    # Add 2-4 test specimens per stress level with log-normal scatter
    n_samples = np.random.randint(2, 5)
    for _ in range(n_samples):
        scatter = np.exp(np.random.normal(0, 0.3))
        cycles_data.append(N_mean * scatter)
        stress_data.append(stress + np.random.normal(0, 5))

cycles = np.array(cycles_data)
stress = np.array(stress_data)

# Fit line using Basquin equation (log-linear fit)
log_cycles = np.log10(cycles)
log_stress = np.log10(stress)
coeffs = np.polyfit(log_cycles, log_stress, 1)
fit_cycles = np.logspace(2, 8, 100)
fit_stress = 10 ** (coeffs[0] * np.log10(fit_cycles) + coeffs[1])

# Material property reference values (typical for structural steel)
ultimate_strength = 500  # MPa
yield_strength = 350  # MPa
endurance_limit = 200  # MPa

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "style": {"fontFamily": "Arial, sans-serif"},
    "marginBottom": 150,
    "marginLeft": 150,
}

# Title
chart.options.title = {
    "text": "sn-curve-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# X-axis (logarithmic for cycles)
chart.options.x_axis = {
    "type": "logarithmic",
    "title": {"text": "Number of Cycles to Failure (N)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}, "rotation": 0},
    "min": 100,
    "max": 100000000,
    "gridLineWidth": 1,
    "gridLineColor": "#cccccc",
    "gridLineDashStyle": "Dash",
    "tickInterval": 1,  # Show only major ticks (powers of 10)
}

# Y-axis (logarithmic for stress)
chart.options.y_axis = {
    "type": "logarithmic",
    "title": {"text": "Stress Amplitude (MPa)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "min": 150,
    "max": 600,
    "gridLineWidth": 1,
    "gridLineColor": "#cccccc",
    "gridLineDashStyle": "Dash",
    "plotLines": [
        {
            "value": ultimate_strength,
            "color": "#E53935",
            "width": 4,
            "dashStyle": "Dash",
            "label": {
                "text": f"Ultimate Strength ({ultimate_strength} MPa)",
                "align": "right",
                "style": {"fontSize": "24px", "color": "#E53935", "fontWeight": "bold"},
                "x": -10,
            },
            "zIndex": 3,
        },
        {
            "value": yield_strength,
            "color": "#FB8C00",
            "width": 4,
            "dashStyle": "Dash",
            "label": {
                "text": f"Yield Strength ({yield_strength} MPa)",
                "align": "right",
                "style": {"fontSize": "24px", "color": "#FB8C00", "fontWeight": "bold"},
                "x": -10,
            },
            "zIndex": 3,
        },
        {
            "value": endurance_limit,
            "color": "#43A047",
            "width": 4,
            "dashStyle": "Dash",
            "label": {
                "text": f"Endurance Limit ({endurance_limit} MPa)",
                "align": "right",
                "style": {"fontSize": "24px", "color": "#43A047", "fontWeight": "bold"},
                "x": -10,
            },
            "zIndex": 3,
        },
    ],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 80,
}

# Plot options
chart.options.plot_options = {
    "scatter": {
        "marker": {"radius": 14, "symbol": "circle", "lineWidth": 2, "lineColor": "#ffffff"},
        "states": {"hover": {"enabled": False}},
    },
    "line": {"lineWidth": 5, "marker": {"enabled": False}, "states": {"hover": {"enabled": False}}},
}

# Add test data scatter series
scatter_series = ScatterSeries()
scatter_series.data = [[float(c), float(s)] for c, s in zip(cycles, stress, strict=True)]
scatter_series.name = "Test Data"
scatter_series.color = "#306998"
scatter_series.marker = {"fillColor": "#306998", "fillOpacity": 0.7}
chart.add_series(scatter_series)

# Add fitted S-N curve line series
fit_series = LineSeries()
fit_series.data = [[float(c), float(s)] for c, s in zip(fit_cycles, fit_stress, strict=True)]
fit_series.name = "Basquin Fit"
fit_series.color = "#FFD43B"
chart.add_series(fit_series)

# Add annotation series for fatigue regions (using invisible points with data labels)
chart.options.annotations = [
    {
        "labels": [
            {
                "point": {"x": 500, "y": 420, "xAxis": 0, "yAxis": 0},
                "text": "Low-Cycle<br>Fatigue",
                "style": {"fontSize": "28px", "color": "#555555", "fontStyle": "italic"},
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "shadow": False,
            },
            {
                "point": {"x": 100000, "y": 280, "xAxis": 0, "yAxis": 0},
                "text": "High-Cycle<br>Fatigue",
                "style": {"fontSize": "28px", "color": "#555555", "fontStyle": "italic"},
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "shadow": False,
            },
            {
                "point": {"x": 50000000, "y": 180, "xAxis": 0, "yAxis": 0},
                "text": "Infinite Life",
                "style": {"fontSize": "28px", "color": "#555555", "fontStyle": "italic"},
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "shadow": False,
            },
        ],
        "labelOptions": {"shape": "rect"},
    }
]

# Credits
chart.options.credits = {"enabled": False}

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
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")  # Slightly taller to capture full chart

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Find the container element and take screenshot of just that element
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>sn-curve-basic · highcharts · pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/annotations.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
