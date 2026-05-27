""" anyplot.ai
dendrogram-radial: Radial Dendrogram
Library: highcharts unknown | Python 3.13.13
Quality: 82/100 | Created: 2026-05-14
"""

import json
import math
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data: simulated gene expression clustering (40 genes, 5 functional groups)
np.random.seed(42)
n_leaves = 40
n_groups = 5
gene_labels = [f"Gene{i + 1:02d}" for i in range(n_leaves)]

parts = []
for _g in range(n_groups):
    center = np.random.randn(10) * 2
    parts.append(center + np.random.randn(n_leaves // n_groups, 10) * 0.4)
expression_data = np.vstack(parts)

Z = linkage(expression_data, method="ward")
cluster_ids = fcluster(Z, t=n_groups, criterion="maxclust")

dend = dendrogram(Z, no_plot=True, labels=gene_labels)
icoord = np.array(dend["icoord"])
dcoord = np.array(dend["dcoord"])
leaves = dend["leaves"]

max_i = float(10 * n_leaves)
max_d = float(dcoord.max())


# Angle: 0° = top, clockwise.  Radius: root at center (d=max_d→r=0), leaves at edge (d=0→r=max_d)
def to_angle_rad(x):
    return math.radians((x / max_i) * 360.0)


def to_radius(d):
    return max_d - d


# Polar → Cartesian: 0° at top, clockwise
def p2c(angle_rad, r):
    return [round(r * math.sin(angle_rad), 5), round(r * math.cos(angle_rad), 5)]


def arc_cartesian(a_start_rad, a_end_rad, r):
    span_deg = abs(math.degrees(a_end_rad - a_start_rad))
    n = max(6, int(span_deg / 4))
    return [p2c(a, r) for a in np.linspace(a_start_rad, a_end_rad, n)]


# Map leaf icoord positions → cluster assignment
leaf_pos_to_cluster = {5 + 10 * i: int(cluster_ids[leaves[i]]) for i in range(n_leaves)}


def get_merge_cluster(x_left, x_right):
    clusters = {cl for pos, cl in leaf_pos_to_cluster.items() if x_left - 0.1 <= pos <= x_right + 0.1}
    return clusters.pop() if len(clusters) == 1 else 0


def cluster_color(cl):
    return IMPRINT[cl - 1] if cl > 0 else INK_SOFT


# Build Cartesian line segments grouped by cluster (0=neutral, 1-5=clusters)
# Null separates disconnected segments within each series
seg_data = {i: [] for i in range(6)}

for k in range(len(icoord)):
    x0, x1, x2, x3 = icoord[k]
    y0, y1, y2, y3 = dcoord[k]
    cl = get_merge_cluster(x0, x3)
    idx = cl

    a0 = to_angle_rad(x0)
    a3 = to_angle_rad(x3)
    r_ll = to_radius(y0)
    r_top = to_radius(y1)
    r_rl = to_radius(y3)

    if seg_data[idx]:
        seg_data[idx].append(None)

    # Left radial branch (leaf/child → merge level)
    seg_data[idx].extend([p2c(a0, r_ll), p2c(a0, r_top)])
    seg_data[idx].append(None)

    # Arc at constant radius connecting the two branches
    seg_data[idx].extend(arc_cartesian(a0, a3, r_top))
    seg_data[idx].append(None)

    # Right radial branch (leaf/child → merge level)
    seg_data[idx].extend([p2c(a3, r_rl), p2c(a3, r_top)])

# Leaf scatter markers at outer ring, colored by cluster
leaf_data = []
for i, leaf_idx in enumerate(leaves):
    a = to_angle_rad(5 + 10 * i)
    cl = int(cluster_ids[leaf_idx])
    x, y = p2c(a, max_d * 0.995)
    leaf_data.append({"x": round(x, 5), "y": round(y, 5), "color": IMPRINT[cl - 1]})

cluster_names = ["Cross-cluster", "Cluster A", "Cluster B", "Cluster C", "Cluster D", "Cluster E"]

series_list = []
for idx in range(6):
    if not seg_data[idx]:
        continue
    series_list.append(
        {
            "type": "line",
            "name": cluster_names[idx],
            "data": seg_data[idx],
            "color": cluster_color(idx),
            "lineWidth": 3,
            "marker": {"enabled": False},
            "showInLegend": idx > 0,
            "enableMouseTracking": False,
            "connectNulls": False,
        }
    )

series_list.append(
    {
        "type": "scatter",
        "name": "Genes",
        "data": leaf_data,
        "marker": {"radius": 14, "symbol": "circle"},
        "showInLegend": False,
        "enableMouseTracking": False,
    }
)

axis_range = max_d * 1.08

options = {
    "chart": {
        "type": "scatter",
        "width": 3600,
        "height": 3600,
        "backgroundColor": PAGE_BG,
        "animation": False,
        "margin": [100, 340, 60, 60],
    },
    "title": {
        "text": "Gene Expression Clustering · dendrogram-radial · highcharts · anyplot.ai",
        "style": {"fontSize": "26px", "color": INK, "fontWeight": "500"},
        "margin": 30,
        "y": 60,
    },
    "xAxis": {
        "min": -axis_range,
        "max": axis_range,
        "labels": {"enabled": False},
        "lineWidth": 0,
        "gridLineWidth": 0,
        "tickWidth": 0,
        "title": {"text": ""},
    },
    "yAxis": {
        "min": -axis_range,
        "max": axis_range,
        "labels": {"enabled": False},
        "gridLineWidth": 0,
        "lineWidth": 0,
        "tickWidth": 0,
        "title": {"text": ""},
    },
    "legend": {
        "enabled": True,
        "layout": "vertical",
        "align": "right",
        "verticalAlign": "middle",
        "itemStyle": {"color": INK_SOFT, "fontSize": "22px", "fontWeight": "normal"},
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
        "padding": 24,
        "itemMarginBottom": 16,
        "symbolRadius": 0,
        "symbolHeight": 4,
        "symbolWidth": 24,
    },
    "tooltip": {"enabled": False},
    "plotOptions": {
        "line": {"states": {"hover": {"enabled": False}}, "turboThreshold": 0},
        "scatter": {"states": {"hover": {"enabled": False}}},
        "series": {"animation": False},
    },
    "credits": {"enabled": False},
    "series": series_list,
}

# Download Highcharts JS for inline embedding (required for headless Chrome file:// URLs)
hc_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.2.0/highcharts.js"
with urllib.request.urlopen(hc_url, timeout=30) as resp:
    hc_js = resp.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{hc_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:3600px; height:3600px;"></div>
    <script>Highcharts.chart('container', {json.dumps(options)});</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

opts = Options()
opts.add_argument("--headless")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--disable-gpu")
opts.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=opts)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
