"""anyplot.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: highcharts unknown | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-23
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# anyplot palette
COLOR_PRICE = "#009E73"  # position 1 — brand green
COLOR_VOLUME = "#9418DB"  # position 2
COLOR_RSI = "#B71D27"  # position 3

# Data — stock-like price, volume, RSI over 150 trading days
np.random.seed(42)
n_points = 150
dates = pd.date_range("2024-01-01", periods=n_points, freq="B")

price_returns = np.random.normal(0.001, 0.015, n_points)
price = 100 * np.cumprod(1 + price_returns)

volume_base = np.random.lognormal(mean=15, sigma=0.3, size=n_points)
volume = volume_base * (1 + np.abs(price_returns) * 10)

rsi = 50 + np.cumsum(np.random.normal(0, 3, n_points))
rsi[:18] -= 30  # force early oversold zone demonstration
rsi = np.clip(rsi, 10, 90)

start_price = float(price[0])

timestamps = [int(d.timestamp() * 1000) for d in dates]
price_data = [[t, float(p)] for t, p in zip(timestamps, price, strict=True)]
volume_data = [[t, float(v)] for t, v in zip(timestamps, volume, strict=True)]
rsi_data = [[t, float(r)] for t, r in zip(timestamps, rsi, strict=True)]

# Download Highcharts JS (jsdelivr mirrors the official build)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

title = "dashboard-synchronized-crosshair · python · highcharts · anyplot.ai"
# len(title) == 67 → default 66px font-size, no scaling needed

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html, body {{
            width: 3200px;
            height: 1800px;
            overflow: hidden;
            background-color: {PAGE_BG};
            font-family: Arial, sans-serif;
        }}
        .dashboard {{
            width: 3200px;
            height: 1800px;
            padding: 30px;
        }}
        .dashboard-title {{
            height: 70px;
            line-height: 70px;
            text-align: center;
            font-size: 66px;
            font-weight: bold;
            color: {INK};
            margin-bottom: 15px;
        }}
        #chart1 {{ height: 640px; margin-bottom: 25px; }}
        #chart2 {{ height: 473px; margin-bottom: 25px; }}
        #chart3 {{ height: 473px; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="dashboard-title">{title}</div>
        <div id="chart1"></div>
        <div id="chart2"></div>
        <div id="chart3"></div>
    </div>

    <script>
    (function() {{
        'use strict';

        var priceData = {price_data};
        var volumeData = {volume_data};
        var rsiData = {rsi_data};

        var charts = [];

        function syncCrosshairs(e) {{
            var chart = this;
            var event = chart.pointer.normalize(e);
            var point, i;
            for (i = 0; i < charts.length; i++) {{
                var targetChart = charts[i];
                if (targetChart !== chart) {{
                    point = targetChart.series[0].searchPoint(event, true);
                    if (point) {{
                        point.onMouseOver();
                        targetChart.xAxis[0].drawCrosshair(event, point);
                    }}
                }}
            }}
        }}

        function syncMouseLeave() {{
            for (var i = 0; i < charts.length; i++) {{
                charts[i].tooltip.hide();
                charts[i].xAxis[0].hideCrosshair();
            }}
        }}

        var commonOptions = {{
            chart: {{
                backgroundColor: '{PAGE_BG}',
                style: {{ fontFamily: 'Arial, sans-serif', color: '{INK}' }},
                spacingLeft: 10,
                spacingRight: 20,
                spacingTop: 5,
                spacingBottom: 10
            }},
            credits: {{ enabled: false }},
            legend: {{ enabled: false }},
            xAxis: {{
                type: 'datetime',
                crosshair: {{
                    width: 3,
                    color: '{INK_SOFT}',
                    dashStyle: 'Dash'
                }},
                labels: {{
                    style: {{ fontSize: '44px', color: '{INK_SOFT}' }},
                    format: '{{value:%b %d}}'
                }},
                title: {{ style: {{ fontSize: '52px', color: '{INK}' }} }},
                lineColor: '{INK_SOFT}',
                tickColor: '{INK_SOFT}',
                gridLineWidth: 1,
                gridLineColor: '{GRID}',
                tickInterval: 14 * 24 * 3600 * 1000
            }},
            yAxis: {{
                labels: {{ style: {{ fontSize: '44px', color: '{INK_SOFT}' }} }},
                title: {{ style: {{ fontSize: '52px', color: '{INK}' }} }},
                lineColor: '{INK_SOFT}',
                gridLineWidth: 1,
                gridLineColor: '{GRID}'
            }},
            tooltip: {{
                shared: false,
                style: {{ fontSize: '36px', color: '{INK}' }},
                backgroundColor: '{ELEVATED_BG}',
                borderColor: '{INK_SOFT}',
                xDateFormat: '%Y-%m-%d'
            }},
            plotOptions: {{
                series: {{
                    states: {{ inactive: {{ opacity: 1 }} }}
                }}
            }}
        }};

        var chart1 = Highcharts.chart('chart1', Highcharts.merge(commonOptions, {{
            title: {{
                text: 'Price',
                style: {{ fontSize: '54px', fontWeight: 'bold', color: '{INK}' }}
            }},
            yAxis: {{
                title: {{ text: 'Price (USD)' }},
                plotLines: [{{
                    value: {start_price:.2f},
                    color: '{INK_SOFT}',
                    dashStyle: 'LongDash',
                    width: 2,
                    label: {{
                        text: 'Start ${start_price:.0f}',
                        style: {{ fontSize: '32px', color: '{INK_SOFT}' }},
                        align: 'right',
                        x: -10
                    }}
                }}]
            }},
            series: [{{
                type: 'line',
                name: 'Price',
                data: priceData,
                color: '{COLOR_PRICE}',
                lineWidth: 3,
                marker: {{
                    enabled: false,
                    states: {{ hover: {{ enabled: true, radius: 6 }} }}
                }}
            }}]
        }}));
        charts.push(chart1);

        var chart2 = Highcharts.chart('chart2', Highcharts.merge(commonOptions, {{
            title: {{
                text: 'Volume',
                style: {{ fontSize: '54px', fontWeight: 'bold', color: '{INK}' }}
            }},
            yAxis: {{ title: {{ text: 'Volume' }} }},
            series: [{{
                type: 'column',
                name: 'Volume',
                data: volumeData,
                color: '{COLOR_VOLUME}',
                borderWidth: 0,
                pointPadding: 0.1,
                groupPadding: 0.05
            }}]
        }}));
        charts.push(chart2);

        var chart3 = Highcharts.chart('chart3', Highcharts.merge(commonOptions, {{
            title: {{
                text: 'RSI Indicator',
                style: {{ fontSize: '54px', fontWeight: 'bold', color: '{INK}' }}
            }},
            yAxis: {{
                title: {{ text: 'RSI' }},
                min: 0,
                max: 100,
                plotBands: [{{
                    from: 0,
                    to: 30,
                    color: 'rgba(0,158,115,0.10)',
                    label: {{
                        text: 'Oversold',
                        style: {{ fontSize: '40px', color: '{COLOR_PRICE}' }}
                    }}
                }}, {{
                    from: 70,
                    to: 100,
                    color: 'rgba(183,29,39,0.10)',
                    label: {{
                        text: 'Overbought',
                        style: {{ fontSize: '40px', color: '{COLOR_RSI}' }}
                    }}
                }}]
            }},
            series: [{{
                type: 'area',
                name: 'RSI',
                data: rsiData,
                color: '{COLOR_RSI}',
                fillOpacity: 0.2,
                lineWidth: 3,
                marker: {{
                    enabled: false,
                    states: {{ hover: {{ enabled: true, radius: 6 }} }}
                }}
            }}]
        }}));
        charts.push(chart3);

        ['chart1', 'chart2', 'chart3'].forEach(function(id) {{
            var container = document.getElementById(id);
            container.addEventListener('mousemove', function(e) {{
                syncCrosshairs.call(Highcharts.charts.find(function(c) {{ return c && c.renderTo.id === id; }}), e);
            }});
            container.addEventListener('mouseleave', syncMouseLeave);
        }});

        // Synchronized zoom/pan via afterSetExtremes
        var isSyncing = false;
        charts.forEach(function(c) {{
            Highcharts.addEvent(c.xAxis[0], 'afterSetExtremes', function(e) {{
                if (!isSyncing) {{
                    isSyncing = true;
                    charts.forEach(function(other) {{
                        if (other !== c) {{
                            other.xAxis[0].setExtremes(e.min, e.max, true, false);
                        }}
                    }});
                    isSyncing = false;
                }}
            }});
        }});

    }})();
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium for PNG
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact canvas dims (safety net for off-by-one rounding)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
