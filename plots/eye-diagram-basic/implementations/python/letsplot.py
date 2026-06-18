"""anyplot.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-06-18
"""

import os

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

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Oscilloscope screen always dark (domain-appropriate regardless of theme)
SCOPE_BG = "#000004"

# Imprint palette — Imprint-anchored oscilloscope density colormap:
# scope background → brand green → lavender → near-white phosphor glow
DENSITY_COLORS = ["#000004", "#009E73", "#C475FD", "#F0EFE8"]

# Imprint cyan for eye measurement annotations
ANN_COLOR = "#2ABCCD"

# Data — Simulated NRZ eye diagram
np.random.seed(42)
n_traces = 400
samples_per_ui = 150
# Use 7 bits total and extract from interior to eliminate boundary artifacts
n_bits_total = 7
n_samples = samples_per_ui * n_bits_total
time_full = np.linspace(0, n_bits_total, n_samples, endpoint=False)

amplitude = 1.0
noise_sigma = 0.05 * amplitude
jitter_sigma = 0.03
steepness = 8.0 / 0.7

all_time = []
all_voltage = []

for _ in range(n_traces):
    bits = np.random.randint(0, 2, n_bits_total + 1)
    voltage = np.ones(n_samples) * bits[0] * amplitude

    for bit_idx in range(1, n_bits_total + 1):
        transition_time = bit_idx + np.random.normal(0, jitter_sigma)
        if bits[bit_idx] != bits[bit_idx - 1]:
            direction = (bits[bit_idx] - bits[bit_idx - 1]) * amplitude
            voltage += direction / (1.0 + np.exp(-steepness * (time_full - transition_time)))

    voltage += np.random.normal(0, noise_sigma, n_samples)

    # Extract 2 UI window from bits 3–5 — well away from signal boundaries
    mask = (time_full >= 3.0) & (time_full < 5.0)
    t_window = time_full[mask] - 3.0
    v_window = voltage[mask]

    all_time.extend(t_window)
    all_voltage.extend(v_window)

all_time = np.array(all_time)
all_voltage = np.array(all_voltage)

# 2D density heatmap
n_time_bins = 300
n_voltage_bins = 180
time_edges = np.linspace(0, 2.0, n_time_bins + 1)
voltage_edges = np.linspace(-0.3, 1.3, n_voltage_bins + 1)

density, _, _ = np.histogram2d(all_time, all_voltage, bins=[time_edges, voltage_edges])
density = density / density.max()

# Long-form DataFrame
time_centers = (time_edges[:-1] + time_edges[1:]) / 2
voltage_centers = (voltage_edges[:-1] + voltage_edges[1:]) / 2
time_grid, voltage_grid = np.meshgrid(time_centers, voltage_centers, indexing="ij")

df = pd.DataFrame({"time_ui": time_grid.ravel(), "voltage": voltage_grid.ravel(), "density": density.ravel()})
df = df[df["density"] > 0].reset_index(drop=True)

# Eye measurements at center column
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

mid_row = np.argmin(np.abs(voltage_centers - eye_mid_v))
row_density = density[:, mid_row]
low_density_time = time_centers[row_density < threshold]
eye_time_region = low_density_time[(low_density_time > 0.6) & (low_density_time < 1.4)]
eye_left = eye_time_region.min() if len(eye_time_region) > 0 else 0.75
eye_right = eye_time_region.max() if len(eye_time_region) > 0 else 1.25
eye_width = eye_right - eye_left

# Annotation DataFrames
height_x = 1.34
height_seg = pd.DataFrame({"x": [height_x], "y": [eye_bottom], "xend": [height_x], "yend": [eye_top]})
width_seg = pd.DataFrame({"x": [eye_left], "y": [eye_mid_v], "xend": [eye_right], "yend": [eye_mid_v]})
height_label = pd.DataFrame({"x": [height_x + 0.04], "y": [eye_mid_v], "label": [f"Eye Height: {eye_height:.2f} V"]})
width_label = pd.DataFrame(
    {"x": [(eye_left + eye_right) / 2], "y": [eye_mid_v - 0.09], "label": [f"Eye Width: {eye_width:.2f} UI"]}
)

# Title with font scaling
title = "eye-diagram-basic · python · letsplot · anyplot.ai"
title_size = round(16 * min(1.0, 67 / len(title)))

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
        aes(x="x", y="y", xend="xend", yend="yend"), data=height_seg, color=ANN_COLOR, size=1.2, inherit_aes=False
    )
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"), data=width_seg, color=ANN_COLOR, size=1.2, inherit_aes=False
    )
    + geom_text(
        aes(x="x", y="y", label="label"), data=height_label, color=ANN_COLOR, size=4, hjust=0, inherit_aes=False
    )
    + geom_text(
        aes(x="x", y="y", label="label"), data=width_label, color=ANN_COLOR, size=4, hjust=0.5, inherit_aes=False
    )
    + scale_fill_gradientn(
        colors=DENSITY_COLORS, name="Trace\nDensity", guide=guide_colorbar(barwidth=10, barheight=200, nbin=256)
    )
    + scale_x_continuous(name="Time (UI)", breaks=[0.0, 0.5, 1.0, 1.5, 2.0], expand=[0, 0])
    + scale_y_continuous(name="Voltage (V)", breaks=[0.0, 0.5, 1.0], labels=["0.0", "0.5", "1.0"], expand=[0, 0])
    + labs(title=title)
    + theme(
        plot_title=element_text(size=title_size, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK_SOFT),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, face="bold", color=INK),
        panel_grid=element_blank(),
        panel_background=element_rect(fill=SCOPE_BG, color=SCOPE_BG),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_margin=[40, 30, 20, 20],
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
