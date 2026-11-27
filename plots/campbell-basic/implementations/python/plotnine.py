"""anyplot.ai
campbell-basic: Campbell Diagram
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_linetype_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order, first always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
CRITICAL_COLOR = "#AE3030"  # semantic red: critical speed

# Constants
ENGINE_ORDERS = [1, 2, 3]  # excitation lines: frequency = order * speed / 60
MODE_WIDTH = 1.5  # line width of the natural frequency curves
EO_WIDTH = 0.8  # engine order lines stay thinner than the modes

# Columns: set these to your table's column names
SPEED = "Rotational Speed (RPM)"  # role: speed
ENGINE_ORDER = "Engine order"  # role: engine_order
CRITICAL_SPEED = "Critical speed (RPM)"  # role: critical_speeds
MODES = ["1st Bending", "2nd Bending", "1st Torsional", "2nd Torsional", "Axial"]  # role: frequency_mode_

# Data: replace this block with your own table, for example df = pd.read_csv("modes.csv")
np.random.seed(42)
speed = np.linspace(0, 6000, 80)
base_hz = [18, 45, 52, 75, 90]
slope_hz_per_rpm = [0.0015, -0.002, 0.0025, 0.001, -0.0004]
df = pd.DataFrame(
    {SPEED: speed}
    | {
        mode: base + slope * speed + np.random.normal(0, 0.12, len(speed))
        for mode, base, slope in zip(MODES, base_hz, slope_hz_per_rpm, strict=True)
    }
)

# Plot: reads only df and the constants above
FREQUENCY = "Natural Frequency (Hz)"
MODE = "Mode"
speeds = df[SPEED].to_numpy()
mode_names = list(MODES)
mode_colors = {mode: IMPRINT_PALETTE[i] for i, mode in enumerate(mode_names)}
df_modes = df.melt(id_vars=SPEED, value_vars=MODES, var_name=MODE, value_name=FREQUENCY)
top = df_modes[FREQUENCY].max() * 1.1

# Engine order lines from the origin, clipped to the frequency range
eo_names = [f"{order}× EO" for order in ENGINE_ORDERS]
df_eo = pd.DataFrame(
    [
        {SPEED: s, FREQUENCY: order * s / 60, ENGINE_ORDER: order, MODE: name}
        for order, name in zip(ENGINE_ORDERS, eo_names, strict=True)
        for s in speeds
        if order * s / 60 <= top
    ]
)

# Order labels at the upper end of each engine order line
df_eo_labels = df_eo.groupby(MODE, sort=False).tail(1).copy()
df_eo_labels[FREQUENCY] += top * 0.03
df_eo_labels["label"] = [f"{order}×" for order in ENGINE_ORDERS]

# Critical speeds: where an engine order line crosses a mode curve (linear interpolation)
critical_points = []
for order in ENGINE_ORDERS:
    eo_freq = order * speeds / 60
    for mode in mode_names:
        gap = eo_freq - df[mode].to_numpy()
        for i in np.where(gap[:-1] * gap[1:] < 0)[0]:
            t = gap[i] / (gap[i] - gap[i + 1])
            crit_speed = speeds[i] + t * (speeds[i + 1] - speeds[i])
            crit_freq = order * crit_speed / 60
            if crit_freq <= top:
                critical_points.append({CRITICAL_SPEED: crit_speed, FREQUENCY: crit_freq})
df_critical = pd.DataFrame(critical_points, columns=[CRITICAL_SPEED, FREQUENCY])

# One colour and linetype scale for modes and engine orders, with a single legend entry for the lines
color_map = {**mode_colors, **dict.fromkeys(eo_names, INK_MUTED)}
ltype_map = {**dict.fromkeys(mode_names, "solid"), **dict.fromkeys(eo_names, "dashed")}
breaks = mode_names + eo_names[:1]
labels = mode_names + ["Engine Order (" + ", ".join(f"{o}×" for o in ENGINE_ORDERS) + ")"]

plot = (
    ggplot(df_modes, aes(SPEED, FREQUENCY, color=MODE, linetype=MODE, group=MODE))
    + geom_line(size=MODE_WIDTH)
    + geom_line(df_eo, size=EO_WIDTH)
    + geom_point(
        df_critical,
        aes(CRITICAL_SPEED, FREQUENCY),
        color=CRITICAL_COLOR,
        fill=PAGE_BG,
        size=3.6,
        shape="D",
        stroke=1.2,
        inherit_aes=False,
    )
    + geom_text(
        df_eo_labels,
        aes(SPEED, FREQUENCY, label="label"),
        color=INK_SOFT,
        size=9,
        fontstyle="italic",
        fontweight="bold",
        inherit_aes=False,
    )
    + scale_color_manual(values=color_map, breaks=breaks, labels=labels)
    + scale_linetype_manual(values=ltype_map, breaks=breaks, labels=labels)
    + coord_cartesian(xlim=(0, np.nanmax(speeds)), ylim=(0, top))
    + labs(title="campbell-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.12),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.3),
        plot_title=element_text(size=12, ha="center", face="bold", color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_blank(),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key_width=30,
        legend_key_height=15,
        legend_position="bottom",
        legend_direction="horizontal",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
