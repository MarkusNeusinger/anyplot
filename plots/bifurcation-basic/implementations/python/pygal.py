"""anyplot.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: pygal | Python 3.14
Quality: pending | Created: 2026-06-17
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first series ALWAYS brand green, then canonical order
GREEN = "#009E73"
LAVENDER = "#C475FD"
BLUE = "#4467A3"

# Data — logistic map x(n+1) = r * x(n) * (1 - x(n))
np.random.seed(42)
transient = 200
iterations = 100
x0 = 0.1 + np.random.uniform(-0.01, 0.01)

# Key bifurcation thresholds
R_PERIOD2 = 3.0
R_PERIOD4 = 3.449
R_PERIOD8 = 3.544
R_CHAOS = 3.57

# Variable-density sampling: more points in complex regions
r_stable = np.linspace(2.5, R_PERIOD2, 250)
r_periodic = np.linspace(R_PERIOD2, R_CHAOS, 500)
r_chaotic = np.linspace(R_CHAOS, 4.0, 700)
r_values = np.concatenate([r_stable, r_periodic, r_chaotic])

# Three regions narrating the route to chaos (abstract → canonical Imprint order)
regions = {
    "Stable Fixed Point": (2.5, R_PERIOD2, GREEN),
    "Period-Doubling Cascade": (R_PERIOD2, R_CHAOS, LAVENDER),
    "Chaotic Regime": (R_CHAOS, 4.0, BLUE),
}

region_data = {name: [] for name in regions}

for r in r_values:
    x = x0
    for _ in range(transient):
        x = r * x * (1.0 - x)
    for _ in range(iterations):
        x = r * x * (1.0 - x)
        for name, (lo, hi, _) in regions.items():
            if lo <= r < hi or (name == "Chaotic Regime" and r == 4.0):
                region_data[name].append(
                    {"value": (round(float(r), 5), round(float(x), 5)), "label": f"r={r:.4f}, x={x:.4f}"}
                )
                break

# Downsample each region to balance visual density
max_per_region = {"Stable Fixed Point": 5000, "Period-Doubling Cascade": 16000, "Chaotic Regime": 24000}
for name in region_data:
    pts = region_data[name]
    cap = max_per_region[name]
    if len(pts) > cap:
        idx = np.random.choice(len(pts), cap, replace=False)
        idx.sort()
        region_data[name] = [pts[i] for i in idx]

# Publication-quality style on the theme-adaptive Imprint surface
font = "'Helvetica Neue', 'DejaVu Sans', Helvetica, Arial, sans-serif"
region_colors = tuple(c for _, (_, _, c) in regions.items())
all_colors = region_colors + (INK_MUTED,)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    guide_stroke_dasharray="2, 6",
    major_guide_stroke_color=INK_MUTED,
    major_guide_stroke_dasharray="2, 4",
    colors=all_colors,
    font_family=font,
    title_font_family=font,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    legend_font_family=font,
    tooltip_font_size=36,
    tooltip_font_family=font,
    opacity=0.55,
    opacity_hover=1.0,
)

# XY scatter with pygal-specific features: per-point tooltip metadata + custom formatters
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="bifurcation-basic · python · pygal · anyplot.ai",
    x_title="Growth Rate Parameter (r)",
    y_title="Steady-State Population (xₙ)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=26,
    stroke=False,
    dots_size=1.3,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda v: f"{v:.3f}",
    value_formatter=lambda v: f"{v:.4f}",
    margin_bottom=70,
    margin_left=60,
    margin_right=40,
    margin_top=60,
    xrange=(2.5, 4.0),
    range=(0.0, 1.0),
    print_values=False,
    print_zeroes=False,
    js=[],
    x_labels=[2.5, R_PERIOD2, 3.2, R_PERIOD4, R_PERIOD8, 3.7, 3.8, 4.0],
    x_labels_major=[R_PERIOD2, R_PERIOD4, R_PERIOD8],
    y_labels=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
    truncate_legend=-1,
    no_data_text="",
    allow_interruptions=True,
    include_x_axis=True,
)

# Add each region as a separate series with per-point tooltip metadata
# (short legend labels avoid bottom-row overlap; r-ranges live on the x-axis)
for name in regions:
    chart.add(name, region_data[name], stroke=False, show_dots=True, allow_interruptions=True)

# Dashed vertical reference lines at the period-doubling thresholds (one legend entry,
# drawn on the primary axis so no secondary y-axis clutters the right edge)
annotation_points = [
    (R_PERIOD2, "r≈3.0: Period-2 onset"),
    (R_PERIOD4, "r≈3.449: Period-4 onset"),
    (R_PERIOD8, "r≈3.544: Period-8 onset"),
]

annotation_data = []
for r_val, label in annotation_points:
    annotation_data.append({"value": (r_val, 0.0), "label": label})
    annotation_data.append({"value": (r_val, 1.0), "label": label})
    annotation_data.append(None)

chart.add(
    "Bifurcation Points",
    annotation_data,
    stroke=True,
    stroke_style={"width": 4, "dasharray": "12, 8"},
    show_dots=False,
    dots_size=0,
)

# Dual render: PNG for static preview, HTML for pygal's native SVG interactivity
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
