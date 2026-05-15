""" anyplot.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_path,
    geom_point,
    geom_vline,
    ggplot,
    ggsave,
    labs,
    scale_color_cmap,
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
BRAND = "#009E73"  # Okabe-Ito position 1

# Data: Damped harmonic oscillator (spiral trajectory converging to equilibrium)
np.random.seed(42)

# System parameters
omega = 2 * np.pi  # Natural frequency
gamma = 0.15  # Damping coefficient

# Time array for smooth trajectory
t = np.linspace(0, 8, 800)

# Solution for damped harmonic oscillator: x = A * exp(-gamma*t) * cos(omega*t)
A = 2.0  # Initial amplitude
x = A * np.exp(-gamma * t) * np.cos(omega * t)
dx_dt = A * np.exp(-gamma * t) * (-gamma * np.cos(omega * t) - omega * np.sin(omega * t))

# Create DataFrame with time for color gradient
df = pd.DataFrame({"x": x, "dx_dt": dx_dt, "t": t})

# Theme-adaptive chrome
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.6),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=16),
    figure_size=(16, 9),
)

# Create phase diagram
plot = (
    ggplot(df, aes(x="x", y="dx_dt", color="t"))
    + geom_path(size=1.5, alpha=0.9)
    + geom_point(data=df.iloc[[0]], size=5, color=BRAND, show_legend=False)  # Start point
    + geom_point(data=df.iloc[[-1]], size=5, color=INK_SOFT, shape="s", show_legend=False)  # End point
    + geom_hline(yintercept=0, linetype="dashed", color=INK_MUTED, alpha=0.5, size=0.5)
    + geom_vline(xintercept=0, linetype="dashed", color=INK_MUTED, alpha=0.5, size=0.5)
    + scale_color_cmap(cmap_name="viridis", name="Time (s)")
    + labs(x="Position x", y="Velocity dx/dt", title="phase-diagram · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

# Save
ggsave(plot, f"plot-{THEME}.png", dpi=300, verbose=False)
