"""pyplots.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: highcharts unknown | Python 3.14.3
Quality: 81/100 | Created: 2026-03-19
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Generate SPC data for CNC shaft diameter measurements
np.random.seed(42)

n_samples = 30
subgroup_size = 5
target_diameter = 25.000  # mm
process_std = 0.010  # mm

# Control chart constants for n=5
A2 = 0.577
D3 = 0.0
D4 = 2.114
d2 = 2.326

# Generate subgroup measurements
measurements = np.random.normal(target_diameter, process_std, (n_samples, subgroup_size))

# Inject out-of-control points
measurements[7] += 0.025  # Shift up - sample 8
measurements[18] -= 0.030  # Shift down - sample 19
measurements[24] += 0.028  # Shift up - sample 25

# Calculate sample means and ranges
sample_means = measurements.mean(axis=1)
sample_ranges = measurements.max(axis=1) - measurements.min(axis=1)

# Calculate control limits
x_bar_bar = sample_means.mean()
r_bar = sample_ranges.mean()

xbar_ucl = x_bar_bar + A2 * r_bar
xbar_lcl = x_bar_bar - A2 * r_bar
xbar_uwl = x_bar_bar + (2 / 3) * A2 * r_bar  # Warning at ±2 sigma
xbar_lwl = x_bar_bar - (2 / 3) * A2 * r_bar

r_ucl = D4 * r_bar
r_lcl = D3 * r_bar  # 0 for n=5
r_uwl = r_bar + (2 / 3) * (r_ucl - r_bar)

# Identify out-of-control points
xbar_ooc = []
xbar_normal = []
for i in range(n_samples):
    point = [i + 1, round(float(sample_means[i]), 4)]
    if sample_means[i] > xbar_ucl or sample_means[i] < xbar_lcl:
        xbar_ooc.append(point)
    else:
        xbar_normal.append(point)

r_ooc = []
r_normal = []
for i in range(n_samples):
    point = [i + 1, round(float(sample_ranges[i]), 4)]
    if sample_ranges[i] > r_ucl or sample_ranges[i] < r_lcl:
        r_ooc.append(point)
    else:
        r_normal.append(point)

# All points for the connecting line
xbar_all = [[i + 1, round(float(sample_means[i]), 4)] for i in range(n_samples)]
r_all = [[i + 1, round(float(sample_ranges[i]), 4)] for i in range(n_samples)]

# Convert to JSON
xbar_all_json = json.dumps(xbar_all)
xbar_ooc_json = json.dumps(xbar_ooc)
r_all_json = json.dumps(r_all)
r_ooc_json = json.dumps(r_ooc)

sample_labels = json.dumps([str(i + 1) for i in range(n_samples)])

# Chart
chart_js = f"""
Highcharts.chart('container', {{
    chart: {{
        width: 4800,
        height: 2700,
        backgroundColor: '#ffffff',
        spacingTop: 40,
        spacingBottom: 160,
        spacingLeft: 100,
        spacingRight: 100,
        marginBottom: 280,
        style: {{
            fontFamily: 'Arial, sans-serif'
        }}
    }},

    title: {{
        text: 'CNC Shaft Diameter Monitoring \\u00b7 spc-xbar-r \\u00b7 highcharts \\u00b7 pyplots.ai',
        style: {{
            fontSize: '44px',
            fontWeight: 'bold'
        }}
    }},

    credits: {{
        enabled: false
    }},

    legend: {{
        enabled: true,
        itemStyle: {{
            fontSize: '24px'
        }},
        symbolRadius: 6,
        symbolWidth: 24,
        verticalAlign: 'top',
        y: 60
    }},

    xAxis: [{{
        categories: {sample_labels},
        visible: false,
        lineWidth: 0,
        min: 0,
        max: {n_samples - 1}
    }}, {{
        categories: {sample_labels},
        title: {{
            text: 'Sample Number',
            style: {{
                fontSize: '28px',
                fontWeight: 'bold'
            }},
            y: 30
        }},
        labels: {{
            style: {{
                fontSize: '24px'
            }},
            y: 35,
            step: 1
        }},
        lineWidth: 2,
        lineColor: '#333333',
        tickWidth: 2,
        offset: 0,
        min: 0,
        max: {n_samples - 1}
    }}],

    yAxis: [{{
        title: {{
            text: 'X\\u0304 (Sample Mean, mm)',
            style: {{
                fontSize: '26px',
                fontWeight: 'bold'
            }}
        }},
        labels: {{
            style: {{
                fontSize: '22px'
            }},
            format: '{{value:.3f}}'
        }},
        height: '38%',
        top: '8%',
        offset: 0,
        lineWidth: 2,
        lineColor: '#333333',
        gridLineWidth: 1,
        gridLineColor: 'rgba(0, 0, 0, 0.08)',
        plotLines: [{{
            value: {round(float(x_bar_bar), 4)},
            color: '#306998',
            width: 3,
            zIndex: 3,
            label: {{
                text: 'CL = {x_bar_bar:.4f}',
                align: 'right',
                style: {{ fontSize: '20px', color: '#306998', fontWeight: 'bold' }},
                x: -10,
                y: -8
            }}
        }}, {{
            value: {round(float(xbar_ucl), 4)},
            color: '#D32F2F',
            width: 3,
            dashStyle: 'Dash',
            zIndex: 3,
            label: {{
                text: 'UCL = {xbar_ucl:.4f}',
                align: 'right',
                style: {{ fontSize: '20px', color: '#D32F2F', fontWeight: 'bold' }},
                x: -10,
                y: -8
            }}
        }}, {{
            value: {round(float(xbar_lcl), 4)},
            color: '#D32F2F',
            width: 3,
            dashStyle: 'Dash',
            zIndex: 3,
            label: {{
                text: 'LCL = {xbar_lcl:.4f}',
                align: 'right',
                style: {{ fontSize: '20px', color: '#D32F2F', fontWeight: 'bold' }},
                x: -10,
                y: 24
            }}
        }}, {{
            value: {round(float(xbar_uwl), 4)},
            color: '#FF9800',
            width: 2,
            dashStyle: 'ShortDot',
            zIndex: 2,
            label: {{
                text: 'UWL',
                align: 'left',
                style: {{ fontSize: '18px', color: '#FF9800' }},
                x: 10,
                y: -6
            }}
        }}, {{
            value: {round(float(xbar_lwl), 4)},
            color: '#FF9800',
            width: 2,
            dashStyle: 'ShortDot',
            zIndex: 2,
            label: {{
                text: 'LWL',
                align: 'left',
                style: {{ fontSize: '18px', color: '#FF9800' }},
                x: 10,
                y: -10
            }}
        }}]
    }}, {{
        title: {{
            text: 'R (Sample Range, mm)',
            style: {{
                fontSize: '26px',
                fontWeight: 'bold'
            }}
        }},
        labels: {{
            style: {{
                fontSize: '22px'
            }},
            format: '{{value:.3f}}'
        }},
        height: '38%',
        top: '53%',
        offset: 0,
        lineWidth: 2,
        lineColor: '#333333',
        gridLineWidth: 1,
        gridLineColor: 'rgba(0, 0, 0, 0.08)',
        min: 0,
        max: {round(float(r_ucl * 1.15), 4)},
        plotLines: [{{
            value: {round(float(r_bar), 4)},
            color: '#306998',
            width: 3,
            zIndex: 3,
            label: {{
                text: 'CL = {r_bar:.4f}',
                align: 'right',
                style: {{ fontSize: '20px', color: '#306998', fontWeight: 'bold' }},
                x: -10,
                y: -8
            }}
        }}, {{
            value: {round(float(r_ucl), 4)},
            color: '#D32F2F',
            width: 3,
            dashStyle: 'Dash',
            zIndex: 3,
            label: {{
                text: 'UCL = {r_ucl:.4f}',
                align: 'right',
                style: {{ fontSize: '20px', color: '#D32F2F', fontWeight: 'bold' }},
                x: -10,
                y: -8
            }}
        }}, {{
            value: {round(float(r_uwl), 4)},
            color: '#FF9800',
            width: 2,
            dashStyle: 'ShortDot',
            zIndex: 2,
            label: {{
                text: 'UWL',
                align: 'left',
                style: {{ fontSize: '18px', color: '#FF9800' }},
                x: 10,
                y: -6
            }}
        }}]
    }}],

    tooltip: {{
        shared: false,
        style: {{
            fontSize: '20px'
        }},
        valueDecimals: 4,
        valueSuffix: ' mm'
    }},

    plotOptions: {{
        line: {{
            lineWidth: 3,
            marker: {{
                enabled: true,
                radius: 7,
                symbol: 'circle'
            }},
            states: {{
                hover: {{
                    lineWidthPlus: 1
                }}
            }}
        }},
        scatter: {{
            marker: {{
                radius: 12,
                symbol: 'circle',
                lineWidth: 3,
                lineColor: '#D32F2F'
            }},
            zIndex: 10
        }}
    }},

    series: [{{
        type: 'line',
        name: 'X\\u0304 (Sample Mean)',
        data: {xbar_all_json},
        color: '#306998',
        xAxis: 0,
        yAxis: 0,
        marker: {{
            fillColor: '#306998',
            lineColor: '#ffffff',
            lineWidth: 2,
            radius: 7
        }},
        showInLegend: true
    }}, {{
        type: 'scatter',
        name: 'Out of Control',
        data: {xbar_ooc_json},
        color: '#D32F2F',
        xAxis: 0,
        yAxis: 0,
        marker: {{
            radius: 12,
            symbol: 'circle',
            fillColor: '#D32F2F',
            lineColor: '#ffffff',
            lineWidth: 3
        }},
        showInLegend: true
    }}, {{
        type: 'line',
        name: 'R (Sample Range)',
        data: {r_all_json},
        color: '#306998',
        xAxis: 1,
        yAxis: 1,
        marker: {{
            fillColor: '#306998',
            lineColor: '#ffffff',
            lineWidth: 2,
            radius: 7
        }},
        showInLegend: true
    }}, {{
        type: 'scatter',
        name: 'Out of Control (R)',
        data: {r_ooc_json},
        color: '#D32F2F',
        xAxis: 1,
        yAxis: 1,
        marker: {{
            radius: 12,
            symbol: 'circle',
            fillColor: '#D32F2F',
            lineColor: '#ffffff',
            lineWidth: 3
        }},
        showInLegend: false
    }}]
}});
"""

# Download Highcharts JS
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
if not highcharts_js:
    raise RuntimeError("Failed to download Highcharts JS from all CDN sources")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
    {chart_js}
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot using Selenium
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

# Clean up temp file
Path(temp_path).unlink()
