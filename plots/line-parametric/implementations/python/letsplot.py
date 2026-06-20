"""anyplot.ai
line-parametric: Parametric Curve Plot
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-06-20
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "#E3E2DB" if THEME == "light" else "#2A2A27"

# Imprint sequential colormap: brand green (t=0) → blue (t=max)
GRAD_LOW = "#009E73"  # Imprint position 1 — first series / start
GRAD_HIGH = "#4467A3"  # Imprint position 3 — end

# Data — Lissajous figure: x = sin(3t), y = sin(2t), t ∈ [0, 2π]
t_lissajous = np.linspace(0, 2 * np.pi, 1000)
df_lissajous = pd.DataFrame({"x": np.sin(3 * t_lissajous), "y": np.sin(2 * t_lissajous), "t": t_lissajous})

# Data — Archimedean spiral: x = t·cos(t), y = t·sin(t), t ∈ [0, 4π]
t_spiral = np.linspace(0, 4 * np.pi, 1000)
df_spiral = pd.DataFrame({"x": t_spiral * np.cos(t_spiral), "y": t_spiral * np.sin(t_spiral), "t": t_spiral})

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=GRID_COLOR, size=0.4),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=12, color=INK),
    axis_text=element_text(size=10, color=INK_SOFT),
    axis_line=element_blank(),
    axis_ticks=element_blank(),
    plot_title=element_text(size=13, color=INK, face="bold"),
    legend_text=element_text(size=10, color=INK_SOFT),
    legend_title=element_text(size=10, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
)

# Plot — Lissajous figure (closed curve: start ≡ end at origin, show only start)
plot_lissajous = (
    ggplot(df_lissajous, aes(x="x", y="y", color="t"))
    + geom_path(size=1.5, alpha=0.9, tooltips=layer_tooltips().line("t = @t").format("t", ".2f"))
    + geom_point(data=df_lissajous.iloc[[0]], mapping=aes(x="x", y="y"), color=GRAD_LOW, size=5, shape=16)
    + scale_color_gradient(low=GRAD_LOW, high=GRAD_HIGH, name="t (rad)", format=".1f")
    + coord_fixed()
    + labs(x="x(t) = sin(3t)", y="y(t) = sin(2t)", title="Lissajous Figure  ·  3:2 frequency ratio, closed")
    + anyplot_theme
)

# Plot — Archimedean spiral (open curve: show both start and end markers)
plot_spiral = (
    ggplot(df_spiral, aes(x="x", y="y", color="t"))
    + geom_path(size=1.5, alpha=0.9, tooltips=layer_tooltips().line("t = @t").format("t", ".2f"))
    + geom_point(data=df_spiral.iloc[[0]], mapping=aes(x="x", y="y"), color=GRAD_LOW, size=5, shape=16)
    + geom_point(data=df_spiral.iloc[[-1]], mapping=aes(x="x", y="y"), color=GRAD_HIGH, size=5, shape=17)
    + scale_color_gradient(low=GRAD_LOW, high=GRAD_HIGH, name="t (rad)", format=".1f")
    + coord_fixed()
    + labs(x="x(t) = t·cos(t)", y="y(t) = t·sin(t)", title="Archimedean Spiral  ·  expanding outward")
    + anyplot_theme
)

# Side-by-side layout with overall title
grid_plot = gggrid([plot_lissajous, plot_spiral], ncol=2)
title_str = "line-parametric · python · letsplot · anyplot.ai"
final_plot = (
    grid_plot
    + ggsize(800, 450)
    + ggtitle(title_str)
    + theme(
        plot_title=element_text(size=16, color=INK, face="bold"),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

# Save PNG and interactive HTML
ggsave(final_plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(final_plot, f"plot-{THEME}.html", path=".")
