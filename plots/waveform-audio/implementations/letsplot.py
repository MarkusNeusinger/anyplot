"""pyplots.ai
waveform-audio: Audio Waveform Plot
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-07
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
attack = int(0.05 * sample_rate)
release = int(0.3 * sample_rate)
envelope[:attack] = np.linspace(0, 1, attack)
envelope[-release:] = np.linspace(1, 0, release)
envelope[int(0.4 * sample_rate) : int(0.7 * sample_rate)] *= 0.5

signal = signal * envelope
signal = signal / np.max(np.abs(signal))

# Downsample using min/max envelope for clean rendering
n_bins = 2000
bin_size = n_samples // n_bins
time_env = []
amp_min = []
amp_max = []

for i in range(n_bins):
    start = i * bin_size
    end = min(start + bin_size, n_samples)
    chunk = signal[start:end]
    t_mid = time[start + (end - start) // 2]
    time_env.append(t_mid)
    amp_min.append(float(np.min(chunk)))
    amp_max.append(float(np.max(chunk)))

time_env = np.array(time_env)
amp_min = np.array(amp_min)
amp_max = np.array(amp_max)

df = pd.DataFrame(
    {"time": np.concatenate([time_env, time_env[::-1]]), "amplitude": np.concatenate([amp_max, amp_min[::-1]])}
)

df_line_top = pd.DataFrame({"time": time_env, "amplitude": amp_max})
df_line_bot = pd.DataFrame({"time": time_env, "amplitude": amp_min})
df_zero = pd.DataFrame({"time": [0, duration], "amplitude": [0.0, 0.0]})

# Plot
plot = (
    ggplot()  # noqa: F405
    + geom_polygon(  # noqa: F405
        data=df,
        mapping=aes(x="time", y="amplitude"),  # noqa: F405
        fill="#306998",
        alpha=0.35,
    )
    + geom_line(  # noqa: F405
        data=df_line_top,
        mapping=aes(x="time", y="amplitude"),  # noqa: F405
        color="#306998",
        size=0.5,
    )
    + geom_line(  # noqa: F405
        data=df_line_bot,
        mapping=aes(x="time", y="amplitude"),  # noqa: F405
        color="#306998",
        size=0.5,
    )
    + geom_line(  # noqa: F405
        data=df_zero,
        mapping=aes(x="time", y="amplitude"),  # noqa: F405
        color="#888888",
        size=0.6,
        linetype="dashed",
    )
    + scale_x_continuous(name="Time (seconds)")  # noqa: F405
    + scale_y_continuous(  # noqa: F405
        name="Amplitude", limits=[-1.05, 1.05], breaks=[-1.0, -0.5, 0.0, 0.5, 1.0]
    )
    + labs(title="waveform-audio \u00b7 letsplot \u00b7 pyplots.ai")  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.3),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
