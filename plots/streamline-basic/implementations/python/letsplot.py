""" pyplots.ai
streamline-basic: Basic Streamline Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    geom_path,
    ggplot,
    ggsize,
    labs,
    scale_color_gradient,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave
from scipy.integrate import solve_ivp


LetsPlot.setup_html()

# Data - Create a vortex flow field: u = -y, v = x (circular streamlines)
np.random.seed(42)


# Define the vector field
def velocity_field(t, point):
    x, y = point
    # Rotation field: creates circular streamlines
    u = -y
    v = x
    return [u, v]


# Grid bounds
x_min, x_max = -3, 3
y_min, y_max = -3, 3

# Seed points for streamlines - distributed radially for good coverage
radii = np.linspace(0.3, 2.8, 8)  # More radii for better coverage

seed_points = []
for r in radii:
    # Single seed point per radius (circles are symmetric)
    seed_points.append([r, 0.0])

# Integrate streamlines forward
streamline_data = []
streamline_id = 0

for seed in seed_points:
    # Integrate forward in time
    t_span = [0, 2 * np.pi]  # One full rotation for circular field
    t_eval = np.linspace(0, 2 * np.pi, 100)

    try:
        sol = solve_ivp(velocity_field, t_span, seed, t_eval=t_eval, method="RK45", dense_output=True, max_step=0.1)

        if sol.success:
            xs = sol.y[0]
            ys = sol.y[1]

            # Clip to bounds
            mask = (xs >= x_min) & (xs <= x_max) & (ys >= y_min) & (ys <= y_max)

            # Find continuous segments within bounds
            if np.any(mask):
                xs_clipped = xs[mask]
                ys_clipped = ys[mask]

                # Calculate velocity magnitude for coloring
                magnitudes = np.sqrt(xs_clipped**2 + ys_clipped**2)

                for i in range(len(xs_clipped)):
                    streamline_data.append(
                        {
                            "x": xs_clipped[i],
                            "y": ys_clipped[i],
                            "magnitude": magnitudes[i],
                            "streamline": streamline_id,
                        }
                    )
                streamline_id += 1
    except Exception:
        continue

# Create DataFrame
df = pd.DataFrame(streamline_data)

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", group="streamline", color="magnitude"))
    + geom_path(size=1.5, alpha=0.85)
    + scale_color_gradient(low="#306998", high="#FFD43B", name="Field Strength")
    + labs(x="X Position", y="Y Position", title="Vortex Flow Field · streamline-basic · letsplot · pyplots.ai")
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        axis_text=element_text(size=16),
        axis_title=element_text(size=20),
        plot_title=element_text(size=24),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
    )
)

# Save PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, filename="plot.html", path=".")
