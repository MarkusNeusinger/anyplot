""" pyplots.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Stock-like data with price, volume, and RSI indicator over 150 trading days
np.random.seed(42)
n_points = 150
dates = pd.date_range("2024-01-01", periods=n_points, freq="B")

# Price series - random walk with upward trend
price_returns = np.random.normal(0.001, 0.015, n_points)
price = 100 * np.cumprod(1 + price_returns)

# Volume series - log-normal distribution with some correlation to price movement
volume_base = np.random.lognormal(mean=15, sigma=0.3, size=n_points)
volume = volume_base * (1 + np.abs(price_returns) * 10)  # Higher volume on bigger moves

# RSI-like indicator (simulated oscillator 0-100)
rsi = 50 + np.cumsum(np.random.normal(0, 3, n_points))
rsi = np.clip(rsi, 10, 90)  # Bound to realistic RSI range

# Convert dates to timestamps for Highcharts
timestamps = [int(d.timestamp() * 1000) for d in dates]

# Prepare series data as [timestamp, value] pairs
price_data = [[t, float(p)] for t, p in zip(timestamps, price, strict=True)]
volume_data = [[t, float(v)] for t, v in zip(timestamps, volume, strict=True)]
rsi_data = [[t, float(r)] for t, r in zip(timestamps, rsi, strict=True)]

# Download Highcharts JS libraries
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Title and styling
title = "dashboard-synchronized-crosshair · highcharts · pyplots.ai"
colors = ["#306998", "#FFD43B", "#9467BD"]

# Build the HTML with three synchronized charts
# Highcharts provides a built-in synchronization mechanism via shared events
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <style>
        body {{
            margin: 0;
            padding: 60px;
            background-color: #ffffff;
            font-family: Arial, sans-serif;
        }}
        .dashboard-title {{
            text-align: center;
            font-size: 56px;
            font-weight: bold;
            color: #333333;
            margin-bottom: 40px;
        }}
        .chart-container {{
            width: 4680px;
            margin-bottom: 30px;
        }}
        #chart1 {{ height: 750px; }}
        #chart2 {{ height: 550px; }}
        #chart3 {{ height: 550px; }}
    </style>
</head>
<body>
    <div class="dashboard-title">{title}</div>
    <div id="chart1" class="chart-container"></div>
    <div id="chart2" class="chart-container"></div>
    <div id="chart3" class="chart-container"></div>

    <script>
    (function() {{
        'use strict';

        // Data
        var priceData = {price_data};
        var volumeData = {volume_data};
        var rsiData = {rsi_data};

        // Keep track of all charts for synchronization
        var charts = [];

        // Function to synchronize crosshairs and tooltips
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

        // Function to hide tooltips on all charts
        function syncMouseLeave() {{
            for (var i = 0; i < charts.length; i++) {{
                charts[i].tooltip.hide();
                charts[i].xAxis[0].hideCrosshair();
            }}
        }}

        // Common chart options
        var commonOptions = {{
            chart: {{
                backgroundColor: '#ffffff',
                style: {{
                    fontFamily: 'Arial, sans-serif'
                }}
            }},
            credits: {{
                enabled: false
            }},
            legend: {{
                enabled: true,
                itemStyle: {{
                    fontSize: '24px',
                    fontWeight: 'normal'
                }}
            }},
            xAxis: {{
                type: 'datetime',
                crosshair: {{
                    width: 2,
                    color: '#666666',
                    dashStyle: 'Dash'
                }},
                labels: {{
                    style: {{
                        fontSize: '22px'
                    }},
                    format: '{{value:%b %d}}'
                }},
                title: {{
                    style: {{
                        fontSize: '24px'
                    }}
                }},
                gridLineWidth: 1,
                gridLineColor: '#e0e0e0',
                tickInterval: 7 * 24 * 3600 * 1000  // Weekly intervals
            }},
            yAxis: {{
                labels: {{
                    style: {{
                        fontSize: '22px'
                    }}
                }},
                title: {{
                    style: {{
                        fontSize: '26px'
                    }}
                }},
                gridLineWidth: 1,
                gridLineColor: '#e0e0e0'
            }},
            tooltip: {{
                shared: false,
                style: {{
                    fontSize: '20px'
                }},
                xDateFormat: '%Y-%m-%d'
            }},
            plotOptions: {{
                series: {{
                    states: {{
                        inactive: {{
                            opacity: 1
                        }}
                    }},
                    point: {{
                        events: {{
                            mouseOver: function() {{
                                // Sync tooltip on other charts
                                var chart = this.series.chart;
                                var pointIndex = this.index;
                                for (var i = 0; i < charts.length; i++) {{
                                    if (charts[i] !== chart && charts[i].series[0].points[pointIndex]) {{
                                        charts[i].series[0].points[pointIndex].setState('hover');
                                        charts[i].tooltip.refresh(charts[i].series[0].points[pointIndex]);
                                        charts[i].xAxis[0].drawCrosshair(null, charts[i].series[0].points[pointIndex]);
                                    }}
                                }}
                            }},
                            mouseOut: function() {{
                                for (var i = 0; i < charts.length; i++) {{
                                    var points = charts[i].series[0].points;
                                    for (var j = 0; j < points.length; j++) {{
                                        points[j].setState('');
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }};

        // Chart 1: Price (Line chart)
        var chart1 = Highcharts.chart('chart1', Highcharts.merge(commonOptions, {{
            title: {{
                text: 'Price',
                style: {{
                    fontSize: '36px',
                    fontWeight: 'bold'
                }}
            }},
            yAxis: {{
                title: {{
                    text: 'Price ($)'
                }}
            }},
            series: [{{
                type: 'line',
                name: 'Price',
                data: priceData,
                color: '{colors[0]}',
                lineWidth: 3,
                marker: {{
                    enabled: false,
                    radius: 4,
                    states: {{
                        hover: {{
                            enabled: true,
                            radius: 6
                        }}
                    }}
                }}
            }}]
        }}));
        charts.push(chart1);

        // Chart 2: Volume (Column chart)
        var chart2 = Highcharts.chart('chart2', Highcharts.merge(commonOptions, {{
            title: {{
                text: 'Volume',
                style: {{
                    fontSize: '36px',
                    fontWeight: 'bold'
                }}
            }},
            yAxis: {{
                title: {{
                    text: 'Volume'
                }}
            }},
            series: [{{
                type: 'column',
                name: 'Volume',
                data: volumeData,
                color: '{colors[1]}',
                borderWidth: 0,
                pointPadding: 0.1,
                groupPadding: 0.1
            }}]
        }}));
        charts.push(chart2);

        // Chart 3: RSI (Area chart)
        var chart3 = Highcharts.chart('chart3', Highcharts.merge(commonOptions, {{
            title: {{
                text: 'RSI Indicator',
                style: {{
                    fontSize: '36px',
                    fontWeight: 'bold'
                }}
            }},
            yAxis: {{
                title: {{
                    text: 'RSI'
                }},
                min: 0,
                max: 100,
                plotBands: [{{
                    from: 0,
                    to: 30,
                    color: 'rgba(147, 103, 189, 0.1)',
                    label: {{
                        text: 'Oversold',
                        style: {{
                            fontSize: '18px',
                            color: '#9467BD'
                        }}
                    }}
                }}, {{
                    from: 70,
                    to: 100,
                    color: 'rgba(147, 103, 189, 0.1)',
                    label: {{
                        text: 'Overbought',
                        style: {{
                            fontSize: '18px',
                            color: '#9467BD'
                        }}
                    }}
                }}]
            }},
            series: [{{
                type: 'area',
                name: 'RSI',
                data: rsiData,
                color: '{colors[2]}',
                fillOpacity: 0.3,
                lineWidth: 3,
                marker: {{
                    enabled: false,
                    radius: 4,
                    states: {{
                        hover: {{
                            enabled: true,
                            radius: 6
                        }}
                    }}
                }}
            }}]
        }}));
        charts.push(chart3);

        // Add mouse move event listeners for crosshair sync
        ['chart1', 'chart2', 'chart3'].forEach(function(id) {{
            var container = document.getElementById(id);
            container.addEventListener('mousemove', function(e) {{
                syncCrosshairs.call(Highcharts.charts.find(c => c && c.renderTo.id === id), e);
            }});
            container.addEventListener('mouseleave', syncMouseLeave);
        }});

    }})();
    </script>
</body>
</html>"""

# Save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium for PNG
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
time.sleep(5)  # Wait for charts to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
