""" anyplot.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 76/100 | Updated: 2026-11-22
"""

import importlib
import os
import sys

import numpy as np
import pandas as pd


# This file is named plotnine.py, which shadows the plotnine library.
# Remove the script directory before importing the library.
_here = os.path.dirname(os.path.abspath(__file__))
if _here in sys.path:
    sys.path.remove(_here)
del _here

_pn = importlib.import_module("plotnine")
aes = _pn.aes
annotate = _pn.annotate
element_line = _pn.element_line
element_rect = _pn.element_rect
element_text = _pn.element_text
geom_point = _pn.geom_point
geom_polygon = _pn.geom_polygon
geom_segment = _pn.geom_segment
ggplot = _pn.ggplot
labs = _pn.labs
scale_x_continuous = _pn.scale_x_continuous
scale_y_continuous = _pn.scale_y_continuous
theme = _pn.theme
theme_minimal = _pn.theme_minimal
del _pn

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1

# Columns: set these to your table's column names
LONGITUDE = "Longitude (°E)"  # role: x
LATITUDE = "Latitude (°N)"  # role: y
U_WIND = "Zonal wind u (kt)"  # role: u
V_WIND = "Meridional wind v (kt)"  # role: v

# Constants
CALM_KT = 2.5  # winds below this speed are drawn as an open circle

# Data: replace this block with your own table, for example df = pd.read_csv("winds.csv")
np.random.seed(42)
xx, yy = np.meshgrid(np.linspace(0, 10, 6), np.linspace(0, 8, 5))
u = np.random.uniform(-30, 30, xx.size)
v = np.random.uniform(-25, 25, xx.size)
# Two calm stations and two strong ones with pennants
u[[0, 5, 15, 20]] = [0.5, 1.0, 45, 55]
v[[0, 5, 15, 20]] = [0.3, -0.8, 35, 10]
df = pd.DataFrame({LONGITUDE: xx.flatten(), LATITUDE: yy.flatten(), U_WIND: u, V_WIND: v})

# Plot: reads only df and the constants above
x = df[LONGITUDE].to_numpy()
y = df[LATITUDE].to_numpy()
u = df[U_WIND].to_numpy()
v = df[V_WIND].to_numpy()
x_span = np.nanmax(x) - np.nanmin(x)
y_span = np.nanmax(y) - np.nanmin(y)

# Calculate wind speed and direction
wind_speed = np.sqrt(u**2 + v**2)
# Direction FROM which wind blows (meteorological convention)
wind_direction_rad = np.arctan2(-u, -v)

# Build wind barb components: staffs, barb flags, pennants, calm circles
staff_records = []
barb_records = []
pennant_records = []
calm_records = []

scale = 0.06  # Scale factor for staff length
staff_max = 0.3 * y_span  # longest staff in data units

for i in range(len(x)):
    speed = wind_speed[i]

    if np.isnan(speed):
        continue
    if speed < CALM_KT:
        calm_records.append({"x": x[i], "y": y[i], "speed": speed})
    else:
        dir_rad = wind_direction_rad[i]
        ux = -np.sin(dir_rad)
        uy = -np.cos(dir_rad)

        staff_len = min(speed * scale, staff_max)
        x2 = x[i] + ux * staff_len
        y2 = y[i] + uy * staff_len
        staff_records.append({"x": x[i], "y": y[i], "xend": x2, "yend": y2, "speed": speed})

        # Perpendicular vector for barb flags (left side, Northern Hemisphere)
        px = -uy
        py = ux

        remaining_speed = speed
        barb_pos = 0.85
        barb_idx = 0

        # Pennants (50 knots each)
        pennant_id = 0
        while remaining_speed >= 50 and barb_idx < 3:
            pos_factor = barb_pos - barb_idx * 0.15
            bx = x[i] + ux * staff_len * pos_factor
            by = y[i] + uy * staff_len * pos_factor

            tri_base = 0.25
            tri_height = 0.35
            tip_x = bx + px * tri_height
            tip_y = by + py * tri_height
            base1_x = bx - ux * tri_base / 2
            base1_y = by - uy * tri_base / 2
            base2_x = bx + ux * tri_base / 2
            base2_y = by + uy * tri_base / 2

            group_id = f"{i}_{pennant_id}"
            pennant_records.append({"x": base1_x, "y": base1_y, "group": group_id, "order": 1})
            pennant_records.append({"x": tip_x, "y": tip_y, "group": group_id, "order": 2})
            pennant_records.append({"x": base2_x, "y": base2_y, "group": group_id, "order": 3})

            remaining_speed -= 50
            barb_idx += 1
            pennant_id += 1

        # Full barbs (10 knots each)
        while remaining_speed >= 10 and barb_idx < 8:
            pos_factor = barb_pos - barb_idx * 0.12
            bx = x[i] + ux * staff_len * pos_factor
            by = y[i] + uy * staff_len * pos_factor
            barb_len = 0.40
            barb_records.append(
                {"x": bx, "y": by, "xend": bx + px * barb_len, "yend": by + py * barb_len, "type": "full"}
            )
            remaining_speed -= 10
            barb_idx += 1

        # Half barb (5 knots)
        if remaining_speed >= 5:
            pos_factor = barb_pos - barb_idx * 0.12
            bx = x[i] + ux * staff_len * pos_factor
            by = y[i] + uy * staff_len * pos_factor
            barb_len = 0.22
            barb_records.append(
                {"x": bx, "y": by, "xend": bx + px * barb_len, "yend": by + py * barb_len, "type": "half"}
            )

# Create DataFrames
staff_df = pd.DataFrame(staff_records) if staff_records else pd.DataFrame(columns=["x", "y", "xend", "yend", "speed"])
barb_df = pd.DataFrame(barb_records) if barb_records else pd.DataFrame(columns=["x", "y", "xend", "yend", "type"])
pennant_df = pd.DataFrame(pennant_records) if pennant_records else pd.DataFrame(columns=["x", "y", "group", "order"])
calm_df = pd.DataFrame(calm_records) if calm_records else pd.DataFrame(columns=["x", "y", "speed"])

# Axis limits enclose every drawn mark, so no staff or barb is dropped at the border
x_all = np.concatenate([x, staff_df["xend"], barb_df["xend"], pennant_df["x"]]).astype(float)
y_all = np.concatenate([y, staff_df["yend"], barb_df["yend"], pennant_df["y"]]).astype(float)
x_lo, x_hi = np.nanmin(x_all), np.nanmax(x_all)
y_lo, y_hi = np.nanmin(y_all), np.nanmax(y_all)

# Plot - layer composition using grammar of graphics
plot = (
    ggplot()
    + geom_segment(data=staff_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color=BRAND, size=1.2)
    + geom_point(data=staff_df, mapping=aes(x="x", y="y"), color=BRAND, size=1.5)
)

if len(barb_df) > 0:
    plot = plot + geom_segment(data=barb_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color=BRAND, size=1.2)

if len(pennant_df) > 0:
    plot = plot + geom_polygon(
        data=pennant_df, mapping=aes(x="x", y="y", group="group"), fill=BRAND, color=BRAND, size=0.5
    )

if len(calm_df) > 0:
    plot = plot + geom_point(data=calm_df, mapping=aes(x="x", y="y"), color=BRAND, fill=PAGE_BG, size=3.5, stroke=1.0)

# Legend annotation positioned in the right margin outside the data area
legend_text = f"Wind Barb Key:\n○  Calm (< {CALM_KT} kt)\n╲  Half barb = 5 kt\n╲╲ Full barb = 10 kt\n▲  Pennant = 50 kt"

plot = (
    plot
    + annotate(
        "label",
        x=x_hi + 0.4 * x_span,
        y=np.nanmin(y) + 0.5 * y_span,
        label=legend_text,
        size=8,
        ha="right",
        va="center",
        fill=ELEVATED_BG,
        alpha=0.95,
        label_padding=0.5,
        color=INK_SOFT,
    )
    + scale_x_continuous(limits=(x_lo - 0.03 * x_span, x_hi + 0.45 * x_span))
    + scale_y_continuous(limits=(y_lo - 0.03 * y_span, y_hi + 0.03 * y_span))
    + labs(x=LONGITUDE, y=LATITUDE, title="windbarb-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        axis_line=element_line(color=INK_SOFT),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3, alpha=0.12),
        panel_grid_minor=element_line(color=INK_SOFT, size=0.15, alpha=0.06),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, verbose=False)
