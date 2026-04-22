""" pyplots.ai
ternary-density: Ternary Density Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from scipy.stats import gaussian_kde
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Generate ternary compositional data (sand/silt/clay sediment composition)
np.random.seed(42)

# Generate clustered compositional data with three distinct modes
n_samples = 500

# Cluster 1: High sand content (sandy deposits)
cluster1_size = 180
alpha1 = np.array([8, 2, 1])  # Dirichlet parameters
comp1 = np.random.dirichlet(alpha1, cluster1_size) * 100

# Cluster 2: High clay content (clay-rich sediments)
cluster2_size = 160
alpha2 = np.array([1, 2, 8])
comp2 = np.random.dirichlet(alpha2, cluster2_size) * 100

# Cluster 3: Balanced silt-dominated (loess-like)
cluster3_size = 160
alpha3 = np.array([2, 7, 2])
comp3 = np.random.dirichlet(alpha3, cluster3_size) * 100

# Combine all clusters
compositions = np.vstack([comp1, comp2, comp3])
sand = compositions[:, 0]
silt = compositions[:, 1]
clay = compositions[:, 2]

# Convert ternary to Cartesian coordinates
total = sand + silt + clay
b_norm = silt / total
c_norm = clay / total
x_data = 0.5 * (2 * b_norm + c_norm)
y_data = (np.sqrt(3) / 2) * c_norm

# Compute KDE on Cartesian coordinates
points = np.vstack([x_data, y_data])
kde = gaussian_kde(points, bw_method="scott")

# Create grid for density estimation
grid_res = 100
x_grid = np.linspace(0, 1, grid_res)
y_grid = np.linspace(0, np.sqrt(3) / 2, grid_res)
X, Y = np.meshgrid(x_grid, y_grid)
grid_points = np.vstack([X.ravel(), Y.ravel()])

# Evaluate KDE on grid
Z = kde(grid_points).reshape(X.shape)

# Mask points outside the triangle using vectorized barycentric coordinates
# Triangle vertices: (0,0), (1,0), (0.5, sqrt(3)/2)
v0_x, v0_y = 0, 0
v1_x, v1_y = 1, 0
v2_x, v2_y = 0.5, np.sqrt(3) / 2

# Compute barycentric sign for each point
d1 = (X - v2_x) * (v0_y - v2_y) - (v0_x - v2_x) * (Y - v2_y)
d2 = (X - v0_x) * (v1_y - v0_y) - (v1_x - v0_x) * (Y - v0_y)
d3 = (X - v1_x) * (v2_y - v1_y) - (v2_x - v1_x) * (Y - v1_y)

has_neg = (d1 < 0) | (d2 < 0) | (d3 < 0)
has_pos = (d1 > 0) | (d2 > 0) | (d3 > 0)
mask = has_neg & has_pos  # Outside triangle

Z_masked = np.where(mask, np.nan, Z)

# Normalize Z to 0-1 range for color mapping
Z_valid = Z_masked[~np.isnan(Z_masked)]
Z_min, Z_max = Z_valid.min(), Z_valid.max()
Z_norm = (Z_masked - Z_min) / (Z_max - Z_min)

# Create heatmap data for Highcharts
heatmap_data = []
for i in range(grid_res):
    for j in range(grid_res):
        if not np.isnan(Z_norm[i, j]):
            heatmap_data.append([j, i, round(float(Z_norm[i, j]), 4)])

# Download required Highcharts modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
heatmap_url = "https://code.highcharts.com/modules/heatmap.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")
with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

# Prepare heatmap series data as JSON
heatmap_data_json = json.dumps(heatmap_data)

# Build complete HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
    </style>
</head>
<body>
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>
        // Heatmap data
        var heatmapData = {heatmap_data_json};

        // Triangle annotation coordinates (in plot coordinates)
        var gridRes = {grid_res};

        // Create the chart
        Highcharts.chart('container', {{
            chart: {{
                type: 'heatmap',
                width: 3600,
                height: 3600,
                backgroundColor: '#ffffff',
                marginTop: 200,
                marginBottom: 250,
                marginLeft: 200,
                marginRight: 300,
                events: {{
                    load: function() {{
                        var chart = this,
                            renderer = chart.renderer;

                        // Calculate triangle coordinates in pixels
                        var plotLeft = chart.plotLeft,
                            plotTop = chart.plotTop,
                            plotWidth = chart.plotWidth,
                            plotHeight = chart.plotHeight;

                        // Triangle vertices in pixel coordinates
                        var v1 = [plotLeft, plotTop + plotHeight];  // Bottom left (Sand)
                        var v2 = [plotLeft + plotWidth, plotTop + plotHeight];  // Bottom right (Silt)
                        var v3 = [plotLeft + plotWidth/2, plotTop];  // Top (Clay)

                        // Draw triangle outline
                        renderer.path([
                            'M', v1[0], v1[1],
                            'L', v2[0], v2[1],
                            'L', v3[0], v3[1],
                            'Z'
                        ]).attr({{
                            'stroke-width': 4,
                            stroke: '#333333',
                            fill: 'none',
                            zIndex: 5
                        }}).add();

                        // Draw grid lines (ternary grid)
                        var gridLines = 10;
                        for (var i = 1; i < gridLines; i++) {{
                            var frac = i / gridLines;

                            // Lines parallel to bottom edge
                            var p1 = [v1[0] + (v3[0] - v1[0]) * frac, v1[1] + (v3[1] - v1[1]) * frac];
                            var p2 = [v2[0] + (v3[0] - v2[0]) * frac, v2[1] + (v3[1] - v2[1]) * frac];
                            renderer.path(['M', p1[0], p1[1], 'L', p2[0], p2[1]]).attr({{
                                'stroke-width': 1,
                                stroke: '#666666',
                                opacity: 0.5,
                                zIndex: 4
                            }}).add();

                            // Lines parallel to left edge
                            p1 = [v1[0] + (v2[0] - v1[0]) * frac, v1[1]];
                            p2 = [v3[0] + (v2[0] - v1[0]) * frac / 2, v3[1] + (v1[1] - v3[1]) * frac];
                            renderer.path(['M', p1[0], p1[1], 'L', p2[0], p2[1]]).attr({{
                                'stroke-width': 1,
                                stroke: '#666666',
                                opacity: 0.5,
                                zIndex: 4
                            }}).add();

                            // Lines parallel to right edge
                            p1 = [v2[0] - (v2[0] - v1[0]) * frac, v2[1]];
                            p2 = [v3[0] - (v2[0] - v1[0]) * frac / 2, v3[1] + (v2[1] - v3[1]) * frac];
                            renderer.path(['M', p1[0], p1[1], 'L', p2[0], p2[1]]).attr({{
                                'stroke-width': 1,
                                stroke: '#666666',
                                opacity: 0.5,
                                zIndex: 4
                            }}).add();
                        }}

                        // Vertex labels
                        renderer.text('Sand (100%)', v1[0] - 80, v1[1] + 60).attr({{
                            zIndex: 6
                        }}).css({{
                            fontSize: '36px',
                            fontWeight: 'bold',
                            color: '#306998'
                        }}).add();

                        renderer.text('Silt (100%)', v2[0] - 60, v2[1] + 60).attr({{
                            zIndex: 6
                        }}).css({{
                            fontSize: '36px',
                            fontWeight: 'bold',
                            color: '#306998'
                        }}).add();

                        renderer.text('Clay (100%)', v3[0] - 80, v3[1] - 30).attr({{
                            zIndex: 6
                        }}).css({{
                            fontSize: '36px',
                            fontWeight: 'bold',
                            color: '#306998'
                        }}).add();

                        // Tick labels along edges
                        for (var i = 2; i <= 8; i += 2) {{
                            var frac = i / 10;
                            var label = (i * 10) + '%';

                            // Bottom edge (Sand decreasing, Silt increasing)
                            var bx = v1[0] + (v2[0] - v1[0]) * frac;
                            renderer.text(label, bx - 25, v1[1] + 45).attr({{ zIndex: 6 }}).css({{
                                fontSize: '24px',
                                color: '#555555'
                            }}).add();
                        }}
                    }}
                }}
            }},
            title: {{
                text: 'ternary-density · highcharts · pyplots.ai',
                style: {{ fontSize: '52px', fontWeight: 'bold' }}
            }},
            subtitle: {{
                text: 'Sediment Composition: Sand/Silt/Clay Distribution (n={n_samples})',
                style: {{ fontSize: '36px' }}
            }},
            xAxis: {{
                visible: false,
                min: 0,
                max: gridRes - 1
            }},
            yAxis: {{
                visible: false,
                min: 0,
                max: gridRes - 1
            }},
            colorAxis: {{
                min: 0,
                max: 1,
                stops: [
                    [0, '#440154'],
                    [0.25, '#3b528b'],
                    [0.5, '#21918c'],
                    [0.75, '#5ec962'],
                    [1, '#fde725']
                ],
                labels: {{
                    style: {{ fontSize: '28px' }}
                }}
            }},
            legend: {{
                enabled: true,
                title: {{
                    text: 'Density',
                    style: {{ fontSize: '32px', fontWeight: 'bold' }}
                }},
                layout: 'vertical',
                align: 'right',
                verticalAlign: 'middle',
                symbolHeight: 500,
                symbolWidth: 50
            }},
            tooltip: {{
                formatter: function() {{
                    return '<b>Relative Density:</b> ' + (this.point.value * 100).toFixed(1) + '%';
                }}
            }},
            plotOptions: {{
                heatmap: {{
                    borderWidth: 0,
                    nullColor: 'transparent',
                    colsize: 1,
                    rowsize: 1
                }}
            }},
            credits: {{ enabled: false }},
            series: [{{
                name: 'Density',
                data: heatmapData,
                boostThreshold: 100,
                turboThreshold: 0
            }}]
        }});
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
