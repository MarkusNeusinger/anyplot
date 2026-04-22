""" pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: highcharts unknown | Python 3.14.3
Quality: 89/100 | Created: 2026-03-15
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
from highcharts_core.utility_classes.javascript_functions import CallbackFunction
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: 15 RCTs comparing drug vs placebo (log odds ratios)
np.random.seed(42)

studies = [
    "Adams et al. 2017",
    "Baker et al. 2018",
    "Chen et al. 2018",
    "Davis et al. 2019",
    "Evans et al. 2019",
    "Fischer et al. 2020",
    "Garcia et al. 2020",
    "Huang et al. 2020",
    "Ibrahim et al. 2021",
    "Jones et al. 2021",
    "Kim et al. 2022",
    "Lee et al. 2022",
    "Morales et al. 2023",
    "Nakamura et al. 2023",
    "Olsen et al. 2024",
]

# Standard errors (smaller = more precise = larger study)
std_errors = np.array([0.08, 0.12, 0.15, 0.10, 0.22, 0.09, 0.18, 0.25, 0.14, 0.20, 0.11, 0.30, 0.16, 0.28, 0.35])

# Effect sizes (log odds ratios) - slight asymmetry to show publication bias
effect_sizes = np.array(
    [-0.42, -0.35, -0.55, -0.38, -0.15, -0.40, -0.28, -0.08, -0.45, -0.20, -0.36, 0.05, -0.32, -0.50, -0.65]
)

# Pooled effect (inverse-variance weighted)
weights = 1.0 / std_errors**2
pooled_effect = np.sum(effect_sizes * weights) / np.sum(weights)

# SE range for funnel lines
se_max = 0.40
se_values = np.linspace(0, se_max, 50)

# Pseudo 95% CI funnel boundaries
funnel_left = [pooled_effect - 1.96 * se for se in se_values]
funnel_right = [pooled_effect + 1.96 * se for se in se_values]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafbfc",
    "marginLeft": 200,
    "marginRight": 100,
    "marginBottom": 200,
    "marginTop": 150,
    "style": {"fontFamily": "'Segoe UI', Arial, sans-serif"},
}

chart.options.title = {
    "text": "funnel-meta-analysis \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold", "color": "#1a1a2e"},
}

chart.options.subtitle = {
    "text": "Drug vs Placebo \u2014 15 Randomized Controlled Trials",
    "style": {"fontSize": "32px", "color": "#555555"},
}

# X-axis: effect size with plotLines (Highcharts-distinctive feature)
chart.options.x_axis = {
    "title": {
        "text": "Log Odds Ratio",
        "style": {"fontSize": "36px", "fontWeight": "bold", "color": "#333333"},
        "margin": 25,
    },
    "labels": {"style": {"fontSize": "26px", "color": "#444444"}},
    "plotLines": [
        {
            "value": float(pooled_effect),
            "color": "#306998",
            "width": 4,
            "zIndex": 3,
            "label": {
                "text": f"Pooled Effect ({pooled_effect:.2f})",
                "style": {"fontSize": "30px", "color": "#306998", "fontWeight": "bold"},
                "rotation": 0,
                "align": "left",
                "verticalAlign": "top",
                "y": 15,
                "x": 10,
            },
        },
        {
            "value": 0,
            "color": "#888888",
            "width": 3,
            "dashStyle": "Dash",
            "zIndex": 2,
            "label": {
                "text": "Null Effect (0)",
                "style": {"fontSize": "28px", "color": "#888888", "fontWeight": "bold"},
                "rotation": 0,
                "align": "right",
                "verticalAlign": "top",
                "y": 15,
                "x": -10,
            },
        },
    ],
    "gridLineWidth": 0,
    "lineWidth": 2,
    "lineColor": "#cccccc",
    "min": -1.1,
    "max": 0.4,
    "tickInterval": 0.2,
}

# Y-axis: standard error (inverted) with plotBands for precision zones
chart.options.y_axis = {
    "title": {
        "text": "Standard Error",
        "style": {"fontSize": "36px", "fontWeight": "bold", "color": "#333333"},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "26px", "color": "#444444"}},
    "reversed": True,
    "min": 0,
    "max": 0.40,
    "gridLineWidth": 1,
    "gridLineColor": "#e8e8e8",
    "gridLineDashStyle": "Dot",
    "tickInterval": 0.05,
    "lineWidth": 2,
    "lineColor": "#cccccc",
    "plotBands": [
        {
            "from": 0,
            "to": 0.12,
            "color": "rgba(48, 105, 152, 0.07)",
            "label": {
                "text": "High precision",
                "style": {"fontSize": "28px", "color": "#7a9bb5", "fontWeight": "bold"},
                "align": "right",
                "x": -15,
            },
        },
        {
            "from": 0.28,
            "to": 0.40,
            "color": "rgba(196, 119, 60, 0.05)",
            "label": {
                "text": "Low precision",
                "style": {"fontSize": "28px", "color": "#c4976a", "fontWeight": "bold"},
                "align": "right",
                "x": -15,
            },
        },
    ],
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

chart.options.plot_options = {"series": {"animation": False}, "line": {"lineWidth": 3, "marker": {"enabled": False}}}

# Left funnel boundary using LineSeries (idiomatic Highcharts)
left_line_data = [[float(funnel_left[i]), float(se_values[i])] for i in range(len(se_values))]

left_series = LineSeries()
left_series.data = left_line_data
left_series.name = "95% CI Left"
left_series.color = "#5a8aa8"
left_series.line_width = 3
left_series.dash_style = "ShortDash"
left_series.enable_mouse_tracking = False
left_series.show_in_legend = False

chart.add_series(left_series)

# Right funnel boundary using LineSeries
right_line_data = [[float(funnel_right[i]), float(se_values[i])] for i in range(len(se_values))]

right_series = LineSeries()
right_series.data = right_line_data
right_series.name = "95% CI Right"
right_series.color = "#5a8aa8"
right_series.line_width = 3
right_series.dash_style = "ShortDash"
right_series.enable_mouse_tracking = False
right_series.show_in_legend = False

chart.add_series(right_series)

# Study points with marker size varying by inverse-variance weight
weight_normalized = weights / weights.max()
marker_radii = 14 + 16 * weight_normalized

# Color studies by precision: high-precision (low SE) in deep blue, low-precision in warm amber
# This creates a meaningful visual gradient and tells the publication bias story
se_normalized = (std_errors - std_errors.min()) / (std_errors.max() - std_errors.min())


# Interpolate between deep blue (#306998) and warm amber (#c4773c)
study_data = []
for i in range(len(studies)):
    t = float(se_normalized[i])
    r, g, b = int(48 + t * 148), int(105 + t * 14), int(152 - t * 92)
    fill_color = f"#{r:02x}{g:02x}{b:02x}"
    study_data.append(
        {
            "x": float(effect_sizes[i]),
            "y": float(std_errors[i]),
            "marker": {
                "radius": int(marker_radii[i]),
                "lineWidth": 3,
                "lineColor": "#ffffff",
                "fillColor": fill_color,
                "symbol": "circle",
            },
            "name": studies[i],
        }
    )

study_series = ScatterSeries()
study_series.data = study_data
study_series.name = "Studies"
study_series.color = "#306998"
study_series.z_index = 5

chart.add_series(study_series)

# Custom tooltip formatter using CallbackFunction (Highcharts-distinctive)
tooltip_formatter = CallbackFunction.from_js_literal(
    """function() {
        if (!this.point.name) return false;
        return '<div style="padding:8px;font-size:22px;line-height:1.6">' +
            '<b style="font-size:24px;color:#306998">' + this.point.name + '</b><br/>' +
            'Log OR: <b>' + this.x.toFixed(3) + '</b><br/>' +
            'SE: <b>' + this.y.toFixed(3) + '</b><br/>' +
            'Weight: <b>' + (1 / (this.y * this.y)).toFixed(1) + '</b>' +
            '</div>';
    }"""
)

chart.options.tooltip = {
    "useHTML": True,
    "formatter": tooltip_formatter,
    "backgroundColor": "rgba(255, 255, 255, 0.96)",
    "borderWidth": 2,
    "borderColor": "#306998",
    "borderRadius": 8,
    "shadow": {"offsetX": 2, "offsetY": 2, "opacity": 0.15, "width": 4},
}

# Load Highcharts JS for inline embedding
highcharts_js_path = Path(__file__).resolve().parents[3] / "node_modules" / "highcharts" / "highcharts.js"
if highcharts_js_path.exists():
    highcharts_js = highcharts_js_path.read_text(encoding="utf-8")
else:
    highcharts_url = "https://code.highcharts.com/highcharts.js"
    req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
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

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4900,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
