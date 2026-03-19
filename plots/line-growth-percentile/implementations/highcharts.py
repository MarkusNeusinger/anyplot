""" pyplots.ai
line-growth-percentile: Pediatric Growth Chart with Percentile Curves
Library: highcharts unknown | Python 3.14.3
Quality: 91/100 | Created: 2026-03-19
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


# Data - WHO-style weight-for-age reference for boys, 0-36 months
np.random.seed(42)
age_months = np.arange(0, 37, 1)

# Realistic weight-for-age percentile curves (boys, 0-36 months, kg)
median = 3.3 + 0.7 * age_months - 0.008 * age_months**2 + 0.00004 * age_months**3
spread = 0.4 + 0.03 * age_months

percentiles = {
    "P3": median - 1.88 * spread,
    "P10": median - 1.28 * spread,
    "P25": median - 0.67 * spread,
    "P50": median,
    "P75": median + 0.67 * spread,
    "P90": median + 1.28 * spread,
    "P97": median + 1.88 * spread,
}

# Individual patient data - boy tracking near P25-P40 range (realistic trajectory)
patient_ages = np.array([0, 1, 2, 4, 6, 9, 12, 15, 18, 24, 30, 36])
patient_weights = np.array([3.3, 3.8, 4.5, 5.8, 7.0, 8.7, 10.3, 11.8, 13.1, 15.5, 17.5, 19.0])

# Band colors - graduated blue tones (darker at extremes, lighter near median)
band_colors = [
    {"low": "P3", "high": "P10", "color": "rgba(30, 80, 140, 0.30)"},
    {"low": "P10", "high": "P25", "color": "rgba(48, 105, 165, 0.20)"},
    {"low": "P25", "high": "P75", "color": "rgba(70, 140, 200, 0.10)"},
    {"low": "P75", "high": "P90", "color": "rgba(48, 105, 165, 0.20)"},
    {"low": "P90", "high": "P97", "color": "rgba(30, 80, 140, 0.30)"},
]

# Compute y-axis max from data
y_max = float(np.ceil(percentiles["P97"].max() + 0.5))

# Chart setup
font_family = "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"

chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafbfc",
    "marginBottom": 200,
    "marginLeft": 220,
    "marginRight": 320,
    "marginTop": 160,
    "style": {"fontFamily": font_family},
}

chart.options.title = {
    "text": "Boys Weight-for-Age · line-growth-percentile · highcharts · pyplots.ai",
    "style": {"fontSize": "46px", "fontWeight": "700", "color": "#1a2a3a", "fontFamily": font_family},
    "margin": 30,
}

chart.options.subtitle = {
    "text": "WHO Growth Standards, Birth to 36 Months",
    "style": {"fontSize": "30px", "color": "#5a6a7a", "fontWeight": "400", "fontFamily": font_family},
}

# X-axis
chart.options.x_axis = {
    "title": {
        "text": "Age (months)",
        "style": {"fontSize": "34px", "color": "#3a4a5a", "fontFamily": font_family},
        "margin": 24,
    },
    "labels": {"style": {"fontSize": "26px", "color": "#4a5a6a", "fontFamily": font_family}},
    "tickInterval": 3,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.05)",
    "gridLineDashStyle": "Dot",
    "lineColor": "#c0c8d0",
    "lineWidth": 2,
    "tickColor": "#c0c8d0",
    "tickWidth": 1,
    "tickLength": 8,
    "min": 0,
    "max": 36,
}

# Y-axis with tight range
chart.options.y_axis = {
    "title": {
        "text": "Weight (kg)",
        "style": {"fontSize": "34px", "color": "#3a4a5a", "fontFamily": font_family},
        "margin": 24,
    },
    "labels": {"style": {"fontSize": "26px", "color": "#4a5a6a", "fontFamily": font_family}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.05)",
    "gridLineDashStyle": "Dot",
    "lineColor": "#c0c8d0",
    "lineWidth": 2,
    "min": 0,
    "max": y_max,
    "tickInterval": 2,
    "plotBands": [
        {
            "from": float(percentiles["P25"][-1]),
            "to": float(percentiles["P75"][-1]),
            "color": "rgba(48, 105, 152, 0.03)",
            "label": {
                "text": "Normal Range",
                "align": "left",
                "x": 10,
                "style": {
                    "fontSize": "20px",
                    "color": "rgba(48, 105, 152, 0.4)",
                    "fontStyle": "italic",
                    "fontFamily": font_family,
                },
            },
        }
    ],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -60,
    "y": 60,
    "floating": True,
    "backgroundColor": "rgba(255, 255, 255, 0.92)",
    "borderRadius": 8,
    "borderWidth": 0,
    "shadow": {"enabled": True, "color": "rgba(0,0,0,0.06)", "offsetX": 1, "offsetY": 2, "width": 6},
    "itemStyle": {"fontSize": "26px", "fontWeight": "normal", "color": "#3a4a5a", "fontFamily": font_family},
    "itemMarginBottom": 10,
    "symbolWidth": 40,
    "symbolHeight": 16,
    "symbolRadius": 4,
}

chart.options.plot_options = {
    "arearange": {
        "fillOpacity": 1.0,
        "lineWidth": 0,
        "marker": {"enabled": False},
        "enableMouseTracking": False,
        "states": {"hover": {"enabled": False}},
    },
    "line": {"lineWidth": 4, "marker": {"enabled": False}},
    "spline": {"lineWidth": 4, "marker": {"enabled": True, "radius": 10}},
    "series": {"animation": False},
}

chart.options.tooltip = {"enabled": False}

chart.options.credits = {"enabled": False}

# Build series
series_data = []

# Percentile bands as arearange series
for band in band_colors:
    low_key = band["low"]
    high_key = band["high"]
    low_vals = percentiles[low_key]
    high_vals = percentiles[high_key]
    data = [
        [int(a), round(float(lo), 2), round(float(hi), 2)]
        for a, lo, hi in zip(age_months, low_vals, high_vals, strict=True)
    ]
    series_data.append(
        {
            "name": f"{low_key}–{high_key}",
            "type": "arearange",
            "data": data,
            "color": band["color"],
            "fillOpacity": 1.0,
            "showInLegend": False,
            "zIndex": 0,
        }
    )

# Percentile lines with staggered right-margin labels to avoid cramping
percentile_styles = {
    "P3": {"color": "rgba(30, 80, 140, 0.50)", "dashStyle": "Dash", "lineWidth": 2},
    "P10": {"color": "rgba(30, 80, 140, 0.40)", "dashStyle": "ShortDash", "lineWidth": 2},
    "P25": {"color": "rgba(48, 105, 165, 0.35)", "dashStyle": "ShortDot", "lineWidth": 2},
    "P50": {"color": "#1e507a", "dashStyle": "Solid", "lineWidth": 6},
    "P75": {"color": "rgba(48, 105, 165, 0.35)", "dashStyle": "ShortDot", "lineWidth": 2},
    "P90": {"color": "rgba(30, 80, 140, 0.40)", "dashStyle": "ShortDash", "lineWidth": 2},
    "P97": {"color": "rgba(30, 80, 140, 0.50)", "dashStyle": "Dash", "lineWidth": 2},
}

# Stagger label y-offsets to prevent overlap where curves converge
label_y_offsets = {"P3": 8, "P10": 4, "P25": 0, "P50": 0, "P75": 0, "P90": -4, "P97": -8}

for pname, pvals in percentiles.items():
    style = percentile_styles[pname]
    line_data = [[int(a), round(float(v), 2)] for a, v in zip(age_months, pvals, strict=True)]
    show_legend = pname == "P50"
    is_median = pname == "P50"
    series_data.append(
        {
            "name": "50th Percentile (Median)" if is_median else pname,
            "type": "line",
            "data": line_data,
            "color": style["color"],
            "dashStyle": style["dashStyle"],
            "lineWidth": style["lineWidth"],
            "marker": {"enabled": False},
            "showInLegend": show_legend,
            "zIndex": 3 if is_median else 1,
            "dataLabels": {
                "enabled": True,
                "align": "left",
                "x": 15,
                "y": label_y_offsets[pname],
                "format": pname,
                "style": {
                    "fontSize": "24px",
                    "color": "#1e507a" if is_median else "#2a6090",
                    "fontWeight": "bold" if is_median else "600",
                    "textOutline": "4px white",
                    "fontFamily": font_family,
                },
                "filter": {"property": "x", "operator": "==", "value": 36},
            },
        }
    )

# Patient data overlay with per-point labels at key moments
patient_data = []
for a, w in zip(patient_ages, patient_weights, strict=True):
    point = {"x": int(a), "y": float(w)}
    if a == 0:
        point["dataLabels"] = {
            "enabled": True,
            "format": "Birth<br>{y:.1f} kg",
            "align": "right",
            "x": -15,
            "y": -10,
            "style": {
                "fontSize": "22px",
                "color": "#c04010",
                "fontWeight": "bold",
                "textOutline": "3px white",
                "fontFamily": font_family,
            },
        }
    elif a == 36:
        point["dataLabels"] = {
            "enabled": True,
            "format": "36 mo<br>{y:.1f} kg",
            "align": "left",
            "x": 15,
            "y": -10,
            "style": {
                "fontSize": "22px",
                "color": "#c04010",
                "fontWeight": "bold",
                "textOutline": "3px white",
                "fontFamily": font_family,
            },
        }
    patient_data.append(point)

series_data.append(
    {
        "name": "Patient (Boy, Age 0–36m)",
        "type": "spline",
        "data": patient_data,
        "color": "#D94F1A",
        "lineWidth": 5,
        "marker": {
            "enabled": True,
            "radius": 11,
            "symbol": "circle",
            "fillColor": "#D94F1A",
            "lineColor": "#ffffff",
            "lineWidth": 3,
        },
        "zIndex": 5,
        "shadow": {"enabled": True, "color": "rgba(217, 79, 26, 0.2)", "offsetX": 0, "offsetY": 2, "width": 4},
    }
)

chart.options.series = series_data

# Download Highcharts JS (inline for headless Chrome)
cdn_base = "https://cdn.jsdelivr.net/npm/highcharts@11.4"
js_urls = {"highcharts": f"{cdn_base}/highcharts.js", "highcharts_more": f"{cdn_base}/highcharts-more.js"}
js_modules = {}
for name, url in js_urls.items():
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        js_modules[name] = response.read().decode("utf-8")

highcharts_js = js_modules["highcharts"]
highcharts_more_js = js_modules["highcharts_more"]

# Generate HTML
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot
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
