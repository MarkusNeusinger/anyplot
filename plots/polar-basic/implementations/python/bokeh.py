""" anyplot.ai
polar-basic: Basic Polar Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-04-30
"""

import os
import sys


# Prevent this file (bokeh.py) from shadowing the installed bokeh package
_here = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))
sys.path = [p for p in sys.path if os.path.normpath(os.path.abspath(p or ".")) != _here]

import numpy as np  # noqa: E402
from bokeh.io import export_png, output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource  # noqa: E402
from bokeh.plotting import figure  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Okabe-Ito position 1

IMPL_DIR = os.path.dirname(os.path.abspath(__file__))

# Data — hourly temperature readings (24-hour cycle)
np.random.seed(42)
hours = np.arange(24)
theta = hours * (2 * np.pi / 24)

base_temp = 15 + 8 * np.sin(theta - np.pi / 2)  # peak ~14:00, low ~04:00
temperature = base_temp + np.random.randn(24) * 1.5
radius = temperature - temperature.min() + 2  # shift to positive values

# Convert polar to Cartesian (Bokeh has no native polar support)
# +π/2 rotation puts midnight (0h) at the top
x = radius * np.cos(theta + np.pi / 2)
y = radius * np.sin(theta + np.pi / 2)

source = ColumnDataSource(data={"x": x, "y": y, "radius": radius, "theta": theta, "hour": hours, "temp": temperature})

# Plot
p = figure(width=3600, height=3600, title="polar-basic · bokeh · anyplot.ai", match_aspect=True, toolbar_location=None)

max_radius = np.ceil(radius.max()) + 1.5
grid_radii = np.linspace(0, max_radius, 5)[1:]

# Concentric circle gridlines
for r in grid_radii:
    ct = np.linspace(0, 2 * np.pi, 120)
    p.line(r * np.cos(ct), r * np.sin(ct), line_color=INK, line_width=2, line_alpha=0.10)

# Spoke gridlines at 3-hour intervals
for h in [0, 3, 6, 9, 12, 15, 18, 21]:
    a = h * (2 * np.pi / 24) + np.pi / 2
    p.line([0, max_radius * np.cos(a)], [0, max_radius * np.sin(a)], line_color=INK, line_width=2, line_alpha=0.10)

# Hour labels around the perimeter
label_r = max_radius + 1.8
for h in [0, 3, 6, 9, 12, 15, 18, 21]:
    a = h * (2 * np.pi / 24) + np.pi / 2
    p.text(
        x=[label_r * np.cos(a)],
        y=[label_r * np.sin(a)],
        text=[f"{h:02d}:00"],
        text_align="center",
        text_baseline="middle",
        text_font_size="22pt",
        text_color=INK_SOFT,
    )

# Closed data line
p.line(x="x", y="y", source=source, line_color=BRAND, line_width=4, line_alpha=0.85)
p.line([x[-1], x[0]], [y[-1], y[0]], line_color=BRAND, line_width=4, line_alpha=0.85)

# Data points
p.scatter(x="x", y="y", source=source, size=22, color=BRAND, alpha=0.9, line_color=PAGE_BG, line_width=2)

# Center marker
p.scatter([0], [0], size=10, color=INK_MUTED, alpha=0.5)

# Style
p.title.text_font_size = "32pt"
p.title.align = "center"
p.title.text_color = INK
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# Save
export_png(p, filename=os.path.join(IMPL_DIR, f"plot-{THEME}.png"))
output_file(os.path.join(IMPL_DIR, f"plot-{THEME}.html"), title="polar-basic · bokeh · anyplot.ai")
save(p)
