""" anyplot.ai
line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-27
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import Band, ColumnDataSource, HoverTool, Label, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import load_wine
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
THRESHOLDS = [90, 95]  # percent of variance to retain, the spec's common thresholds
PERCENT = 100  # the full scale of the y axis

# Columns: set these to your table's column names
COMPONENT = "Number of Principal Components"  # role: n_components
VARIANCE_RATIO = "Explained variance ratio"  # role: explained_variance_ratio
INDIVIDUAL = "Individual Variance (%)"  # role: extra
CUMULATIVE = "Cumulative Explained Variance (%)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("pca.csv")
wine = load_wine()
pca = PCA().fit(StandardScaler().fit_transform(wine.data))
df = pd.DataFrame(
    {COMPONENT: np.arange(1, len(pca.explained_variance_ratio_) + 1), VARIANCE_RATIO: pca.explained_variance_ratio_}
)

# Plot: reads only df and the constants above
table = df.copy()
table[INDIVIDUAL] = df[VARIANCE_RATIO] * PERCENT
table[CUMULATIVE] = df[VARIANCE_RATIO].cumsum() * PERCENT
source = ColumnDataSource(table)
components = table[COMPONENT].to_numpy()

# Crossing of each threshold: the first component count that reaches it
crossings = [int(components[np.argmax(table[CUMULATIVE].to_numpy() >= th)]) for th in THRESHOLDS]
cumulative_at = dict(zip(components, table[CUMULATIVE], strict=True))

# Title — scale fontsize if > 67 chars
title_str = "line-pca-variance-cumulative · python · bokeh · anyplot.ai"
ratio = 67 / len(title_str) if len(title_str) > 67 else 1.0
title_fontsize = f"{max(34, round(50 * ratio))}pt"

# Bars need more opacity on the dark page to stay visible
bar_alpha = 0.20 if THEME == "light" else 0.32
band_alpha = 0.08 if THEME == "light" else 0.12

p = figure(
    width=3200,
    height=1800,
    title=title_str,
    x_axis_label=COMPONENT,
    y_axis_label=CUMULATIVE,
    toolbar_location=None,
    y_range=(-0.02 * PERCENT, 1.12 * PERCENT),
    x_range=(components.min() - 0.7, components.max() + 0.7),
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=120,
)

# Area fill under the cumulative curve (Bokeh Band — library-distinctive)
p.add_layout(
    Band(
        base=COMPONENT,
        upper=CUMULATIVE,
        lower=0,
        source=source,
        fill_color=IMPRINT_PALETTE[0],
        fill_alpha=band_alpha,
        line_color=None,
    )
)

# Individual variance bars (subtle background, secondary series)
p.vbar(
    x=COMPONENT,
    top=INDIVIDUAL,
    source=source,
    width=0.5,
    fill_color=IMPRINT_PALETTE[1],
    fill_alpha=bar_alpha,
    line_color=IMPRINT_PALETTE[1],
    line_alpha=0.30,
    line_width=1.5,
    legend_label="Individual Variance",
)

# Cumulative variance line — capture renderer for HoverTool attachment
cumulative_renderer = p.line(
    x=COMPONENT,
    y=CUMULATIVE,
    source=source,
    line_width=6,
    line_color=IMPRINT_PALETTE[0],
    line_alpha=0.9,
    legend_label="Cumulative Variance",
)

# Markers at each component count
p.scatter(
    x=COMPONENT,
    y=CUMULATIVE,
    source=source,
    size=18,
    fill_color=IMPRINT_PALETTE[0],
    line_color=PAGE_BG,
    line_width=3,
    fill_alpha=0.95,
)

# Threshold reference lines, edge labels, glow rings and crossing annotations
for i, (th, crossing) in enumerate(zip(THRESHOLDS, crossings, strict=True)):
    color = IMPRINT_PALETTE[2 + i]
    value = cumulative_at[crossing]
    below = i == 0  # the lower line's labels sit below it, the upper line's above
    p.add_layout(
        Span(location=th, dimension="width", line_color=color, line_width=2.5, line_dash="dashed", line_alpha=0.7)
    )
    p.add_layout(
        Label(
            x=components.max() + 0.2,
            y=th,
            y_offset=-12 if below else 12,
            text=f"{th}%",
            text_font_size="30pt",
            text_color=color,
            text_align="right",
            text_baseline="top" if below else "bottom",
            text_font_style="bold",
        )
    )
    p.scatter(
        x=[crossing],
        y=[value],
        size=42,
        fill_color=color,
        fill_alpha=0.15,
        line_color=color,
        line_alpha=0.3,
        line_width=2,
    )
    p.scatter(x=[crossing], y=[value], size=28, fill_color=color, line_color=PAGE_BG, line_width=3, fill_alpha=0.9)
    p.add_layout(
        Label(
            x=crossing - 1.0 if below else crossing + 1.5,
            y=value - 16 if below else value + 3,
            text=f"{crossing} components ({value:.1f}%)",
            text_font_size="28pt",
            text_color=color,
            text_font_style="bold",
            text_align="center",
        )
    )

# HoverTool attached to the named renderer
p.add_tools(
    HoverTool(
        tooltips=[
            ("Component", f"@{{{COMPONENT}}}"),
            ("Cumulative Variance", f"@{{{CUMULATIVE}}}{{0.1}}%"),
            ("Individual Variance", f"@{{{INDIVIDUAL}}}{{0.1}}%"),
        ],
        mode="vline",
        renderers=[cumulative_renderer],
    )
)

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = title_fontsize
p.title.text_color = INK
p.title.align = "center"
p.title.text_font_style = "bold"

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

p.xaxis.ticker = list(components)

p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15
p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.08

p.legend.location = "center_right"
p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.border_line_width = 1
p.legend.padding = 20
p.legend.margin = 30
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.spacing = 16

# Save interactive HTML (required catalog artifact)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome — CDP override pins the inner viewport to exact dims
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
# Paint the page in the theme color so no white edge shows through the canvas
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
