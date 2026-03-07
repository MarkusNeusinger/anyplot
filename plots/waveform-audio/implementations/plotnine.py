""" pyplots.ai
waveform-audio: Audio Waveform Plot
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-07
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_ribbon,
    geom_vline,
    ggplot,
    labs,
    scale_alpha_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - synthetic audio waveform: tone with harmonics and amplitude envelope
np.random.seed(42)
sample_rate = 22050
duration = 1.5
num_samples = int(sample_rate * duration)
time = np.linspace(0, duration, num_samples)

# Primary tone at 220 Hz with harmonics
fundamental = 220
signal = (
    0.6 * np.sin(2 * np.pi * fundamental * time)
    + 0.25 * np.sin(2 * np.pi * fundamental * 2 * time)
    + 0.1 * np.sin(2 * np.pi * fundamental * 3 * time)
    + 0.05 * np.sin(2 * np.pi * fundamental * 5 * time)
)

# Amplitude envelope: attack-sustain-release shape
envelope = np.ones_like(time)
attack_end = int(0.05 * sample_rate)
sustain_end = int(1.1 * sample_rate)
envelope[:attack_end] = np.linspace(0, 1, attack_end)
envelope[sustain_end:] = np.linspace(1, 0, num_samples - sustain_end)

# Add slight vibrato and noise for realism
vibrato = 1.0 + 0.03 * np.sin(2 * np.pi * 5 * time)
noise = np.random.normal(0, 0.02, num_samples)
amplitude = np.clip((signal * envelope * vibrato) + noise, -1.0, 1.0)

# Downsample for plotting using min/max envelope to avoid aliasing
chunk_size = 64
num_chunks = num_samples // chunk_size
time_chunks = np.array([time[i * chunk_size] for i in range(num_chunks)])
amp_min = np.array([amplitude[i * chunk_size : (i + 1) * chunk_size].min() for i in range(num_chunks)])
amp_max = np.array([amplitude[i * chunk_size : (i + 1) * chunk_size].max() for i in range(num_chunks)])

# Classify each chunk into attack/sustain/release phase for storytelling
attack_time = 0.05
sustain_time = 1.1
phase = []
for t in time_chunks:
    if t < attack_time:
        phase.append("Attack")
    elif t < sustain_time:
        phase.append("Sustain")
    else:
        phase.append("Release")

df = pd.DataFrame(
    {
        "time": time_chunks,
        "amp_min": amp_min,
        "amp_max": amp_max,
        "phase": pd.Categorical(phase, categories=["Attack", "Sustain", "Release"], ordered=True),
    }
)

# Phase colors: distinct hues to tell the waveform story
phase_colors = {"Attack": "#E8651A", "Sustain": "#306998", "Release": "#6A4C93"}
phase_alphas = {"Attack": 0.85, "Sustain": 0.65, "Release": 0.55}

# Plot - use fill mapped to phase for data storytelling (DE-03)
plot = (
    ggplot(df, aes(x="time"))
    + geom_ribbon(aes(ymin="amp_min", ymax="amp_max", fill="phase", alpha="phase"), show_legend=False)
    + scale_fill_manual(values=phase_colors)
    + scale_alpha_manual(values=phase_alphas)
    + geom_hline(yintercept=0, color="#888888", size=0.3, linetype="solid")
    # Phase boundary markers
    + geom_vline(xintercept=attack_time, color="#E8651A", size=0.4, linetype="dashed", alpha=0.6)
    + geom_vline(xintercept=sustain_time, color="#6A4C93", size=0.4, linetype="dashed", alpha=0.6)
    # Phase labels via annotate (DE-03 storytelling)
    + annotate("text", x=0.025, y=0.92, label="Attack", size=11, color="#E8651A", fontstyle="italic")
    + annotate("text", x=0.575, y=0.92, label="Sustain", size=11, color="#306998", fontstyle="italic")
    + annotate("text", x=1.30, y=0.92, label="Release", size=11, color="#6A4C93", fontstyle="italic")
    + labs(x="Time (seconds)", y="Amplitude", title="waveform-audio · plotnine · pyplots.ai")
    + scale_x_continuous(
        breaks=np.arange(0, duration + 0.1, 0.25), labels=lambda lst: [f"{v:.2f}" for v in lst], expand=(0.01, 0.01)
    )
    + scale_y_continuous(limits=(-1.0, 1.0), breaks=np.arange(-1.0, 1.1, 0.25))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#2d2d2d"),
        axis_title=element_text(size=20, color="#2d2d2d", margin={"t": 12, "r": 12}),
        axis_text=element_text(size=16, color="#555555"),
        plot_title=element_text(size=24, weight="bold", color="#1a1a1a", margin={"b": 12}),
        panel_background=element_rect(fill="#f5f5f0", color="none"),
        plot_background=element_rect(fill="#ffffff", color="none"),
        panel_grid_major_y=element_line(color="#dcdcdc", size=0.25, linetype="dotted"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(color="#888888", size=0.5),
        axis_ticks_major_x=element_line(color="#888888", size=0.4),
        axis_ticks_major_y=element_blank(),
        plot_margin=0.02,
    )
)

plot.save("plot.png", dpi=300, verbose=False)
