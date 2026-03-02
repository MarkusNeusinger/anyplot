"""pyplots.ai
heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-02
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    ggsize,
    guide_colorbar,
    labs,
    layer_tooltips,
    scale_fill_viridis,
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
base_counts = 1000 * np.exp(-0.022 * amp_grid) * np.exp(-0.0004 * (mean_grid - 15) ** 2)
noise = np.random.exponential(scale=0.2, size=base_counts.shape)
raw_counts = np.round(base_counts * (1 + noise)).astype(int)

# Secondary cluster: resonance-induced loading event at moderate amplitude / higher mean
# Simulates a distinct operating condition (e.g., resonance at a specific RPM)
resonance_amp = 80.0
resonance_mean = 55.0
secondary = 250 * np.exp(-0.008 * (amp_grid - resonance_amp) ** 2) * np.exp(-0.005 * (mean_grid - resonance_mean) ** 2)
raw_counts = raw_counts + np.round(secondary * (1 + noise * 0.3)).astype(int)

raw_counts[raw_counts < 3] = 0

# Build long-form DataFrame (only non-zero bins)
rows = []
for i, amp in enumerate(amplitude_centers):
    for j, mn in enumerate(mean_centers):
        count = raw_counts[i, j]
        if count > 0:
            rows.append({"amplitude": round(float(amp), 1), "mean_stress": round(float(mn), 1), "cycles": int(count)})

df = pd.DataFrame(rows)

# Annotation label for the peak region
peak_row = df.loc[df["cycles"].idxmax()]
peak_label = pd.DataFrame(
    {
        "mean_stress": [peak_row["mean_stress"]],
        "amplitude": [peak_row["amplitude"] + amp_step * 1.3],
        "label": [f"Peak: {int(peak_row['cycles']):,} cycles"],
    }
)

# Plot - Plasma palette with log10 color scale for clear intensity differentiation
plot = (
    ggplot(df, aes(x="mean_stress", y="amplitude", fill="cycles"))
    + geom_tile(
        width=mean_step * 0.92,
        height=amp_step * 0.92,
        tooltips=layer_tooltips()
        .format("@amplitude", ".0f")
        .format("@mean_stress", ".0f")
        .format("@cycles", ",d")
        .line("Amplitude: @amplitude MPa")
        .line("Mean Stress: @mean_stress MPa")
        .line("Cycles: @cycles"),
    )
    + geom_text(
        aes(x="mean_stress", y="amplitude", label="label"),
        data=peak_label,
        inherit_aes=False,
        size=12,
        color="#1a1a2e",
        fontface="bold",
    )
    + scale_fill_viridis(
        option="plasma",
        name="Cycle Count",
        trans="log10",
        format=",d",
        breaks=[5, 10, 50, 100, 500, 1000],
        labels=["5", "10", "50", "100", "500", "1,000"],
        guide=guide_colorbar(barwidth=18, barheight=320, nbin=256),
    )
    + scale_x_continuous(
        name="Mean Stress (MPa)", breaks=[-40, -20, 0, 20, 40, 60, 80, 100], format="d", expand=[0.02, 0]
    )
    + scale_y_continuous(
        name="Stress Amplitude (MPa)",
        breaks=[20, 40, 60, 80, 100, 120, 140, 160, 180, 200],
        format="d",
        expand=[0.02, 0],
    )
    + coord_cartesian(xlim=[-60, 110], ylim=[0, 210])
    + labs(
        title="heatmap-rainflow · letsplot · pyplots.ai",
        subtitle="Variable-amplitude fatigue load spectrum with resonance-induced secondary cluster",
        caption="Simulated rainflow matrix · cycle counts on log\u2081\u2080 scale",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=26, face="bold", color="#1a1a2e"),
        plot_subtitle=element_text(size=16, color="#5a5a7a", face="italic"),
        plot_caption=element_text(size=12, color="#8a8aaa"),
        axis_title=element_text(size=20, color="#2d2d44", face="bold"),
        axis_text=element_text(size=16, color="#3d3d55"),
        axis_line=element_line(color="#cccccc", size=0.5),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16, face="bold", color="#2d2d44"),
        panel_grid=element_blank(),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="#f8f8fb", color="#f8f8fb"),
        plot_margin=[40, 20, 20, 20],
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
