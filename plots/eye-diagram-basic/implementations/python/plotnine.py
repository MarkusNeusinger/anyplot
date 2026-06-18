"""anyplot.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: plotnine 0.15.7 | Python 3.13.13
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    after_stat,
    annotate,
    element_line,
    element_rect,
    element_text,
    geom_bin2d,
    ggplot,
    labs,
    scale_fill_gradient,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — imprint_seq endpoints for density heatmap
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
TRACE_LOW = IMPRINT_PALETTE[0]  # brand green — low trace density
TRACE_HIGH = IMPRINT_PALETTE[2]  # blue — high trace density (imprint_seq)
ANN_HEIGHT = IMPRINT_PALETTE[1]  # lavender — eye height annotation
ANN_WIDTH = IMPRINT_PALETTE[3]  # ochre — eye width annotation

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

    # Smooth transitions with moving-average kernel
    kernel_len = samples_per_ui // 4
    kernel = np.ones(kernel_len) / kernel_len
    signal = np.convolve(signal, kernel, mode="same")

    signal += np.random.normal(0, noise_sigma, len(signal))

    # Per-bit jitter + sub-sample dither to prevent bin aliasing
    jittered_t = t_full.copy()
    for b in range(n_bits):
        start = b * samples_per_ui
        end = (b + 1) * samples_per_ui
        jittered_t[start:end] += np.random.normal(0, jitter_sigma)
    jittered_t += np.random.uniform(-0.5 / samples_per_ui, 0.5 / samples_per_ui, len(jittered_t))

    # Overlay 2-UI windows
    for b in range(n_bits - ui_window):
        start = b * samples_per_ui
        end = (b + ui_window) * samples_per_ui
        seg_t = jittered_t[start:end] - jittered_t[start]
        seg_v = signal[start:end]
        all_time.extend(seg_t)
        all_voltage.extend(seg_v)

df = pd.DataFrame({"time": np.array(all_time), "voltage": np.array(all_voltage)})

# Eye height: sample vertical opening at t=0.5 UI
eye_center_t = 0.5
center_mask = (df["time"] > eye_center_t - 0.05) & (df["time"] < eye_center_t + 0.05)
center_voltages = df.loc[center_mask, "voltage"]
upper_rail = center_voltages[center_voltages > 0.5]
lower_rail = center_voltages[center_voltages <= 0.5]
eye_top = upper_rail.quantile(0.10)
eye_bot = lower_rail.quantile(0.90)
eye_height_val = eye_top - eye_bot

# Eye width: find sparse transition zone via mid-voltage histogram
mid_mask = (df["voltage"] > 0.3) & (df["voltage"] < 0.7)
mid_times = df.loc[mid_mask, "time"]
counts, bin_edges = np.histogram(mid_times[(mid_times > 0) & (mid_times < 1)], bins=100)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
threshold = counts.max() * 0.1
sparse_bins = bin_centers[counts < threshold]
left_edge = sparse_bins[sparse_bins < 0.5].min() if (sparse_bins < 0.5).any() else 0.15
right_edge = sparse_bins[sparse_bins > 0.5].max() if (sparse_bins > 0.5).any() else 0.85
eye_width_val = right_edge - left_edge

# Title — count chars and scale font size if longer than 67-char baseline
title = "eye-diagram-basic · python · plotnine · anyplot.ai"
n = len(title)
title_fs = max(8, round(12 * (67 / n if n > 67 else 1.0)))

# Plot
plot = (
    ggplot(df, aes(x="time", y="voltage"))
    + geom_bin2d(aes(fill=after_stat("count")), bins=(160, 100), alpha=0.9)
    + scale_fill_gradient(low=TRACE_LOW, high=TRACE_HIGH, name="Trace\nDensity")
    + scale_x_continuous(expand=(0, 0), breaks=[0, 0.5, 1.0, 1.5, 2.0], name="Time (UI)")
    + scale_y_continuous(expand=(0, 0.02), breaks=[0, 0.5, 1.0], name="Voltage (V)")
    + annotate(
        "segment",
        x=eye_center_t,
        xend=eye_center_t,
        y=eye_bot,
        yend=eye_top,
        color=ANN_HEIGHT,
        size=0.7,
        linetype="dashed",
    )
    + annotate(
        "text",
        x=eye_center_t + 0.04,
        y=0.65,
        label=f"Eye Height\n{eye_height_val:.2f} V",
        color=ANN_HEIGHT,
        size=5,
        ha="left",
        va="center",
    )
    + annotate("segment", x=left_edge, xend=right_edge, y=0.5, yend=0.5, color=ANN_WIDTH, size=0.7, linetype="dashed")
    + annotate(
        "text",
        x=(left_edge + right_edge) / 2,
        y=0.35,
        label=f"Eye Width\n{eye_width_val:.2f} UI",
        color=ANN_WIDTH,
        size=5,
        ha="center",
        va="center",
    )
    + labs(title=title)
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        text=element_text(size=7, color=INK_SOFT),
        axis_title=element_text(size=10, color=INK, margin={"r": 12, "t": 12}),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_text_x=element_text(margin={"t": 6}),
        axis_text_y=element_text(margin={"r": 6}),
        axis_line=element_line(color=INK_SOFT, size=0.3),
        axis_ticks=element_line(color=INK_SOFT, size=0.2),
        plot_title=element_text(size=title_fs, color=INK, weight="bold", margin={"b": 12}),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        plot_margin=0.02,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
