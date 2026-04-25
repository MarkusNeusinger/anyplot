""" anyplot.ai
gauge-basic: Basic Gauge Chart
Library: plotnine 0.15.3 | Python 3.14.4
Quality: 86/100 | Created: 2026-04-25
"""

import os
import sys


# Avoid name collision: drop this script's directory from sys.path
# so `from plotnine import ...` resolves to the installed package.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _HERE]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    geom_point,
    geom_polygon,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_void,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito zone colors (colorblind-safe red/yellow/green)
ZONE_BAD = "#D55E00"  # vermillion
ZONE_WARN = "#E69F00"  # orange
ZONE_GOOD = "#009E73"  # bluish green (brand)

# Data
value = 72
min_value = 0
max_value = 100
thresholds = [30, 70]

# Geometry
inner_radius = 0.7
outer_radius = 1.0
start_angle = np.pi
end_angle = 0.0

# Zone arc polygons
zone_colors = [ZONE_BAD, ZONE_WARN, ZONE_GOOD]
zone_bounds = [min_value, *thresholds, max_value]
zone_records = []
for i in range(len(zone_colors)):
    start_pct = (zone_bounds[i] - min_value) / (max_value - min_value)
    end_pct = (zone_bounds[i + 1] - min_value) / (max_value - min_value)
    start_ang = start_angle - start_pct * (start_angle - end_angle)
    end_ang = start_angle - end_pct * (start_angle - end_angle)
    n_points = 60
    angles_outer = np.linspace(start_ang, end_ang, n_points)
    angles_inner = np.linspace(end_ang, start_ang, n_points)
    xs = np.concatenate([outer_radius * np.cos(angles_outer), inner_radius * np.cos(angles_inner)])
    ys = np.concatenate([outer_radius * np.sin(angles_outer), inner_radius * np.sin(angles_inner)])
    for j in range(len(xs)):
        zone_records.append({"x": xs[j], "y": ys[j], "zone": str(i)})

df_zones = pd.DataFrame(zone_records)

# Needle pointing to current value
value_pct = (value - min_value) / (max_value - min_value)
needle_angle = start_angle - value_pct * (start_angle - end_angle)
needle_length = inner_radius * 0.92
df_needle = pd.DataFrame(
    {"x": [0], "y": [0], "xend": [needle_length * np.cos(needle_angle)], "yend": [needle_length * np.sin(needle_angle)]}
)

# Tick marks and labels
major_ticks = [0, 25, 50, 75, 100]
minor_ticks = [t for t in range(0, 101, 5) if t not in major_ticks]

minor_tick_records = []
for tv in minor_ticks:
    pct = (tv - min_value) / (max_value - min_value)
    ang = start_angle - pct * (start_angle - end_angle)
    minor_tick_records.append(
        {
            "x": (outer_radius * 1.02) * np.cos(ang),
            "y": (outer_radius * 1.02) * np.sin(ang),
            "xend": (outer_radius * 1.05) * np.cos(ang),
            "yend": (outer_radius * 1.05) * np.sin(ang),
        }
    )

major_tick_records = []
label_records = []
for tv in major_ticks:
    pct = (tv - min_value) / (max_value - min_value)
    ang = start_angle - pct * (start_angle - end_angle)
    major_tick_records.append(
        {
            "x": (outer_radius * 1.02) * np.cos(ang),
            "y": (outer_radius * 1.02) * np.sin(ang),
            "xend": (outer_radius * 1.10) * np.cos(ang),
            "yend": (outer_radius * 1.10) * np.sin(ang),
        }
    )
    label_records.append(
        {"x": (outer_radius * 1.20) * np.cos(ang), "y": (outer_radius * 1.20) * np.sin(ang), "label": str(tv)}
    )

df_minor_ticks = pd.DataFrame(minor_tick_records)
df_major_ticks = pd.DataFrame(major_tick_records)
df_labels = pd.DataFrame(label_records)

# Center cap (two layered points for definition)
df_cap_outer = pd.DataFrame({"x": [0], "y": [0]})
df_cap_inner = pd.DataFrame({"x": [0], "y": [0]})

# Value display and context
df_value = pd.DataFrame({"x": [0], "y": [-0.30], "label": [str(value)]})
df_context = pd.DataFrame({"x": [0], "y": [-0.55], "label": ["Current Sales"]})

# Title
df_title = pd.DataFrame({"x": [0], "y": [1.42], "label": ["gauge-basic · plotnine · anyplot.ai"]})

# Build plot
plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", fill="zone", group="zone"), data=df_zones, color=PAGE_BG, size=1.2)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_minor_ticks, color=INK_SOFT, size=0.8)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_major_ticks, color=INK, size=1.6)
    + geom_text(aes(x="x", y="y", label="label"), data=df_labels, color=INK_SOFT, size=18, fontweight="bold")
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_needle, color=INK, size=4, lineend="round")
    + geom_point(aes(x="x", y="y"), data=df_cap_outer, color=INK, size=14)
    + geom_point(aes(x="x", y="y"), data=df_cap_inner, color=PAGE_BG, size=5)
    + geom_text(aes(x="x", y="y", label="label"), data=df_value, color=ZONE_GOOD, size=56, fontweight="bold")
    + geom_text(aes(x="x", y="y", label="label"), data=df_context, color=INK_MUTED, size=20)
    + geom_text(aes(x="x", y="y", label="label"), data=df_title, color=INK, size=24, fontweight="medium")
    + scale_fill_manual(values=zone_colors, guide=None)
    + coord_fixed(ratio=1, xlim=(-1.5, 1.5), ylim=(-0.75, 1.55))
    + labs(x="", y="")
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_position="none",
        axis_text=element_blank(),
        axis_title=element_blank(),
    )
)

plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
