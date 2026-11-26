"""anyplot.ai
line-parametric: Parametric Curve Plot
Library: letsplot 4.10.1 | Python 3.13.14
Quality: 90/100 | Updated: 2026-06-20
"""

import math
import os
from itertools import pairwise

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette (all eight positions, canonical order)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for marks (colored lines on the page), as (position, hex) stops
SEQ_MARKS = (
    [(0.0, "#009E73"), (0.338, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Columns: set these to your table's column names
CURVE = "Curve"  # role: extra
T = "t (rad)"  # role: t
X = "x(t)"  # role: x
Y = "y(t)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("curves.csv")
# Two parametric curves stacked in one table, each ordered by t
t_lissajous = np.linspace(0, 2 * np.pi, 1000)
t_spiral = np.linspace(0, 4 * np.pi, 1000)
df = pd.DataFrame(
    {
        CURVE: ["Lissajous figure · sin 3t, sin 2t"] * 1000 + ["Archimedean spiral · t·cos t, t·sin t"] * 1000,
        T: np.concatenate([t_lissajous, t_spiral]),
        X: np.concatenate([np.sin(3 * t_lissajous), t_spiral * np.cos(t_spiral)]),
        Y: np.concatenate([np.sin(2 * t_lissajous), t_spiral * np.sin(t_spiral)]),
    }
)

# Plot: reads only df and the constants above
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=GRID, size=0.4),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=12, color=INK),
    axis_text=element_text(size=10, color=INK_SOFT),
    axis_line=element_blank(),
    axis_ticks=element_blank(),
    plot_title=element_text(size=14, color=INK, face="bold"),
    legend_text=element_text(size=10, color=INK_SOFT),
    legend_title=element_text(size=10, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
)

ramp = [ramp_color(SEQ_MARKS, k / 255) for k in range(256)]
start_color, end_color = ramp[0], ramp[-1]
closed_tol = 1e-6 * max(df[X].abs().max(), df[Y].abs().max())

panels = []
for name, curve in df.groupby(CURVE, sort=False):
    first, last = curve.iloc[[0]], curve.iloc[[-1]]
    closed = math.hypot(first[X].iloc[0] - last[X].iloc[0], first[Y].iloc[0] - last[Y].iloc[0]) <= closed_tol
    panel = (
        ggplot(curve, aes(x=X, y=Y, color=T))
        + geom_path(size=1.5, alpha=0.9)
        + geom_point(data=first, mapping=aes(x=X, y=Y), color=start_color, size=7, shape=16)
        + scale_color_gradientn(colors=ramp, name=T, format=".1f")
        + coord_fixed()
        + labs(title=name)
        + anyplot_theme
    )
    # An open curve gets an end marker too; a closed one ends where it starts
    if not closed:
        panel += geom_point(data=last, mapping=aes(x=X, y=Y), color=end_color, size=7, shape=17)
    panels.append(panel)

# Side-by-side layout with overall title; the composite carries the page color
final_plot = (
    gggrid(panels, ncol=2)
    + ggsize(800, 450)
    + ggtitle("line-parametric · python · letsplot · anyplot.ai")
    + theme(
        plot_title=element_text(size=16, color=INK, face="bold"),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

# Save PNG and interactive HTML
ggsave(final_plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(final_plot, f"plot-{THEME}.html", path=".")
