""" pyplots.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 93/100 | Updated: 2026-03-18
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    after_stat,
    annotate,
    element_rect,
    element_text,
    geom_bin2d,
    ggplot,
    labs,
    scale_fill_cmap,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
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

# Compute eye metrics at center of first eye opening (t=0.5 UI)
eye_center_t = 0.5
center_mask = (df["time"] > eye_center_t - 0.05) & (df["time"] < eye_center_t + 0.05)
center_voltages = df.loc[center_mask, "voltage"]
upper_rail = center_voltages[center_voltages > 0.5]
lower_rail = center_voltages[center_voltages <= 0.5]
eye_top = upper_rail.quantile(0.10)
eye_bot = lower_rail.quantile(0.90)
eye_height = eye_top - eye_bot

# Eye width: find inner boundary of transition zone using histogram of mid-voltage
mid_mask = (df["voltage"] > 0.3) & (df["voltage"] < 0.7)
mid_times = df.loc[mid_mask, "time"]
counts, bin_edges = np.histogram(mid_times[(mid_times > 0) & (mid_times < 1)], bins=100)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
threshold = counts.max() * 0.1
sparse_mask = counts < threshold
sparse_bins = bin_centers[sparse_mask]
left_edge = sparse_bins[sparse_bins < 0.5].min() if (sparse_bins < 0.5).any() else 0.15
right_edge = sparse_bins[sparse_bins > 0.5].max() if (sparse_bins > 0.5).any() else 0.85
eye_width = right_edge - left_edge

# Plot — geom_bin2d with after_stat for density, annotate for eye metrics
plot = (
    ggplot(df, aes(x="time", y="voltage"))
    + geom_bin2d(aes(fill=after_stat("count")), bins=(250, 150))
    + scale_fill_cmap(cmap_name="inferno", name="Trace\nDensity")
    + scale_x_continuous(expand=(0, 0), breaks=[0, 0.5, 1.0, 1.5, 2.0], name="Time (UI)")
    + scale_y_continuous(expand=(0, 0.02), breaks=[0, 0.5, 1.0], name="Voltage (V)")
    + annotate(
        "segment",
        x=eye_center_t,
        xend=eye_center_t,
        y=eye_bot,
        yend=eye_top,
        color="#00ff88",
        size=1.0,
        linetype="dashed",
    )
    + annotate(
        "text",
        x=eye_center_t + 0.04,
        y=0.65,
        label=f"Eye Height\n{eye_height:.2f} V",
        color="#00ff88",
        size=11,
        ha="left",
        va="center",
    )
    + annotate("segment", x=left_edge, xend=right_edge, y=0.5, yend=0.5, color="#00ccff", size=1.0, linetype="dashed")
    + annotate(
        "text",
        x=(left_edge + right_edge) / 2,
        y=0.35,
        label=f"Eye Width\n{eye_width:.2f} UI",
        color="#00ccff",
        size=11,
        ha="center",
        va="center",
    )
    + labs(title="eye-diagram-basic · plotnine · pyplots.ai")
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill="#0d0221"),
        panel_background=element_rect(fill="#0d0221"),
        text=element_text(size=14, color="#cccccc"),
        axis_title=element_text(size=20, color="#eeeeee", margin={"r": 12, "t": 12}),
        axis_text=element_text(size=16, color="#bbbbbb"),
        axis_text_x=element_text(margin={"t": 6}),
        axis_text_y=element_text(margin={"r": 6}),
        plot_title=element_text(size=24, color="#eeeeee", weight="bold", margin={"b": 12}),
        legend_text=element_text(size=14, color="#cccccc"),
        legend_title=element_text(size=16, color="#eeeeee"),
        legend_background=element_rect(fill="#0d0221"),
        plot_margin=0.02,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
