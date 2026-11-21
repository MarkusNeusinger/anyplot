"""anyplot.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
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
    geom_path,
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

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per trajectory in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
EQUILIBRIUM = (0.0, 0.0)  # a damped oscillator comes to rest at x = 0, dx/dt = 0

# Columns: set these to your table's column names
POSITION = "Position (x)"  # role: x
VELOCITY = "Velocity (dx/dt)"  # role: dx_dt
TIME = "Time (s)"  # role: t
START = "Initial condition"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("trajectories.csv")
# Damped harmonic oscillator: dx/dt = v, dv/dt = -omega^2 * x - gamma * v
omega, gamma = 1.5, 0.5
initial_conditions = [
    (2.5, 1.0, "High position, rising"),
    (-2.0, -2.5, "Left position, falling"),
    (0.8, 3.0, "Near center, rising fast"),
]
t = np.linspace(0, 12, 400)
dt = t[1] - t[0]
frames = []
for x0, v0, label in initial_conditions:
    x = np.zeros_like(t)
    v = np.zeros_like(t)
    x[0], v[0] = x0, v0
    for i in range(1, len(t)):
        x[i] = x[i - 1] + v[i - 1] * dt
        v[i] = v[i - 1] + (-(omega**2) * x[i - 1] - gamma * v[i - 1]) * dt
    frames.append(pd.DataFrame({POSITION: x, VELOCITY: v, TIME: t, START: label}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
starts = df.groupby(START, sort=False).head(1)
rest = pd.DataFrame({POSITION: [EQUILIBRIUM[0]], VELOCITY: [EQUILIBRIUM[1]]})

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.1),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=12),
    legend_position="right",
)

plot = (
    ggplot(df, aes(x=POSITION, y=VELOCITY, color=START))
    + geom_path(size=1.0, alpha=0.85)
    # Hollow rings mark where each trajectory starts
    + geom_point(
        data=starts, mapping=aes(x=POSITION, y=VELOCITY), size=4, shape=21, fill=PAGE_BG, stroke=1.5, color=INK_SOFT
    )
    # Cross marks the fixed point the spirals converge on
    + geom_point(
        data=rest, mapping=aes(x=POSITION, y=VELOCITY), color=INK, size=6, shape=4, stroke=2, inherit_aes=False
    )
    + scale_color_manual(values=IMPRINT_PALETTE)
    + labs(title="phase-diagram · python · letsplot · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save PNG (scale 4x for 3200 x 1800) and interactive HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
