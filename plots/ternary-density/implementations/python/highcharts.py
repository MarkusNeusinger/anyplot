""" anyplot.ai
ternary-density: Ternary Density Plot
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-19
"""

import json
import os
import tempfile
import time
from pathlib import Path

import numpy as np
from scipy.stats import gaussian_kde
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data: sediment composition (sand/silt/clay) with three distinct modes
np.random.seed(42)

n_samples = 500

# Cluster 1: High sand content (sandy deposits)
comp1 = np.random.dirichlet([8, 2, 1], 180) * 100

# Cluster 2: High clay content (clay-rich sediments)
comp2 = np.random.dirichlet([1, 2, 8], 160) * 100

# Cluster 3: Silt-dominated (loess-like)
comp3 = np.random.dirichlet([2, 7, 2], 160) * 100

compositions = np.vstack([comp1, comp2, comp3])
sand = compositions[:, 0]
silt = compositions[:, 1]
clay = compositions[:, 2]

# Convert ternary to Cartesian coordinates for KDE
total = sand + silt + clay
b_norm = silt / total
c_norm = clay / total
x_data = 0.5 * (2 * b_norm + c_norm)
y_data = (np.sqrt(3) / 2) * c_norm

# Compute KDE on Cartesian coordinates
kde = gaussian_kde(np.vstack([x_data, y_data]), bw_method="scott")

# Create grid for density estimation (higher res for smoother triangle boundary)
grid_res = 150
x_grid = np.linspace(0, 1, grid_res)
y_grid = np.linspace(0, np.sqrt(3) / 2, grid_res)
X, Y = np.meshgrid(x_grid, y_grid)
Z = kde(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape)

# Mask cells outside the equilateral triangle using barycentric coordinates
v0_x, v0_y = 0.0, 0.0
v1_x, v1_y = 1.0, 0.0
v2_x, v2_y = 0.5, np.sqrt(3) / 2

d1 = (X - v2_x) * (v0_y - v2_y) - (v0_x - v2_x) * (Y - v2_y)
d2 = (X - v0_x) * (v1_y - v0_y) - (v1_x - v0_x) * (Y - v0_y)
d3 = (X - v1_x) * (v2_y - v1_y) - (v2_x - v1_x) * (Y - v1_y)
mask = (d1 < 0) | (d2 < 0) | (d3 < 0)
has_pos = (d1 > 0) | (d2 > 0) | (d3 > 0)
Z_masked = np.where(mask & has_pos, np.nan, Z)

# Normalize density to [0, 1]
Z_valid = Z_masked[~np.isnan(Z_masked)]
Z_norm = (Z_masked - Z_valid.min()) / (Z_valid.max() - Z_valid.min())

# Build heatmap data list for Highcharts [col, row, value]
heatmap_data = [
    [j, i, round(float(Z_norm[i, j]), 4)]
    for i in range(grid_res)
    for j in range(grid_res)
    if not np.isnan(Z_norm[i, j])
]

# Load Highcharts modules from local npm package (CDN is blocked in CI)
_repo_root = Path(__file__).resolve().parents[4]
highcharts_js = (_repo_root / "node_modules/highcharts/highcharts.js").read_text(encoding="utf-8")
heatmap_js = (_repo_root / "node_modules/highcharts/modules/heatmap.js").read_text(encoding="utf-8")

heatmap_data_json = json.dumps(heatmap_data)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width:3600px; height:3600px;"></div>
    <script>
        var heatmapData = {heatmap_data_json};
        var gridRes = {grid_res};

        Highcharts.chart('container', {{
            chart: {{
                type: 'heatmap',
                width: 3600,
                height: 3600,
                backgroundColor: '{PAGE_BG}',
                marginTop: 230,
                marginBottom: 290,
                marginLeft: 230,
                marginRight: 330,
                events: {{
                    load: function() {{
                        var chart = this,
                            renderer = chart.renderer,
                            plotLeft = chart.plotLeft,
                            plotTop = chart.plotTop,
                            plotWidth = chart.plotWidth,
                            plotHeight = chart.plotHeight;

                        // Triangle vertices: v1=Sand(bottom-left), v2=Silt(bottom-right), v3=Clay(top)
                        var v1 = [plotLeft, plotTop + plotHeight];
                        var v2 = [plotLeft + plotWidth, plotTop + plotHeight];
                        var v3 = [plotLeft + plotWidth / 2, plotTop];

                        // Triangle outline
                        renderer.path([
                            'M', v1[0], v1[1],
                            'L', v2[0], v2[1],
                            'L', v3[0], v3[1],
                            'Z'
                        ]).attr({{
                            'stroke-width': 3,
                            stroke: '{INK}',
                            fill: 'none',
                            zIndex: 5
                        }}).add();

                        // Ternary grid lines (3 families of parallels, 10 intervals each)
                        var nGrid = 10;
                        for (var gi = 1; gi < nGrid; gi++) {{
                            var fr = gi / nGrid;

                            // Lines parallel to base (constant clay %)
                            var pa1 = [v1[0] + (v3[0] - v1[0]) * fr, v1[1] + (v3[1] - v1[1]) * fr];
                            var pa2 = [v2[0] + (v3[0] - v2[0]) * fr, v2[1] + (v3[1] - v2[1]) * fr];
                            renderer.path(['M', pa1[0], pa1[1], 'L', pa2[0], pa2[1]]).attr({{
                                'stroke-width': 1, stroke: '{INK_SOFT}', opacity: 0.25, zIndex: 4
                            }}).add();

                            // Lines parallel to left edge (constant silt %)
                            var pb1 = [v1[0] + (v2[0] - v1[0]) * fr, v1[1]];
                            var pb2 = [v3[0] + (v2[0] - v1[0]) * fr / 2, v3[1] + (v1[1] - v3[1]) * fr];
                            renderer.path(['M', pb1[0], pb1[1], 'L', pb2[0], pb2[1]]).attr({{
                                'stroke-width': 1, stroke: '{INK_SOFT}', opacity: 0.25, zIndex: 4
                            }}).add();

                            // Lines parallel to right edge (constant sand %)
                            var pc1 = [v2[0] - (v2[0] - v1[0]) * fr, v2[1]];
                            var pc2 = [v3[0] - (v2[0] - v1[0]) * fr / 2, v3[1] + (v2[1] - v3[1]) * fr];
                            renderer.path(['M', pc1[0], pc1[1], 'L', pc2[0], pc2[1]]).attr({{
                                'stroke-width': 1, stroke: '{INK_SOFT}', opacity: 0.25, zIndex: 4
                            }}).add();
                        }}

                        // Vertex labels (component name + 100%)
                        renderer.text('Sand', v1[0] - 20, v1[1] + 70)
                            .attr({{ zIndex: 6, align: 'right' }})
                            .css({{ fontSize: '42px', fontWeight: 'bold', color: '{INK}' }}).add();
                        renderer.text('100%', v1[0] - 20, v1[1] + 115)
                            .attr({{ zIndex: 6, align: 'right' }})
                            .css({{ fontSize: '28px', color: '{INK_SOFT}' }}).add();

                        renderer.text('Silt', v2[0] + 20, v2[1] + 70)
                            .attr({{ zIndex: 6 }})
                            .css({{ fontSize: '42px', fontWeight: 'bold', color: '{INK}' }}).add();
                        renderer.text('100%', v2[0] + 20, v2[1] + 115)
                            .attr({{ zIndex: 6 }})
                            .css({{ fontSize: '28px', color: '{INK_SOFT}' }}).add();

                        renderer.text('Clay', v3[0], v3[1] - 55)
                            .attr({{ zIndex: 6, align: 'center' }})
                            .css({{ fontSize: '42px', fontWeight: 'bold', color: '{INK}' }}).add();
                        renderer.text('100%', v3[0], v3[1] - 12)
                            .attr({{ zIndex: 6, align: 'center' }})
                            .css({{ fontSize: '28px', color: '{INK_SOFT}' }}).add();

                        // Tick labels on all three edges at 20%, 40%, 60%, 80%
                        for (var ti = 2; ti <= 8; ti += 2) {{
                            var tf = ti / 10;
                            var tpct = (ti * 10) + '%';

                            // Bottom edge (Silt increases left→right)
                            var bx = v1[0] + (v2[0] - v1[0]) * tf;
                            renderer.text(tpct, bx, v1[1] + 52)
                                .attr({{ zIndex: 6, align: 'center' }})
                                .css({{ fontSize: '26px', color: '{INK_MUTED}' }}).add();

                            // Left edge (Clay increases bottom→top)
                            var lx = v1[0] + (v3[0] - v1[0]) * tf;
                            var ly = v1[1] + (v3[1] - v1[1]) * tf;
                            renderer.text(tpct, lx - 55, ly + 12)
                                .attr({{ zIndex: 6, align: 'right' }})
                                .css({{ fontSize: '26px', color: '{INK_MUTED}' }}).add();

                            // Right edge (Clay increases bottom→top)
                            var rx = v2[0] + (v3[0] - v2[0]) * tf;
                            var ry = v2[1] + (v3[1] - v2[1]) * tf;
                            renderer.text(tpct, rx + 15, ry + 12)
                                .attr({{ zIndex: 6 }})
                                .css({{ fontSize: '26px', color: '{INK_MUTED}' }}).add();
                        }}
                    }}
                }}
            }},
            title: {{
                text: 'ternary-density · python · highcharts · anyplot.ai',
                style: {{ fontSize: '48px', fontWeight: 'bold', color: '{INK}' }}
            }},
            subtitle: {{
                text: 'Sediment Composition: Sand / Silt / Clay Distribution (n = {n_samples})',
                style: {{ fontSize: '30px', color: '{INK_SOFT}' }}
            }},
            xAxis: {{ visible: false, min: 0, max: gridRes - 1 }},
            yAxis: {{ visible: false, min: 0, max: gridRes - 1 }},
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
                labels: {{ style: {{ fontSize: '24px', color: '{INK_SOFT}' }} }}
            }},
            legend: {{
                enabled: true,
                title: {{
                    text: 'Density',
                    style: {{ fontSize: '28px', fontWeight: 'bold', color: '{INK}' }}
                }},
                layout: 'vertical',
                align: 'right',
                verticalAlign: 'middle',
                symbolHeight: 500,
                symbolWidth: 50,
                itemStyle: {{ color: '{INK_SOFT}' }},
                backgroundColor: '{ELEVATED_BG}',
                borderColor: '{INK_SOFT}',
                borderWidth: 1
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
                turboThreshold: 0
            }}]
        }});
    </script>
</body>
</html>"""

# Save HTML artifact (theme-suffixed)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML for Selenium screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Take screenshot with headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
