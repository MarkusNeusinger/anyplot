""" anyplot.ai
bar-race-animated: Animated Bar Chart Race
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-19
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column, gridplot
from bokeh.models import ColumnDataSource, HoverTool, Range1d, Title
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — first series always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9"]

# Data: Streaming platform subscriber counts (millions) over 8 years
np.random.seed(42)

platforms = ["StreamMax", "ViewHub", "FlixNet", "WatchNow", "CineCloud", "MediaFlow"]
years = list(range(2016, 2024))
platform_colors = dict(zip(platforms, OKABE_ITO, strict=True))

# Generate realistic growth patterns
data_rows = []
base_values = [50, 80, 120, 30, 20, 40]
growth_rates = [1.35, 1.15, 1.08, 1.45, 1.55, 1.25]

for i, platform in enumerate(platforms):
    value = base_values[i]
    for year in years:
        noise = np.random.uniform(0.9, 1.1)
        value = value * growth_rates[i] * noise
        data_rows.append({"platform": platform, "year": year, "subscribers": round(value, 1)})

df = pd.DataFrame(data_rows)

# 4 key snapshots for the small multiples grid
snapshot_years = [2016, 2018, 2021, 2023]
max_subscribers = df["subscribers"].max() * 1.15

# Build individual plots for each snapshot year
plots = []
for idx, year in enumerate(snapshot_years):
    year_data = df[df["year"] == year].copy()
    year_data = year_data.sort_values("subscribers", ascending=True)

    y_positions = list(range(len(platforms)))
    bar_colors = [platform_colors[p] for p in year_data["platform"]]

    source = ColumnDataSource(
        data={
            "y": y_positions,
            "right": year_data["subscribers"].tolist(),
            "platform": year_data["platform"].tolist(),
            "color": bar_colors,
        }
    )

    p = figure(
        width=2400,
        height=1120,
        x_range=Range1d(0, max_subscribers),
        y_range=(-0.5, len(platforms) - 0.5),
        x_axis_label="Subscribers (millions)" if idx >= 2 else None,
        tools="",
        toolbar_location=None,
    )

    # Year title above each panel
    p.add_layout(Title(text=str(year), text_font_size="36pt", text_font_style="bold", text_color=INK), "above")

    # Horizontal bars
    bars = p.hbar(
        y="y", right="right", height=0.65, source=source, color="color", alpha=0.9, line_color=PAGE_BG, line_width=2
    )

    # HoverTool for HTML interactivity
    hover = HoverTool(renderers=[bars], tooltips=[("Platform", "@platform"), ("Subscribers", "@right{0.0}M")])
    p.add_tools(hover)

    # Platform labels inside bars
    platform_list = year_data["platform"].tolist()
    for _, row in year_data.iterrows():
        y_pos = platform_list.index(row["platform"])
        p.text(
            x=[row["subscribers"] * 0.03],
            y=[y_pos],
            text=[row["platform"]],
            text_font_size="18pt",
            text_font_style="bold",
            text_color="white",
            text_baseline="middle",
        )
        # Value labels at bar end
        p.text(
            x=[row["subscribers"] + max_subscribers * 0.01],
            y=[y_pos],
            text=[f"{row['subscribers']:.0f}M"],
            text_font_size="16pt",
            text_color=INK_SOFT,
            text_baseline="middle",
        )

    # Theme-adaptive chrome
    p.background_fill_color = PAGE_BG
    p.border_fill_color = PAGE_BG
    p.outline_line_color = None
    p.yaxis.visible = False
    p.xaxis.axis_label_text_font_size = "22pt"
    p.xaxis.axis_label_text_color = INK
    p.xaxis.major_label_text_font_size = "18pt"
    p.xaxis.major_label_text_color = INK_SOFT
    p.xaxis.axis_line_color = INK_SOFT
    p.xaxis.major_tick_line_color = INK_SOFT
    p.xgrid.grid_line_color = INK
    p.xgrid.grid_line_alpha = 0.08
    p.ygrid.grid_line_color = None
    p.min_border_right = 110

    plots.append(p)

# 2×2 grid
grid = gridplot([[plots[0], plots[1]], [plots[2], plots[3]]], merge_tools=False)

# Overall title figure
title_fig = figure(width=4800, height=130, tools="", toolbar_location=None, x_range=(0, 1), y_range=(0, 1))
title_fig.background_fill_color = PAGE_BG
title_fig.border_fill_color = PAGE_BG
title_fig.outline_line_color = None
title_fig.xaxis.visible = False
title_fig.yaxis.visible = False
title_fig.xgrid.grid_line_color = None
title_fig.ygrid.grid_line_color = None
title_fig.text(
    x=[0.5],
    y=[0.5],
    text=["bar-race-animated · python · bokeh · anyplot.ai"],
    text_font_size="32pt",
    text_font_style="bold",
    text_align="center",
    text_baseline="middle",
    text_color=INK,
)

# Color legend strip at the bottom
n = len(platforms)
legend_fig = figure(width=4800, height=105, tools="", toolbar_location=None, x_range=(0, n), y_range=(0, 1))
legend_fig.background_fill_color = PAGE_BG
legend_fig.border_fill_color = PAGE_BG
legend_fig.outline_line_color = None
legend_fig.xaxis.visible = False
legend_fig.yaxis.visible = False
legend_fig.xgrid.grid_line_color = None
legend_fig.ygrid.grid_line_color = None

for i, (platform, color) in enumerate(zip(platforms, OKABE_ITO, strict=True)):
    legend_fig.rect(x=[i + 0.12], y=[0.5], width=0.17, height=0.5, color=color, alpha=0.9)
    legend_fig.text(
        x=[i + 0.25], y=[0.5], text=[platform], text_font_size="20pt", text_color=INK_SOFT, text_baseline="middle"
    )

# Full layout
layout = column(title_fig, grid, legend_fig)

# Save HTML
output_file(f"plot-{THEME}.html")
save(layout)

# Screenshot with headless Chrome
W, H = 4800, 2700
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
