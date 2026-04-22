""" pyplots.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Temperature measurements across geographic region
np.random.seed(42)
n_points = 150
x = np.random.uniform(0, 100, n_points)  # Longitude-like
y = np.random.uniform(0, 80, n_points)  # Latitude-like
# Temperature increases toward bottom-right with some noise
color_values = 0.4 * x + 0.3 * y + np.random.normal(0, 8, n_points)
color_values = np.clip(color_values, 0, 80)  # Temperature range 0-80°C

# Normalize color values to 0-1 for colormap interpolation
color_min, color_max = float(color_values.min()), float(color_values.max())

# Viridis-like colormap (colorblind-safe)
viridis_stops = [(0.0, "#440154"), (0.25, "#3B528B"), (0.5, "#21918C"), (0.75, "#5EC962"), (1.0, "#FDE725")]


def interpolate_color(value):
    """Interpolate viridis colormap for a value between 0 and 1."""
    for i in range(len(viridis_stops) - 1):
        if viridis_stops[i][0] <= value <= viridis_stops[i + 1][0]:
            t = (value - viridis_stops[i][0]) / (viridis_stops[i + 1][0] - viridis_stops[i][0])
            c1 = viridis_stops[i][1]
            c2 = viridis_stops[i + 1][1]
            r = int(int(c1[1:3], 16) * (1 - t) + int(c2[1:3], 16) * t)
            g = int(int(c1[3:5], 16) * (1 - t) + int(c2[3:5], 16) * t)
            b = int(int(c1[5:7], 16) * (1 - t) + int(c2[5:7], 16) * t)
            return f"#{r:02x}{g:02x}{b:02x}"
    return viridis_stops[-1][1]


# Normalize and create data points with individual colors
color_normalized = (color_values - color_min) / (color_max - color_min)
data_points = []
for i in range(n_points):
    point_color = interpolate_color(color_normalized[i])
    data_points.append(
        {
            "x": round(float(x[i]), 2),
            "y": round(float(y[i]), 2),
            "color": point_color,
            "z": round(float(color_values[i]), 1),
        }
    )

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# JSON data for JavaScript
data_json = json.dumps(data_points)

# Generate HTML with inline Highcharts configuration and custom colorbar
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background-color: #ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        var data = {data_json};

        Highcharts.chart('container', {{
            chart: {{
                type: 'scatter',
                width: 4800,
                height: 2700,
                backgroundColor: '#ffffff',
                marginRight: 280,
                marginBottom: 150,
                events: {{
                    load: function() {{
                        var chart = this;
                        var renderer = chart.renderer;

                        // Colorbar dimensions and position
                        var barX = chart.plotLeft + chart.plotWidth + 80;
                        var barY = chart.plotTop + 50;
                        var barWidth = 50;
                        var barHeight = chart.plotHeight - 100;

                        // Draw gradient bar (approximated with rectangles)
                        var numSteps = 100;
                        var viridisStops = [
                            [0.0, '#440154'],
                            [0.25, '#3B528B'],
                            [0.5, '#21918C'],
                            [0.75, '#5EC962'],
                            [1.0, '#FDE725']
                        ];

                        function interpolateColor(c1, c2, t) {{
                            var r1 = parseInt(c1.substring(1,3), 16);
                            var g1 = parseInt(c1.substring(3,5), 16);
                            var b1 = parseInt(c1.substring(5,7), 16);
                            var r2 = parseInt(c2.substring(1,3), 16);
                            var g2 = parseInt(c2.substring(3,5), 16);
                            var b2 = parseInt(c2.substring(5,7), 16);
                            var r = Math.round(r1 + (r2 - r1) * t);
                            var g = Math.round(g1 + (g2 - g1) * t);
                            var b = Math.round(b1 + (b2 - b1) * t);
                            return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
                        }}

                        function getViridisColor(ratio) {{
                            for (var i = 0; i < viridisStops.length - 1; i++) {{
                                if (ratio >= viridisStops[i][0] && ratio <= viridisStops[i+1][0]) {{
                                    var t = (ratio - viridisStops[i][0]) / (viridisStops[i+1][0] - viridisStops[i][0]);
                                    return interpolateColor(viridisStops[i][1], viridisStops[i+1][1], t);
                                }}
                            }}
                            return viridisStops[viridisStops.length-1][1];
                        }}

                        for (var i = 0; i < numSteps; i++) {{
                            var ratio = i / numSteps;
                            var yPos = barY + (1 - ratio) * barHeight;
                            var height = barHeight / numSteps + 1;
                            var color = getViridisColor(ratio);

                            renderer.rect(barX, yPos, barWidth, height)
                                .attr({{fill: color, 'stroke-width': 0}})
                                .add();
                        }}

                        // Border around colorbar
                        renderer.rect(barX, barY, barWidth, barHeight)
                            .attr({{fill: 'none', stroke: '#333333', 'stroke-width': 3}})
                            .add();

                        // Tick labels
                        var minVal = {color_min};
                        var maxVal = {color_max};
                        var tickCount = 5;
                        for (var i = 0; i <= tickCount; i++) {{
                            var ratio = i / tickCount;
                            var val = minVal + ratio * (maxVal - minVal);
                            var yPos = barY + (1 - ratio) * barHeight;

                            // Tick mark
                            renderer.path(['M', barX + barWidth, yPos, 'L', barX + barWidth + 15, yPos])
                                .attr({{stroke: '#333333', 'stroke-width': 3}})
                                .add();

                            // Label
                            renderer.text(val.toFixed(0), barX + barWidth + 25, yPos + 12)
                                .css({{fontSize: '32px', color: '#333333'}})
                                .add();
                        }}

                        // Colorbar title
                        renderer.text('Temperature (°C)', barX + barWidth / 2, barY - 25)
                            .attr({{align: 'center'}})
                            .css({{fontSize: '36px', fontWeight: 'bold', color: '#333333'}})
                            .add();
                    }}
                }}
            }},
            title: {{
                text: 'scatter-color-mapped · highcharts · pyplots.ai',
                style: {{fontSize: '52px', fontWeight: 'bold'}}
            }},
            xAxis: {{
                title: {{
                    text: 'X Position',
                    style: {{fontSize: '40px'}}
                }},
                labels: {{style: {{fontSize: '32px'}}}},
                gridLineWidth: 1,
                gridLineColor: 'rgba(0,0,0,0.15)',
                lineWidth: 2,
                tickWidth: 2
            }},
            yAxis: {{
                title: {{
                    text: 'Y Position',
                    style: {{fontSize: '40px'}}
                }},
                labels: {{style: {{fontSize: '32px'}}}},
                gridLineWidth: 1,
                gridLineColor: 'rgba(0,0,0,0.15)',
                lineWidth: 2
            }},
            legend: {{
                enabled: false
            }},
            tooltip: {{
                style: {{fontSize: '24px'}},
                headerFormat: '',
                pointFormat: 'X: {{point.x}}<br>Y: {{point.y}}<br>Temperature: {{point.z}}°C'
            }},
            plotOptions: {{
                scatter: {{
                    marker: {{
                        radius: 18,
                        lineWidth: 2,
                        lineColor: 'rgba(0,0,0,0.25)'
                    }}
                }}
            }},
            series: [{{
                name: 'Temperature',
                data: data
            }}],
            credits: {{
                enabled: false
            }}
        }});
    </script>
</body>
</html>"""

# Save HTML file
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with Selenium
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
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
