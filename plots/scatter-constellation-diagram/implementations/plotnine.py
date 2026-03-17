""" pyplots.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-17
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_fixed,
    element_blank,
    element_line,
    element_text,
    geom_hline,
    geom_point,
    geom_rect,
    geom_segment,
    geom_vline,
    ggplot,
    labs,
    scale_alpha_identity,
    scale_color_identity,
    scale_size_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data
np.random.seed(42)

ideal_coords = [-3, -1, 1, 3]
ideal_i = np.array([i for i in ideal_coords for _ in ideal_coords])
ideal_q = np.array([q for _ in ideal_coords for q in ideal_coords])

n_symbols = 1000
snr_db = 20
snr_linear = 10 ** (snr_db / 10)
avg_power = np.mean(ideal_i**2 + ideal_q**2)
noise_std = np.sqrt(avg_power / (2 * snr_linear))

symbol_indices = np.random.randint(0, 16, size=n_symbols)
received_i = ideal_i[symbol_indices] + np.random.normal(0, noise_std, n_symbols)
received_q = ideal_q[symbol_indices] + np.random.normal(0, noise_std, n_symbols)

error_i = received_i - ideal_i[symbol_indices]
error_q = received_q - ideal_q[symbol_indices]
evm = np.sqrt(np.mean(error_i**2 + error_q**2)) / np.sqrt(avg_power) * 100

df_received = pd.DataFrame({"i": received_i, "q": received_q, "color": "#306998", "alpha": 0.35, "size": 3.0})

df_ideal = pd.DataFrame({"i": ideal_i, "q": ideal_q, "color": "#D04848", "alpha": 1.0, "size": 7})

df_all = pd.concat([df_received, df_ideal], ignore_index=True)

# Decision region background rectangles (checkerboard shading)
region_edges = [-4.5, -2, 0, 2, 4.5]
rects = []
for ri, xmin in enumerate(region_edges[:-1]):
    for ci, ymin in enumerate(region_edges[:-1]):
        rects.append(
            {
                "xmin": xmin,
                "xmax": region_edges[ri + 1],
                "ymin": ymin,
                "ymax": region_edges[ci + 1],
                "shade": "#F0F4F8" if (ri + ci) % 2 == 0 else "#FFFFFF",
            }
        )
df_rects = pd.DataFrame(rects)

# Decision boundaries
boundary_vals = [-2, 0, 2]

# Error vector samples — show a few error vectors for storytelling
rng = np.random.default_rng(42)
ev_idx = rng.choice(n_symbols, size=12, replace=False)
df_ev = pd.DataFrame(
    {
        "i_start": ideal_i[symbol_indices[ev_idx]],
        "q_start": ideal_q[symbol_indices[ev_idx]],
        "i_end": received_i[ev_idx],
        "q_end": received_q[ev_idx],
    }
)

# Plot
plot = (
    ggplot(df_all, aes(x="i", y="q"))
    # Decision region shading
    + geom_rect(
        data=df_rects,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill=df_rects["shade"].tolist(),
        alpha=0.6,
        inherit_aes=False,
    )
    # Decision boundary lines
    + geom_vline(xintercept=boundary_vals, linetype="dashed", color="#AAAAAA", size=0.5)
    + geom_hline(yintercept=boundary_vals, linetype="dashed", color="#AAAAAA", size=0.5)
    # Received symbols
    + geom_point(data=df_received, mapping=aes(x="i", y="q", color="color", alpha="alpha", size="size"))
    # Error vectors (distinctive plotnine feature: geom_segment)
    + geom_segment(
        data=df_ev,
        mapping=aes(x="i_start", y="q_start", xend="i_end", yend="q_end"),
        color="#D04848",
        alpha=0.5,
        size=0.6,
        inherit_aes=False,
    )
    # Ideal constellation points
    + geom_point(
        data=df_ideal, mapping=aes(x="i", y="q", color="color", alpha="alpha", size="size"), shape="X", stroke=1.5
    )
    + scale_color_identity()
    + scale_alpha_identity()
    + scale_size_identity()
    # Custom tick positions at constellation points (distinctive plotnine feature)
    + scale_x_continuous(breaks=[-3, -1, 0, 1, 3], minor_breaks=[])
    + scale_y_continuous(breaks=[-3, -1, 0, 1, 3], minor_breaks=[])
    # Annotations
    + annotate(
        "text", x=4.2, y=-3.7, label=f"EVM = {evm:.1f}%", size=16, ha="right", color="#222222", fontweight="bold"
    )
    + annotate(
        "text", x=4.2, y=-4.15, label=f"SNR = {snr_db} dB  ·  {n_symbols} symbols", size=11, ha="right", color="#777777"
    )
    + coord_fixed(ratio=1, xlim=(-4.5, 4.5), ylim=(-4.5, 4.5))
    + labs(x="In-Phase (I)", y="Quadrature (Q)", title="scatter-constellation-diagram · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, weight="bold", ha="center"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color="#333333", size=0.6),
        legend_position="none",
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
