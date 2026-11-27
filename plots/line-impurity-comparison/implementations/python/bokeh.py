"""anyplot.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-29
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, NumeralTickFormatter, Span
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

# Imprint palette — first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

GINI_COLOR, ENTROPY_COLOR = IMPRINT_PALETTE[0], IMPRINT_PALETTE[1]

# Columns: set these to your table's column names
P = "Probability (p)"  # role: p
GINI = "Gini impurity"  # role: extra
ENTROPY = "Entropy"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("impurity.csv")
p_vals = np.linspace(0, 1, 201)
with np.errstate(divide="ignore", invalid="ignore"):
    entropy_vals = -p_vals * np.log2(p_vals) - (1 - p_vals) * np.log2(1 - p_vals)
df = pd.DataFrame(
    {
        P: p_vals,
        GINI: 2 * p_vals * (1 - p_vals),  # already in [0, 1]
        ENTROPY: np.nan_to_num(entropy_vals, nan=0.0),  # defined as 0 at p = 0 and p = 1
    }
)

# Plot: reads only df and the constants above
source = ColumnDataSource(df)
source_diff = ColumnDataSource(
    data={"x": np.concatenate([df[P], df[P][::-1]]), "y": np.concatenate([df[ENTROPY], df[GINI][::-1]])}
)

# Peak of each curve, found from the data
gini_peak = df.loc[df[GINI].idxmax()]
entropy_peak = df.loc[df[ENTROPY].idxmax()]
peak_p = float(gini_peak[P])
gini_max = float(gini_peak[GINI])
entropy_max = float(entropy_peak[ENTROPY])
title = "line-impurity-comparison · python · bokeh · anyplot.ai"

fig = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label=P,
    y_axis_label="Impurity Measure (normalized to [0, 1])",
    x_range=(df[P].min() - 0.02, df[P].max() + 0.02),
    y_range=(-0.05, entropy_max * 1.12),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Shaded area between curves — muted fill emphasises the gap without competing
fig.patch(x="x", y="y", source=source_diff, fill_color=INK_MUTED, fill_alpha=0.08, line_alpha=0)

# Vertical reference line at p=0.5
ref_line = Span(
    location=peak_p, dimension="height", line_color=INK_SOFT, line_width=2, line_dash="dotted", line_alpha=0.5
)
fig.add_layout(ref_line)

# Lines
line_gini = fig.line(x=P, y=GINI, source=source, line_width=7, line_color=GINI_COLOR)
line_entropy = fig.line(x=P, y=ENTROPY, source=source, line_width=7, line_color=ENTROPY_COLOR, line_dash=[14, 7])

# Markers at maxima (p=0.5): Gini peaks at 0.5, Entropy peaks at 1.0
fig.scatter(
    x=[peak_p, peak_p],
    y=[gini_max, entropy_max],
    size=28,
    fill_color=[GINI_COLOR, ENTROPY_COLOR],
    line_color=PAGE_BG,
    line_width=4,
)

# Connector segment between the two maxima dots
fig.segment(
    x0=[peak_p], y0=[gini_max], x1=[peak_p], y1=[entropy_max], line_color=INK_SOFT, line_width=3, line_dash="dotted"
)

# Annotation at p=0.5 maximum impurity
max_label = Label(
    x=peak_p + 0.03,
    y=entropy_max,
    text=f"p = {peak_p:g}  (maximum impurity)",
    text_font_size="28pt",
    text_font_style="bold",
    text_color=INK,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.92,
    border_line_color=INK_SOFT,
    border_line_alpha=0.4,
    border_line_width=2,
)
fig.add_layout(max_label)

# Value labels at each maximum dot
gini_val_label = Label(
    x=peak_p * 0.36,
    y=gini_max * 0.88,
    text=f"Gini max = {gini_max:g}",
    text_font_size="22pt",
    text_color=GINI_COLOR,
    text_font_style="italic",
)
fig.add_layout(gini_val_label)

entropy_val_label = Label(
    x=peak_p + 0.06,
    y=entropy_max * 0.78,
    text=f"Entropy max = {entropy_max:g}",
    text_font_size="22pt",
    text_color=ENTROPY_COLOR,
    text_font_style="italic",
)
fig.add_layout(entropy_val_label)

# HoverTool for interactive HTML export
hover = HoverTool(
    renderers=[line_gini, line_entropy],
    tooltips=[("p", f"@{{{P}}}{{0.00}}"), (GINI, f"@{{{GINI}}}{{0.000}}"), (ENTROPY, f"@{{{ENTROPY}}}{{0.000}}")],
    mode="vline",
)
fig.add_tools(hover)

# Legend with formulas — click_policy lets viewers isolate each curve in HTML
legend = Legend(
    items=[("Gini: 2p(1−p)", [line_gini]), ("Entropy: −p log₂p − (1−p) log₂(1−p)", [line_entropy])],
    location="top_left",
    label_text_font_size="30pt",
    label_text_color=INK_SOFT,
    glyph_width=70,
    glyph_height=35,
    spacing=18,
    padding=30,
    border_line_alpha=0,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.9,
    click_policy="hide",
)
fig.add_layout(legend)

# Text sizing for 3200×1800 canvas
fig.title.text_font_size = "50pt"
fig.title.text_color = INK
fig.xaxis.axis_label_text_font_size = "42pt"
fig.yaxis.axis_label_text_font_size = "42pt"
fig.xaxis.major_label_text_font_size = "34pt"
fig.yaxis.major_label_text_font_size = "34pt"
fig.xaxis.axis_label_text_color = INK
fig.yaxis.axis_label_text_color = INK
fig.xaxis.major_label_text_color = INK_SOFT
fig.yaxis.major_label_text_color = INK_SOFT

# Tick formatters
fig.xaxis.formatter = NumeralTickFormatter(format="0.0")
fig.yaxis.formatter = NumeralTickFormatter(format="0.0")

# Grid — y-axis only, subtle
fig.xgrid.grid_line_alpha = 0
fig.ygrid.grid_line_color = INK
fig.ygrid.grid_line_alpha = 0.15
fig.ygrid.grid_line_dash = [4, 4]

# Theme-adaptive chrome
fig.background_fill_color = PAGE_BG
fig.border_fill_color = PAGE_BG
fig.outline_line_color = None

fig.xaxis.axis_line_color = INK_SOFT
fig.yaxis.axis_line_color = INK_SOFT
fig.xaxis.major_tick_line_color = INK_SOFT
fig.yaxis.major_tick_line_color = INK_SOFT
fig.axis.minor_tick_line_color = None
fig.axis.major_tick_out = 8

# Save HTML (interactive catalog artifact)
output_file(f"plot-{THEME}.html")
save(fig)

# Screenshot with headless Chrome — Selenium 4 / Selenium Manager.
# Use CDP Emulation.setDeviceMetricsOverride to pin the viewport to exactly
# W×H before navigating; --window-size alone under-delivers by ~139 px.
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
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
