""" pyplots.ai
bland-altman-basic: Bland-Altman Agreement Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
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


# Data: Simulated blood pressure readings from two sphygmomanometers
np.random.seed(42)
n_subjects = 80

# True blood pressure values (systolic, mmHg)
true_bp = np.random.normal(130, 15, n_subjects)

# Method 1: Reference device (small measurement error)
method1 = true_bp + np.random.normal(0, 3, n_subjects)

# Method 2: New device being validated (slightly higher readings with more variability)
method2 = true_bp + np.random.normal(2, 5, n_subjects)

# Bland-Altman calculations
mean_values = (method1 + method2) / 2
differences = method1 - method2
mean_diff = np.mean(differences)
std_diff = np.std(differences, ddof=1)
upper_loa = mean_diff + 1.96 * std_diff
lower_loa = mean_diff - 1.96 * std_diff

# X-axis range for reference lines
x_min = np.min(mean_values)
x_max = np.max(mean_values)
x_padding = (x_max - x_min) * 0.05
line_x_min = x_min - x_padding
line_x_max = x_max + x_padding

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginRight": 250,
    "marginBottom": 200,
    "spacingBottom": 50,
}

# Title
chart.options.title = {
    "text": "bland-altman-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Axes
chart.options.x_axis = {
    "title": {"text": "Mean of Two Methods (mmHg)", "style": {"fontSize": "36px"}, "offset": 20},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "min": float(line_x_min),
    "max": float(line_x_max),
}

chart.options.y_axis = {
    "title": {"text": "Difference (Method 1 - Method 2) (mmHg)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "plotLines": [
        {
            "value": float(mean_diff),
            "color": "#306998",
            "width": 4,
            "zIndex": 3,
            "label": {
                "text": f"Mean: {mean_diff:.2f}",
                "align": "right",
                "style": {"fontSize": "28px", "fontWeight": "bold", "color": "#306998"},
            },
        },
        {
            "value": float(upper_loa),
            "color": "#DC2626",
            "width": 3,
            "dashStyle": "Dash",
            "zIndex": 3,
            "label": {
                "text": f"+1.96 SD: {upper_loa:.2f}",
                "align": "right",
                "style": {"fontSize": "28px", "fontWeight": "bold", "color": "#DC2626"},
            },
        },
        {
            "value": float(lower_loa),
            "color": "#DC2626",
            "width": 3,
            "dashStyle": "Dash",
            "zIndex": 3,
            "label": {
                "text": f"−1.96 SD: {lower_loa:.2f}",
                "align": "right",
                "style": {"fontSize": "28px", "fontWeight": "bold", "color": "#DC2626"},
            },
        },
    ],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px"},
    "align": "right",
    "verticalAlign": "top",
    "y": 80,
    "x": -50,
}

# Plot options
chart.options.plot_options = {
    "scatter": {
        "marker": {"radius": 14, "fillColor": "rgba(48, 105, 152, 0.6)", "lineWidth": 2, "lineColor": "#306998"}
    }
}

# Add scatter series for data points
scatter_series = ScatterSeries()
scatter_series.data = [{"x": float(x), "y": float(y)} for x, y in zip(mean_values, differences, strict=True)]
scatter_series.name = "Paired Observations"
scatter_series.color = "#306998"
chart.add_series(scatter_series)

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline script
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
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
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
