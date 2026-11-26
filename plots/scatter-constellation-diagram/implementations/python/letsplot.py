""" anyplot.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-26
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

RECEIVED_COLOR = "#009E73"  # Imprint palette position 1 — received symbols (primary data)
IDEAL_COLOR = "#BD8233"  # Imprint palette position 4 ochre — ideal markers (colorblind-safe)

# Constants
SNR_DB = 20  # signal-to-noise ratio of the example channel

# Columns: set these to your table's column names
IN_PHASE = "In-Phase (I)"  # role: i
QUADRATURE = "Quadrature (Q)"  # role: q
IDEAL_IN_PHASE = "Ideal in-phase (I)"  # role: ideal_i
IDEAL_QUADRATURE = "Ideal quadrature (Q)"  # role: ideal_q

# Data: replace this block with your own table, for example df = pd.read_csv("symbols.csv")
np.random.seed(42)
grid_vals = np.array([-3, -1, 1, 3])  # 16-QAM: 4x4 grid at +/-1, +/-3
grid_i, grid_q = np.meshgrid(grid_vals, grid_vals)
grid_i = grid_i.flatten()
grid_q = grid_q.flatten()

n_symbols = 1000
symbol_indices = np.random.randint(0, 16, n_symbols)
noise_std = np.sqrt(np.mean(grid_i**2 + grid_q**2) / (2 * 10 ** (SNR_DB / 10)))
df = pd.DataFrame(
    {
        IN_PHASE: grid_i[symbol_indices] + np.random.normal(0, noise_std, n_symbols),
        QUADRATURE: grid_q[symbol_indices] + np.random.normal(0, noise_std, n_symbols),
        IDEAL_IN_PHASE: grid_i[symbol_indices],
        IDEAL_QUADRATURE: grid_q[symbol_indices],
    }
)

# Plot
ideal_df = df[[IDEAL_IN_PHASE, IDEAL_QUADRATURE]].drop_duplicates()

# EVM: RMS error vector relative to the RMS of the ideal constellation
error_sq = (df[IN_PHASE] - df[IDEAL_IN_PHASE]) ** 2 + (df[QUADRATURE] - df[IDEAL_QUADRATURE]) ** 2
rms_reference = np.sqrt(np.mean(ideal_df[IDEAL_IN_PHASE] ** 2 + ideal_df[IDEAL_QUADRATURE] ** 2))
evm_percent = np.sqrt(error_sq.mean()) / rms_reference * 100

# Decision boundaries run midway between neighbouring ideal values; limits are symmetric about the origin
levels = np.sort(np.unique(ideal_df[IDEAL_IN_PHASE]))
midpoints = (levels[:-1] + levels[1:]) / 2
lim = np.abs(levels).max() * 1.5
edges = [-lim, *midpoints, lim]
tick_vals = np.arange(-np.floor(lim), np.floor(lim) + 1)

# Alternating decision-region shading, theme-adaptive (dark needs a wider step to show on the near-black page)
colors_alt = ["#F0EDE5", "#E8E5DE"] if THEME == "light" else ["#2B2B27", "#201F1C"]
rects_df = pd.DataFrame(
    [
        {"xmin": x0, "xmax": x1, "ymin": y0, "ymax": y1, "fill": colors_alt[(ri + ci) % 2]}
        for ri, (y0, y1) in enumerate(zip(edges[:-1], edges[1:], strict=True))
        for ci, (x0, x1) in enumerate(zip(edges[:-1], edges[1:], strict=True))
    ]
)
boundary_df = pd.DataFrame({"pos": midpoints})
evm_df = pd.DataFrame({"x": [lim - 0.7], "y": [lim - 0.4], "label": [f"EVM = {evm_percent:.1f}%"]})

# Title with scaled font size, calibrated for ggsize(600, 600)
title = "16-QAM Constellation · scatter-constellation-diagram · python · letsplot · anyplot.ai"
title_size = max(9, round(13 * 67 / len(title)))

plot = (
    ggplot()  # noqa: F405
    # Shaded decision regions
    + geom_rect(  # noqa: F405
        data=rects_df,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="fill"),  # noqa: F405
        alpha=1.0,
        color=PAGE_BG,
        size=0.3,
    )
    + scale_fill_identity()  # noqa: F405
    # Dashed decision boundaries
    + geom_vline(data=boundary_df, mapping=aes(xintercept="pos"), linetype="dashed", color=INK_SOFT, size=0.5)  # noqa: F405
    + geom_hline(data=boundary_df, mapping=aes(yintercept="pos"), linetype="dashed", color=INK_SOFT, size=0.5)  # noqa: F405
    # Axis lines through the origin
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.7)  # noqa: F405
    + geom_vline(xintercept=0, color=INK_SOFT, size=0.7)  # noqa: F405
    # 2D density contours of the received symbols
    + geom_density2d(  # noqa: F405
        data=df,
        mapping=aes(x=IN_PHASE, y=QUADRATURE),  # noqa: F405
        color=RECEIVED_COLOR,
        alpha=0.4,
        size=0.5,
    )
    # Received symbols
    + geom_point(  # noqa: F405
        data=df,
        mapping=aes(x=IN_PHASE, y=QUADRATURE),  # noqa: F405
        color=RECEIVED_COLOR,
        size=2.0,
        alpha=0.35,
    )
    # Ideal constellation markers (crosses)
    + geom_point(  # noqa: F405
        data=ideal_df,
        mapping=aes(x=IDEAL_IN_PHASE, y=IDEAL_QUADRATURE),  # noqa: F405
        color=IDEAL_COLOR,
        size=7,
        shape=4,
        stroke=2.5,
    )
    # EVM annotation
    + geom_label(  # noqa: F405
        data=evm_df,
        mapping=aes(x="x", y="y", label="label"),  # noqa: F405
        size=4,
        color=INK,
        fill=ELEVATED_BG,
        alpha=0.9,
        hjust=1,
        label_padding=0.5,
        label_r=0.2,
        label_size=0.6,
    )
    + labs(x=IN_PHASE, y=QUADRATURE, title=title)  # noqa: F405
    + coord_fixed()  # noqa: F405
    + scale_x_continuous(limits=[-lim, lim], breaks=tick_vals)  # noqa: F405
    + scale_y_continuous(limits=[-lim, lim], breaks=tick_vals)  # noqa: F405
    + ggsize(600, 600)  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=title_size, color=INK, face="bold"),  # noqa: F405
        axis_title=element_text(size=12, color=INK),  # noqa: F405
        axis_text=element_text(size=10, color=INK_SOFT),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG, color=INK_SOFT, size=0.5),  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG),  # noqa: F405
        panel_grid_major=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_ticks=element_line(color=INK_SOFT, size=0.5),  # noqa: F405
        axis_line=element_line(color=INK_SOFT, size=0.5),  # noqa: F405
        plot_margin=[20, 20, 20, 20],
    )
)

# A fixed aspect leaves transparent strips: a one-panel grid paints the whole canvas in the page color
plot = (
    gggrid([plot])  # noqa: F405
    + ggsize(600, 600)  # noqa: F405
    + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))  # noqa: F405
)

# Save
export_ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
export_ggsave(plot, filename=f"plot-{THEME}.html", path=".")
