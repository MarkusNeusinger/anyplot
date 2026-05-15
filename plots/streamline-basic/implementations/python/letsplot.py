""" anyplot.ai
streamline-basic: Basic Streamline Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_line,
    element_rect,
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

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Create a vortex flow field: u = -y, v = x (circular streamlines)
np.random.seed(42)

x_min, x_max = -3, 3
y_min, y_max = -3, 3

# Seed points for streamlines - distributed radially for good coverage
radii = np.linspace(0.3, 2.8, 8)
seed_points = [[r, 0.0] for r in radii]

# Integrate streamlines forward
streamline_data = []
streamline_id = 0

for seed in seed_points:
    t_span = [0, 2 * np.pi]
    t_eval = np.linspace(0, 2 * np.pi, 100)

    # Inline velocity field calculation: rotation field u=-y, v=x
    def velocity_field(t, point):
        x, y = point
        return [-y, x]

    try:
        sol = solve_ivp(velocity_field, t_span, seed, t_eval=t_eval, method="RK45", dense_output=True, max_step=0.1)

        if sol.success:
            xs = sol.y[0]
            ys = sol.y[1]

            mask = (xs >= x_min) & (xs <= x_max) & (ys >= y_min) & (ys <= y_max)

            if np.any(mask):
                xs_clipped = xs[mask]
                ys_clipped = ys[mask]
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

df = pd.DataFrame(streamline_data)

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", group="streamline", color="magnitude"))
    + geom_path(size=1.5, alpha=0.85)
    + scale_color_gradient(low="#306998", high="#FFD43B", name="Field Strength")
    + labs(x="X Position", y="Y Position", title="streamline-basic · letsplot · anyplot.ai")
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_title=element_text(size=20, color=INK),
        plot_title=element_text(size=24, color=INK),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=14, color=INK_SOFT),
    )
)

# Save PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
