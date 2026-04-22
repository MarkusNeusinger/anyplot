""" pyplots.ai
heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
Library: highcharts unknown | Python 3.14.3
Quality: 90/100 | Updated: 2026-03-06
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Simulated rainflow counting matrix from variable-amplitude loading
np.random.seed(42)

n_amp_bins = 20
n_mean_bins = 20

# Bin centers in MPa
amplitude_bins = np.linspace(10, 200, n_amp_bins)
mean_bins = np.linspace(-50, 250, n_mean_bins)

# Generate realistic rainflow matrix
# Most cycles at low amplitude, centered around mean ~100 MPa
amp_grid, mean_grid = np.meshgrid(amplitude_bins, mean_bins, indexing="ij")

# Exponential decay with amplitude (low amplitude = many cycles)
amp_factor = np.exp(-0.025 * amp_grid)

# Gaussian distribution around mean ~100 MPa
mean_factor = np.exp(-0.5 * ((mean_grid - 100) / 60) ** 2)

# Combined cycle counts
raw_counts = amp_factor * mean_factor * 5000
raw_counts += np.random.exponential(scale=raw_counts * 0.15 + 1)
cycle_counts = np.round(raw_counts).astype(int)
cycle_counts = np.clip(cycle_counts, 0, None)

# Set very low counts to zero for sparsity (realistic for high-amplitude regions)
cycle_counts[cycle_counts < 3] = 0

# Amplitude labels (y-axis) and mean labels (x-axis)
amp_labels = [f"{v:.0f}" for v in amplitude_bins]
mean_labels = [f"{v:.0f}" for v in mean_bins]

# Build heatmap data: [x_index (mean), y_index (amplitude), value or None]
heatmap_data = []
max_count = 0
for y_idx in range(n_amp_bins):
    for x_idx in range(n_mean_bins):
        val = int(cycle_counts[y_idx, x_idx])
        if val > max_count:
            max_count = val
        heatmap_data.append([x_idx, y_idx, val if val > 0 else None])

# Build chart using highcharts-core Python wrapper
chart = Chart(container="container")
chart.options = HighchartsOptions.from_dict(
    {
        "chart": {
            "type": "heatmap",
            "width": 4800,
            "height": 2700,
            "backgroundColor": "#fafafa",
            "marginTop": 180,
            "marginBottom": 200,
            "marginRight": 380,
            "marginLeft": 320,
            "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
        },
        "title": {
            "text": "heatmap-rainflow \u00b7 highcharts \u00b7 pyplots.ai",
            "style": {"fontSize": "52px", "fontWeight": "600", "color": "#2c3e50"},
            "y": 30,
        },
        "subtitle": {
            "text": "Rainflow cycle counting matrix \u2014 low-amplitude cycles near 100 MPa mean dominate the fatigue spectrum",
            "style": {"fontSize": "30px", "fontWeight": "normal", "color": "#7f8c8d"},
            "y": 80,
        },
        "xAxis": {
            "categories": mean_labels,
            "title": {
                "text": "Cycle Mean (MPa)",
                "style": {"fontSize": "34px", "fontWeight": "600", "color": "#34495e"},
                "margin": 20,
            },
            "labels": {"style": {"fontSize": "28px", "color": "#34495e"}, "rotation": 315, "y": 30},
            "lineWidth": 0,
            "tickLength": 0,
        },
        "yAxis": {
            "categories": amp_labels,
            "title": {
                "text": "Cycle Amplitude (MPa)",
                "style": {"fontSize": "34px", "fontWeight": "600", "color": "#34495e"},
                "margin": 20,
            },
            "labels": {"style": {"fontSize": "28px", "color": "#34495e"}},
            "reversed": False,
            "lineWidth": 0,
            "gridLineWidth": 0,
        },
        "colorAxis": {
            "min": 1,
            "max": int(max_count),
            "type": "logarithmic",
            "stops": [
                [0, "#440154"],
                [0.12, "#482878"],
                [0.25, "#3e4989"],
                [0.37, "#31688e"],
                [0.50, "#26828e"],
                [0.62, "#1f9e89"],
                [0.75, "#35b779"],
                [0.87, "#6ece58"],
                [1, "#fde725"],
            ],
            "labels": {"style": {"fontSize": "28px", "color": "#34495e"}},
        },
        "legend": {
            "title": {"text": "Cycle Count", "style": {"fontSize": "28px", "fontWeight": "600", "color": "#34495e"}},
            "align": "right",
            "layout": "vertical",
            "verticalAlign": "middle",
            "symbolHeight": 900,
            "symbolWidth": 36,
            "itemStyle": {"fontSize": "24px", "color": "#34495e"},
            "x": -40,
            "margin": 40,
        },
        "tooltip": {
            "style": {"fontSize": "30px"},
            "headerFormat": "",
            "pointFormat": (
                "Amplitude: <b>{series.yAxis.categories.(point.y)} MPa</b><br>"
                "Mean: <b>{series.xAxis.categories.(point.x)} MPa</b><br>"
                "Cycles: <b>{point.value}</b>"
            ),
        },
        "credits": {"enabled": False},
        "plotOptions": {"heatmap": {"colsize": 1, "rowsize": 1}},
        "series": [
            {
                "type": "heatmap",
                "name": "Cycle Count",
                "data": heatmap_data,
                "borderWidth": 2,
                "borderColor": "#fafafa",
                "nullColor": "#f0f0f0",
            }
        ],
    }
)

# Generate chart JS literal via highcharts-core wrapper
js_literal = chart.to_js_literal()

# Download Highcharts JS and heatmap module with retry
urls = {
    "highcharts": "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js",
    "heatmap": "https://cdn.jsdelivr.net/npm/highcharts/modules/heatmap.js",
}
scripts = {}
for name, url in urls.items():
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                scripts[name] = response.read().decode("utf-8")
            break
        except urllib.error.HTTPError:
            time.sleep(2 * (attempt + 1))
    else:
        raise RuntimeError(f"Failed to download {url}")

highcharts_js = scripts["highcharts"]
heatmap_js = scripts["heatmap"]

# Generate HTML with inline scripts and renderer annotation for data storytelling
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:#fafafa;">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>
        {js_literal}
    </script>
    <script>
        // Add annotation highlighting the dominant fatigue region
        // (separate DOMContentLoaded ensures chart is created first)
        document.addEventListener('DOMContentLoaded', function() {{
            var ch = Highcharts.charts[Highcharts.charts.length - 1];
            if (ch) {{
                ch.renderer.label(
                    '\\u25B6 Peak region: low-amplitude cycles near<br>' +
                    '\\u2003 100 MPa mean stress dominate fatigue damage',
                    ch.plotLeft + ch.plotWidth * 0.55,
                    ch.plotTop + ch.plotHeight * 0.78
                ).css({{
                    fontSize: '28px',
                    color: '#333',
                    fontStyle: 'italic',
                    lineHeight: '40px'
                }}).attr({{
                    fill: 'rgba(255, 255, 255, 0.93)',
                    stroke: '#888',
                    'stroke-width': 1.5,
                    padding: 18,
                    r: 8,
                    zIndex: 5
                }}).add();
            }}
        }});
    </script>
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot using headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2840")
chrome_options.add_argument("--force-device-scale-factor=1")
chrome_options.add_argument("--hide-scrollbars")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(4800, 2840)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
