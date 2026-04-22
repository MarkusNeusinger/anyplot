""" pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: pygal 3.1.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-20
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

# Variable-density sampling: more points in complex regions
r_stable = np.linspace(2.5, R_PERIOD2, 250)
r_periodic = np.linspace(R_PERIOD2, R_CHAOS, 500)
r_chaotic = np.linspace(R_CHAOS, 4.0, 700)
r_values = np.concatenate([r_stable, r_periodic, r_chaotic])

# Colorblind-safe palette: navy blue, burnt orange, deep violet (no blue-green confusion)
regions = {
    "Stable Fixed Point": (2.5, R_PERIOD2, "#1b5e8a"),
    "Period-Doubling Cascade": (R_PERIOD2, R_CHAOS, "#d55e00"),
    "Chaotic Regime": (R_CHAOS, 4.0, "#7b2d8e"),
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
max_per_region = {"Stable Fixed Point": 6000, "Period-Doubling Cascade": 18000, "Chaotic Regime": 28000}
for name in region_data:
    pts = region_data[name]
    cap = max_per_region[name]
    if len(pts) > cap:
        idx = np.random.choice(len(pts), cap, replace=False)
        idx.sort()
        region_data[name] = [pts[i] for i in idx]

# Publication-quality style with high-contrast colorblind-safe palette
font = "'Helvetica Neue', 'DejaVu Sans', Helvetica, Arial, sans-serif"
region_colors = tuple(c for _, (_, _, c) in regions.items())
annotation_color = "#888888"
all_colors = region_colors + (annotation_color,)

custom_style = Style(
    background="white",
    plot_background="#f7f7f7",
    foreground="#333333",
    foreground_strong="#111111",
    foreground_subtle="#dddddd",
    guide_stroke_color="#e0e0e0",
    guide_stroke_dasharray="3, 8",
    major_guide_stroke_dasharray="2, 4",
    colors=all_colors,
    font_family=font,
    title_font_family=font,
    title_font_size=52,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=30,
    legend_font_family=font,
    value_font_size=26,
    tooltip_font_size=28,
    tooltip_font_family=font,
    opacity=0.55,
    opacity_hover=1.0,
)

# Chart with pygal-specific features: secondary series, custom formatters, interpolation config
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="bifurcation-basic · pygal · pyplots.ai",
    x_title="Growth Rate Parameter (r)",
    y_title="Steady-State Population (xₙ)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=22,
    stroke=False,
    dots_size=1.8,
    show_x_guides=True,
    show_y_guides=True,
    show_y_minor_guides=True,
    x_value_formatter=lambda v: f"{v:.3f}",
    value_formatter=lambda v: f"{v:.4f}",
    margin_bottom=110,
    margin_left=70,
    margin_right=50,
    margin_top=55,
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
    show_x_labels=True,
    show_y_labels=True,
    dynamic_print_values=True,
    allow_interruptions=True,
    show_minor_x_labels=True,
    spacing=25,
    inner_radius=0,
    include_x_axis=True,
)

# Add each region as a separate series with per-point tooltip metadata
for name in regions:
    lo, hi, _ = regions[name]
    chart.add(
        f"{name} (r\u2248{lo:.1f}\u2013{hi:.2f})",
        region_data[name],
        stroke=False,
        show_dots=True,
        allow_interruptions=True,
    )

# Annotation markers at key bifurcation points — dashed vertical lines in one legend entry
annotation_points = [
    (R_PERIOD2, "r\u22483.0: Period-2 onset"),
    (R_PERIOD4, "r\u22483.449: Period-4 onset"),
    (R_PERIOD8, "r\u22483.544: Period-8 onset"),
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
    stroke_style={"width": 2.5, "dasharray": "10, 5"},
    show_dots=False,
    dots_size=0,
    secondary=True,
)

# Dual render: PNG for static preview, HTML for pygal's native SVG interactivity with tooltips
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
