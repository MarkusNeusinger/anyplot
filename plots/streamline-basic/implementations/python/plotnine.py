""" pyplots.ai
streamline-basic: Basic Streamline Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    ggplot,
    labs,
    scale_color_gradient,
    theme,
    theme_minimal,
)
from scipy.integrate import solve_ivp
from scipy.interpolate import RegularGridInterpolator


# Set seed for reproducibility
np.random.seed(42)

# Create grid for vector field
nx, ny = 40, 40
x = np.linspace(-3, 3, nx)
y = np.linspace(-3, 3, ny)
X, Y = np.meshgrid(x, y)

# Define vector field: vortex flow with a dipole effect
# u = -y, v = x creates circular streamlines (vortex)
U = -Y
V = X

# Create interpolators for the velocity field
u_interp = RegularGridInterpolator((y, x), U, bounds_error=False, fill_value=0)
v_interp = RegularGridInterpolator((y, x), V, bounds_error=False, fill_value=0)

# Compute streamlines from various starting points
streamlines_data = []
arrow_data = []
streamline_id = 0

# Create varied starting points - grid on one side and scattered points
# This shows field topology better than just radial starting points
start_points = []

# Grid of starting points on left side
for sx in np.linspace(-2.8, -1.5, 4):
    for sy in np.linspace(-2.5, 2.5, 6):
        start_points.append((sx, sy))

# Some radial starting points to show circular nature
for r in [0.6, 1.3, 2.2]:
    for angle in np.linspace(0, 2 * np.pi, 6, endpoint=False):
        start_points.append((r * np.cos(angle), r * np.sin(angle)))

for x0, y0 in start_points:
    # Integrate forward - inline velocity calculation (no function definition)
    try:
        result = solve_ivp(
            lambda t, pos: [u_interp([pos[1], pos[0]])[0], v_interp([pos[1], pos[0]])[0]],
            [0, 4],
            [x0, y0],
            max_step=0.05,
            dense_output=True,
        )
        if result.success and len(result.t) > 2:
            t_eval = np.linspace(0, result.t[-1], 100)
            trajectory = result.sol(t_eval)

            # Calculate velocity magnitude at each point
            for j in range(len(t_eval)):
                px, py = trajectory[0, j], trajectory[1, j]
                # Keep points within bounds
                if -3 <= px <= 3 and -3 <= py <= 3:
                    speed = np.sqrt(px**2 + py**2)  # For vortex: speed = r
                    streamlines_data.append({"x": px, "y": py, "streamline": streamline_id, "order": j, "speed": speed})

            # Add arrow marker at ~60% along the streamline to show direction
            arrow_idx = int(len(t_eval) * 0.6)
            if arrow_idx < len(t_eval):
                ax, ay = trajectory[0, arrow_idx], trajectory[1, arrow_idx]
                if -3 <= ax <= 3 and -3 <= ay <= 3:
                    arrow_speed = np.sqrt(ax**2 + ay**2)
                    arrow_data.append({"x": ax, "y": ay, "speed": arrow_speed})

            streamline_id += 1
    except Exception:
        pass

# Convert to DataFrames
df = pd.DataFrame(streamlines_data)
df_arrows = pd.DataFrame(arrow_data)

# Create the plot using plotnine's native geom_path
# Use 1:1 canvas (12x12) for circular pattern - avoids empty horizontal space
plot = (
    ggplot(df, aes(x="x", y="y", group="streamline", color="speed"))
    + geom_path(size=1.2, alpha=0.8)
    + geom_point(
        data=df_arrows,
        mapping=aes(x="x", y="y", color="speed"),
        shape=">",
        size=4,
        inherit_aes=False,
        show_legend=False,
    )
    + scale_color_gradient(low="#306998", high="#FFD43B", name="Flow Speed")
    + labs(x="X Position", y="Y Position", title="streamline-basic · plotnine · pyplots.ai")
    + coord_fixed(ratio=1)
    + theme_minimal()
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        panel_background=element_rect(fill="white"),
        plot_background=element_rect(fill="white"),
    )
)

# Save the plot
plot.save("plot.png", dpi=300, verbose=False)
