"""anyplot.ai
streamline-basic: Basic Streamline Plot
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_line,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    ggplot,
    labs,
    scale_color_cmap,
    theme,
    theme_minimal,
)
from scipy.integrate import solve_ivp
from scipy.interpolate import RegularGridInterpolator


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

np.random.seed(42)

nx, ny = 40, 40
x = np.linspace(-3, 3, nx)
y = np.linspace(-3, 3, ny)
X, Y = np.meshgrid(x, y)

U = -Y
V = X

u_interp = RegularGridInterpolator((y, x), U, bounds_error=False, fill_value=0)
v_interp = RegularGridInterpolator((y, x), V, bounds_error=False, fill_value=0)

streamlines_data = []
arrow_data = []
streamline_id = 0

start_points = []

for sx in np.linspace(-2.8, -1.5, 4):
    for sy in np.linspace(-2.5, 2.5, 6):
        start_points.append((sx, sy))

for r in [0.6, 1.3, 2.2]:
    for angle in np.linspace(0, 2 * np.pi, 6, endpoint=False):
        start_points.append((r * np.cos(angle), r * np.sin(angle)))

for x0, y0 in start_points:
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

            for j in range(len(t_eval)):
                px, py = trajectory[0, j], trajectory[1, j]
                if -3 <= px <= 3 and -3 <= py <= 3:
                    speed = np.sqrt(px**2 + py**2)
                    streamlines_data.append({"x": px, "y": py, "streamline": streamline_id, "order": j, "speed": speed})

            arrow_idx = int(len(t_eval) * 0.6)
            if arrow_idx < len(t_eval):
                ax, ay = trajectory[0, arrow_idx], trajectory[1, arrow_idx]
                if -3 <= ax <= 3 and -3 <= ay <= 3:
                    arrow_speed = np.sqrt(ax**2 + ay**2)
                    arrow_data.append({"x": ax, "y": ay, "speed": arrow_speed})

            streamline_id += 1
    except Exception:
        pass

df = pd.DataFrame(streamlines_data)
df_arrows = pd.DataFrame(arrow_data)

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    plot_title=element_text(size=24, color=INK),
    legend_text=element_text(size=16, color=INK_SOFT),
    legend_title=element_text(size=18, color=INK),
    figure_size=(16, 9),
)

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
    + scale_color_cmap(cmap_name="viridis", name="Flow Speed")
    + labs(x="X Position", y="Y Position", title="streamline-basic · plotnine · anyplot.ai")
    + coord_fixed(ratio=1)
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
