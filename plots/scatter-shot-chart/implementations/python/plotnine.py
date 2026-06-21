"""anyplot.ai
scatter-shot-chart: Basketball Shot Chart
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-06-21
"""

import os
import sys


# Prevent self-import: when Python runs plotnine.py its own directory lands on
# sys.path[0], shadowing the real plotnine library.  Remove it before the import.
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _this_dir]

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — semantic assignment
MADE_COLOR = "#009E73"  # Imprint pos 1 — brand green (made shot = success)
MISSED_COLOR = "#AE3030"  # Imprint pos 5 — matte red (miss = loss/fail semantic)
COURT_COLOR = INK_MUTED

# NBA half-court dimensions (feet, basket center at origin)
BASELINE_Y = -5.25  # baseline is 5.25 ft behind basket rim
HALFCOURT_Y = 41.75  # half-court line from basket
THREE_R = 23.75  # three-point arc radius
CORNER_X = 22.0  # x-coordinate where corner three meets the arc
CORNER_BREAK_Y = float(np.sqrt(THREE_R**2 - CORNER_X**2))  # ~8.95 ft
FT_Y = 13.75  # free-throw line (19 ft from baseline minus 5.25 ft basket offset)
FT_R = 6.0  # free-throw circle radius
PAINT_W = 8.0  # half-width of the 16 ft key/paint
BACKBOARD_Y = -1.25  # backboard (4 ft from baseline = -5.25 + 4)

# Court geometry — one DataFrame per segment, combined for geom_path
_segs = []

# Outer boundary
_segs.append(pd.DataFrame({"x": [-25, 25], "y": [BASELINE_Y] * 2, "seg": "baseline"}))
_segs.append(pd.DataFrame({"x": [25] * 2, "y": [BASELINE_Y, HALFCOURT_Y], "seg": "side_r"}))
_segs.append(pd.DataFrame({"x": [-25] * 2, "y": [BASELINE_Y, HALFCOURT_Y], "seg": "side_l"}))
_segs.append(pd.DataFrame({"x": [-25, 25], "y": [HALFCOURT_Y] * 2, "seg": "halfcourt"}))

# Paint / key rectangle
_segs.append(pd.DataFrame({"x": [-PAINT_W] * 2, "y": [BASELINE_Y, FT_Y], "seg": "paint_l"}))
_segs.append(pd.DataFrame({"x": [PAINT_W] * 2, "y": [BASELINE_Y, FT_Y], "seg": "paint_r"}))
_segs.append(pd.DataFrame({"x": [-PAINT_W, PAINT_W], "y": [FT_Y] * 2, "seg": "ft_line"}))

# Free-throw circle upper half
_a = np.linspace(0, np.pi, 60)
_segs.append(pd.DataFrame({"x": FT_R * np.cos(_a), "y": FT_Y + FT_R * np.sin(_a), "seg": "ft_upper"}))

# Free-throw circle lower half
_a = np.linspace(np.pi, 2 * np.pi, 60)
_segs.append(pd.DataFrame({"x": FT_R * np.cos(_a), "y": FT_Y + FT_R * np.sin(_a), "seg": "ft_lower"}))

# Three-point arc (from right corner break to left, sweeping through top)
_theta1 = float(np.arctan2(CORNER_BREAK_Y, CORNER_X))
_theta2 = np.pi - _theta1
_a = np.linspace(_theta1, _theta2, 120)
_segs.append(pd.DataFrame({"x": THREE_R * np.cos(_a), "y": THREE_R * np.sin(_a), "seg": "three_arc"}))

# Corner three straight sections
_segs.append(pd.DataFrame({"x": [CORNER_X] * 2, "y": [BASELINE_Y, CORNER_BREAK_Y], "seg": "corner_r"}))
_segs.append(pd.DataFrame({"x": [-CORNER_X] * 2, "y": [BASELINE_Y, CORNER_BREAK_Y], "seg": "corner_l"}))

# Restricted area arc (4 ft radius, above baseline)
_a = np.linspace(0, np.pi, 60)
_segs.append(pd.DataFrame({"x": 4.0 * np.cos(_a), "y": 4.0 * np.sin(_a), "seg": "restricted"}))

# Basket rim circle (0.75 ft radius)
_a = np.linspace(0, 2 * np.pi, 60)
_segs.append(pd.DataFrame({"x": 0.75 * np.cos(_a), "y": 0.75 * np.sin(_a), "seg": "basket"}))

# Backboard
_segs.append(pd.DataFrame({"x": [-3.0, 3.0], "y": [BACKBOARD_Y] * 2, "seg": "backboard"}))

# Half-court center circle (6 ft radius — partially visible at top)
_a = np.linspace(0, 2 * np.pi, 80)
_segs.append(pd.DataFrame({"x": 6.0 * np.cos(_a), "y": HALFCOURT_Y + 6.0 * np.sin(_a), "seg": "hc_circle"}))

court_df = pd.concat(_segs, ignore_index=True)

# Shot data — simulated NBA player shot chart (~350 attempts, zone-realistic FG%)
np.random.seed(42)

# Paint (layups, post-ups, close range)
_x1 = np.random.normal(0, 4.0, 90)
_y1 = np.random.normal(4.0, 3.0, 90)
_m1 = np.random.random(90) < 0.62

# Left elbow mid-range
_x2 = np.random.normal(-11, 2.5, 40)
_y2 = np.random.normal(FT_Y, 3.0, 40)
_m2 = np.random.random(40) < 0.41

# Right elbow mid-range
_x3 = np.random.normal(11, 2.5, 40)
_y3 = np.random.normal(FT_Y, 3.0, 40)
_m3 = np.random.random(40) < 0.41

# Above-the-break three (top of key)
_x4 = np.random.normal(0, 5.5, 65)
_y4 = np.random.normal(26.0, 1.5, 65)
_m4 = np.random.random(65) < 0.37

# Left corner three
_x5 = np.random.normal(-22.5, 1.0, 25)
_y5 = np.random.normal(2.0, 1.8, 25)
_m5 = np.random.random(25) < 0.42

# Right corner three
_x6 = np.random.normal(22.5, 1.0, 25)
_y6 = np.random.normal(2.0, 1.8, 25)
_m6 = np.random.random(25) < 0.42

# Left wing three
_x7 = np.random.normal(-20, 2.0, 30)
_y7 = np.random.normal(19, 2.0, 30)
_m7 = np.random.random(30) < 0.34

# Right wing three
_x8 = np.random.normal(20, 2.0, 30)
_y8 = np.random.normal(19, 2.0, 30)
_m8 = np.random.random(30) < 0.34

_sx = np.concatenate([_x1, _x2, _x3, _x4, _x5, _x6, _x7, _x8])
_sy = np.concatenate([_y1, _y2, _y3, _y4, _y5, _y6, _y7, _y8])
_sm = np.concatenate([_m1, _m2, _m3, _m4, _m5, _m6, _m7, _m8])

shots_df = pd.DataFrame({"x": _sx, "y": _sy, "made": _sm})
shots_df["outcome"] = shots_df["made"].map({True: "Made", False: "Missed"})
shots_df = shots_df[shots_df["x"].between(-25, 25) & shots_df["y"].between(BASELINE_Y, HALFCOURT_Y)].reset_index(
    drop=True
)

# Plot — square canvas for 1:1 court geometry (2400×2400 at dpi=400)
_title = "scatter-shot-chart · python · plotnine · anyplot.ai"

plot = (
    ggplot()
    + geom_path(data=court_df, mapping=aes(x="x", y="y", group="seg"), color=COURT_COLOR, size=0.5)
    + geom_point(data=shots_df, mapping=aes(x="x", y="y", color="outcome"), size=2.2, alpha=0.75)
    + scale_color_manual(values={"Made": MADE_COLOR, "Missed": MISSED_COLOR}, name="")
    + coord_fixed(ratio=1, xlim=(-26.5, 26.5), ylim=(-7.5, 45.5))
    + labs(title=_title, x="", y="")
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        plot_title=element_text(color=INK, size=12),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=8),
        legend_title=element_blank(),
        legend_key=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_position="bottom",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
