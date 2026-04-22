""" pyplots.ai
heatmap-clustered: Clustered Heatmap
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.heatmap import HeatmapSeries
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Gene expression data (simulated microarray experiment)
np.random.seed(42)
n_genes = 20
n_samples = 12

# Sample names (experimental conditions)
sample_labels = [
    "Control_1",
    "Control_2",
    "Control_3",
    "Drug_A_1",
    "Drug_A_2",
    "Drug_A_3",
    "Drug_B_1",
    "Drug_B_2",
    "Drug_B_3",
    "Drug_C_1",
    "Drug_C_2",
    "Drug_C_3",
]

# Gene names
gene_labels = [f"Gene_{i + 1:02d}" for i in range(n_genes)]

# Generate expression data with cluster structure
base_pattern = np.zeros((n_genes, n_samples))

# Group 1: Genes upregulated by Drug A (genes 0-5)
base_pattern[0:6, 3:6] = 2.5
base_pattern[0:6, 0:3] = -0.5

# Group 2: Genes upregulated by Drug B (genes 6-11)
base_pattern[6:12, 6:9] = 2.0
base_pattern[6:12, 0:3] = -0.3

# Group 3: Genes upregulated by Drug C (genes 12-16)
base_pattern[12:17, 9:12] = 2.2
base_pattern[12:17, 0:3] = -0.4

# Group 4: Genes downregulated by all drugs (genes 17-19)
base_pattern[17:20, 3:12] = -1.8
base_pattern[17:20, 0:3] = 0.5

# Add noise
expression_data = base_pattern + np.random.randn(n_genes, n_samples) * 0.5

# Perform hierarchical clustering
row_linkage = linkage(pdist(expression_data, metric="euclidean"), method="ward")
col_linkage = linkage(pdist(expression_data.T, metric="euclidean"), method="ward")

# Get the reordering from dendrograms
row_dendro = dendrogram(row_linkage, no_plot=True)
col_dendro = dendrogram(col_linkage, no_plot=True)
row_order = row_dendro["leaves"]
col_order = col_dendro["leaves"]

# Reorder data and labels
reordered_data = expression_data[row_order, :][:, col_order]
reordered_gene_labels = [gene_labels[i] for i in row_order]
reordered_sample_labels = [sample_labels[i] for i in col_order]

# Prepare heatmap data for Highcharts
heatmap_data = []
for i in range(n_genes):
    for j in range(n_samples):
        heatmap_data.append([j, n_genes - 1 - i, round(reordered_data[i, j], 2)])

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration - use square format for clustered heatmap
chart.options.chart = {
    "type": "heatmap",
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#ffffff",
    "marginTop": 380,
    "marginBottom": 320,
    "marginLeft": 380,
    "marginRight": 260,
}

# Title
chart.options.title = {
    "text": "Gene Expression Clusters \u00b7 heatmap-clustered \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "42px", "fontWeight": "bold"},
    "y": 40,
}

# Subtitle
chart.options.subtitle = {
    "text": "Hierarchical clustering reveals drug-specific expression patterns",
    "style": {"fontSize": "28px", "color": "#666666"},
    "y": 90,
}

# X-axis (samples)
chart.options.x_axis = {
    "categories": reordered_sample_labels,
    "title": {"text": "Samples", "style": {"fontSize": "36px"}, "y": 20},
    "labels": {"style": {"fontSize": "24px"}, "rotation": 315},
    "opposite": False,
}

# Y-axis (genes) - reversed so Gene_01 is at top visually
chart.options.y_axis = {
    "categories": list(reversed(reordered_gene_labels)),
    "title": {"text": "Genes", "style": {"fontSize": "36px"}, "x": -30},
    "labels": {"style": {"fontSize": "22px"}},
    "reversed": False,
}

# Color axis - diverging colormap (blue-white-red for expression data)
vmin = float(np.min(reordered_data))
vmax = float(np.max(reordered_data))
vabs = max(abs(vmin), abs(vmax))

chart.options.color_axis = {
    "min": -vabs,
    "max": vabs,
    "stops": [[0, "#306998"], [0.5, "#FFFFFF"], [1, "#B40426"]],
    "labels": {"style": {"fontSize": "24px"}},
}

# Legend (colorbar)
chart.options.legend = {
    "align": "right",
    "layout": "vertical",
    "verticalAlign": "middle",
    "symbolHeight": 500,
    "itemStyle": {"fontSize": "22px"},
    "title": {"text": "Expression", "style": {"fontSize": "24px"}},
}

# Tooltip
chart.options.tooltip = {"style": {"fontSize": "22px"}}

# Create and add heatmap series
series = HeatmapSeries()
series.name = "Expression"
series.data = heatmap_data
series.border_width = 1
series.border_color = "#ffffff"
series.data_labels = {"enabled": False}

chart.add_series(series)


# Generate dendrogram SVG paths for drawing
def get_dendro_paths(linkage_matrix, n_leaves, orientation, plot_area):
    """Generate SVG path strings for dendrogram."""
    dendro_info = dendrogram(linkage_matrix, no_plot=True)
    icoord = np.array(dendro_info["icoord"])
    dcoord = np.array(dendro_info["dcoord"])

    # Normalize height
    if len(dcoord) > 0:
        max_d = dcoord.max()
        if max_d > 0:
            dcoord = dcoord / max_d

    svg_paths = []
    for xs, ys in zip(icoord, dcoord, strict=True):
        if orientation == "top":
            # Column dendrogram above heatmap
            x_scale = plot_area["width"] / (n_leaves * 10)
            x_offset = plot_area["left"]
            y_scale = plot_area["dendro_height"]
            y_offset = plot_area["top"] - 30

            px = [x * x_scale + x_offset for x in xs]
            py = [y_offset - y * y_scale for y in ys]
        else:
            # Row dendrogram left of heatmap
            y_scale = plot_area["height"] / (n_leaves * 10)
            y_offset = plot_area["top"]
            x_scale = plot_area["dendro_width"]
            x_offset = plot_area["left"] - 50  # More space from labels

            px = [x_offset - y * x_scale for y in ys]
            py = [(n_leaves * 10 - x) * y_scale + y_offset for x in xs]

        # SVG path string
        path = (
            f"M {px[0]:.0f} {py[0]:.0f} L {px[1]:.0f} {py[1]:.0f} L {px[2]:.0f} {py[2]:.0f} L {px[3]:.0f} {py[3]:.0f}"
        )
        svg_paths.append(path)

    return svg_paths


# Plot area dimensions (must match chart margins)
plot_area = {
    "left": 380,
    "top": 380,
    "width": 3600 - 380 - 260,
    "height": 3600 - 380 - 320,
    "dendro_height": 220,
    "dendro_width": 170,
}

col_paths = get_dendro_paths(col_linkage, n_samples, "top", plot_area)
row_paths = get_dendro_paths(row_linkage, n_genes, "left", plot_area)

# Download Highcharts JS and heatmap module
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

heatmap_url = "https://code.highcharts.com/modules/heatmap.js"
with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

# Generate base chart JS
html_str = chart.to_js_literal()

# Create SVG elements for dendrograms as inline SVG overlay
all_paths = col_paths + row_paths
svg_path_elements = "\n".join([f'<path d="{p}" stroke="#306998" stroke-width="3" fill="none"/>' for p in all_paths])

# Generate HTML with inline scripts and SVG overlay for dendrograms
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
    <style>
        #dendro-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            width: 3600px;
            height: 3600px;
            pointer-events: none;
        }}
    </style>
</head>
<body style="margin:0; background-color: #ffffff; position: relative;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <svg id="dendro-overlay" viewBox="0 0 3600 3600">
        {svg_path_elements}
    </svg>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML file for screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save interactive HTML version
with open("plot.html", "w", encoding="utf-8") as f:
    standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/heatmap.js"></script>
    <style>
        #dendro-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100vh;
            pointer-events: none;
        }}
    </style>
</head>
<body style="margin:0; background-color: #ffffff; position: relative;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <svg id="dendro-overlay" viewBox="0 0 3600 3600" preserveAspectRatio="xMidYMid meet">
        {svg_path_elements}
    </svg>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(standalone_html)

# Configure headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3600")

# Take screenshot
driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
