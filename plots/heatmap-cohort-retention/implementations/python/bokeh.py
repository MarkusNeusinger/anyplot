"""anyplot.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: bokeh 3.9.1 | Python 3.13.14
Quality: 87/100 | Updated: 2026-06-20
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, HoverTool, Label, LinearColorMapper
from bokeh.plotting import figure
from bokeh.transform import transform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — Imprint palette chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint sequential colormap (imprint_seq) — single-polarity continuous retention data
# Interpolates #009E73 (brand green) → #4467A3 (blue) across 256 stops
ANYPLOT_SEQ256 = [
    "#{:02X}{:02X}{:02X}".format(round(68 * t / 255), round(158 - 55 * t / 255), round(115 + 48 * t / 255))
    for t in range(256)
]

# Data: Monthly SaaS signup cohorts with retention tracking
np.random.seed(42)
cohort_labels = [
    "Jan 2024",
    "Feb 2024",
    "Mar 2024",
    "Apr 2024",
    "May 2024",
    "Jun 2024",
    "Jul 2024",
    "Aug 2024",
    "Sep 2024",
    "Oct 2024",
]
n_cohorts = len(cohort_labels)
n_periods = 10
cohort_sizes = np.random.randint(800, 2500, size=n_cohorts)

# Generate realistic triangular retention data
retention = np.full((n_cohorts, n_periods), np.nan)
for i in range(n_cohorts):
    max_periods = n_periods - i
    retention[i, 0] = 100.0
    base_decay = np.random.uniform(0.65, 0.80)
    for j in range(1, max_periods):
        decay = base_decay + np.random.uniform(-0.05, 0.05)
        retention[i, j] = retention[i, j - 1] * decay
        retention[i, j] = max(retention[i, j], 2.0)

# Flatten into ColumnDataSource format
period_labels = [f"Month {i}" for i in range(n_periods)]
y_labels = [f"{label} (n={size:,})" for label, size in zip(cohort_labels, cohort_sizes, strict=True)]

x_coords, y_coords, values, text_vals = [], [], [], []
for i in range(n_cohorts):
    for j in range(n_periods):
        if not np.isnan(retention[i, j]):
            x_coords.append(period_labels[j])
            y_coords.append(y_labels[i])
            values.append(retention[i, j])
            text_vals.append(f"{retention[i, j]:.1f}%")

source = ColumnDataSource(data={"x": x_coords, "y": y_coords, "value": values, "text": text_vals})

# Color mapper using Imprint sequential palette
mapper = LinearColorMapper(palette=ANYPLOT_SEQ256, low=0, high=100)

# Figure — square 2400×2400 canvas for symmetric heatmap
TITLE = "heatmap-cohort-retention · python · bokeh · anyplot.ai"
W, H = 2400, 2400
p = figure(
    width=W,
    height=H,
    x_range=period_labels,
    y_range=list(reversed(y_labels)),
    title=TITLE,
    x_axis_location="above",
    toolbar_location=None,
    min_border_left=290,
    min_border_right=130,
    min_border_top=230,
    min_border_bottom=90,
)

# Heatmap rectangles with Imprint sequential fill
rects = p.rect(
    x="x",
    y="y",
    width=1,
    height=1,
    source=source,
    fill_color=transform("value", mapper),
    line_color=PAGE_BG,
    line_width=2,
)

# HoverTool — Bokeh's distinctive interactive exploration feature
hover = HoverTool(renderers=[rects], tooltips=[("Cohort", "@y"), ("Period", "@x"), ("Retention", "@text")])
p.add_tools(hover)

# Cell text — white is readable against both Imprint seq endpoints (both mid-dark)
p.text(
    x="x",
    y="y",
    text="text",
    source=source,
    text_align="center",
    text_baseline="middle",
    text_font_size="22pt",
    text_color="white",
    text_font_style="bold",
)

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = "50pt"
p.title.align = "center"
p.title.text_color = INK
p.title.text_font_style = "bold"

p.xaxis.axis_label = "Months Since Signup"
p.yaxis.axis_label = "Signup Cohort"
p.xaxis.axis_label_text_font_size = "34pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_font_style = "bold"
p.yaxis.axis_label_text_font_style = "bold"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK

p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.axis.axis_line_color = None
p.axis.major_tick_line_color = None
p.axis.minor_tick_line_color = None
p.grid.grid_line_color = None

# Insight annotation — Month 3 retention variance across cohorts
month3_retentions = {y_labels[i]: retention[i, 3] for i in range(n_cohorts) if not np.isnan(retention[i, 3])}
best_val = month3_retentions[max(month3_retentions, key=month3_retentions.get)]
worst_val = month3_retentions[min(month3_retentions, key=month3_retentions.get)]

p.add_layout(
    Label(
        x=1000,
        y=400,
        x_units="screen",
        y_units="screen",
        text=f"Month 3 retention: {worst_val:.0f}%–{best_val:.0f}% across cohorts",
        text_font_size="24pt",
        text_color=INK_MUTED,
        text_font_style="italic",
    )
)

# Color bar with theme-adaptive styling
color_bar = ColorBar(
    color_mapper=mapper,
    ticker=BasicTicker(desired_num_ticks=6),
    label_standoff=16,
    major_label_text_font_size="28pt",
    major_label_text_color=INK_SOFT,
    title="Retention %",
    title_text_font_size="30pt",
    title_text_font_style="bold",
    title_text_color=INK,
    title_standoff=20,
    width=50,
    location=(0, 0),
    bar_line_color=None,
    border_line_color=None,
    background_fill_color=PAGE_BG,
)
p.add_layout(color_bar, "right")

# Save HTML (interactive artifact) then screenshot with headless Chrome
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
# Use CDP to force exact viewport dimensions (avoids outer-window-vs-viewport discrepancy)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
