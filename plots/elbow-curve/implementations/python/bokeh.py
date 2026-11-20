"""anyplot.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-10
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MIN_GAIN = 0.10  # an extra cluster that removes under this share of the total drop is past the elbow

# Columns: set these to your table's column names
CLUSTERS = "Number of clusters (k)"  # role: k_values
INERTIA = "Inertia (within-cluster sum of squares)"  # role: inertia

# Data: replace this block with your own table, for example df = pd.read_csv("inertia.csv")
np.random.seed(42)
inertia_values = [5000.0]
for k in range(2, 11):
    if k <= 4:
        # Sharp decrease before the elbow
        inertia_values.append(5000 * (0.35 ** (k - 1)) + np.random.uniform(50, 100))
    else:
        # Gradual decrease after the elbow (diminishing returns)
        inertia_values.append(inertia_values[-1] * 0.85 + np.random.uniform(20, 50))
df = pd.DataFrame({CLUSTERS: np.arange(1, 11), INERTIA: inertia_values})

# Plot: reads only df and the constants above
# Elbow = first k whose gain over k-1 is below MIN_GAIN of the total drop (diminishing returns)
gain = -df[INERTIA].diff() / (df[INERTIA].max() - df[INERTIA].min())
elbow = df.loc[(gain < MIN_GAIN).idxmax()]
elbow_k = int(elbow[CLUSTERS])
elbow_source = ColumnDataSource(pd.DataFrame([elbow]))

source = ColumnDataSource(df)

p = figure(
    width=3200,
    height=1800,
    title="elbow-curve · python · bokeh · anyplot.ai",
    x_axis_label=CLUSTERS,
    y_axis_label=INERTIA,
    tools="",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

p.line(x=CLUSTERS, y=INERTIA, source=source, line_width=6, line_color=IMPRINT_PALETTE[0], line_alpha=0.85)
p.scatter(
    x=CLUSTERS,
    y=INERTIA,
    source=source,
    size=22,
    fill_color=IMPRINT_PALETTE[0],
    line_color=PAGE_BG,
    line_width=3,
    legend_label="Inertia",
)

# Highlight the optimal k at its own point on the curve
p.scatter(
    x=CLUSTERS,
    y=INERTIA,
    source=elbow_source,
    size=38,
    fill_color=IMPRINT_PALETTE[1],
    line_color=PAGE_BG,
    line_width=4,
    legend_label=f"Elbow point (k={elbow_k})",
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"

p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK

p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# k is a count: ticks on whole numbers only
p.xaxis.ticker = df[CLUSTERS].dropna().astype(int).tolist()

p.legend.location = "top_right"
p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.padding = 20
p.legend.margin = 30
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.spacing = 12

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save HTML and screenshot with headless Chrome
html_file = Path(f"plot-{THEME}.html").resolve()
output_file(str(html_file))
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
driver.get(f"file://{html_file}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(str(Path(f"plot-{THEME}.png").resolve()))
driver.quit()
