""" pyplots.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
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

# Create phase diagram
plot = (
    ggplot(df, aes(x="x", y="dx_dt", color="t"))
    + geom_path(size=1.5, alpha=0.9)
    + geom_point(data=df.iloc[[0]], size=5, color="#306998", show_legend=False)  # Start point
    + geom_point(data=df.iloc[[-1]], size=5, color="#FFD43B", shape="s", show_legend=False)  # End point (equilibrium)
    + geom_hline(yintercept=0, linetype="dashed", alpha=0.4, size=0.5)
    + geom_vline(xintercept=0, linetype="dashed", alpha=0.4, size=0.5)
    + scale_color_gradient(low="#306998", high="#FFD43B", name="Time (s)")
    + labs(x="Position x", y="Velocity dx/dt", title="phase-diagram · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16),
        panel_grid_major=element_line(alpha=0.3),
        panel_grid_minor=element_line(alpha=0.15),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
