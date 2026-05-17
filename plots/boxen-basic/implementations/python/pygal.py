"""anyplot.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: pygal | Python 3.13
Quality: pending | Created: 2026-05-17
"""

import importlib
import os
import sys

import numpy as np


# Avoid name collision with this script's filename by removing current directory from path
script_dir = sys.path[0]
sys.path.pop(0)
pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style
sys.path.insert(0, script_dir)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data - Server response times (ms) across 4 endpoints
np.random.seed(42)
endpoints = ["API-Auth", "API-Search", "API-Report", "API-Download"]

# Generate realistic response time distributions (skewed, with outliers)
api_auth = np.concatenate(
    [
        np.random.gamma(shape=2, scale=20, size=3500),  # Main distribution
        np.random.uniform(200, 1000, size=200),  # Outliers
    ]
)

api_search = np.concatenate([np.random.gamma(shape=1.5, scale=30, size=3500), np.random.uniform(300, 1200, size=200)])

api_report = np.concatenate([np.random.gamma(shape=2.5, scale=25, size=3500), np.random.uniform(250, 900, size=200)])

api_download = np.concatenate([np.random.gamma(shape=2, scale=35, size=3500), np.random.uniform(400, 1500, size=200)])

# Create custom style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=2,
)

# Create box plot
box_chart = pygal.Box(
    title="boxen-basic · pygal · anyplot.ai",
    x_title="Endpoint",
    y_title="Response Time (ms)",
    width=4800,
    height=2700,
    style=custom_style,
    show_legend=False,
    range=(0, 1200),
)

# Add data series for each endpoint
box_chart.add("API-Auth", api_auth.tolist())
box_chart.add("API-Search", api_search.tolist())
box_chart.add("API-Report", api_report.tolist())
box_chart.add("API-Download", api_download.tolist())

# Set x-axis labels
box_chart.x_labels = endpoints

# Save outputs
box_chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(box_chart.render())
