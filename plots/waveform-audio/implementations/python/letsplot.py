"""anyplot.ai
waveform-audio: Audio Waveform Plot
Library: letsplot | Python
Quality: pending | Created: 2026-06-03
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F401
from lets_plot.export import ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID_COLOR = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Data — synthetic audio waveform: 220 Hz tone with harmonics and ASR amplitude envelope
np.random.seed(42)
sample_rate = 22050
duration = 1.5
n_samples = int(sample_rate * duration)
time = np.linspace(0, duration, n_samples)

fundamental = 220
signal = (
    0.6 * np.sin(2 * np.pi * fundamental * time)
    + 0.25 * np.sin(2 * np.pi * fundamental * 2 * time)
    + 0.1 * np.sin(2 * np.pi * fundamental * 3 * time)
    + 0.05 * np.sin(2 * np.pi * fundamental * 5 * time)
)

# Attack-sustain-release amplitude envelope
envelope = np.ones(n_samples)
attack_samples = int(0.05 * sample_rate)
release_samples = int(0.3 * sample_rate)
envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
envelope[-release_samples:] = np.linspace(1, 0, release_samples)
envelope[int(0.4 * sample_rate) : int(0.7 * sample_rate)] *= 0.5

signal = signal * envelope
signal = signal / np.max(np.abs(signal))

# Downsample via min/max envelope binning to avoid aliasing at display resolution
n_bins = 800
bin_edges = np.linspace(0, n_samples, n_bins + 1, dtype=int)
time_env = np.array([time[(bin_edges[i] + bin_edges[i + 1]) // 2] for i in range(n_bins)])
amp_max = np.array([signal[bin_edges[i] : bin_edges[i + 1]].max() for i in range(n_bins)])
amp_min = np.array([signal[bin_edges[i] : bin_edges[i + 1]].min() for i in range(n_bins)])
amp_range = amp_max - amp_min

df = pd.DataFrame({"time": time_env, "ymin": amp_min, "ymax": amp_max, "intensity": amp_range})

ann_data = pd.DataFrame(
    {
        "time": [0.025, 0.225, 0.55, 0.95, 1.35],
        "y": [1.07, 1.07, 1.07, 1.07, 1.07],
        "label": ["Attack", "Sustain", "Dip", "Sustain", "Release"],
    }
)

section_df = pd.DataFrame({"x": [0.05, 0.4, 0.7, 1.2]})

subtitle = "220 Hz fundamental + harmonics · ASR envelope with amplitude dip at 0.4–0.7 s"

# Theme-adaptive chrome applied after theme_minimal()
anyplot_chrome = theme(  # noqa: F405
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
    panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
    panel_grid_major_y=element_line(color=GRID_COLOR, size=0.3),  # noqa: F405
    panel_grid_major_x=element_blank(),  # noqa: F405
    panel_grid_minor=element_blank(),  # noqa: F405
    axis_title=element_text(color=INK, size=12),  # noqa: F405
    axis_text=element_text(color=INK_SOFT, size=10),  # noqa: F405
    axis_line=element_line(color=INK_SOFT),  # noqa: F405
    plot_title=element_text(color=INK, size=16),  # noqa: F405
    plot_subtitle=element_text(color=INK_SOFT, size=10),  # noqa: F405
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
    legend_text=element_text(color=INK_SOFT, size=10),  # noqa: F405
    legend_title=element_text(color=INK, size=12),  # noqa: F405
    legend_position="right",
    plot_margin=[40, 20, 20, 20],
)

plot = (
    ggplot(df)  # noqa: F405
    # DAW-style vertical bars coloured by local amplitude range (Imprint sequential cmap)
    + geom_segment(  # noqa: F405
        mapping=aes(x="time", y="ymin", xend="time", yend="ymax", color="intensity"),  # noqa: F405
        size=1.5,
        alpha=0.85,
        tooltips=layer_tooltips()  # noqa: F405
        .format("ymax", ".2f")
        .format("ymin", ".2f")
        .format("time", ".3f")
        .line("Time: @time s")
        .line("Max: @ymax")
        .line("Min: @ymin"),
    )
    # Imprint sequential: brand green (#009E73) → blue (#4467A3) for single-polarity data
    + scale_color_gradient(low="#009E73", high="#4467A3", name="Amplitude\nRange")  # noqa: F405
    # Zero reference line
    + geom_hline(yintercept=0, color=INK_MUTED, size=0.5, linetype="dashed")  # noqa: F405
    # Envelope section boundary markers
    + geom_vline(  # noqa: F405
        data=section_df,
        mapping=aes(xintercept="x"),  # noqa: F405
        color=INK_MUTED,
        size=0.4,
        linetype="dotted",
    )
    # Section labels — geom_text size is in mm (~2.845 mm = 1 pt)
    + geom_text(  # noqa: F405
        data=ann_data,
        mapping=aes(x="time", y="y", label="label"),  # noqa: F405
        size=4,
        color=INK,
        fontface="italic",
    )
    + scale_x_continuous(name="Time (seconds)", limits=[0, duration])  # noqa: F405
    + scale_y_continuous(  # noqa: F405
        name="Amplitude", limits=[-1.15, 1.18], breaks=[-1.0, -0.5, 0.0, 0.5, 1.0]
    )
    + labs(title="waveform-audio · python · letsplot · anyplot.ai", subtitle=subtitle)  # noqa: F405
    # Canvas: 800×450 × scale=4 → 3200×1800 px (landscape 16:9)
    + ggsize(800, 450)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + anyplot_chrome
)

# Save PNG (3200×1800 px) and interactive HTML — path="." keeps files in the current dir
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
