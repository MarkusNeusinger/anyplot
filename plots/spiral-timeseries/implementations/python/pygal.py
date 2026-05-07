"""anyplot.ai
spiral-timeseries: Spiral Time Series Chart
Library: pygal | Python 3.13
Quality: pending | Created: 2026-05-07
"""

import datetime
import importlib
import math
import os
import sys


# Remove the script's own directory from sys.path so importlib resolves
# "pygal" to the installed package, not this file (same package name).
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _this_dir]

np = importlib.import_module("numpy")
pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00")

# Data — daily average temperatures over 5 years (Northern Hemisphere city)
np.random.seed(42)
n_years = 5
days_per_year = 365
n_points = n_years * days_per_year

day_indices = np.arange(n_points)
year_idx = day_indices // days_per_year
day_of_year = day_indices % days_per_year

annual_mean = 12.0  # °C, annual mean
amplitude = 13.0  # °C, seasonal amplitude
temp = (
    annual_mean
    + amplitude * np.cos(2 * np.pi * day_of_year / days_per_year + np.pi)
    + np.random.normal(0, 2.5, n_points)
    + year_idx * 0.4  # subtle multi-year warming trend
)

# Archimedean spiral: θ = day-of-year fraction × 2π (Jan 1 at 12 o'clock)
# r = base + revolution_spacing × year + temperature_deviation
base_r = 3.0
rev_gap = 2.5
temp_scale = 0.8  # radial deviation amplitude (< rev_gap/2 avoids crossings)
t_norm = (temp - annual_mean) / (amplitude + 3.0)  # normalised ~[-1, 1]

theta = 2 * np.pi * day_of_year / days_per_year - math.pi / 2
radius = base_r + year_idx * rev_gap + temp_scale * t_norm
x_coords = (radius * np.cos(theta)).tolist()
y_coords = (radius * np.sin(theta)).tolist()

# Month spokes — radial guide lines from origin to outer ring
outer_r = base_r + (n_years - 1) * rev_gap + temp_scale + 1.2
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
spoke_points = []
for m in range(12):
    th = 2 * math.pi * m / 12 - math.pi / 2
    spoke_points.append({"value": (0.0, 0.0), "label": month_names[m]})
    spoke_points.append({"value": (outer_r * math.cos(th), outer_r * math.sin(th)), "label": month_names[m]})
    if m < 11:
        spoke_points.append(None)

# Pygal style — Okabe-Ito for year series, INK_MUTED for month spokes
all_colors = OKABE_ITO + (INK_MUTED,)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=all_colors,
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

chart = pygal.XY(
    style=custom_style,
    width=3600,
    height=3600,
    title="spiral-timeseries · pygal · anyplot.ai",
    show_dots=False,
    stroke=True,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=6,
)

# Year series — one Archimedean revolution per year, temperature as radial deviation
start_year = 2019
base_date = datetime.date(start_year, 1, 1)
for y in range(n_years):
    pts = []
    for d in range(days_per_year):
        i = y * days_per_year + d
        date_str = (base_date + datetime.timedelta(days=i)).strftime("%b %d, %Y")
        pts.append({"value": (x_coords[i], y_coords[i]), "label": f"{date_str}: {temp[i]:.1f}°C"})
    chart.add(str(start_year + y), pts)

# Month guide spokes (radial reference lines at monthly boundaries)
chart.add("Months", spoke_points)

# Save PNG and interactive HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
