""" anyplot.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito colors
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Damped harmonic oscillator with distinct parameters
# dx/dt = v, dv/dt = -omega^2 * x - gamma * v
np.random.seed(42)

omega = 1.5  # Natural frequency (different from bokeh's 2.0)
gamma = 0.5  # Higher damping coefficient (different from bokeh's 0.3)

# Three trajectories from different initial conditions
trajectories = []

initial_conditions = [
    (2.5, 1.0, "High position, rising"),
    (-2.0, -2.5, "Left position, falling"),
    (0.8, 3.0, "Near center, rising fast"),
]

for x0, v0, label in initial_conditions:
    t = np.linspace(0, 12, 400)
    dt = t[1] - t[0]

    x = np.zeros_like(t)
    v = np.zeros_like(t)
    x[0], v[0] = x0, v0

    # Euler integration for damped harmonic oscillator
    for i in range(1, len(t)):
        x[i] = x[i - 1] + v[i - 1] * dt
        v[i] = v[i - 1] + (-(omega**2) * x[i - 1] - gamma * v[i - 1]) * dt

    traj_df = pd.DataFrame({"x": x, "dx_dt": v, "time": t, "trajectory": label})
    trajectories.append(traj_df)

df = pd.concat(trajectories, ignore_index=True)

# Create phase diagram
anyplot_theme = theme(  # noqa: F405
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
    panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
    panel_grid_major=element_line(color=INK_SOFT, size=0.3, linetype="solid"),  # noqa: F405
    axis_title=element_text(color=INK, size=20),  # noqa: F405
    axis_text=element_text(color=INK_SOFT, size=16),  # noqa: F405
    plot_title=element_text(color=INK, size=24),  # noqa: F405
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
    legend_text=element_text(color=INK_SOFT, size=14),  # noqa: F405
    legend_title=element_text(color=INK, size=16),  # noqa: F405
    legend_position="right",
)

plot = (
    ggplot(df, aes(x="x", y="dx_dt", color="trajectory"))  # noqa: F405
    + geom_path(size=1.3, alpha=0.85)  # noqa: F405
    + geom_point(  # noqa: F405
        mapping=aes(x="x", y="dx_dt"),  # noqa: F405
        data=df.groupby("trajectory").head(1),
        size=7,
        shape=21,
        fill=PAGE_BG,
        stroke=2.5,
        color=INK_SOFT,
    )
    # Mark the fixed point (equilibrium at origin)
    + geom_point(  # noqa: F405
        mapping=aes(x="x", y="dx_dt"),  # noqa: F405
        data=pd.DataFrame({"x": [0], "dx_dt": [0]}),
        color=INK_SOFT,
        size=10,
        shape=4,
        stroke=3,
        inherit_aes=False,
    )
    + scale_color_manual(values=IMPRINT)  # noqa: F405
    + labs(  # noqa: F405
        x="Position (x)", y="Velocity (dx/dt)", title="phase-diagram · letsplot · anyplot.ai", color="Initial Condition"
    )
    + theme_minimal()  # noqa: F405
    + anyplot_theme
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG (scale 3x for 4800 x 2700)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)  # noqa: F405

# Save interactive HTML
ggsave(plot, f"plot-{THEME}.html", path=".")  # noqa: F405
