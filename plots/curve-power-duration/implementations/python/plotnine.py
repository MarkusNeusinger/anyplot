"""anyplot.ai
curve-power-duration: Mean-Maximal Power Duration Curve
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-06-13
"""

import os
import sys


sys.path = [p for p in sys.path if os.path.abspath(p) != os.getcwd()]

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_line,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    scale_linetype_manual,
    scale_x_log10,
    theme,
)
from scipy.interpolate import PchipInterpolator


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — position 1 always first series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Data: well-trained cyclist power-duration profile
np.random.seed(42)
CP = 280  # Critical Power in watts (aerobic asymptote)
W_PRIME = 20000  # Anaerobic work capacity in joules

# Anchor points for realistic empirical mean-maximal power curve
anchor_dur = np.array([1, 5, 15, 30, 60, 120, 300, 600, 1200, 3600, 7200, 18000])
anchor_pwr = np.array([1050, 820, 620, 520, 430, 365, 350, 316, 298, 287, 283, 278])

# 50 empirical points, log-spaced, via monotone cubic interpolation
log_interp = PchipInterpolator(np.log10(anchor_dur), anchor_pwr)
durations = np.logspace(0, np.log10(18000), 50)
empirical_power = log_interp(np.log10(durations))

# Realistic noise — stronger at short neuromuscular efforts
noise_scale = np.where(durations < 120, 0.025, 0.012)
empirical_power = empirical_power + np.random.normal(0, empirical_power * noise_scale)

# Enforce monotonically non-increasing (MMP is always the BEST effort at each duration)
for i in range(1, len(empirical_power)):
    empirical_power[i] = min(empirical_power[i], empirical_power[i - 1])

# CP model: P(t) = CP + W′/t, shown from 5 min (valid aerobic-anaerobic range)
model_dur = np.logspace(np.log10(300), np.log10(18000), 200)
model_pwr = CP + W_PRIME / model_dur

# Build tidy DataFrames
SERIES_EMP = "Mean-maximal power"
SERIES_MOD = "CP model  (P = CP + W′/t)"

df_emp = pd.DataFrame({"duration_s": durations, "power_w": empirical_power, "series": SERIES_EMP})
df_mod = pd.DataFrame({"duration_s": model_dur, "power_w": model_pwr, "series": SERIES_MOD})
df_all = pd.concat([df_emp, df_mod], ignore_index=True)

# Title length scaling
title = "curve-power-duration · python · plotnine · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))

# Series color and linetype mappings
color_map = {SERIES_EMP: BRAND, SERIES_MOD: IMPRINT_PALETTE[1]}
linetype_map = {SERIES_EMP: "solid", SERIES_MOD: "dashed"}

# X-axis: human-readable log ticks
x_breaks = [1, 5, 30, 60, 300, 1200, 3600, 18000]
x_labels = ["1 s", "5 s", "30 s", "1 min", "5 min", "20 min", "1 h", "5 h"]

# Theme
anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    panel_border=element_blank(),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    plot_title=element_text(color=INK, size=title_fontsize, weight="medium"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_blank(),
    legend_key=element_rect(fill=PAGE_BG),
    legend_position="top",
    legend_direction="horizontal",
)

# Plot
plot = (
    ggplot(df_all, aes("duration_s", "power_w", color="series", linetype="series"))
    + geom_line(size=1.0)
    # Reference duration markers
    + geom_vline(xintercept=[5, 60, 300, 1200], color=INK_MUTED, linetype="dotted", size=0.5)
    # CP asymptote
    + geom_hline(yintercept=CP, color=INK_MUTED, linetype="dotted", size=0.4)
    # Duration annotation labels
    + annotate("text", x=5, y=1000, label="5 s", color=INK_MUTED, size=2.8, ha="center")
    + annotate("text", x=60, y=1000, label="1 min", color=INK_MUTED, size=2.8, ha="center")
    + annotate("text", x=300, y=1000, label="5 min", color=INK_MUTED, size=2.8, ha="center")
    + annotate("text", x=1200, y=1000, label="20 min\n(FTP proxy)", color=INK_MUTED, size=2.8, ha="center")
    # CP label
    + annotate("text", x=1.5, y=CP + 16, label=f"CP = {CP} W", color=INK_MUTED, size=2.5, ha="left")
    # Scales
    + scale_x_log10(breaks=x_breaks, labels=x_labels)
    + scale_color_manual(values=color_map, name="")
    + scale_linetype_manual(values=linetype_map, name="")
    + labs(x="Duration", y="Power (W)", title=title)
    + coord_cartesian(ylim=(220, 1120))
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
