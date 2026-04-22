""" pyplots.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()  # noqa: F405

# Data - Simple damped harmonic oscillator (damped pendulum)
# dx/dt = v, dv/dt = -omega^2 * x - gamma * v
np.random.seed(42)

omega = 2.0  # Natural frequency
gamma = 0.3  # Damping coefficient

# Multiple trajectories from different initial conditions
trajectories = []

initial_conditions = [
    (3.0, 0.0),  # Start displaced right, no velocity
    (-2.5, 2.0),  # Start left with upward velocity
    (0.5, -3.0),  # Start near center with downward velocity
    (2.0, 2.5),  # Start with both positive
]

for x0, v0 in initial_conditions:
    t = np.linspace(0, 15, 500)
    dt = t[1] - t[0]

    x = np.zeros_like(t)
    v = np.zeros_like(t)
    x[0], v[0] = x0, v0

    # Euler integration for damped harmonic oscillator
    for i in range(1, len(t)):
        x[i] = x[i - 1] + v[i - 1] * dt
        v[i] = v[i - 1] + (-(omega**2) * x[i - 1] - gamma * v[i - 1]) * dt

    traj_df = pd.DataFrame({"x": x, "dx_dt": v, "time": t, "trajectory": f"Initial ({x0}, {v0})"})
    trajectories.append(traj_df)

df = pd.concat(trajectories, ignore_index=True)

# Create phase diagram  # noqa: F405
plot = (
    ggplot(df, aes(x="x", y="dx_dt", color="trajectory"))  # noqa: F405
    + geom_path(size=1.2, alpha=0.8)  # noqa: F405
    + geom_point(  # noqa: F405
        mapping=aes(x="x", y="dx_dt"),  # noqa: F405
        data=df.groupby("trajectory").head(1),
        size=6,
        shape=21,
        fill="white",
        stroke=2,
    )
    # Mark the fixed point (equilibrium at origin)
    + geom_point(  # noqa: F405
        mapping=aes(x="x", y="dx_dt"),  # noqa: F405
        data=pd.DataFrame({"x": [0], "dx_dt": [0]}),
        color="#DC2626",
        size=8,
        shape=4,
        stroke=3,
        inherit_aes=False,
    )
    + scale_color_manual(values=["#306998", "#FFD43B", "#16A34A", "#9333EA"])  # noqa: F405
    + labs(  # noqa: F405
        x="Position (x)",
        y="Velocity (dx/dt)",
        title="phase-diagram · letsplot · pyplots.ai",
        color="Starting Condition",
    )
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        legend_text=element_text(size=14),  # noqa: F405
        legend_title=element_text(size=16),  # noqa: F405
        legend_position="right",
        panel_grid=element_line(color="#E5E7EB", size=0.5),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG (scale 3x for 4800 x 2700)
ggsave(plot, "plot.png", scale=3)  # noqa: F405

# Save interactive HTML
ggsave(plot, "plot.html")  # noqa: F405
