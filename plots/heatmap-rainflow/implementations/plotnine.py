""" pyplots.ai
heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-02
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    labs,
    scale_fill_cmap,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Simulate rainflow counting results from variable-amplitude loading
np.random.seed(42)

n_amp_bins = 20
n_mean_bins = 20
amplitude_edges = np.linspace(0, 200, n_amp_bins + 1)
mean_edges = np.linspace(-100, 100, n_mean_bins + 1)
amplitude_centers = (amplitude_edges[:-1] + amplitude_edges[1:]) / 2
mean_centers = (mean_edges[:-1] + mean_edges[1:]) / 2

# Build rainflow matrix: most cycles at low amplitude near zero mean
amp_grid, mean_grid = np.meshgrid(amplitude_centers, mean_centers, indexing="ij")
cycle_rate = np.exp(-0.03 * amp_grid) * np.exp(-0.0005 * mean_grid**2)
cycle_counts = np.random.poisson(lam=cycle_rate * 500)

# Add a secondary cluster at moderate amplitude / positive mean (realistic loading)
cluster = 80 * np.exp(-0.01 * (amp_grid - 60) ** 2 - 0.002 * (mean_grid - 30) ** 2)
cycle_counts += np.random.poisson(lam=cluster)

# Build long-form DataFrame
rows = []
for i in range(n_amp_bins):
    for j in range(n_mean_bins):
        rows.append(
            {
                "Amplitude (MPa)": amplitude_centers[i],
                "Mean Stress (MPa)": mean_centers[j],
                "Cycle Count": cycle_counts[i, j],
            }
        )
df = pd.DataFrame(rows)

# Tile dimensions for seamless coverage
tile_w = mean_centers[1] - mean_centers[0]
tile_h = amplitude_centers[1] - amplitude_centers[0]

# Separate zero and nonzero for visual distinction
df_nonzero = df[df["Cycle Count"] > 0].copy()
df_nonzero["Log Count"] = np.log10(df_nonzero["Cycle Count"])

# Plot
plot = (
    ggplot()
    # Layer 1: White tiles for zero-count bins (distinct from viridis palette)
    + geom_tile(
        data=df,
        mapping=aes(x="Mean Stress (MPa)", y="Amplitude (MPa)"),
        fill="white",
        color="#e0e0e0",
        size=0.15,
        width=tile_w,
        height=tile_h,
    )
    # Layer 2: Viridis-colored tiles for nonzero bins
    + geom_tile(
        data=df_nonzero,
        mapping=aes(x="Mean Stress (MPa)", y="Amplitude (MPa)", fill="Log Count"),
        width=tile_w,
        height=tile_h,
    )
    # Native viridis colormap — perceptually uniform, colorblind-safe
    + scale_fill_cmap(cmap_name="viridis", name="Cycle Count\n(log₁₀)")
    # Annotations: guide viewer to fatigue-critical regions
    + annotate(
        "label",
        x=-80,
        y=35,
        label="Peak\nconcentration",
        size=14,
        color="#222222",
        ha="center",
        fill="white",
        alpha=0.85,
        label_size=0,
    )
    + annotate("segment", x=-68, xend=-15, y=22, yend=10, color="white", size=1.0, alpha=0.9)
    + annotate(
        "label",
        x=85,
        y=120,
        label="Secondary\nloading cluster",
        size=14,
        color="#222222",
        ha="center",
        fill="white",
        alpha=0.85,
        label_size=0,
    )
    + annotate("segment", x=75, xend=42, y=105, yend=70, color="white", size=1.0, alpha=0.9)
    + scale_x_continuous(expand=(0, 2))
    + scale_y_continuous(expand=(0, 2))
    + labs(x="Mean Stress (MPa)", y="Stress Amplitude (MPa)", title="heatmap-rainflow · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(family="sans-serif"),
        plot_title=element_text(size=24, ha="center", weight="bold", margin={"b": 12}),
        axis_title_x=element_text(size=20, margin={"t": 10}),
        axis_title_y=element_text(size=20, margin={"r": 10}),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        legend_key_height=50,
        legend_key_width=18,
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="white", color="none"),
        plot_background=element_rect(fill="#fafafa", color="none"),
        plot_margin=0.02,
    )
)

plot.save("plot.png", dpi=300, verbose=False)
