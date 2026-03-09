""" pyplots.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: highcharts unknown | Python 3.14.3
Quality: 83/100 | Created: 2026-03-09
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Cumulative paid claims triangle (10 accident years x 10 development periods)
np.random.seed(42)

accident_years = list(range(2015, 2025))
development_periods = list(range(1, 11))
n_years = len(accident_years)
n_periods = len(development_periods)

# Base initial claims for each accident year (increasing over time)
base_claims = np.array([3200, 3500, 3800, 4100, 4500, 4900, 5300, 5700, 6100, 6500])

# Development factors (decreasing as claims mature)
dev_factors = np.array([1.0, 2.15, 1.45, 1.22, 1.12, 1.07, 1.04, 1.025, 1.015, 1.008])

# Build cumulative triangle
cumulative = np.zeros((n_years, n_periods))
for i in range(n_years):
    cumulative[i, 0] = base_claims[i] + np.random.normal(0, 200)
    for j in range(1, n_periods):
        noise = 1 + np.random.normal(0, 0.02)
        cumulative[i, j] = cumulative[i, j - 1] * dev_factors[j] * noise

cumulative = np.round(cumulative, 0)

# Determine actual vs projected: actual if accident_year_index + dev_period_index < n_years
is_actual = np.zeros((n_years, n_periods), dtype=bool)
for i in range(n_years):
    for j in range(n_periods):
        if i + j < n_years:
            is_actual[i, j] = True

# Age-to-age development factors (column averages from actual data)
age_to_age = []
for j in range(1, n_periods):
    factors = []
    for i in range(n_years):
        if is_actual[i, j] and is_actual[i, j - 1]:
            factors.append(cumulative[i, j] / cumulative[i, j - 1])
    age_to_age.append(round(np.mean(factors), 3) if factors else dev_factors[j])

# Prepare heatmap data with per-point styling
actual_data = []
projected_data = []
all_values = cumulative.flatten()
val_min = float(np.min(all_values))
val_max = float(np.max(all_values))

for i in range(n_years):
    for j in range(n_periods):
        val = float(cumulative[i, j])
        if is_actual[i, j]:
            actual_data.append({"x": j, "y": i, "value": val})
        else:
            projected_data.append({"x": j, "y": i, "value": val})

# Format age-to-age factors for subtitle
factors_str = "   ".join(
    [f"{development_periods[k]}\u2192{development_periods[k + 1]}: {f:.3f}" for k, f in enumerate(age_to_age)]
)

# Chart options
chart_options = {
    "chart": {
        "type": "heatmap",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginTop": 200,
        "marginBottom": 280,
        "marginLeft": 200,
        "marginRight": 260,
        "events": {"load": "__LOAD_EVENT__"},
    },
    "title": {
        "text": "heatmap-loss-triangle \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "42px", "fontWeight": "bold"},
        "y": 30,
    },
    "subtitle": {
        "text": "Cumulative Paid Claims ($K) \u2014 Actual vs Projected (IBNR)",
        "style": {"fontSize": "28px", "color": "#555555"},
        "y": 70,
    },
    "xAxis": {
        "categories": [str(p) for p in development_periods],
        "title": {
            "text": "Development Period (Years)",
            "style": {"fontSize": "28px", "color": "#333333"},
            "margin": 25,
        },
        "labels": {"style": {"fontSize": "24px"}},
    },
    "yAxis": {
        "categories": [str(y) for y in accident_years],
        "title": {"text": "Accident Year", "style": {"fontSize": "28px", "color": "#333333"}},
        "labels": {"style": {"fontSize": "24px"}},
        "reversed": True,
    },
    "colorAxis": {
        "min": val_min,
        "max": val_max,
        "stops": [
            [0, "#f7fbff"],
            [0.12, "#d2e3f3"],
            [0.25, "#9ecae1"],
            [0.45, "#4292c6"],
            [0.65, "#2171b5"],
            [0.85, "#084594"],
            [1, "#042f66"],
        ],
        "labels": {"style": {"fontSize": "22px"}, "formatter": "__COLORAXIS_FORMATTER__"},
    },
    "legend": {
        "align": "right",
        "layout": "vertical",
        "verticalAlign": "middle",
        "symbolHeight": 400,
        "itemStyle": {"fontSize": "22px"},
        "title": {"text": "Cumulative<br/>Claims ($K)", "style": {"fontSize": "20px"}},
    },
    "tooltip": {"formatter": "__TOOLTIP_FORMATTER__", "style": {"fontSize": "22px"}, "useHTML": True},
    "credits": {"enabled": False},
    "plotOptions": {
        "heatmap": {"dataLabels": {"enabled": True, "formatter": "__DATALABEL_FORMATTER__", "useHTML": True}}
    },
    "series": [
        {"type": "heatmap", "name": "Actual Claims", "data": actual_data, "borderWidth": 3, "borderColor": "#ffffff"},
        {
            "type": "heatmap",
            "name": "Projected (IBNR)",
            "data": projected_data,
            "borderWidth": 3,
            "borderColor": "#d4a853",
        },
    ],
}

# Convert to JSON and inject JavaScript formatters
options_json = json.dumps(chart_options)

threshold = (val_min + val_max) / 2
datalabel_formatter = (
    """function() {
    var val = Highcharts.numberFormat(this.point.value, 0, '.', ',');
    var isProjected = (this.series.name === 'Projected (IBNR)');
    var color = this.point.value > %d ? '#ffffff' : '#1a1a1a';
    if (isProjected) {
        return '<span style="color:' + color + ';font-size:20px;font-style:italic">' + val + '</span>';
    }
    return '<span style="color:' + color + ';font-size:20px;font-weight:bold">' + val + '</span>';
}"""
    % threshold
)

tooltip_formatter = """function() {
    var year = this.series.yAxis.categories[this.point.y];
    var period = this.series.xAxis.categories[this.point.x];
    var val = Highcharts.numberFormat(this.point.value, 0, '.', ',');
    var type = this.series.name;
    return '<b>Accident Year: ' + year + '</b><br>' +
           'Development Period: <b>' + period + '</b><br>' +
           'Cumulative Claims: <b>$' + val + 'K</b><br>' +
           'Type: <b>' + type + '</b>';
}"""

coloraxis_formatter = """function() {
    return Highcharts.numberFormat(this.value, 0, '.', ',');
}"""

# Add annotation for age-to-age factors and actual/projected legend after chart loads
load_event = """function() {
    var chart = this;
    var y = chart.plotTop + chart.plotHeight + 110;
    var x = chart.plotLeft;

    chart.renderer.text(
        '<b>Age-to-Age Development Factors:</b>  %s',
        x, y
    ).css({fontSize: '22px', color: '#444444'}).add();

    var ly = chart.plotTop + chart.plotHeight + 155;
    chart.renderer.rect(x, ly - 14, 28, 18, 0)
        .attr({fill: '#4292c6', stroke: '#ffffff', 'stroke-width': 2}).add();
    chart.renderer.text('Actual (observed)', x + 38, ly)
        .css({fontSize: '22px', color: '#333333'}).add();

    chart.renderer.rect(x + 280, ly - 14, 28, 18, 0)
        .attr({fill: '#4292c6', stroke: '#d4a853', 'stroke-width': 2}).add();
    chart.renderer.text('Projected (IBNR estimate)', x + 318, ly)
        .css({fontSize: '22px', color: '#333333', fontStyle: 'italic'}).add();
}""" % factors_str.replace("'", "\\'")

options_json = options_json.replace('"__DATALABEL_FORMATTER__"', datalabel_formatter)
options_json = options_json.replace('"__TOOLTIP_FORMATTER__"', tooltip_formatter)
options_json = options_json.replace('"__COLORAXIS_FORMATTER__"', coloraxis_formatter)
options_json = options_json.replace('"__LOAD_EVENT__"', load_event)

# Download Highcharts JS and heatmap module
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
heatmap_url = "https://cdn.jsdelivr.net/npm/highcharts/modules/heatmap.js"
headers = {"User-Agent": "Mozilla/5.0"}

req = urllib.request.Request(highcharts_url, headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req = urllib.request.Request(heatmap_url, headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

# Generate HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0;background:#ffffff;">
    <div id="container" style="width:4800px;height:2700px;"></div>
    <script>
        var opts = {options_json};
        Highcharts.chart('container', opts);
    </script>
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
