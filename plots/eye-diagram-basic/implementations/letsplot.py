"""pyplots.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-17
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_raster,
    ggplot,
    ggsize,
    guide_colorbar,
    labs,
    layer_tooltips,
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Simulated NRZ eye diagram
np.random.seed(42)
n_traces = 400
samples_per_ui = 150
n_bits = 3
n_samples = samples_per_ui * n_bits
time_full = np.linspace(0, n_bits, n_samples, endpoint=False)

# Signal parameters
amplitude = 1.0
noise_sigma = 0.05 * amplitude
jitter_sigma = 0.03

# Sigmoid steepness for bandwidth-limited edges
steepness = 8.0 / 0.15

# Generate overlaid traces
all_time = []
all_voltage = []

for _ in range(n_traces):
    bits = np.random.randint(0, 2, n_bits + 1)
    voltage = np.ones(n_samples) * bits[0] * amplitude

    for bit_idx in range(1, n_bits + 1):
        transition_time = bit_idx + np.random.normal(0, jitter_sigma)
        if bits[bit_idx] != bits[bit_idx - 1]:
            direction = (bits[bit_idx] - bits[bit_idx - 1]) * amplitude
            voltage = voltage + direction / (1.0 + np.exp(-steepness * (time_full - transition_time)))

    voltage += np.random.normal(0, noise_sigma, n_samples)

    # Extract 2 UI window centered on the pattern (from 0.5 to 2.5 UI)
    mask = (time_full >= 0.5) & (time_full < 2.5)
    t_window = time_full[mask] - 0.5
    v_window = voltage[mask]

    all_time.extend(t_window)
    all_voltage.extend(v_window)
all_time = np.array(all_time)
all_voltage = np.array(all_voltage)

# Create 2D density heatmap by binning
n_time_bins = 200
n_voltage_bins = 120
time_edges = np.linspace(0, 2.0, n_time_bins + 1)
voltage_edges = np.linspace(-0.3, 1.3, n_voltage_bins + 1)

density, _, _ = np.histogram2d(all_time, all_voltage, bins=[time_edges, voltage_edges])

# Normalize density
density = density / density.max()

# Build long-form DataFrame
time_centers = (time_edges[:-1] + time_edges[1:]) / 2
voltage_centers = (voltage_edges[:-1] + voltage_edges[1:]) / 2
time_grid, voltage_grid = np.meshgrid(time_centers, voltage_centers, indexing="ij")

df = pd.DataFrame({"time_ui": time_grid.ravel(), "voltage": voltage_grid.ravel(), "density": density.ravel()})

# Filter out zero-density cells for cleaner rendering
df = df[df["density"] > 0].reset_index(drop=True)

# Hot colormap - dark background with warm trace colors
hot_colors = [
    "#0a0a0a",
    "#1a0505",
    "#3d0c0c",
    "#6b1010",
    "#991515",
    "#cc2222",
    "#e04020",
    "#f06020",
    "#f08830",
    "#f0a840",
    "#f0c860",
    "#f5e080",
    "#faf0a0",
    "#fdfcd0",
    "#ffffff",
]

# Plot
plot = (
    ggplot(df, aes(x="time_ui", y="voltage", fill="density"))
    + geom_raster(
        tooltips=layer_tooltips()
        .format("@time_ui", ".2f")
        .format("@voltage", ".2f")
        .format("@density", ".3f")
        .line("Time: @time_ui UI")
        .line("Voltage: @voltage V")
        .line("Density: @density")
    )
    + scale_fill_gradientn(
        colors=hot_colors, name="Trace\nDensity", guide=guide_colorbar(barwidth=14, barheight=260, nbin=256)
    )
    + scale_x_continuous(name="Time (UI)", breaks=[0.0, 0.5, 1.0, 1.5, 2.0], expand=[0, 0])
    + scale_y_continuous(name="Voltage (V)", breaks=[0.0, 0.5, 1.0], labels=["0.0", "0.5", "1.0"], expand=[0, 0])
    + labs(title="eye-diagram-basic · letsplot · pyplots.ai")
    + theme(
        plot_title=element_text(size=28, face="bold", color="#e0e0e0", margin=[0, 0, 10, 0]),
        axis_title_x=element_text(size=20, color="#cccccc", margin=[10, 0, 0, 0]),
        axis_title_y=element_text(size=20, color="#cccccc", margin=[0, 10, 0, 0]),
        axis_text_x=element_text(size=16, color="#aaaaaa"),
        axis_text_y=element_text(size=16, color="#aaaaaa"),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        legend_text=element_text(size=14, color="#cccccc"),
        legend_title=element_text(size=16, face="bold", color="#cccccc"),
        panel_grid=element_blank(),
        panel_background=element_rect(fill="#0a0a0a", color="#0a0a0a"),
        plot_background=element_rect(fill="#1a1a1a", color="#1a1a1a"),
        plot_margin=[40, 30, 20, 20],
        legend_background=element_rect(fill="#1a1a1a", color="#1a1a1a"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
