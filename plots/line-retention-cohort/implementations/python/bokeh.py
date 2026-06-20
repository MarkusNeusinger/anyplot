""" anyplot.ai
line-retention-cohort: User Retention Curve by Cohort
Library: bokeh 3.9.1 | Python 3.13.14
Quality: 89/100 | Updated: 2026-06-20
"""

import io
import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, Span
from bokeh.plotting import figure
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — positions 1-5
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data — wider decay spread (0.22 → 0.06) so curves diverge clearly at week 12
np.random.seed(42)
weeks = np.arange(0, 13)

cohorts = {
    "Jan 2025": {"size": 1245, "decay": 0.22},
    "Feb 2025": {"size": 1380, "decay": 0.17},
    "Mar 2025": {"size": 1520, "decay": 0.13},
    "Apr 2025": {"size": 1410, "decay": 0.09},
    "May 2025": {"size": 1680, "decay": 0.06},
}

retention_data = {}
for cohort, params in cohorts.items():
    base = 100 * np.exp(-params["decay"] * weeks)
    noise = np.random.normal(0, 1.2, len(weeks))
    retention = np.clip(base + noise, 0, 100)
    retention[0] = 100.0
    retention_data[cohort] = retention

# Title — 52 chars, under the 67-char baseline; no scaling needed
title = "line-retention-cohort · python · bokeh · anyplot.ai"

# Plot — 3200×1800 landscape canvas, toolbar hidden for static PNG
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label="Weeks Since Signup",
    y_axis_label="Retention Rate (%)",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

# Progressive visual weight: older cohorts are thinner and more transparent
line_widths = [2.5, 3.0, 3.5, 4.5, 5.5]
alphas = [0.55, 0.65, 0.75, 0.88, 1.0]
dash_patterns = ["dashed", "dashed", "solid", "solid", "solid"]

legend_items = []
for i, (cohort, params) in enumerate(cohorts.items()):
    source = ColumnDataSource(
        data={
            "week": weeks,
            "retention": retention_data[cohort],
            "cohort": [cohort] * len(weeks),
            "size": [params["size"]] * len(weeks),
            "retention_fmt": [f"{r:.1f}" for r in retention_data[cohort]],
        }
    )
    label = f"{cohort} (n={params['size']:,})"
    color = IMPRINT_PALETTE[i]

    line = p.line(
        x="week",
        y="retention",
        source=source,
        line_width=line_widths[i],
        line_color=color,
        line_alpha=alphas[i],
        line_dash=dash_patterns[i],
    )
    scatter = p.scatter(
        x="week",
        y="retention",
        source=source,
        size=9 + i * 2,
        fill_color=color,
        fill_alpha=alphas[i],
        line_color=PAGE_BG,
        line_width=2,
    )
    legend_items.append((label, [line, scatter]))

# HoverTool for interactive HTML
hover = HoverTool(
    tooltips=[("Cohort", "@cohort"), ("Week", "@week"), ("Retention", "@retention_fmt%"), ("Cohort Size", "@size{,}")],
    mode="mouse",
)
p.add_tools(hover)

# Reference line at 20% retention threshold
threshold = Span(
    location=20, dimension="width", line_color=INK_MUTED, line_dash="dashed", line_width=2.5, line_alpha=0.75
)
p.add_layout(threshold)

threshold_label = Label(
    x=11.8, y=20, text="20% threshold", text_font_size="26pt", text_color=INK_MUTED, y_offset=10, text_align="right"
)
p.add_layout(threshold_label)

# Legend — larger text for canvas readability
legend = Legend(items=legend_items, location="top_right")
legend.label_text_font_size = "28pt"
legend.label_text_color = INK_SOFT
legend.glyph_height = 36
legend.glyph_width = 36
legend.spacing = 14
legend.padding = 24
legend.background_fill_color = ELEVATED_BG
legend.background_fill_alpha = 0.92
legend.border_line_color = INK_SOFT
legend.border_line_alpha = 0.3
p.add_layout(legend)

# Axis ranges
p.y_range.start = 0
p.y_range.end = 105
p.x_range.start = -0.3
p.x_range.end = 12.3

# Theme-adaptive chrome
p.title.text_font_size = "50pt"
p.title.text_color = INK

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

p.xgrid.grid_line_alpha = 0
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.12

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None  # remove box frame — L-shape via axes only

p.axis.axis_line_width = 2

# Save HTML (no toolbar) for screenshot
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot via headless Chrome — use oversized viewport then crop to exact canvas
W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H + 200}",  # extra height absorbs any browser chrome overhead
    "--hide-scrollbars",
    "--force-device-scale-factor=1",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H + 200)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
raw_png = driver.get_screenshot_as_png()
driver.quit()
img = Image.open(io.BytesIO(raw_png)).crop((0, 0, W, H))
img.save(f"plot-{THEME}.png")

# Re-save HTML with toolbar for the interactive catalog artifact
p.toolbar_location = "above"
output_file(f"plot-{THEME}.html")
save(p)
