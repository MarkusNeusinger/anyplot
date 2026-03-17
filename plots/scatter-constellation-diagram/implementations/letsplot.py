"""pyplots.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-17
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

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

# Decision boundary rectangles for shaded regions
rects = []
boundary_edges = [-4.5, -2, 0, 2, 4.5]
colors_alt = ["#F0F4F8", "#E8EDF2"]
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

# Plot
plot = (
    ggplot()  # noqa: F405
    # Shaded decision regions (lets-plot geom_rect with identity scale)
    + geom_rect(  # noqa: F405
        data=rects_df,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="fill"),  # noqa: F405
        alpha=1.0,
        color="white",
        size=0.3,
    )
    + scale_fill_identity()  # noqa: F405
    # Decision boundary grid lines
    + geom_vline(  # noqa: F405
        data=boundary_v,
        mapping=aes(xintercept="x"),  # noqa: F405
        linetype="dashed",
        color="#B0B8C4",
        size=0.5,
    )
    + geom_hline(  # noqa: F405
        data=boundary_h,
        mapping=aes(yintercept="y"),  # noqa: F405
        linetype="dashed",
        color="#B0B8C4",
        size=0.5,
    )
    # Axis lines through origin
    + geom_hline(yintercept=0, color="#8899AA", size=0.7)  # noqa: F405
    + geom_vline(xintercept=0, color="#8899AA", size=0.7)  # noqa: F405
    # Received symbols
    + geom_point(  # noqa: F405
        data=received_df,
        mapping=aes(x="I", y="Q"),  # noqa: F405
        color="#306998",
        size=3,
        alpha=0.4,
    )
    # Ideal constellation points
    + geom_point(  # noqa: F405
        data=ideal_df,
        mapping=aes(x="I", y="Q"),  # noqa: F405
        color="#CC3333",
        size=9,
        shape=4,
        stroke=3.5,
    )
    # EVM annotation with geom_label (lets-plot distinctive feature)
    + geom_label(  # noqa: F405
        data=evm_df,
        mapping=aes(x="x", y="y", label="label"),  # noqa: F405
        size=15,
        color="#1A2A3A",
        fill="#FFFFFF",
        alpha=0.85,
        hjust=1,
        label_padding=0.6,
        label_r=0.3,
        label_size=0.8,
    )
    + labs(  # noqa: F405
        x="In-Phase (I)",
        y="Quadrature (Q)",
        title="16-QAM Constellation · scatter-constellation-diagram · letsplot · pyplots.ai",
    )
    + coord_fixed()  # noqa: F405
    + scale_x_continuous(limits=[-4.5, 4.5], breaks=tick_vals)  # noqa: F405
    + scale_y_continuous(limits=[-4.5, 4.5], breaks=tick_vals)  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24, color="#1A2A3A", face="bold"),  # noqa: F405
        axis_title=element_text(size=20, color="#3A4A5A"),  # noqa: F405
        axis_text=element_text(size=16, color="#5A6A7A"),  # noqa: F405
        panel_background=element_rect(fill="#F7F9FB", color="#D0D8E0", size=1),  # noqa: F405
        plot_background=element_rect(fill="#FFFFFF"),  # noqa: F405
        panel_grid_major=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_ticks=element_line(color="#B0B8C4", size=0.5),  # noqa: F405
        axis_line=element_line(color="#B0B8C4", size=0.5),  # noqa: F405
        plot_margin=[40, 20, 20, 20],
    )
    + ggsize(1200, 1200)  # noqa: F405
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
