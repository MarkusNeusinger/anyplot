"""anyplot.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 91/100 | Updated: 2026-06-18
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

RECEIVED_COLOR = "#009E73"  # Imprint position 1 — received symbols (primary data)
IDEAL_COLOR = "#BD8233"  # Imprint position 4 ochre — ideal markers (colorblind-safe)

# Data
np.random.seed(42)

# 16-QAM ideal constellation points on a 4x4 grid at +/-1, +/-3
grid_vals = np.array([-3, -1, 1, 3])
ideal_i, ideal_q = np.meshgrid(grid_vals, grid_vals)
ideal_i = ideal_i.flatten()
ideal_q = ideal_q.flatten()

# Generate received symbols with additive Gaussian noise (~20 dB SNR)
n_symbols = 1000
symbol_indices = np.random.randint(0, 16, n_symbols)
snr_db = 20
signal_power = np.mean(ideal_i**2 + ideal_q**2)
noise_std = np.sqrt(signal_power / (2 * 10 ** (snr_db / 10)))

received_i = ideal_i[symbol_indices] + np.random.normal(0, noise_std, n_symbols)
received_q = ideal_q[symbol_indices] + np.random.normal(0, noise_std, n_symbols)

# Compute EVM
error_vectors = np.sqrt((received_i - ideal_i[symbol_indices]) ** 2 + (received_q - ideal_q[symbol_indices]) ** 2)
rms_reference = np.sqrt(np.mean(ideal_i**2 + ideal_q**2))
evm_percent = np.sqrt(np.mean(error_vectors**2)) / rms_reference * 100

# DataFrames
received_df = pd.DataFrame({"I": received_i, "Q": received_q})
ideal_df = pd.DataFrame({"I": ideal_i, "Q": ideal_q})

# Decision boundary rectangles — theme-adaptive shading
if THEME == "light":
    colors_alt = ["#F0EDE5", "#E8E5DE"]
else:
    colors_alt = ["#222220", "#1E1E1B"]

rects = []
boundary_edges = [-4.5, -2, 0, 2, 4.5]
for ri, (y0, y1) in enumerate(zip(boundary_edges[:-1], boundary_edges[1:], strict=True)):
    for ci, (x0, x1) in enumerate(zip(boundary_edges[:-1], boundary_edges[1:], strict=True)):
        rects.append({"xmin": x0, "xmax": x1, "ymin": y0, "ymax": y1, "fill": colors_alt[(ri + ci) % 2]})
rects_df = pd.DataFrame(rects)

# Decision boundary line positions
boundary_vals = np.array([-2, 0, 2])
boundary_v = pd.DataFrame({"x": boundary_vals})
boundary_h = pd.DataFrame({"y": boundary_vals})

# EVM annotation
evm_df = pd.DataFrame({"x": [3.8], "y": [4.1], "label": [f"EVM = {evm_percent:.1f}%"]})

# Custom tick positions at constellation grid values
tick_vals = [-4, -3, -2, -1, 0, 1, 2, 3, 4]

# Title with scaled font size — calibrated for ggsize(600,600)
title = "16-QAM Constellation · scatter-constellation-diagram · python · letsplot · anyplot.ai"
title_size = max(9, round(13 * 67 / len(title)))

# Plot
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
    # Decision boundary lines
    + geom_vline(  # noqa: F405
        data=boundary_v,
        mapping=aes(xintercept="x"),  # noqa: F405
        linetype="dashed",
        color=INK_SOFT,
        size=0.5,
    )
    + geom_hline(  # noqa: F405
        data=boundary_h,
        mapping=aes(yintercept="y"),  # noqa: F405
        linetype="dashed",
        color=INK_SOFT,
        size=0.5,
    )
    # Axis lines through origin
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.7)  # noqa: F405
    + geom_vline(xintercept=0, color=INK_SOFT, size=0.7)  # noqa: F405
    # 2D density contours — lets-plot stat showing cluster density of received symbols
    + geom_density2d(  # noqa: F405
        data=received_df,
        mapping=aes(x="I", y="Q"),  # noqa: F405
        color=RECEIVED_COLOR,
        alpha=0.4,
        size=0.5,
    )
    # Received symbols
    + geom_point(  # noqa: F405
        data=received_df,
        mapping=aes(x="I", y="Q"),  # noqa: F405
        color=RECEIVED_COLOR,
        size=2.0,
        alpha=0.35,
    )
    # Ideal constellation markers (cross shape, Imprint ochre — colorblind-safe)
    + geom_point(  # noqa: F405
        data=ideal_df,
        mapping=aes(x="I", y="Q"),  # noqa: F405
        color=IDEAL_COLOR,
        size=7,
        shape=4,
        stroke=2.5,
    )
    # EVM annotation with lets-plot geom_label styling
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
    + labs(  # noqa: F405
        x="In-Phase (I)", y="Quadrature (Q)", title=title
    )
    + coord_fixed()  # noqa: F405
    + scale_x_continuous(limits=[-4.5, 4.5], breaks=tick_vals)  # noqa: F405
    + scale_y_continuous(limits=[-4.5, 4.5], breaks=tick_vals)  # noqa: F405
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

# Save
export_ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
export_ggsave(plot, filename=f"plot-{THEME}.html", path=".")
