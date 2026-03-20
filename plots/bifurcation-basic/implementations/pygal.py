"""pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: pygal 3.1.0 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-20
"""

import numpy as np
import pygal
from pygal.style import Style


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

# Use higher resolution in chaotic region for denser coverage
r_stable = np.linspace(2.5, R_PERIOD2, 200)
r_periodic = np.linspace(R_PERIOD2, R_CHAOS, 400)
r_chaotic = np.linspace(R_CHAOS, 4.0, 600)
r_values = np.concatenate([r_stable, r_periodic, r_chaotic])

# Region labels for coloring
regions = {
    "Stable Fixed Point": (2.5, R_PERIOD2, "#306998"),
    "Period-Doubling Cascade": (R_PERIOD2, R_CHAOS, "#e07b39"),
    "Chaotic Regime": (R_CHAOS, 4.0, "#c44e52"),
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
                region_data[name].append((float(r), float(x)))
                break

# Downsample each region independently to preserve density balance
max_per_region = {"Stable Fixed Point": 5000, "Period-Doubling Cascade": 15000, "Chaotic Regime": 25000}
for name in region_data:
    pts = region_data[name]
    cap = max_per_region[name]
    if len(pts) > cap:
        idx = np.random.choice(len(pts), cap, replace=False)
        idx.sort()
        region_data[name] = [pts[i] for i in idx]

# Style — three-color palette for route to chaos, plus gray for annotation lines
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
region_colors = tuple(c for _, (_, _, c) in regions.items())
all_colors = region_colors + ("#888888", "#888888", "#888888")

custom_style = Style(
    background="white",
    plot_background="#f8f8f8",
    foreground="#2a2a2a",
    foreground_strong="#1a1a1a",
    foreground_subtle="#e0e0e0",
    guide_stroke_color="#e0e0e0",
    guide_stroke_dasharray="4, 4",
    colors=all_colors,
    font_family=font,
    title_font_family=font,
    title_font_size=56,
    label_font_size=42,
    major_label_font_size=38,
    legend_font_size=34,
    legend_font_family=font,
    value_font_size=28,
    tooltip_font_size=28,
    tooltip_font_family=font,
    opacity=0.3,
    opacity_hover=0.9,
)

# Chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="bifurcation-basic \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Growth Rate Parameter (r)",
    y_title="Steady-State Population (x\u2099)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=6,
    stroke=False,
    dots_size=1.2,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda v: f"{v:.3f}",
    value_formatter=lambda v: f"{v:.3f}",
    margin_bottom=120,
    margin_left=60,
    margin_right=40,
    margin_top=50,
    xrange=(2.5, 4.0),
    range=(0.0, 1.0),
    print_values=False,
    print_zeroes=False,
    js=[],
    x_labels=[2.5, R_PERIOD2, R_PERIOD4, R_PERIOD8, 3.8, 4.0],
    x_labels_major=[R_PERIOD2, R_PERIOD4, R_PERIOD8],
    truncate_legend=-1,
)

# Add each region as a separate series for color-coded storytelling
for name in regions:
    chart.add(
        f"{name} (r\u2248{regions[name][0]:.1f}\u2013{regions[name][1]:.2f})",
        region_data[name],
        stroke=False,
        show_dots=True,
    )

# Add annotation markers at key bifurcation points as vertical line series
annotation_points = [
    (R_PERIOD2, "r\u22483.0: Period-2"),
    (R_PERIOD4, "r\u22483.449: Period-4"),
    (R_PERIOD8, "r\u22483.544: Period-8"),
]

for r_val, label in annotation_points:
    chart.add(label, [(r_val, 0.0), (r_val, 1.0)], stroke=True, show_dots=False, dots_size=0)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
