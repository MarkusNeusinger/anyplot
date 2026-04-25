""" anyplot.ai
gauge-basic: Basic Gauge Chart
Library: bokeh 3.9.0 | Python 3.14.4
Quality: 87/100 | Updated: 2026-04-25
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import Label
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito zones: low / mid / high (intuitive + colorblind-safe)
ZONE_LOW = "#D55E00"  # vermillion
ZONE_MID = "#E69F00"  # orange
ZONE_HIGH = "#009E73"  # brand bluish green (Okabe-Ito position 1)

# Data
value = 72
min_value = 0
max_value = 100
thresholds = [30, 70]

# Gauge geometry
center_x, center_y = 0.0, 0.0
outer_radius = 0.95
inner_radius = 0.62
needle_length = 0.86
start_angle = np.pi  # left

# Map data values onto the semi-circle (pi → 0 radians)
zone_bounds = np.array([min_value] + thresholds + [max_value])
zone_angles = start_angle - (zone_bounds - min_value) / (max_value - min_value) * np.pi

tick_values = np.array([0, 25, 50, 75, 100])
tick_angles = start_angle - (tick_values - min_value) / (max_value - min_value) * np.pi

needle_angle = start_angle - (value - min_value) / (max_value - min_value) * np.pi

# Figure
p = figure(
    width=4800,
    height=2700,
    title="gauge-basic · bokeh · anyplot.ai",
    x_range=(-1.25, 1.25),
    y_range=(-0.45, 1.20),
    tools="",
    toolbar_location=None,
    background_fill_color=PAGE_BG,
    border_fill_color=PAGE_BG,
    outline_line_color=None,
)
p.axis.visible = False
p.grid.visible = False

p.title.text_font_size = "44pt"
p.title.text_color = INK
p.title.align = "center"

# Zone arcs via annular_wedge (cleaner than manual polygons)
zone_colors = [ZONE_LOW, ZONE_MID, ZONE_HIGH]
for i, color in enumerate(zone_colors):
    p.annular_wedge(
        x=center_x,
        y=center_y,
        inner_radius=inner_radius,
        outer_radius=outer_radius,
        start_angle=zone_angles[i + 1],
        end_angle=zone_angles[i],
        fill_color=color,
        line_color=PAGE_BG,
        line_width=4,
    )

# Tick marks and labels
for tick_val, a in zip(tick_values, tick_angles, strict=True):
    cos_a, sin_a = np.cos(a), np.sin(a)

    p.line(
        [center_x + (outer_radius + 0.02) * cos_a, center_x + (outer_radius + 0.10) * cos_a],
        [center_y + (outer_radius + 0.02) * sin_a, center_y + (outer_radius + 0.10) * sin_a],
        line_color=INK_SOFT,
        line_width=4,
    )

    p.add_layout(
        Label(
            x=center_x + (outer_radius + 0.20) * cos_a,
            y=center_y + (outer_radius + 0.20) * sin_a,
            text=str(tick_val),
            text_font_size="30pt",
            text_color=INK_SOFT,
            text_align="center",
            text_baseline="middle",
        )
    )

# Needle (triangle)
needle_tip_x = center_x + needle_length * np.cos(needle_angle)
needle_tip_y = center_y + needle_length * np.sin(needle_angle)
half_base = 0.035
perp = needle_angle + np.pi / 2
base1_x = center_x + half_base * np.cos(perp)
base1_y = center_y + half_base * np.sin(perp)
base2_x = center_x - half_base * np.cos(perp)
base2_y = center_y - half_base * np.sin(perp)

p.patch(
    [base1_x, needle_tip_x, base2_x], [base1_y, needle_tip_y, base2_y], fill_color=INK, line_color=INK, line_width=2
)

# Center hub
p.scatter(x=[center_x], y=[center_y], size=70, marker="circle", fill_color=INK, line_color=PAGE_BG, line_width=4)

# Value display
p.add_layout(
    Label(
        x=center_x,
        y=-0.28,
        text=str(value),
        text_font_size="84pt",
        text_color=INK,
        text_align="center",
        text_baseline="middle",
        text_font_style="bold",
    )
)

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)
