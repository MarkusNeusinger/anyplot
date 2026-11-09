"""anyplot.ai
scatter-3d: 3D Scatter Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_cartesian,
    element_blank,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_gradient,
    scale_size_identity,
    theme,
    theme_void,
)
from lets_plot.export import ggsave
from matplotlib.ticker import MaxNLocator


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette; altitude is continuous, so it takes imprint_seq: position 1 (green) → position 3 (blue)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

LetsPlot.setup_html()

# Constants: the fixed viewpoint of the 3D frame
ELEVATION = np.radians(22)
AZIMUTH = np.radians(-55)
PANEL_ASPECT = 1.7  # width / height of the panel left beside the title and color bar

# Columns: set these to your table's column names
X_POS = "Easting (m)"  # role: x
Y_POS = "Northing (m)"  # role: y
Z_POS = "Altitude (m)"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("gps_fixes.csv")
# GPS fixes of tagged starlings around a reed-bed roost at dusk: a flock swirling
# above the roost, a commuting line arriving high along the hedgerow, and a group
# still foraging on the meadow just above the ground
np.random.seed(42)
roost_swirl = [np.random.randn(60) * 5 + 30, np.random.randn(60) * 5 + 20, np.random.randn(60) * 5 + 25]
hedgerow_line = [np.random.randn(50) * 18 - 20, np.random.randn(50) * 4 - 10, np.random.randn(50) * 6 + 45]
meadow_group = [np.random.randn(40) * 12 + 5, np.random.randn(40) * 12 - 25, np.abs(np.random.randn(40) * 1.0) + 0.5]
df = pd.DataFrame(
    {
        X_POS: np.concatenate([roost_swirl[0], hedgerow_line[0], meadow_group[0]]),
        Y_POS: np.concatenate([roost_swirl[1], hedgerow_line[1], meadow_group[1]]),
        Z_POS: np.concatenate([roost_swirl[2], hedgerow_line[2], meadow_group[2]]),
    }
)

# Plot: reads only df and the constants above
# Each axis is scaled into a unit cube [-0.5, 0.5]³, then rotated and projected to the page
columns = [X_POS, Y_POS, Z_POS]
lows = df[columns].min().to_numpy(dtype=float)
highs = df[columns].max().to_numpy(dtype=float)
spans = np.where(highs > lows, highs - lows, 1.0)
projection = np.array(
    [
        [np.cos(AZIMUTH), -np.sin(AZIMUTH), 0.0],
        [np.sin(AZIMUTH) * np.sin(ELEVATION), np.cos(AZIMUTH) * np.sin(ELEVATION), np.cos(ELEVATION)],
    ]
)
toward_viewer = np.array(
    [-np.sin(AZIMUTH) * np.cos(ELEVATION), -np.cos(AZIMUTH) * np.cos(ELEVATION), np.sin(ELEVATION)]
)

cube = (df[columns].to_numpy(dtype=float) - lows) / spans - 0.5
points = df.copy()
points["sx"], points["sy"] = (cube @ projection.T).T
nearness = pd.Series(cube @ toward_viewer, index=df.index)
points["size"] = 3.0 + 4.0 * (nearness - nearness.min()) / max(nearness.max() - nearness.min(), 1e-9)
points = points.iloc[np.argsort(nearness.to_numpy())]  # painter's order: far points first

# The three back panes (floor and two walls) face away from the viewer
u_back = 0.5 * np.sign(np.sin(AZIMUTH))
v_back = 0.5 * np.sign(np.cos(AZIMUTH))
tick_text = [MaxNLocator(nbins=4).tick_values(lo, hi) for lo, hi in zip(lows, highs, strict=True)]
tick_text = [t[(t >= lo) & (t <= hi)] for t, lo, hi in zip(tick_text, lows, highs, strict=True)]
ticks = [(t - lo) / span - 0.5 for t, lo, span in zip(tick_text, lows, spans, strict=True)]

grid = []
for t in ticks[0]:
    grid += [(t, -0.5, -0.5, t, 0.5, -0.5), (t, v_back, -0.5, t, v_back, 0.5)]
for t in ticks[1]:
    grid += [(-0.5, t, -0.5, 0.5, t, -0.5), (u_back, t, -0.5, u_back, t, 0.5)]
for t in ticks[2]:
    grid += [(u_back, -0.5, t, u_back, 0.5, t), (-0.5, v_back, t, 0.5, v_back, t)]
edges = [
    (-0.5, -v_back, -0.5, 0.5, -v_back, -0.5),
    (-u_back, -0.5, -0.5, -u_back, 0.5, -0.5),
    (u_back, -v_back, -0.5, u_back, -v_back, 0.5),
    (-0.5, v_back, 0.5, 0.5, v_back, 0.5),
    (u_back, -0.5, 0.5, u_back, 0.5, 0.5),
    (-u_back, v_back, -0.5, -u_back, v_back, 0.5),
]
grid, edges = (pd.DataFrame(s, columns=["u0", "v0", "w0", "u1", "v1", "w1"]) for s in (grid, edges))
for frame in (grid, edges):
    frame["x"], frame["y"] = (frame[["u0", "v0", "w0"]].to_numpy() @ projection.T).T
    frame["xend"], frame["yend"] = (frame[["u1", "v1", "w1"]].to_numpy() @ projection.T).T

# Tick labels sit just outside the front edges; axis titles a little further out
tick_labels = pd.DataFrame(
    [(t, -v_back * 1.22, -0.5, f"{s:g}") for t, s in zip(ticks[0], tick_text[0], strict=True)]
    + [(-u_back * 1.22, t, -0.5, f"{s:g}") for t, s in zip(ticks[1], tick_text[1], strict=True)]
    + [(u_back * 1.18, -v_back * 1.18, t, f"{s:g}") for t, s in zip(ticks[2], tick_text[2], strict=True)],
    columns=["u", "v", "w", "label"],
)
axis_titles = pd.DataFrame(
    [(0.0, -v_back * 1.62, -0.5, X_POS), (-u_back * 1.62, 0.0, -0.5, Y_POS), (u_back, -v_back, 0.68, Z_POS)],
    columns=["u", "v", "w", "label"],
)
for frame in (tick_labels, axis_titles):
    frame["x"], frame["y"] = (frame[["u", "v", "w"]].to_numpy(dtype=float) @ projection.T).T

# Widen the x window to the panel's aspect so the cube keeps equal page units on both axes
text_y = pd.concat([tick_labels["y"], axis_titles["y"]])
text_x = pd.concat([tick_labels["x"], axis_titles["x"], edges["x"], edges["xend"]])
y_limits = [text_y.min() - 0.05, text_y.max() + 0.05]
x_half = (y_limits[1] - y_limits[0]) * PANEL_ASPECT / 2
x_center = (text_x.min() + text_x.max()) / 2  # center the extent, not the mean, so margins balance
x_limits = [x_center - x_half, x_center + x_half]

tooltips = (
    layer_tooltips()
    .line(f"{X_POS}|@{{{X_POS}}}")
    .line(f"{Y_POS}|@{{{Y_POS}}}")
    .line(f"{Z_POS}|@{{{Z_POS}}}")
    .format(f"@{{{X_POS}}}", ".2f")
    .format(f"@{{{Y_POS}}}", ".2f")
    .format(f"@{{{Z_POS}}}", ".2f")
)

plot = (
    ggplot()
    + geom_segment(
        data=grid, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color=INK, alpha=0.15, size=0.4, tooltips="none"
    )
    + geom_segment(
        data=edges,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        color=INK_SOFT,
        alpha=0.7,
        size=0.6,
        tooltips="none",
    )
    + geom_point(
        data=points,
        mapping=aes(x="sx", y="sy", fill=Z_POS, size="size"),
        color=PAGE_BG,
        alpha=0.8,
        stroke=0.4,
        shape=21,
        tooltips=tooltips,
    )
    + geom_text(data=tick_labels, mapping=aes(x="x", y="y", label="label"), color=INK_SOFT, size=5.5)
    + geom_text(data=axis_titles, mapping=aes(x="x", y="y", label="label"), color=INK, size=6.2)
    + scale_fill_gradient(low=IMPRINT_PALETTE[0], high=IMPRINT_PALETTE[2], name=Z_POS)
    + scale_size_identity()
    + coord_cartesian(xlim=x_limits, ylim=y_limits)
    + labs(title="scatter-3d · python · letsplot · anyplot.ai")
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=16, color=INK, face="bold"),
        legend_title=element_text(size=12, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_blank(),
        legend_position="right",
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
