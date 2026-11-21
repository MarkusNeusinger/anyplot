"""anyplot.ai
streamline-basic: Basic Streamline Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    arrow,
    coord_fixed,
    element_line,
    element_rect,
    element_text,
    geom_path,
    geom_segment,
    ggplot,
    labs,
    scale_color_gradient,
    theme,
    theme_minimal,
)
from scipy.integrate import solve_ivp
from scipy.interpolate import RegularGridInterpolator


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: sequential cmap runs from position 1 to position 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_STREAMLINES = 9  # one per ring, spaced from the centre to the edge
ARROW_POSITION = 0.6  # share of each streamline's length where its arrow sits

# Columns: set these to your table's column names
X_POS = "X Position"  # role: x
Y_POS = "Y Position"  # role: y
U_VEL = "Horizontal velocity"  # role: u
V_VEL = "Vertical velocity"  # role: v
SPEED = "Flow Speed"  # role: extra

# Data: replace this block with your own grid, one row per grid point, for example df = pd.read_csv("field.csv")
grid_x = np.linspace(-3, 3, 40)
grid_y = np.linspace(-3, 3, 40)
mesh_x, mesh_y = np.meshgrid(grid_x, grid_y)
df = pd.DataFrame(
    {
        X_POS: mesh_x.ravel(),
        Y_POS: mesh_y.ravel(),
        U_VEL: -mesh_y.ravel(),  # vortex flow: u = -y, v = x
        V_VEL: mesh_x.ravel(),
    }
)

# Plot: reads only df and the constants above
grid = df.dropna(subset=[X_POS, Y_POS])
xs = np.sort(grid[X_POS].unique())
ys = np.sort(grid[Y_POS].unique())
x_lo, x_hi = xs[0], xs[-1]
y_lo, y_hi = ys[0], ys[-1]
field = {
    col: grid.pivot_table(index=Y_POS, columns=X_POS, values=col).reindex(index=ys, columns=xs).to_numpy()
    for col in (U_VEL, V_VEL)
}
u_interp = RegularGridInterpolator((ys, xs), field[U_VEL], bounds_error=False, fill_value=0)
v_interp = RegularGridInterpolator((ys, xs), field[V_VEL], bounds_error=False, fill_value=0)


def velocity(px, py):
    """Field at (px, py); a point without data counts as still water."""
    pts = np.column_stack([np.atleast_1d(py), np.atleast_1d(px)])
    return np.nan_to_num(u_interp(pts)), np.nan_to_num(v_interp(pts))


def direction(_, pos):
    """Unit flow direction, so the trace advances by arc length whatever the units of the field."""
    u, v = velocity(pos[0], pos[1])
    norm = np.hypot(u[0], v[0])
    return [0.0, 0.0] if norm == 0 else [u[0] / norm, v[0] / norm]


# Seeds: one per ring, at evenly spaced radii from the centre to the domain edge and rotated against each other
x_span, y_span = x_hi - x_lo, y_hi - y_lo
centre_x, centre_y = (x_lo + x_hi) / 2, (y_lo + y_hi) / 2
radii = np.linspace(0.12, 0.93, N_STREAMLINES) * min(x_span, y_span) / 2
angles = np.arange(N_STREAMLINES) * 2 * np.pi * 0.382
seeds = list(zip(centre_x + radii * np.cos(angles), centre_y + radii * np.sin(angles), strict=True))
step = min(x_span, y_span) / 120  # largest arc-length step of the integrator

paths = []
arrows = []
for line_id, (x0, y0) in enumerate(seeds):
    turn = 2 * np.pi * np.hypot(x0 - centre_x, y0 - centre_y)  # arc length of one full turn around the centre
    result = solve_ivp(direction, [0, turn], [x0, y0], max_step=step, dense_output=True)
    if not result.success or len(result.t) < 3:
        continue
    px, py = result.sol(np.linspace(0, result.t[-1], 100))
    inside = (px >= x_lo) & (px <= x_hi) & (py >= y_lo) & (py <= y_hi)
    if inside.sum() < 3:
        continue
    px, py = px[inside], py[inside]
    speed = np.hypot(*velocity(px, py))
    paths.append(pd.DataFrame({X_POS: px, Y_POS: py, "streamline": line_id, SPEED: speed}))

    # Direction arrow: a short segment along the path, its head pointing with the flow
    i = int(len(px) * ARROW_POSITION)
    i = min(i, len(px) - 4)
    arrows.append(pd.DataFrame({"x0": [px[i]], "y0": [py[i]], "x1": [px[i + 3]], "y1": [py[i + 3]], SPEED: [speed[i]]}))

paths = pd.concat(paths, ignore_index=True) if paths else pd.DataFrame(columns=[X_POS, Y_POS, "streamline", SPEED])
arrows = pd.concat(arrows, ignore_index=True) if arrows else pd.DataFrame(columns=["x0", "y0", "x1", "y1", SPEED])

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    axis_title=element_text(size=10, color=INK),
    axis_text=element_text(size=8, color=INK_SOFT),
    plot_title=element_text(size=12, color=INK),
    legend_text=element_text(size=8, color=INK_SOFT),
    legend_title=element_text(size=9, color=INK),
    legend_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    figure_size=(6, 6),
)

plot = (
    ggplot(paths, aes(x=X_POS, y=Y_POS, group="streamline", color=SPEED))
    + geom_path(size=1.0, alpha=0.9)
    + geom_segment(
        data=arrows,
        mapping=aes(x="x0", y="y0", xend="x1", yend="y1", color=SPEED),
        arrow=arrow(length=0.08, type="closed", angle=22),
        size=1.0,
        inherit_aes=False,
        show_legend=False,
    )
    + scale_color_gradient(low=IMPRINT_PALETTE[0], high=IMPRINT_PALETTE[2], name=SPEED)
    + labs(x=X_POS, y=Y_POS, title="streamline-basic · python · plotnine · anyplot.ai")
    + coord_fixed(ratio=1)
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
