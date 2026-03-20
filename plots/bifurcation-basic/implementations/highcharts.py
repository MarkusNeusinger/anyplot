"""pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data — logistic map bifurcation diagram
# x(n+1) = r * x(n) * (1 - x(n))
r_values = np.linspace(2.5, 4.0, 1500)
n_transient = 200
n_plot = 40

points = []
for r in r_values:
    x = 0.5
    for _ in range(n_transient):
        x = r * x * (1.0 - x)
    for _ in range(n_plot):
        x = r * x * (1.0 - x)
        points.append([round(float(r), 5), round(float(x), 5)])

data_json = json.dumps(points)

# Download Highcharts JS (with CDN fallback)
cdn_urls = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
highcharts_js = None
for url in cdn_urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue

# Build chart options directly as JS for performance with large datasets
chart_js = (
    """
Highcharts.chart('container', {
    chart: {
        type: 'scatter',
        width: 4800,
        height: 2700,
        backgroundColor: '#fafbfc',
        style: { fontFamily: "'Segoe UI', Helvetica, Arial, sans-serif" },
        marginTop: 160,
        marginBottom: 240,
        marginLeft: 220,
        marginRight: 120
    },
    title: {
        text: 'Logistic Map \\u00b7 bifurcation-basic \\u00b7 highcharts \\u00b7 pyplots.ai',
        style: { fontSize: '58px', fontWeight: '600', color: '#2c3e50', letterSpacing: '1px' },
        margin: 50
    },
    subtitle: {
        text: 'x(n+1) = r \\u00b7 x(n) \\u00b7 (1 \\u2212 x(n)) \\u2014 route from stability to chaos',
        style: { fontSize: '36px', color: '#7f8c8d', fontWeight: '400' }
    },
    xAxis: {
        title: {
            text: 'Growth Rate Parameter (r)',
            style: { fontSize: '42px', color: '#34495e', fontWeight: '500' },
            margin: 30
        },
        labels: { style: { fontSize: '32px', color: '#7f8c8d' } },
        min: 2.5,
        max: 4.0,
        tickInterval: 0.25,
        startOnTick: true,
        endOnTick: true,
        gridLineWidth: 1,
        gridLineColor: 'rgba(0, 0, 0, 0.06)',
        gridLineDashStyle: 'Dot',
        lineColor: '#bdc3c7',
        lineWidth: 2,
        plotLines: [
            {
                value: 3.0,
                color: 'rgba(231, 76, 60, 0.5)',
                width: 2,
                dashStyle: 'LongDash',
                label: {
                    text: 'r \\u2248 3.0 (period-2)',
                    style: { fontSize: '26px', color: 'rgba(231, 76, 60, 0.8)' },
                    rotation: 0,
                    y: -10
                }
            },
            {
                value: 3.449,
                color: 'rgba(231, 76, 60, 0.5)',
                width: 2,
                dashStyle: 'LongDash',
                label: {
                    text: 'r \\u2248 3.449 (period-4)',
                    style: { fontSize: '26px', color: 'rgba(231, 76, 60, 0.8)' },
                    rotation: 0,
                    y: -10
                }
            },
            {
                value: 3.5699,
                color: 'rgba(155, 89, 182, 0.5)',
                width: 2,
                dashStyle: 'LongDash',
                label: {
                    text: 'r \\u2248 3.57 (onset of chaos)',
                    style: { fontSize: '26px', color: 'rgba(155, 89, 182, 0.8)' },
                    rotation: 0,
                    y: -10
                }
            }
        ]
    },
    yAxis: {
        title: {
            text: 'Steady-State x',
            style: { fontSize: '42px', color: '#34495e', fontWeight: '500' },
            margin: 30
        },
        labels: { style: { fontSize: '32px', color: '#7f8c8d' } },
        min: 0,
        max: 1.0,
        tickInterval: 0.2,
        gridLineWidth: 1,
        gridLineColor: 'rgba(0, 0, 0, 0.06)',
        gridLineDashStyle: 'Dot',
        lineColor: '#bdc3c7',
        lineWidth: 2
    },
    legend: { enabled: false },
    credits: { enabled: false },
    tooltip: {
        headerFormat: '',
        pointFormat: '<span style="font-size:26px">r = <b>{point.x:.4f}</b><br/>x = <b>{point.y:.4f}</b></span>',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#306998',
        borderRadius: 10,
        borderWidth: 2,
        style: { fontSize: '26px' }
    },
    plotOptions: {
        scatter: {
            turboThreshold: 100000,
            marker: {
                radius: 1.2,
                symbol: 'circle',
                states: { hover: { radiusPlus: 3 } }
            }
        }
    },
    series: [{
        name: 'Bifurcation',
        color: 'rgba(48, 105, 152, 0.3)',
        data: """
    + data_json
    + """
    }]
});
"""
)

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

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
time.sleep(8)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{chart_js}</script>
</body>
</html>"""
    f.write(interactive_html)
