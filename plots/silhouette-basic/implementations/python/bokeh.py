""" anyplot.ai
silhouette-basic: Silhouette Plot
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-20
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Label, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions, one per cluster in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SIL_MAX = 1.0  # silhouette coefficients never exceed 1
CLUSTER_GAP = 15  # empty rows between two cluster blocks
BAR_HEIGHT = 0.85  # slightly under one row, leaves a hairline gap between bars

# Columns: set these to your table's column names
SAMPLE = "Sample"  # role: samples
CLUSTER = "Cluster"  # role: cluster_labels
SILHOUETTE = "Silhouette coefficient"  # role: silhouette_values

# Data: replace this block with your own table, for example df = pd.read_csv("silhouette.csv")
# Simulated silhouette analysis of a customer segmentation (3 clusters)
np.random.seed(42)
cluster_sizes = [50, 55, 45]
# Cluster 0: well separated, Cluster 1: good with some overlap, Cluster 2: ambiguous with negatives
sil0 = np.clip(np.random.beta(8, 2, cluster_sizes[0]) * 0.6 + 0.35, 0.1, 0.95)
sil1 = np.clip(np.random.beta(5, 2, cluster_sizes[1]) * 0.5 + 0.25, 0.0, 0.85)
sil2 = np.clip(np.random.beta(4, 3, cluster_sizes[2]) * 0.8 - 0.1, -0.15, 0.75)
df = pd.DataFrame(
    {
        SAMPLE: np.arange(sum(cluster_sizes)),
        CLUSTER: np.repeat(np.arange(len(cluster_sizes)), cluster_sizes),
        SILHOUETTE: np.concatenate([sil0, sil1, sil2]),
    }
)

# Plot: reads only df and the constants above
avg_silhouette = float(df[SILHOUETTE].mean())
x_lo = min(float(df[SILHOUETTE].min()), 0.0) - 0.15
x_hi = SIL_MAX + 0.3

bars = []
cluster_info = []
y_lower = CLUSTER_GAP
for i, (cluster, rows) in enumerate(df.groupby(CLUSTER, sort=False)):
    values = np.sort(rows[SILHOUETTE].to_numpy())
    y = y_lower + np.arange(len(values)) + 0.5
    bars.append(
        pd.DataFrame(
            {
                "x": values / 2,
                "y": y,
                "width": np.abs(values),
                "height": BAR_HEIGHT,
                "color": IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
            }
        )
    )
    cluster_info.append((y_lower + len(values) / 2, float(values.mean()), len(values), cluster, i))
    y_lower += len(values) + CLUSTER_GAP
bar_df = pd.concat(bars, ignore_index=True)

p = figure(
    width=3200,
    height=1800,
    title="silhouette-basic · python · bokeh · anyplot.ai",
    x_axis_label=SILHOUETTE,
    y_axis_label="Cluster (samples sorted by silhouette score)",
    x_range=(x_lo, x_hi),
    y_range=(0, y_lower + 5),
    tools="",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Style
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_standoff = 25
p.yaxis.axis_label_standoff = 25

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT

# One horizontal bar per sample
source = ColumnDataSource(bar_df)
p.rect(x="x", y="y", width="width", height="height", color="color", source=source, line_color=None, alpha=0.85)

# Vertical line at the average silhouette score, and the zero baseline
p.add_layout(Span(location=avg_silhouette, dimension="height", line_color=INK_SOFT, line_width=5, line_dash="dashed"))
p.add_layout(Span(location=0, dimension="height", line_color=INK_SOFT, line_width=3, line_alpha=0.5))
p.add_layout(
    Label(
        x=avg_silhouette + 0.02,
        y=y_lower - 5,
        text=f"Average: {avg_silhouette:.3f}",
        text_font_size="30pt",
        text_color=INK_SOFT,
        text_font_style="bold",
        text_baseline="top",
    )
)

# Cluster names on the left, cluster statistics on the right
for center_y, cluster_avg, size, cluster, i in cluster_info:
    p.add_layout(
        Label(
            x=x_lo + 0.03,
            y=center_y,
            text=f"Cluster {cluster}",
            text_font_size="30pt",
            text_color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
            text_font_style="bold",
            text_baseline="middle",
        )
    )
    p.add_layout(
        Label(
            x=SIL_MAX + 0.02,
            y=center_y,
            text=f"n={size}, avg={cluster_avg:.2f}",
            text_font_size="28pt",
            text_color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
            text_baseline="middle",
        )
    )

# Grid: vertical only; y positions are sample ranks, not values
p.xgrid.grid_line_color = RULE
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_alpha = 0.0
p.yaxis.major_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.yaxis.major_label_text_font_size = "0pt"

# Save as HTML, then screenshot with headless Chrome
output_file(f"plot-{THEME}.html")
save(p)

W, H = 3200, 1800
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
