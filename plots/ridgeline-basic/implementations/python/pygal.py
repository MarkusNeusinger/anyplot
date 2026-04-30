""" anyplot.ai
ridgeline-basic: Basic Ridgeline Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-04-30
"""

import os
import sys

import numpy as np


# Pop script directory so local pygal.py doesn't shadow the installed package
_script_dir = sys.path.pop(0)
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _script_dir)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data - Monthly temperature distributions for a temperate city
np.random.seed(42)

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Seasonal temperature baselines (°C)
base_temps = [2, 4, 8, 13, 18, 22, 25, 24, 19, 13, 7, 3]
month_data = []
for base in base_temps:
    temps = np.random.normal(base, 3, 100)
    month_data.append(temps)

# Common x range for all distributions
x_range = np.linspace(-10, 40, 150)

# Compute KDE for each month (inline, no functions)
kde_data = []
for temps in month_data:
    n = len(temps)
    bandwidth = n ** (-1 / 5) * np.std(temps)
    density = np.zeros_like(x_range)
    for xi in temps:
        density += np.exp(-0.5 * ((x_range - xi) / bandwidth) ** 2)
    density /= n * bandwidth * np.sqrt(2 * np.pi)
    kde_data.append(density)

# Normalize all densities
max_density = max(d.max() for d in kde_data)
kde_data = [d / max_density for d in kde_data]

# Seasonal color gradient: cold blues → warm oranges → cold blues
colors = (
    "#2563eb",  # Jan - winter blue
    "#7c3aed",  # Feb - purple
    "#0891b2",  # Mar - teal
    "#10b981",  # Apr - emerald
    "#84cc16",  # May - lime
    "#eab308",  # Jun - yellow
    "#f97316",  # Jul - summer orange
    "#eab308",  # Aug - yellow
    "#84cc16",  # Sep - lime
    "#10b981",  # Oct - emerald
    "#0891b2",  # Nov - teal
    "#2563eb",  # Dec - winter blue
)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=colors,
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=48,
    legend_font_size=36,
    value_font_size=36,
    opacity=0.85,
    opacity_hover=0.97,
)

# Ridge parameters
ridge_height = 2.5
ridge_spacing = 1.8

# Y-axis labels positioned at each ridge baseline
y_label_values = []
for i, month in enumerate(reversed(months)):
    y_label_values.append((i * ridge_spacing + ridge_height * 0.3, month))

chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="Monthly Temperature Distributions · ridgeline-basic · pygal · anyplot.ai",
    x_title="Temperature (°C)",
    y_title="",
    show_legend=False,
    stroke=True,
    fill=True,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=False,
    range=(-0.5, len(months) * ridge_spacing + ridge_height),
    xrange=(-10, 40),
    stroke_style={"width": 2},
)

chart.y_labels = [{"value": v, "label": lbl} for v, lbl in y_label_values]

# Add ridges from back (Dec) to front (Jan) for correct visual layering;
# month names as series labels appear in HTML hover tooltips
for i, (month, density) in enumerate(reversed(list(zip(months, kde_data, strict=True)))):
    baseline = i * ridge_spacing
    scaled_density = density * ridge_height

    bottom_edge = [(float(x), float(baseline)) for x in x_range]
    top_edge = [(float(x), float(baseline + d)) for x, d in zip(x_range[::-1], scaled_density[::-1], strict=True)]
    polygon = bottom_edge + top_edge + [bottom_edge[0]]

    chart.add(month, polygon)

# Save outputs
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
