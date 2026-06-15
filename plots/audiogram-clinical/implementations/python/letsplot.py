"""anyplot.ai
audiogram-clinical: Clinical Audiogram
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-06-15
"""

import os

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — clinical semantic assignment: red=right ear, blue=left ear
RIGHT_COLOR = "#AE3030"  # Imprint matte red (position 5)
LEFT_COLOR = "#4467A3"  # Imprint blue (position 3)

# Data: noise-induced high-frequency sensorineural loss (occupational audiometry)
frequencies = [125, 250, 500, 1000, 2000, 4000, 8000]
threshold_right = [15, 20, 20, 25, 40, 70, 75]
threshold_left = [10, 15, 20, 30, 50, 65, 70]

df_ears = pd.DataFrame(
    {
        "frequency": frequencies * 2,
        "threshold": threshold_right + threshold_left,
        "ear": pd.Categorical(["Right Ear"] * 7 + ["Left Ear"] * 7, categories=["Right Ear", "Left Ear"], ordered=True),
    }
)

# Severity band rectangles (ymin/ymax in dB HL data coordinates)
# Fill colors from Imprint palette at low alpha — structural background, not data series
bands_df = pd.DataFrame(
    {
        "xmin": [100.0] * 6,
        "xmax": [10000.0] * 6,
        "ymin": [-10.0, 25.0, 40.0, 55.0, 70.0, 90.0],
        "ymax": [25.0, 40.0, 55.0, 70.0, 90.0, 120.0],
        "fill_col": ["#009E73", "#99B314", "#BD8233", "#BD8233", "#AE3030", "#AE3030"],
        "alpha_val": [0.08, 0.10, 0.12, 0.16, 0.12, 0.22],
    }
)

band_labels_df = pd.DataFrame(
    {
        "x": [9500.0] * 6,
        "y": [7.5, 32.5, 47.5, 62.5, 80.0, 105.0],
        "label": ["Normal", "Mild", "Moderate", "Mod. Severe", "Severe", "Profound"],
    }
)

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_blank(),
    legend_position="right",
    panel_border=element_rect(color=INK_SOFT),
)

plot = (
    ggplot()
    # Severity bands (background layer)
    + geom_rect(
        data=bands_df,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="fill_col", alpha="alpha_val"),
        color=None,
        show_legend=False,
    )
    + scale_fill_identity()
    + scale_alpha_identity()
    # Severity band labels (right edge)
    + geom_text(data=band_labels_df, mapping=aes(x="x", y="y", label="label"), color=INK_MUTED, size=3.0, hjust=1)
    # Connecting lines per ear
    + geom_line(data=df_ears, mapping=aes(x="frequency", y="threshold", color="ear"), size=1.0)
    # Threshold markers: O (shape=1) for right ear, X (shape=4) for left ear
    + geom_point(
        data=df_ears, mapping=aes(x="frequency", y="threshold", color="ear", shape="ear"), size=4.5, stroke=1.5
    )
    + scale_color_manual(values=[RIGHT_COLOR, LEFT_COLOR], name="")
    + scale_shape_manual(values=[1, 4], name="")
    # Log x-axis with standard audiometric frequency labels
    + scale_x_log10(
        breaks=[125, 250, 500, 1000, 2000, 4000, 8000],
        labels=["125", "250", "500", "1k", "2k", "4k", "8k"],
        limits=[100, 10000],
    )
    # Inverted y-axis: 0 dB HL (best hearing) at top, loss increases downward
    + scale_y_reverse(breaks=list(range(-10, 121, 10)), limits=[-10, 120])
    + labs(x="Frequency (Hz)", y="Hearing Level (dB HL)", title="audiogram-clinical · python · letsplot · anyplot.ai")
    + theme_bw()
    + anyplot_theme
    + ggsize(600, 600)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
