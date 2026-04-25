""" anyplot.ai
errorbar-basic: Basic Error Bar Plot
Library: letsplot 4.9.0 | Python 3.14.4
Quality: 91/100 | Updated: 2026-04-25
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_errorbar,
    geom_point,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito position 1
FOCAL = "#D55E00"  # Okabe-Ito position 2 — emphasises group with largest spread

# Data — experimental measurements with uncertainty
data = pd.DataFrame(
    {
        "experiment": ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D"],
        "mean_value": [45.2, 52.8, 61.3, 48.7, 55.1],
        "error": [4.5, 6.2, 5.8, 3.9, 7.1],
    }
)
data["ymin"] = data["mean_value"] - data["error"]
data["ymax"] = data["mean_value"] + data["error"]

# Highlight the group with the largest error spread to give the chart a focal point
focal_idx = data["error"].idxmax()
data["highlight"] = ["focal" if i == focal_idx else "base" for i in data.index]

color_map = {"base": BRAND, "focal": FOCAL}

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    panel_grid_major_y=element_line(color=INK_SOFT, size=0.3),
    axis_line=element_line(color=INK_SOFT),
    axis_ticks=element_line(color=INK_SOFT),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    plot_title=element_text(color=INK, size=24),
    legend_position="none",
)

plot = (
    ggplot(data, aes(x="experiment", y="mean_value", color="highlight"))
    + geom_errorbar(aes(ymin="ymin", ymax="ymax"), width=0.3, size=1.5)
    + geom_point(size=6)
    + scale_color_manual(values=color_map)
    + labs(x="Experimental Group", y="Measured Value (mg/dL)", title="errorbar-basic · letsplot · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + ggsize(1600, 900)
)

# PNG (scale 3x for 4800 x 2700 px)
ggsave(plot, f"plot-{THEME}.png", scale=3, path=".")

# HTML (interactive)
ggsave(plot, f"plot-{THEME}.html", path=".")
