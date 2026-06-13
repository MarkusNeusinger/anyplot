"""anyplot.ai
curve-power-duration: Mean-Maximal Power Duration Curve
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-06-13
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    geom_text,
    geom_vline,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_linetype_manual,
    scale_x_log10,
    theme,
)
from scipy.interpolate import PchipInterpolator


LetsPlot.setup_html()

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette (hybrid-v3 canonical order)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — synthetic well-trained cyclist: CP = 280 W, W' = 18 500 J
np.random.seed(42)
CP = 280
W_PRIME = 18500

# Realistic MMP anchor points spanning 1 s → 5 h
anchor_dur = np.array([1, 5, 15, 30, 60, 120, 300, 600, 1200, 3600, 7200, 18000])
anchor_pwr = np.array([1100, 920, 750, 640, 545, 450, 385, 342, 316, 291, 284, 279])

# PCHIP interpolation → smooth, monotone empirical curve
interp = PchipInterpolator(np.log10(anchor_dur), anchor_pwr)
durations_s = np.logspace(0, np.log10(18000), 50)
empirical_power = interp(np.log10(durations_s))

# Realistic measurement noise (higher at short sprints, fades at long durations)
noise = np.random.normal(0, 6 * np.exp(-durations_s / 500) + 1.5)
empirical_power = np.maximum(empirical_power + noise, CP + 0.5)

# Enforce monotonically non-increasing (core MMP invariant)
for i in range(1, len(empirical_power)):
    if empirical_power[i] > empirical_power[i - 1]:
        empirical_power[i] = empirical_power[i - 1]

# CP model overlay — valid from ~45 s; overestimates at sprint durations,
# accurate in the 2–20 min range where it is typically fitted
dur_model = np.logspace(np.log10(45), np.log10(18000), 300)
pwr_model = CP + W_PRIME / dur_model

# Series labels (used for legend key lookup)
SERIES_MMP = "Measured MMP"
SERIES_MODEL = "CP Model  (P = CP + W′/t)"

df_empirical = pd.DataFrame({"duration_s": durations_s, "power_w": empirical_power, "series": SERIES_MMP})
df_model_line = pd.DataFrame({"duration_s": dur_model, "power_w": pwr_model, "series": SERIES_MODEL})
df_lines = pd.concat([df_empirical, df_model_line], ignore_index=True)

# Reference duration annotation labels (placed above the data)
ref_x = [5, 60, 300, 1200]
ref_lbl = ["5 s", "1 min", "5 min", "20 min"]
df_ref = pd.DataFrame({"x": ref_x, "y": [1170] * 4, "label": ref_lbl})

# CP asymptote annotation (right-hand side)
df_cp_lbl = pd.DataFrame({"x": [9000], "y": [CP + 25], "label": [f"CP = {CP} W"]})

# Log-axis ticks with human-readable time labels
x_breaks = [1, 5, 30, 60, 300, 1200, 3600]
x_labels = ["1s", "5s", "30s", "1min", "5min", "20min", "1h"]

title = "curve-power-duration · python · letsplot · anyplot.ai"

# Imprint theme
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_y=element_line(color=INK_MUTED, size=0.2),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    panel_border=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    axis_ticks=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_blank(),
    legend_position="bottom",
)

# Plot
plot = (
    ggplot(df_lines, aes(x="duration_s", y="power_w", color="series", linetype="series"))
    # CP horizontal asymptote
    + geom_hline(yintercept=CP, color=INK_MUTED, linetype="dotted", size=0.7, alpha=0.9)
    # Reference duration markers: 5 s, 1 min, 5 min, 20 min
    + geom_vline(xintercept=5, color=INK_MUTED, linetype="dashed", size=0.5, alpha=0.55)
    + geom_vline(xintercept=60, color=INK_MUTED, linetype="dashed", size=0.5, alpha=0.55)
    + geom_vline(xintercept=300, color=INK_MUTED, linetype="dashed", size=0.5, alpha=0.55)
    + geom_vline(xintercept=1200, color=INK_MUTED, linetype="dashed", size=0.5, alpha=0.55)
    # Series lines (empirical solid, model dashed — driven by scale_linetype_manual)
    + geom_line(size=1.5)
    # Scatter markers on empirical curve only
    + geom_point(data=df_empirical, size=2.5, alpha=0.85)
    # Reference duration labels near top
    + geom_text(
        mapping=aes(x="x", y="y", label="label"),
        data=df_ref,
        color=INK_SOFT,
        size=3.2,
        vjust=0,
        hjust=0.5,
        inherit_aes=False,
    )
    # CP value label beside the asymptote
    + geom_text(
        mapping=aes(x="x", y="y", label="label"),
        data=df_cp_lbl,
        color=INK_MUTED,
        size=3.2,
        vjust=0,
        hjust=0.5,
        inherit_aes=False,
    )
    # Imprint color mapping: green = empirical, blue = model
    + scale_color_manual(name="", values=[IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]], breaks=[SERIES_MMP, SERIES_MODEL])
    + scale_linetype_manual(name="", values=["solid", "dashed"], breaks=[SERIES_MMP, SERIES_MODEL])
    # Log x-axis with human-readable duration labels
    + scale_x_log10(breaks=x_breaks, labels=x_labels)
    + labs(x="Duration", y="Mean-Maximal Power (W)", title=title)
    + ggsize(800, 450)
    + anyplot_theme
)

# Save PNG (scale=4 → 3200 × 1800 px) and interactive HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
