""" anyplot.ai
rose-basic: Basic Rose Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-04-30
"""

import os
import sys


# Remove this script's directory from sys.path to prevent bokeh.py from
# shadowing the installed bokeh package when Python adds the script dir.
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _script_dir]

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Monthly rainfall (mm) showing seasonal patterns
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
values = [85, 70, 65, 45, 30, 20, 15, 25, 40, 60, 75, 90]
max_val = max(values)
n = len(months)
angle_width = 2 * np.pi / n

# Calculate wedge angles (equal slices, starting from top/north)
start_angles = np.array([np.pi / 2 - angle_width / 2 - i * angle_width for i in range(n)])
end_angles = start_angles - angle_width
center_angles = (start_angles + end_angles) / 2

# Normalize values to radius (max value = 1.0)
radii = [v / max_val for v in values]

# Brand green with alpha varying by rainfall intensity
alphas = [0.35 + 0.65 * (v / max_val) for v in values]

source = ColumnDataSource(
    data={"start_angle": start_angles, "end_angle": end_angles, "radius": radii, "alphas": alphas}
)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="Monthly Rainfall · rose-basic · bokeh · anyplot.ai",
    x_range=(-1.5, 1.5),
    y_range=(-1.3, 1.35),
    tools="",
    toolbar_location=None,
)

# Draw wedges (rose petals)
p.wedge(
    x=0,
    y=0,
    radius="radius",
    start_angle="end_angle",
    end_angle="start_angle",
    source=source,
    fill_color=BRAND,
    fill_alpha="alphas",
    line_color=PAGE_BG,
    line_width=2,
)

# Radial gridlines (concentric circles)
theta = np.linspace(0, 2 * np.pi, 200)
for r in [0.25, 0.5, 0.75, 1.0]:
    p.line(r * np.cos(theta), r * np.sin(theta), line_color=INK, line_alpha=0.22, line_width=1.5, line_dash="dashed")

# Radial divider lines from center
for i in range(n):
    angle = np.pi / 2 - i * angle_width
    p.line([0, 1.05 * np.cos(angle)], [0, 1.05 * np.sin(angle)], line_color=INK, line_alpha=0.18, line_width=1)

# Month labels centered in each wedge
label_radius = 1.15
for i, month in enumerate(months):
    angle = center_angles[i]
    p.text(
        x=[label_radius * np.cos(angle)],
        y=[label_radius * np.sin(angle)],
        text=[month],
        text_align="center",
        text_baseline="middle",
        text_font_size="20pt",
        text_color=INK,
    )

# Rainfall scale labels (actual mm values, right side)
for r in [0.25, 0.5, 0.75, 1.0]:
    val_label = f"{int(r * max_val + 0.5)} mm"
    p.text(x=[1.2], y=[r], text=[val_label], text_font_size="15pt", text_color=INK_SOFT, text_align="left")

# Title and chrome
p.title.text_font_size = "28pt"
p.title.align = "center"
p.title.text_color = INK
p.title.text_font_style = "normal"

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Hide axes (not needed for rose chart)
p.axis.visible = False
p.grid.visible = False

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)
