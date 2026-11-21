"""anyplot.ai
dendrogram-radial: Radial Dendrogram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import math
import os
import sys
import time
from pathlib import Path


# Prevent the local bokeh.py from shadowing the installed bokeh package
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.dirname(os.path.abspath(__file__))]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, LabelSet, Legend, LegendItem  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from scipy.cluster.hierarchy import leaves_list, linkage  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per cluster in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
GENE = "Gene"  # role: labels
CLUSTER = "Cluster"  # role: clusters

# Data: replace this block with your own table, for example df = pd.read_csv("genes.csv")
# Gene expression of 40 genes in 4 co-expressed groups under 6 conditions
rng = np.random.default_rng(42)
centers = np.array(
    [
        [2.0, 0.5, -1.0, -0.5, 1.5, -0.8],
        [-1.5, 2.0, 0.8, -1.2, 0.3, 1.5],
        [0.5, -1.5, 2.0, 1.0, -1.0, 0.5],
        [-0.8, 0.5, -1.5, 2.0, -0.5, -1.2],
    ]
)
expression = np.vstack([c + rng.normal(0, 0.3, (10, 6)) for c in centers])
df = pd.DataFrame(expression, columns=[f"Condition {i + 1}" for i in range(6)])
df[GENE] = [f"Gene-{i:02d}" for i in range(len(df))]
df[CLUSTER] = [f"Cluster {c + 1}" for c in np.repeat(np.arange(len(centers)), 10)]

# Plot: reads only df and the constants above
n_leaves = len(df)
Z = linkage(df.drop(columns=[GENE, CLUSTER]).to_numpy(), method="ward")
order = leaves_list(Z)
cluster_names = list(df[CLUSTER].unique())
leaf_cluster = df[CLUSTER].map({name: i for i, name in enumerate(cluster_names)}).to_numpy()

# Leaves sit at equal angular spacing in dendrogram order; the root (largest merge) sits at the center
leaf_angle = {int(leaf): 2 * math.pi * pos / n_leaves for pos, leaf in enumerate(order)}
max_dist = Z[-1, 2]
radius = dict.fromkeys(range(n_leaves), 1.0)
angle = dict(leaf_angle)
members = {i: {int(leaf_cluster[i])} for i in range(n_leaves)}
for k, (a, b, dist, _) in enumerate(Z):
    node = n_leaves + k
    a, b = int(a), int(b)
    radius[node] = 1.0 - dist / max_dist
    angle[node] = (angle[a] + angle[b]) / 2
    members[node] = members[a] | members[b]


def branch_color(node):
    return IMPRINT_PALETTE[next(iter(members[node]))] if len(members[node]) == 1 else INK_SOFT


seg_xs, seg_ys, seg_colors = [], [], []
for k, (a, b, _, _) in enumerate(Z):
    node = n_leaves + k
    a, b = int(a), int(b)
    for child in (a, b):
        seg_xs.append([radius[node] * math.cos(angle[child]), radius[child] * math.cos(angle[child])])
        seg_ys.append([radius[node] * math.sin(angle[child]), radius[child] * math.sin(angle[child])])
        seg_colors.append(branch_color(child))
    arc = np.linspace(angle[a], angle[b], max(3, int(abs(angle[b] - angle[a]) / (2 * math.pi) * 90)))
    seg_xs.append(list(radius[node] * np.cos(arc)))
    seg_ys.append(list(radius[node] * np.sin(arc)))
    seg_colors.append(branch_color(node))

# Leaf labels rotated along their branches; left-half labels flip so text never reads upside down
tips = pd.DataFrame(
    {
        "theta": [leaf_angle[int(leaf)] for leaf in order],
        "text": df[GENE].to_numpy()[order],
        "color": [IMPRINT_PALETTE[leaf_cluster[leaf]] for leaf in order],
    }
)
tips["x"] = 1.07 * np.cos(tips["theta"])
tips["y"] = 1.07 * np.sin(tips["theta"])
tips["dot_x"] = 1.03 * np.cos(tips["theta"])
tips["dot_y"] = 1.03 * np.sin(tips["theta"])
on_left = np.cos(tips["theta"]) < -1e-9
tips["angle"] = np.where(on_left, tips["theta"] + math.pi, tips["theta"])

# Figure
W, H = 2400, 2400
title = "dendrogram-radial · python · bokeh · anyplot.ai"
p = figure(
    width=W,
    height=H,
    title=title,
    x_range=(-1.4, 1.4),
    y_range=(-1.4, 1.4),
    toolbar_location=None,
    match_aspect=True,
    min_border_top=110,
    min_border_left=50,
    min_border_right=50,
    min_border_bottom=50,
)
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.xaxis.visible = False
p.yaxis.visible = False

for xs, ys, color in zip(seg_xs, seg_ys, seg_colors, strict=False):
    p.line(xs, ys, line_color=color, line_width=4, line_alpha=0.9)

p.scatter(x="dot_x", y="dot_y", size=16, color="color", line_color=None, source=ColumnDataSource(tips))

for side, align in ((~on_left, "left"), (on_left, "right")):
    p.add_layout(
        LabelSet(
            x="x",
            y="y",
            text="text",
            angle="angle",
            text_font_size="18pt",
            text_color=INK_SOFT,
            text_align=align,
            text_baseline="middle",
            source=ColumnDataSource(tips[side]),
        )
    )

legend_items = []
for i, name in enumerate(cluster_names):
    r = p.scatter([], [], size=26, color=IMPRINT_PALETTE[i], line_color=None)
    legend_items.append(LegendItem(label=name, renderers=[r]))
p.add_layout(
    Legend(
        items=legend_items,
        location="bottom_right",
        title=CLUSTER,
        title_text_color=INK,
        title_text_font_size="26pt",
        background_fill_color=ELEVATED_BG,
        border_line_color=INK_SOFT,
        label_text_color=INK_SOFT,
        label_text_font_size="24pt",
        glyph_width=30,
        glyph_height=30,
    )
)

p.title.text_font_size = "40pt"
p.title.text_color = INK
p.title.align = "center"

# Save
output_file(f"plot-{THEME}.html")
save(p)

opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)

driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
