""" pyplots.ai
heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-02
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    ggsize,
    guide_colorbar,
    labs,
    layer_tooltips,
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Simulate rainflow counting from a variable-amplitude fatigue load signal
np.random.seed(42)

n_bins = 20
amplitude_centers = np.linspace(10, 200, n_bins)
mean_centers = np.linspace(-50, 100, n_bins)
amp_step = float(amplitude_centers[1] - amplitude_centers[0])
mean_step = float(mean_centers[1] - mean_centers[0])

# Realistic rainflow matrix: exponential decay in amplitude, Gaussian in mean
amp_grid, mean_grid = np.meshgrid(amplitude_centers, mean_centers, indexing="ij")
base_counts = 1200 * np.exp(-0.04 * amp_grid) * np.exp(-0.0008 * (mean_grid - 20) ** 2)
noise = np.random.exponential(scale=0.15, size=base_counts.shape)
raw_counts = np.round(base_counts * (1 + noise)).astype(int)
raw_counts[raw_counts < 8] = 0

# Build long-form DataFrame (only non-zero bins)
rows = []
for i, amp in enumerate(amplitude_centers):
    for j, mn in enumerate(mean_centers):
        count = raw_counts[i, j]
        if count > 0:
            rows.append({"amplitude": round(float(amp), 1), "mean_stress": round(float(mn), 1), "cycles": int(count)})

df = pd.DataFrame(rows)

# Plot - Sequential warm colormap for clear intensity gradient
plot = (
    ggplot(df, aes(x="mean_stress", y="amplitude", fill="cycles"))
    + geom_tile(
        width=mean_step * 0.92,
        height=amp_step * 0.92,
        tooltips=layer_tooltips()
        .line("Amplitude: @amplitude MPa")
        .line("Mean: @mean_stress MPa")
        .line("Cycles: @cycles"),
    )
    + scale_fill_gradientn(
        colors=["#d4e6f1", "#306998", "#1a3a5c", "#0a1628"],
        name="Cycle\nCount",
        guide=guide_colorbar(barwidth=18, barheight=300, nbin=256),
    )
    + scale_x_continuous(name="Mean Stress (MPa)", limits=[-60, 110])
    + scale_y_continuous(name="Stress Amplitude (MPa)", limits=[0, 210])
    + labs(title="heatmap-rainflow · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=26, face="bold", color="#1a1a2e"),
        axis_title=element_text(size=20, color="#2d2d44"),
        axis_text=element_text(size=16, color="#2d2d44"),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16, face="bold"),
        panel_grid=element_blank(),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="white", color="white"),
        plot_margin=[40, 20, 20, 20],
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
