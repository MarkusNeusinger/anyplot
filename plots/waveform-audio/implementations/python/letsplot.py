""" pyplots.ai
waveform-audio: Audio Waveform Plot
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-07
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F401
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data — synthetic audio waveform: tone with harmonics and amplitude envelope
np.random.seed(42)
sample_rate = 22050
duration = 1.5
n_samples = int(sample_rate * duration)
time = np.linspace(0, duration, n_samples)

# Primary tone (220 Hz) with harmonics
fundamental = 220
signal = (
    0.6 * np.sin(2 * np.pi * fundamental * time)
    + 0.25 * np.sin(2 * np.pi * fundamental * 2 * time)
    + 0.1 * np.sin(2 * np.pi * fundamental * 3 * time)
    + 0.05 * np.sin(2 * np.pi * fundamental * 5 * time)
)

# Amplitude envelope: attack-sustain-release shape
envelope = np.ones(n_samples)
attack_samples = int(0.05 * sample_rate)
release_samples = int(0.3 * sample_rate)
envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
envelope[-release_samples:] = np.linspace(1, 0, release_samples)
envelope[int(0.4 * sample_rate) : int(0.7 * sample_rate)] *= 0.5

signal = signal * envelope
signal = signal / np.max(np.abs(signal))

# Downsample using min/max envelope — vectorized binning
n_bins = 800
bin_edges = np.linspace(0, n_samples, n_bins + 1, dtype=int)
time_env = np.array([time[(bin_edges[i] + bin_edges[i + 1]) // 2] for i in range(n_bins)])
amp_max = np.array([signal[bin_edges[i] : bin_edges[i + 1]].max() for i in range(n_bins)])
amp_min = np.array([signal[bin_edges[i] : bin_edges[i + 1]].min() for i in range(n_bins)])

# Compute amplitude magnitude per bin for color intensity mapping
amp_range = amp_max - amp_min

# Segment dataframe: vertical bars from ymin to ymax at each time point
df = pd.DataFrame({"time": time_env, "ymin": amp_min, "ymax": amp_max, "intensity": amp_range})

# Annotation data for waveform sections
ann_data = pd.DataFrame(
    {
        "time": [0.025, 0.225, 0.55, 0.95, 1.35],
        "y": [1.07, 1.07, 1.07, 1.07, 1.07],
        "label": ["Attack", "Sustain", "Dip", "Sustain", "Release"],
    }
)

# Section boundaries
section_df = pd.DataFrame({"x": [0.05, 0.4, 0.7, 1.2]})

# Subtitle with signal description
subtitle = "220 Hz fundamental + harmonics \u00b7 ASR envelope with amplitude dip at 0.4\u20130.7 s"

# Plot — vertical segments for DAW-style waveform rendering
plot = (
    ggplot(df)  # noqa: F405
    # Waveform bars: vertical segments colored by intensity
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
    + scale_color_gradient(low="#7bafd4", high="#1a3a5c", name="Amplitude\nRange")  # noqa: F405
    # Zero reference line
    + geom_hline(yintercept=0, color="#999999", size=0.5, linetype="dashed")  # noqa: F405
    # Section boundary markers
    + geom_vline(  # noqa: F405
        data=section_df,
        mapping=aes(xintercept="x"),  # noqa: F405
        color="#CCCCCC",
        size=0.4,
        linetype="dotted",
    )
    # Section annotations for storytelling
    + geom_text(  # noqa: F405
        data=ann_data,
        mapping=aes(x="time", y="y", label="label"),  # noqa: F405
        size=11,
        color="#1a3a5c",
        fontface="italic",
    )
    + scale_x_continuous(name="Time (seconds)", limits=[0, duration])  # noqa: F405
    + scale_y_continuous(  # noqa: F405
        name="Amplitude", limits=[-1.15, 1.18], breaks=[-1.0, -0.5, 0.0, 0.5, 1.0]
    )
    + labs(  # noqa: F405
        title="waveform-audio \u00b7 letsplot \u00b7 pyplots.ai", subtitle=subtitle
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        plot_subtitle=element_text(size=16, color="#555555"),  # noqa: F405
        legend_text=element_text(size=14),  # noqa: F405
        legend_title=element_text(size=16),  # noqa: F405
        legend_position="right",  # noqa: F405
        panel_grid_major_y=element_line(color="#E8E8E8", size=0.3),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_margin=[40, 20, 20, 20],  # noqa: F405
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
