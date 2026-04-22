""" pyplots.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Server response times by endpoint (large dataset, 3000+ points per category)
np.random.seed(42)

endpoints = ["API Gateway", "Auth Service", "Database", "Cache Layer"]
data = {}

# Generate realistic response time distributions
# API Gateway: moderate times with some slow requests
data["API Gateway"] = np.concatenate(
    [np.random.lognormal(mean=3.5, sigma=0.5, size=2500), np.random.lognormal(mean=5.0, sigma=0.3, size=500)]
)

# Auth Service: fast with occasional outliers
data["Auth Service"] = np.concatenate(
    [np.random.lognormal(mean=2.5, sigma=0.4, size=2800), np.random.uniform(200, 500, size=200)]
)

# Database: bimodal - cached vs uncached queries
data["Database"] = np.concatenate(
    [np.random.lognormal(mean=2.0, sigma=0.3, size=1500), np.random.lognormal(mean=4.5, sigma=0.6, size=1500)]
)

# Cache Layer: very fast, tight distribution
data["Cache Layer"] = np.random.lognormal(mean=1.5, sigma=0.3, size=3000)


# Calculate letter values (quantiles) for boxen plot
def calculate_letter_values(values, k=5):
    """Calculate nested quantile ranges for letter-value plot."""
    letter_values = []
    for i in range(k):
        depth = 2 ** (i + 1)
        lower_q = 0.5 / depth
        upper_q = 1 - lower_q

        lower = np.percentile(values, lower_q * 100)
        upper = np.percentile(values, upper_q * 100)
        letter_values.append((lower, upper, depth))

    median = np.median(values)
    return letter_values, median


# Colors for quantile levels - gradient from dark to light (Python blue shades)
colors = ["#1a3d5c", "#306998", "#4a87b8", "#7aaed4", "#b5d4eb"]

# Build series data - create column ranges for each quantile level
# For boxen plot, we use columnrange series stacked to create nested boxes
series_data_by_level = {i: [] for i in range(5)}
outlier_data = []

for cat_idx, endpoint in enumerate(endpoints):
    values = data[endpoint]
    letter_vals, median = calculate_letter_values(values, k=5)

    # Store for outlier calculation
    deepest_lower = letter_vals[-1][0]
    deepest_upper = letter_vals[-1][1]

    # Create data for each quantile level
    for level, (lower, upper, _depth) in enumerate(letter_vals):
        series_data_by_level[level].append(
            {"x": cat_idx, "low": float(lower), "high": float(upper), "median": float(median)}
        )

    # Calculate outliers (beyond deepest letter value)
    outliers = values[(values < deepest_lower) | (values > deepest_upper)]
    for outlier_val in outliers[:30]:  # Limit outliers shown
        outlier_data.append([cat_idx, float(outlier_val)])

# Download Highcharts JS files
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Build series for Highcharts - using columnrange for boxen effect
js_series = []

# Level names for legend
level_names = ["Median ± 25%", "Median ± 37.5%", "Median ± 43.75%", "Median ± 46.875%", "Median ± 48.4%"]

# Add columnrange series for each quantile level (outermost first for layering)
for level in range(4, -1, -1):
    color = colors[level]
    # Point width decreases for inner levels (boxen effect)
    point_width = 180 - (level * 30)

    series_config = {
        "name": level_names[level],
        "type": "columnrange",
        "data": [[d["x"], d["low"], d["high"]] for d in series_data_by_level[level]],
        "color": color,
        "borderColor": "#1a3d5c",
        "borderWidth": 2,
        "pointWidth": point_width,
        "grouping": False,
        "showInLegend": True,
    }
    js_series.append(series_config)

# Add median line as scatter with custom marker
median_data = []
for cat_idx, endpoint in enumerate(endpoints):
    values = data[endpoint]
    median_data.append([cat_idx, float(np.median(values))])

median_series = {
    "name": "Median",
    "type": "scatter",
    "data": median_data,
    "color": "#FFD43B",
    "marker": {"symbol": "diamond", "radius": 12, "fillColor": "#FFD43B", "lineColor": "#1a3d5c", "lineWidth": 3},
    "zIndex": 10,
}
js_series.append(median_series)

# Add outliers as scatter points
outlier_series = {
    "name": "Outliers",
    "type": "scatter",
    "data": outlier_data,
    "color": "#e74c3c",
    "marker": {"radius": 8, "symbol": "circle", "fillColor": "#e74c3c", "lineColor": "#c0392b", "lineWidth": 2},
    "tooltip": {"pointFormat": "Response time: {point.y:.1f} ms"},
}
js_series.append(outlier_series)

series_js = json.dumps(js_series)

# Create custom HTML with proper boxen visualization
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; padding:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {{
            chart: {{
                type: 'columnrange',
                inverted: false,
                width: 4800,
                height: 2700,
                backgroundColor: '#ffffff',
                spacingBottom: 100,
                marginLeft: 200,
                marginRight: 300,
                marginTop: 120
            }},
            title: {{
                text: 'boxen-basic · highcharts · pyplots.ai',
                style: {{ fontSize: '48px', fontWeight: 'bold' }}
            }},
            subtitle: {{
                text: 'Server Response Times by Endpoint (Letter-Value Distribution)',
                style: {{ fontSize: '32px', color: '#666666' }}
            }},
            xAxis: {{
                categories: {json.dumps(endpoints)},
                title: {{
                    text: 'Service Endpoint',
                    style: {{ fontSize: '36px' }},
                    margin: 20
                }},
                labels: {{
                    style: {{ fontSize: '28px' }}
                }}
            }},
            yAxis: {{
                title: {{
                    text: 'Response Time (ms)',
                    style: {{ fontSize: '36px' }}
                }},
                labels: {{
                    style: {{ fontSize: '28px' }}
                }},
                gridLineColor: '#e0e0e0',
                gridLineWidth: 1
            }},
            legend: {{
                enabled: true,
                itemStyle: {{ fontSize: '24px' }},
                layout: 'vertical',
                align: 'right',
                verticalAlign: 'middle',
                x: -50,
                itemMarginTop: 15,
                itemMarginBottom: 15,
                backgroundColor: '#ffffff',
                borderColor: '#cccccc',
                borderWidth: 1,
                padding: 20
            }},
            tooltip: {{
                shared: false,
                style: {{ fontSize: '20px' }},
                formatter: function() {{
                    if (this.series.type === 'columnrange') {{
                        return '<b>' + this.series.name + '</b><br/>' +
                               'Range: ' + this.point.low.toFixed(1) + ' - ' + this.point.high.toFixed(1) + ' ms';
                    }} else if (this.series.name === 'Median') {{
                        return '<b>Median</b>: ' + this.y.toFixed(1) + ' ms';
                    }} else {{
                        return '<b>Outlier</b>: ' + this.y.toFixed(1) + ' ms';
                    }}
                }}
            }},
            plotOptions: {{
                columnrange: {{
                    grouping: false
                }},
                series: {{
                    animation: false
                }}
            }},
            series: {series_js}
        }});
    </script>
</body>
</html>"""

# Save HTML file
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
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
