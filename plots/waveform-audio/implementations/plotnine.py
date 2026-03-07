"""pyplots.ai
waveform-audio: Audio Waveform Plot
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-07
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_ribbon,
    ggplot,
    labs,
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

df = pd.DataFrame({"time": time_chunks, "amp_min": amp_min, "amp_max": amp_max})

# Plot
plot = (
    ggplot(df, aes(x="time"))
    + geom_ribbon(aes(ymin="amp_min", ymax="amp_max"), fill="#306998", alpha=0.7)
    + geom_hline(yintercept=0, color="#888888", size=0.4, linetype="solid")
    + labs(x="Time (seconds)", y="Amplitude", title="waveform-audio · plotnine · pyplots.ai")
    + scale_x_continuous(breaks=np.arange(0, duration + 0.1, 0.25), labels=lambda lst: [f"{v:.2f}" for v in lst])
    + scale_y_continuous(limits=(-1.05, 1.05), breaks=np.arange(-1.0, 1.1, 0.5))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#2d2d2d"),
        axis_title=element_text(size=20, color="#2d2d2d"),
        axis_text=element_text(size=16, color="#555555"),
        plot_title=element_text(size=24, weight="bold", color="#1a1a1a"),
        panel_background=element_rect(fill="#fafafa", color="none"),
        plot_background=element_rect(fill="#ffffff", color="none"),
        panel_grid_major_y=element_line(color="#e0e0e0", size=0.3),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(color="#999999", size=0.5),
        axis_ticks_major_x=element_line(color="#999999", size=0.4),
        axis_ticks_major_y=element_blank(),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
