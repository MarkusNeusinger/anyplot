""" pyplots.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-17
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    after_stat,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_bin2d,
    ggplot,
    labs,
    scale_fill_cmap,
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

    # Add jitter: per-bit timing offset + per-sample dither to prevent bin aliasing
    jittered_t = t_full.copy()
    for b in range(n_bits):
        start = b * samples_per_ui
        end = (b + 1) * samples_per_ui
        jittered_t[start:end] += np.random.normal(0, jitter_sigma)
    jittered_t += np.random.uniform(-0.5 / samples_per_ui, 0.5 / samples_per_ui, len(jittered_t))

    # Slice into 2-UI windows and overlay
    for b in range(n_bits - ui_window):
        start = b * samples_per_ui
        end = (b + ui_window) * samples_per_ui
        seg_t = jittered_t[start:end] - jittered_t[start]
        seg_v = signal[start:end]
        all_time.extend(seg_t)
        all_voltage.extend(seg_v)

df = pd.DataFrame({"time": np.array(all_time), "voltage": np.array(all_voltage)})

# Plot — use geom_bin2d for native plotnine 2D binning and after_stat for density
plot = (
    ggplot(df, aes(x="time", y="voltage"))
    + geom_bin2d(aes(fill=after_stat("count")), bins=(250, 150))
    + scale_fill_cmap(cmap_name="inferno", name="Trace\nDensity")
    + scale_x_continuous(expand=(0, 0), breaks=[0, 0.5, 1.0, 1.5, 2.0], name="Time (UI)")
    + scale_y_continuous(expand=(0, 0), breaks=[0, 0.5, 1.0], name="Voltage (V)")
    + labs(title="eye-diagram-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill="#0d0221"),
        panel_background=element_rect(fill="#0d0221"),
        text=element_text(size=14, color="#cccccc"),
        axis_title=element_text(size=20, color="#eeeeee"),
        axis_text=element_text(size=16, color="#bbbbbb"),
        plot_title=element_text(size=24, color="#eeeeee", weight="bold"),
        legend_text=element_text(size=14, color="#cccccc"),
        legend_title=element_text(size=16, color="#eeeeee"),
        panel_grid_major=element_line(color="#1a1035", size=0.3),
        panel_grid_minor=element_blank(),
        legend_background=element_rect(fill="#0d0221"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
