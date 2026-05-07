""" anyplot.ai
horizon-basic: Horizon Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-07
"""

import os
import sys
import time
from pathlib import Path


# Remove current directory from path FIRST to avoid conflict with local bokeh.py filename
# This must happen before any imports that might add "." back to sys.path
while "" in sys.path:
    sys.path.remove("")
while "." in sys.path:
    sys.path.remove(".")
# Also clear any bokeh module already in sys.modules
if "bokeh" in sys.modules:
    del sys.modules["bokeh"]

import numpy as np  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.layouts import column  # noqa: E402
from bokeh.models import ColumnDataSource, CrosshairTool, HoverTool, Label, Range1d, Title  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Server metrics over 24 hours for 6 servers
np.random.seed(42)

n_points = 200
n_series = 6
server_names = ["Web Server 1", "Web Server 2", "Database", "Cache Server", "API Gateway", "Load Balancer"]

# Create time series data with different patterns
hours = np.linspace(0, 24, n_points)

# Each server has a different pattern
series_data = []
for i, name in enumerate(server_names):
    # Base pattern with some periodicity
    base = np.sin(hours * np.pi / 6 + i * 0.5) * 20
    # Add some noise and trends
    noise = np.random.randn(n_points) * 10
    trend = np.sin(hours * np.pi / 12) * 15 * (1 + i * 0.2)
    # Add some spikes for realism
    spikes = np.zeros(n_points)
    spike_locations = np.random.choice(n_points, size=5, replace=False)
    spikes[spike_locations] = np.random.randn(5) * 30

    values = base + noise + trend + spikes
    series_data.append({"name": name, "hours": hours, "values": values})

# Horizon chart parameters
n_bands = 3  # Number of positive/negative bands
chart_width = 4800
total_height = 2700
individual_height = total_height // n_series  # ~450px per series

# Okabe-Ito palette positions for color intensity (position 1 for primary, positions 2-3 for intensity)
pos_colors = ["#56B4E9", "#0072B2", "#004494"]  # Light to dark blue (Okabe-Ito positions 6, 3, variant)
neg_colors = ["#E69F00", "#D55E00", "#8B3A00"]  # Light to dark orange (Okabe-Ito positions 5, 2, variant)

# Create individual horizon plots
plots = []

for idx, data in enumerate(series_data):
    values = data["values"]
    x = data["hours"]
    name = data["name"]

    # Normalize values to fit in bands
    max_abs = np.max(np.abs(values))
    band_size = max_abs / n_bands

    # Create figure for this series
    p = figure(
        width=chart_width,
        height=individual_height,
        x_range=Range1d(0, 24),
        y_range=Range1d(0, band_size),
        tools="pan,wheel_zoom,box_zoom,reset,hover",
        toolbar_location="right" if idx == 0 else None,
    )

    # Theme-adaptive background - clean minimalist style with no outline borders
    p.background_fill_color = PAGE_BG
    p.border_fill_color = PAGE_BG
    p.outline_line_color = None

    # Configure axes
    if idx < len(series_data) - 1:
        p.xaxis.visible = False
    else:
        p.xaxis.axis_label = "Hour of Day (0-24h)"
        p.xaxis.axis_label_text_font_size = "22pt"
        p.xaxis.major_label_text_font_size = "18pt"
        p.xaxis.axis_label_text_color = INK
        p.xaxis.major_label_text_color = INK_SOFT
        p.xaxis.axis_line_color = INK_SOFT

    p.yaxis.visible = False
    p.grid.visible = False

    # Add series name as label on the left
    label = Label(
        x=0.3,
        y=band_size * 0.5,
        text=name,
        text_font_size="26pt",
        text_font_style="bold",
        text_align="left",
        text_baseline="middle",
        text_color=INK,
    )
    p.add_layout(label)

    # Add customized HoverTool showing actual values and crosshair for better interactivity
    hover = HoverTool(tooltips=[("Server", name), ("Hour", "@x{0.1}"), ("Value", "@original{0.1}")], mode="vline")
    p.add_tools(hover)

    # Add crosshair tool for precision reading
    crosshair = CrosshairTool(dimensions="both", line_color=INK_SOFT, line_alpha=0.4)
    p.add_tools(crosshair)

    # Draw horizon bands (folded areas)
    for band_idx in range(n_bands):
        band_min = band_idx * band_size

        # Positive values for this band
        pos_vals = np.clip(values - band_min, 0, band_size)
        pos_vals = np.where(values > band_min, pos_vals, 0)

        # Negative values for this band (mirrored)
        neg_vals = np.clip(-values - band_min, 0, band_size)
        neg_vals = np.where(values < -band_min, neg_vals, 0)

        # Create patches for positive band
        if np.any(pos_vals > 0):
            source_pos = ColumnDataSource(data={"x": x, "y": pos_vals, "original": values})
            p.varea(x="x", y1=0, y2="y", source=source_pos, fill_color=pos_colors[band_idx], fill_alpha=0.9)

        # Create patches for negative band
        if np.any(neg_vals > 0):
            source_neg = ColumnDataSource(data={"x": x, "y": neg_vals, "original": values})
            p.varea(x="x", y1=0, y2="y", source=source_neg, fill_color=neg_colors[band_idx], fill_alpha=0.9)

    plots.append(p)

# Add main title to the first plot with enhanced styling for visual hierarchy
title = Title(
    text="Server Metrics: Hourly Performance Across 24 Hours", text_font_size="32pt", align="center", text_color=INK
)
plots[0].add_layout(title, "above")

# Add subtitle with library and source attribution
subtitle = Title(text="horizon-basic · bokeh · anyplot.ai", text_font_size="18pt", align="center", text_color=INK_SOFT)
plots[0].add_layout(subtitle, "above")

# Create legend figure explaining color bands - refined styling with elevated background
legend_height = 220
legend_fig = figure(
    width=chart_width,
    height=legend_height,
    x_range=Range1d(0, 100),
    y_range=Range1d(0, 10),
    tools="",
    toolbar_location=None,
)
legend_fig.xaxis.visible = False
legend_fig.yaxis.visible = False
legend_fig.grid.visible = False
# Use elevated background for better visual distinction
legend_fig.background_fill_color = ELEVATED_BG
legend_fig.border_fill_color = ELEVATED_BG
legend_fig.outline_line_color = None

# Add legend title with enhanced styling
legend_fig.add_layout(
    Label(
        x=3, y=8.5, text="Color Bands & Intensity Levels", text_font_size="26pt", text_font_style="bold", text_color=INK
    )
)

# Positive bands legend (left side) - enhanced visual styling
legend_fig.add_layout(
    Label(
        x=20, y=7.8, text="Positive Values (above zero):", text_font_size="20pt", text_font_style="bold", text_color=INK
    )
)
for i, (color, label_text) in enumerate(zip(pos_colors, ["Low (+)", "Medium (+)", "High (+)"], strict=True)):
    # Add subtle background for better visual definition
    legend_fig.rect(x=22 + i * 10, y=5, width=9, height=5.5, fill_color=color, line_color=None, fill_alpha=0.85)
    legend_fig.add_layout(
        Label(x=22 + i * 10, y=2.3, text=label_text, text_font_size="18pt", text_align="center", text_color=INK_SOFT)
    )

# Negative bands legend (right side) - enhanced visual styling
legend_fig.add_layout(
    Label(
        x=56, y=7.8, text="Negative Values (below zero):", text_font_size="20pt", text_font_style="bold", text_color=INK
    )
)
for i, (color, label_text) in enumerate(zip(neg_colors, ["Low (−)", "Medium (−)", "High (−)"], strict=True)):
    # Add subtle background for better visual definition
    legend_fig.rect(x=58 + i * 10, y=5, width=9, height=5.5, fill_color=color, line_color=None, fill_alpha=0.85)
    legend_fig.add_layout(
        Label(x=58 + i * 10, y=2.3, text=label_text, text_font_size="18pt", text_align="center", text_color=INK_SOFT)
    )

# Combine all plots vertically with legend at top
layout = column(legend_fig, *plots)

# Save as HTML (interactive)
output_file(f"plot-{THEME}.html")
save(layout)

# Screenshot with headless Chrome for PNG
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
