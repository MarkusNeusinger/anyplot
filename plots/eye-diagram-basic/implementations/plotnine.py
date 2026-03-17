"""pyplots.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-17
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    labs,
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data
np.random.seed(42)

n_traces = 400
samples_per_ui = 150
n_bits = 12
ui_window = 2
noise_sigma = 0.05
jitter_sigma = 0.03

t_per_bit = np.linspace(0, 1, samples_per_ui, endpoint=False)
t_full = np.concatenate([t_per_bit + i for i in range(n_bits)])

all_time = []
all_voltage = []

for _ in range(n_traces):
    bits = np.random.randint(0, 2, n_bits)
    signal = np.repeat(bits.astype(float), samples_per_ui)

    # Smooth transitions with sigmoid filter
    kernel_len = samples_per_ui // 4
    kernel = np.ones(kernel_len) / kernel_len
    signal = np.convolve(signal, kernel, mode="same")

    # Add noise
    signal += np.random.normal(0, noise_sigma, len(signal))

    # Add jitter by slightly shifting time base per bit
    jittered_t = t_full.copy()
    for b in range(n_bits):
        start = b * samples_per_ui
        end = (b + 1) * samples_per_ui
        jittered_t[start:end] += np.random.normal(0, jitter_sigma)

    # Slice into 2-UI windows and overlay
    for b in range(n_bits - ui_window):
        start = b * samples_per_ui
        end = (b + ui_window) * samples_per_ui
        seg_t = jittered_t[start:end] - jittered_t[start]
        seg_v = signal[start:end]
        all_time.extend(seg_t)
        all_voltage.extend(seg_v)

all_time = np.array(all_time)
all_voltage = np.array(all_voltage)

# Bin into 2D histogram for density heatmap
n_xbins = 200
n_ybins = 120
x_edges = np.linspace(0, ui_window, n_xbins + 1)
y_edges = np.linspace(-0.3, 1.3, n_ybins + 1)
hist, _, _ = np.histogram2d(all_time, all_voltage, bins=[x_edges, y_edges])

x_centers = (x_edges[:-1] + x_edges[1:]) / 2
y_centers = (y_edges[:-1] + y_edges[1:]) / 2
xx, yy = np.meshgrid(x_centers, y_centers, indexing="ij")

df = pd.DataFrame({"Time (UI)": xx.ravel(), "Voltage (V)": yy.ravel(), "Density": hist.ravel()})
df = df[df["Density"] > 0]

# Plot
hot_colors = ["#0d0221", "#1b065e", "#3b185e", "#6b2d5b", "#c2185b", "#e65100", "#f9a825", "#fff176", "#fffde7"]

plot = (
    ggplot(df, aes(x="Time (UI)", y="Voltage (V)", fill="Density"))
    + geom_tile(aes(width=ui_window / n_xbins, height=1.6 / n_ybins))
    + scale_fill_gradientn(colors=hot_colors, name="Trace\nDensity")
    + scale_x_continuous(expand=(0, 0), breaks=[0, 0.5, 1.0, 1.5, 2.0])
    + scale_y_continuous(expand=(0, 0), breaks=[0, 0.5, 1.0])
    + labs(x="Time (UI)", y="Voltage (V)", title="eye-diagram-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill="#0d0221"),
        panel_background=element_rect(fill="#0d0221"),
        text=element_text(size=14, color="#cccccc"),
        axis_title=element_text(size=20, color="#eeeeee"),
        axis_text=element_text(size=16, color="#aaaaaa"),
        plot_title=element_text(size=24, color="#eeeeee", weight="bold"),
        legend_text=element_text(size=14, color="#cccccc"),
        legend_title=element_text(size=16, color="#eeeeee"),
        panel_grid_major=element_line(color="#2a1a3e", size=0.5),
        panel_grid_minor=element_blank(),
        legend_background=element_rect(fill="#0d0221"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
