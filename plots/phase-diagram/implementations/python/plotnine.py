"""anyplot.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
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
    labs,
    scale_color_gradient,
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

# Imprint palette: position 1 for the start marker, sequential stops for time
BRAND = "#009E73"
IMPRINT_SEQ = ["#009E73", "#4467A3"]

# Columns
X = "Position x"  # role: x
DX_DT = "Velocity dx/dt"  # role: dx_dt
TIME = "Time (s)"  # role: t

# Data: damped harmonic oscillator, spiral converging to the equilibrium
omega = 2 * np.pi  # natural frequency
gamma = 0.15  # damping coefficient
amplitude = 2.0  # initial displacement
t = np.linspace(0, 8, 800)
decay = amplitude * np.exp(-gamma * t)
df = pd.DataFrame(
    {X: decay * np.cos(omega * t), DX_DT: decay * (-gamma * np.cos(omega * t) - omega * np.sin(omega * t)), TIME: t}
)

# Plot
# Theme-adaptive chrome
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.6),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=12),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=8),
    figure_size=(8, 4.5),
)

plot = (
    ggplot(df, aes(x=X, y=DX_DT, color=TIME))
    + geom_hline(yintercept=0, linetype="dashed", color=INK_MUTED, alpha=0.5, size=0.5)
    + geom_vline(xintercept=0, linetype="dashed", color=INK_MUTED, alpha=0.5, size=0.5)
    + geom_path(size=1.0, alpha=0.9)
    + geom_point(data=df.iloc[[0]], size=3.5, color=BRAND, show_legend=False)  # start
    + geom_point(data=df.iloc[[-1]], size=3.5, color=INK_SOFT, shape="s", show_legend=False)  # end
    + scale_color_gradient(low=IMPRINT_SEQ[0], high=IMPRINT_SEQ[1])
    + labs(title="phase-diagram · python · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
