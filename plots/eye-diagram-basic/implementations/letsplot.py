"""pyplots.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-17
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
    geom_segment,
    geom_text,
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

# Create 2D density heatmap by binning (high resolution for smooth rendering)
n_time_bins = 300
n_voltage_bins = 180
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

# Inferno-inspired perceptually uniform colormap for density
inferno_colors = [
    "#0d0887",
    "#2d0594",
    "#46039f",
    "#6a00a8",
    "#8f0da4",
    "#b12a90",
    "#cc4778",
    "#e16462",
    "#f1844b",
    "#fca636",
    "#fcce25",
    "#f0f921",
]

# Measure eye opening at center (1.0 UI) for annotations
center_col = n_time_bins // 2
center_density = density[center_col, :]
threshold = 0.05
low_density_mask = center_density < threshold
voltage_center_vals = voltage_centers[low_density_mask]
eye_region = voltage_center_vals[(voltage_center_vals > 0.15) & (voltage_center_vals < 0.85)]
eye_bottom = eye_region.min() if len(eye_region) > 0 else 0.25
eye_top = eye_region.max() if len(eye_region) > 0 else 0.75
eye_height = eye_top - eye_bottom
eye_mid_v = (eye_top + eye_bottom) / 2

# Measure eye width at mid-voltage level
mid_row = np.argmin(np.abs(voltage_centers - eye_mid_v))
row_density = density[:, mid_row]
low_density_time = time_centers[row_density < threshold]
eye_time_region = low_density_time[(low_density_time > 0.6) & (low_density_time < 1.4)]
eye_left = eye_time_region.min() if len(eye_time_region) > 0 else 0.75
eye_right = eye_time_region.max() if len(eye_time_region) > 0 else 1.25
eye_width = eye_right - eye_left

# Annotation DataFrames
ann_color = "#00e5ff"
height_x = 1.38
height_seg = pd.DataFrame({"x": [height_x], "y": [eye_bottom], "xend": [height_x], "yend": [eye_top]})
width_seg = pd.DataFrame({"x": [eye_left], "y": [eye_mid_v], "xend": [eye_right], "yend": [eye_mid_v]})
height_label = pd.DataFrame({"x": [height_x + 0.04], "y": [eye_mid_v], "label": [f"Eye Height: {eye_height:.2f} V"]})
width_label = pd.DataFrame(
    {"x": [(eye_left + eye_right) / 2], "y": [eye_mid_v - 0.09], "label": [f"Eye Width: {eye_width:.2f} UI"]}
)

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
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"), data=height_seg, color=ann_color, size=1.2, inherit_aes=False
    )
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"), data=width_seg, color=ann_color, size=1.2, inherit_aes=False
    )
    + geom_text(
        aes(x="x", y="y", label="label"), data=height_label, color=ann_color, size=11, hjust=0, inherit_aes=False
    )
    + geom_text(
        aes(x="x", y="y", label="label"), data=width_label, color=ann_color, size=11, hjust=0.5, inherit_aes=False
    )
    + scale_fill_gradientn(
        colors=inferno_colors, name="Trace\nDensity", guide=guide_colorbar(barwidth=14, barheight=260, nbin=256)
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
        panel_background=element_rect(fill="#000004", color="#000004"),
        plot_background=element_rect(fill="#0d0d2b", color="#0d0d2b"),
        plot_margin=[40, 30, 20, 20],
        legend_background=element_rect(fill="#0d0d2b", color="#0d0d2b"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
