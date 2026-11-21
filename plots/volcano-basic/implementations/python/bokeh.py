"""anyplot.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-14
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
P_THRESHOLD = 0.05  # significance cutoff on the p-value
FC_THRESHOLD = 1.0  # log2(2): a 2-fold change in either direction
UP, DOWN, NS = "Up-regulated", "Down-regulated", "Not significant"
STATUS_COLORS = {NS: INK_MUTED, DOWN: IMPRINT_PALETTE[2], UP: IMPRINT_PALETTE[4]}  # gray, blue, red

# Columns: set these to your table's column names
LOG2_FC = "Log₂ Fold Change"  # role: log2_fold_change
NEG_LOG_P = "-Log₁₀ (P-value)"  # role: neg_log10_pvalue

# Data: replace this block with your own table, for example df = pd.read_csv("de_results.csv")
np.random.seed(42)
n_genes = 2000
fold_change = np.random.normal(0, 1.5, n_genes)
base_pvals = np.random.uniform(0.001, 1, n_genes)
fold_effect = np.abs(fold_change) / np.max(np.abs(fold_change))
pvals = base_pvals * (1 - 0.7 * fold_effect) + 0.01 * np.random.random(n_genes)
pvals = np.clip(pvals, 1e-50, 1)
df = pd.DataFrame({LOG2_FC: fold_change, NEG_LOG_P: -np.log10(pvals)})

# Plot: reads only df and the constants above
p_cutoff = -np.log10(P_THRESHOLD)
significant = df[NEG_LOG_P] > p_cutoff
STATUS = "Status"
df[STATUS] = np.select(
    [significant & (df[LOG2_FC] > FC_THRESHOLD), significant & (df[LOG2_FC] < -FC_THRESHOLD)], [UP, DOWN], default=NS
)

p = figure(
    width=3200,
    height=1800,
    title="volcano-basic · python · bokeh · anyplot.ai",
    x_axis_label=LOG2_FC,
    y_axis_label=NEG_LOG_P,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Non-significant first, significant on top; alpha keeps the dense mass readable
glyphs = []
for status, size, alpha in ((NS, 12, 0.5), (DOWN, 16, 0.7), (UP, 16, 0.7)):
    rows = ColumnDataSource(df[df[STATUS] == status])
    glyphs.append(
        p.scatter(
            x=LOG2_FC,
            y=NEG_LOG_P,
            source=rows,
            color=STATUS_COLORS[status],
            size=size,
            alpha=alpha,
            legend_label=status,
        )
    )
p.add_tools(
    HoverTool(
        renderers=glyphs,
        tooltips=[
            (STATUS, f"@{{{STATUS}}}"),
            (LOG2_FC, f"@{{{LOG2_FC}}}{{0.00}}"),
            (NEG_LOG_P, f"@{{{NEG_LOG_P}}}{{0.00}}"),
        ],
    )
)

# Threshold lines
for location, dimension in ((p_cutoff, "width"), (FC_THRESHOLD, "height"), (-FC_THRESHOLD, "height")):
    p.add_layout(
        Span(
            location=location,
            dimension=dimension,
            line_color=INK_SOFT,
            line_dash="dashed",
            line_width=2,
            line_alpha=0.6,
        )
    )

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.1
p.ygrid.grid_line_alpha = 0.1
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.legend.location = "top_right"
p.legend.label_text_font_size = "30pt"
p.legend.label_text_color = INK_SOFT
p.legend.glyph_height = 36
p.legend.glyph_width = 36
p.legend.spacing = 10
p.legend.padding = 16
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
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
