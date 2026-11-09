""" anyplot.ai
streamline-basic: Basic Streamline Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_cartesian,
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
from scipy.interpolate import LinearNDInterpolator


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette; the continuous speed scale is imprint_seq (positions 1 -> 3)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]

# Constants
N_STREAMLINES = 8  # seed count: enough to show the pattern, few enough to stay separate
SEED_SPAN = (0.1, 0.93)  # seeds run from the domain center toward its right edge, as fractions of the half-width
PANEL_ASPECT = (
    0.86  # width / height of the panel on the 2400 x 2400 canvas beside the color bar, so x and y share one unit length
)
SPEED = "Speed (m/s)"  # name of the derived speed along each streamline, shown on the color bar

# Columns: set these to your table's column names
X = "x (m)"  # role: x
Y = "y (m)"  # role: y
U = "u (m/s)"  # role: u
V = "v (m/s)"  # role: v

# Data: replace this block with your own table, for example df = pd.read_csv("field.csv")
# A 30 x 30 grid of a rotating fluid vortex in a 6 m tank, u = -y, v = x (rigid rotation at 1 rad/s), one row per grid point
grid = np.linspace(-3, 3, 30)
grid_x, grid_y = np.meshgrid(grid, grid)
df = pd.DataFrame({X: grid_x.ravel(), Y: grid_y.ravel(), U: -grid_y.ravel(), V: grid_x.ravel()})

# Plot: reads only df and the constants above
field = df[[X, Y, U, V]].astype(float).dropna()
points = field[[X, Y]].to_numpy()
velocity = LinearNDInterpolator(points, field[[U, V]].to_numpy())

x_min, x_max = field[X].min(), field[X].max()
y_min, y_max = field[Y].min(), field[Y].max()
center_x, center_y = (x_min + x_max) / 2, (y_min + y_max) / 2
span = max(x_max - x_min, y_max - y_min)
half_width = 1.05 * max((x_max - x_min) / 2, (y_max - y_min) / 2 * PANEL_ASPECT)
speeds = np.hypot(field[U], field[V])
typical_speed = speeds[speeds > 0].median() if (speeds > 0).any() else 1.0
t_max = 4 * span / typical_speed


def field_velocity(t, point):
    uv = velocity([point])[0]
    return [0.0, 0.0] if np.isnan(uv).any() else list(uv)


def leaves_domain(t, point):
    return min(point[0] - x_min, x_max - point[0], point[1] - y_min, y_max - point[1])


leaves_domain.terminal = True
leaves_domain.direction = -1

rows = []
for line_id, offset in enumerate(np.linspace(*SEED_SPAN, N_STREAMLINES) * (x_max - x_min) / 2):
    seed = np.array([center_x + offset, center_y])

    def closes_loop(t, point, seed=seed):
        return np.hypot(point[0] - seed[0], point[1] - seed[1]) - 0.005 * span

    closes_loop.terminal = True
    closes_loop.direction = -1

    sol = solve_ivp(
        field_velocity,
        [0, t_max],
        seed,
        method="RK45",
        dense_output=True,
        max_step=t_max / 200,
        events=[leaves_domain, closes_loop],
    )
    if not sol.success or sol.t[-1] <= 0:
        continue
    path = sol.sol(np.linspace(0, sol.t[-1], 200))
    if len(sol.t_events[1]):
        path = np.column_stack([path, seed])
    xs = np.clip(path[0], x_min, x_max)
    ys = np.clip(path[1], y_min, y_max)
    uv = velocity(xs, ys)
    rows.append(pd.DataFrame({X: xs, Y: ys, SPEED: np.hypot(uv[:, 0], uv[:, 1]), "streamline": line_id}))

lines = pd.concat(rows, ignore_index=True)

plot = (
    ggplot(lines, aes(x=X, y=Y, group="streamline", color=SPEED))
    + geom_path(size=1.2, alpha=0.9)
    + scale_color_gradient(low=IMPRINT_SEQ[0], high=IMPRINT_SEQ[1], name=SPEED)
    + labs(x=X, y=Y, title="streamline-basic · python · letsplot · anyplot.ai")
    + coord_cartesian(
        xlim=[center_x - half_width, center_x + half_width],
        ylim=[center_y - half_width / PANEL_ASPECT, center_y + half_width / PANEL_ASPECT],
    )
    + ggsize(600, 600)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=GRID, size=0.3),
        panel_grid_minor=element_line(color=GRID, size=0.2),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_title=element_text(size=12, color=INK),
        plot_title=element_text(size=16, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=11, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
    )
)

# Save: PNG scaled 4x to 2400 x 2400 px, plus the interactive HTML
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
