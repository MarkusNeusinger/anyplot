""" pyplots.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Coefficients from a regression model predicting housing prices
np.random.seed(42)

variables = [
    "Square Footage",
    "Number of Bedrooms",
    "Number of Bathrooms",
    "Garage Spaces",
    "Lot Size (acres)",
    "Year Built",
    "Distance to City Center",
    "School Rating",
    "Crime Rate Index",
    "Property Tax Rate",
]

# Generate realistic coefficients with varying significance
coefficients = np.array([0.45, 0.12, 0.28, 0.15, 0.08, 0.02, -0.22, 0.35, -0.18, -0.05])
std_errors = np.array([0.08, 0.09, 0.07, 0.06, 0.10, 0.04, 0.05, 0.06, 0.07, 0.08])

# 95% confidence intervals
ci_lower = coefficients - 1.96 * std_errors
ci_upper = coefficients + 1.96 * std_errors

# Determine significance (CI does not cross zero)
significant = (ci_lower > 0) | (ci_upper < 0)

# Sort by coefficient magnitude (highest at top, so reverse for display)
sort_idx = np.argsort(coefficients)[::-1]
variables = [variables[i] for i in sort_idx]
coefficients = coefficients[sort_idx]
ci_lower = ci_lower[sort_idx]
ci_upper = ci_upper[sort_idx]
significant = significant[sort_idx]

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

xrange_url = "https://code.highcharts.com/modules/xrange.js"
with urllib.request.urlopen(xrange_url, timeout=30) as response:
    xrange_js = response.read().decode("utf-8")

# Build data arrays for JavaScript
sig_points = []
nonsig_points = []

for i, (var, coef, sig) in enumerate(zip(variables, coefficients, significant, strict=True)):
    point = {"x": float(coef), "y": i, "name": var}
    if sig:
        sig_points.append(point)
    else:
        nonsig_points.append(point)

# Convert to JS format using json for proper escaping
categories_js = json.dumps(variables)
sig_points_js = json.dumps(sig_points)
nonsig_points_js = json.dumps(nonsig_points)

# Build CI data for xrange series
ci_data = []
for i, (lower, upper, sig) in enumerate(zip(ci_lower, ci_upper, significant, strict=True)):
    ci_data.append({"x": float(lower), "x2": float(upper), "y": i, "color": "#306998" if sig else "#B8860B"})

ci_data_js = json.dumps(ci_data)

# Calculate x-axis range to ensure all points are visible
x_min = float(min(ci_lower)) - 0.05
x_max = float(max(ci_upper)) + 0.05

chart_js = f"""
Highcharts.chart('container', {{
    chart: {{
        width: 4800,
        height: 2700,
        backgroundColor: '#ffffff',
        marginLeft: 420,
        marginRight: 180,
        marginTop: 180,
        marginBottom: 280,
        spacingBottom: 40
    }},
    title: {{
        text: 'coefficient-confidence · highcharts · pyplots.ai',
        style: {{ fontSize: '56px', fontWeight: 'bold' }}
    }},
    subtitle: {{
        text: 'Housing Price Regression Model Coefficients with 95% Confidence Intervals',
        style: {{ fontSize: '36px', color: '#555555' }}
    }},
    xAxis: {{
        min: {x_min},
        max: {x_max},
        title: {{
            text: 'Coefficient Estimate (Standardized)',
            style: {{ fontSize: '40px' }},
            margin: 25
        }},
        labels: {{
            style: {{ fontSize: '32px' }},
            format: '{{value:.1f}}'
        }},
        gridLineWidth: 1,
        gridLineColor: '#e0e0e0',
        tickInterval: 0.1,
        plotLines: [{{
            value: 0,
            color: '#666666',
            width: 4,
            dashStyle: 'Dash',
            zIndex: 3,
            label: {{
                text: 'Null (β = 0)',
                style: {{ fontSize: '28px', color: '#666666', fontWeight: 'bold' }},
                rotation: 0,
                y: 30,
                x: 10
            }}
        }}]
    }},
    yAxis: {{
        title: {{ text: null }},
        categories: {categories_js},
        labels: {{
            style: {{ fontSize: '32px' }}
        }},
        gridLineWidth: 0,
        reversed: false
    }},
    legend: {{
        enabled: true,
        itemStyle: {{ fontSize: '36px' }},
        verticalAlign: 'bottom',
        align: 'center',
        layout: 'horizontal',
        floating: false,
        y: -20,
        symbolRadius: 14,
        symbolHeight: 28,
        symbolWidth: 28,
        itemDistance: 100
    }},
    tooltip: {{
        style: {{ fontSize: '28px' }},
        useHTML: true,
        formatter: function() {{
            if (this.series.type === 'xrange') {{
                return '<b>' + this.yCategory + '</b><br/>CI: [' + this.point.x.toFixed(3) + ', ' + this.point.x2.toFixed(3) + ']';
            }}
            return '<b>' + this.point.name + '</b><br/>Coefficient: ' + this.x.toFixed(3);
        }}
    }},
    plotOptions: {{
        scatter: {{
            marker: {{
                radius: 22,
                symbol: 'circle'
            }},
            zIndex: 10
        }},
        xrange: {{
            borderRadius: 0,
            pointWidth: 8,
            zIndex: 5
        }}
    }},
    series: [{{
        type: 'xrange',
        name: '95% CI',
        data: {ci_data_js},
        showInLegend: false,
        enableMouseTracking: true
    }}, {{
        type: 'scatter',
        name: 'Significant (p < 0.05)',
        color: '#306998',
        data: {sig_points_js},
        marker: {{
            fillColor: '#306998',
            lineWidth: 0,
            radius: 22
        }},
        zIndex: 10,
        clip: false
    }}, {{
        type: 'scatter',
        name: 'Not Significant',
        color: '#FFD43B',
        data: {nonsig_points_js},
        marker: {{
            fillColor: '#FFD43B',
            lineWidth: 4,
            lineColor: '#B8860B',
            radius: 22
        }},
        zIndex: 10,
        clip: false
    }}]
}});
"""

# HTML content with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <script>{xrange_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Chrome options for headless screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")  # Slightly larger to capture legend

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render

# Get the container element and take a screenshot of just that element
container = driver.find_element("id", "container")
container.screenshot("plot.png")

driver.quit()

Path(temp_path).unlink()  # Clean up temp file
