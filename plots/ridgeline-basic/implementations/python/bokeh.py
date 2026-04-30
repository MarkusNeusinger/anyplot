""" anyplot.ai
ridgeline-basic: Basic Ridgeline Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-04-30
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, FactorRange, HoverTool
from bokeh.palettes import Viridis256
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Monthly temperature distributions
np.random.seed(42)

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Generate realistic monthly temperature data (Celsius) with seasonal variation
base_temps = [5, 7, 12, 16, 20, 24, 27, 26, 22, 16, 10, 6]
temp_data = {}
for i, month in enumerate(months):
    temp_data[month] = np.random.normal(base_temps[i], 3, 200)

# CVD-safe sequential gradient via Viridis256 — mapped to mean temperature
# (cold months get dark purple, warm months get yellow)
min_t, max_t = min(base_temps), max(base_temps)
colors_by_month = {
    month: Viridis256[int((base_temps[i] - min_t) / (max_t - min_t) * 255)] for i, month in enumerate(months)
}

# Ridge parameters — height 1.5 → ~50% overlap between adjacent bands (spec: 50-70%)
ridge_height = 1.5
x_grid = np.linspace(-5, 40, 300)

# Pre-compute all patch coordinates for ColumnDataSource
all_xs = []
all_ys = []
all_colors = []
all_months_labels = []

for _i, month in enumerate(reversed(months)):
    temps = temp_data[month]

    # Gaussian KDE — Silverman's bandwidth rule
    n = len(temps)
    std = np.std(temps)
    iqr = np.percentile(temps, 75) - np.percentile(temps, 25)
    bandwidth = 0.9 * min(std, iqr / 1.34) * n ** (-0.2)
    bandwidth = max(bandwidth, 0.1)

    density = np.zeros_like(x_grid, dtype=float)
    for xi in temps:
        density += np.exp(-0.5 * ((x_grid - xi) / bandwidth) ** 2)
    density /= n * bandwidth * np.sqrt(2 * np.pi)

    density_normalized = density / density.max() * ridge_height

    x_patch = np.concatenate([[x_grid[0]], x_grid, [x_grid[-1]]])
    y_patch_numeric = np.concatenate([[0], density_normalized, [0]])
    # Categorical offset tuples: (month_label, float_offset)
    y_patches = [(month, float(v)) for v in y_patch_numeric]

    all_xs.append(list(x_patch))
    all_ys.append(y_patches)
    all_colors.append(colors_by_month[month])
    all_months_labels.append(month)

source = ColumnDataSource(data={"xs": all_xs, "ys": all_ys, "color": all_colors, "month": all_months_labels})

# Plot (4800 × 2700 px) — FactorRange with top padding prevents Jan peak clipping
p = figure(
    width=4800,
    height=2700,
    title="ridgeline-basic · bokeh · anyplot.ai",
    x_axis_label="Temperature (°C)",
    y_axis_label="Month",
    y_range=FactorRange(factors=months[::-1], range_padding=0.4),
    toolbar_location=None,
)

p.patches("xs", "ys", fill_color="color", fill_alpha=0.85, line_color=INK_SOFT, line_width=2, source=source)

# HoverTool — distinctive Bokeh interactivity
hover = HoverTool(tooltips=[("Month", "@month")])
p.add_tools(hover)

# Style
p.title.text_font_size = "32pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Grid
p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.xgrid.grid_line_dash = "solid"
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.05

# Remove y-axis tick marks
p.yaxis.major_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Set x-axis range
p.x_range.start = -5
p.x_range.end = 40

# Background — remove four-sided outline box for cleaner L-frame look
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)
