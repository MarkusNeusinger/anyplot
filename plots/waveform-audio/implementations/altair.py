""" pyplots.ai
waveform-audio: Audio Waveform Plot
Library: altair 6.0.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-07
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - synthetic audio waveform: sine tone with harmonics and amplitude envelope
np.random.seed(42)
sample_rate = 22050
duration = 1.5
num_samples = int(sample_rate * duration)
time = np.linspace(0, duration, num_samples)

# Primary tone (440 Hz) with harmonics
fundamental = 440
signal = (
    0.6 * np.sin(2 * np.pi * fundamental * time)
    + 0.25 * np.sin(2 * np.pi * 2 * fundamental * time)
    + 0.15 * np.sin(2 * np.pi * 3 * fundamental * time)
)

# Amplitude envelope: attack-sustain-release shape
envelope = np.ones_like(time)
attack = int(0.05 * sample_rate)
release = int(0.3 * sample_rate)
envelope[:attack] = np.linspace(0, 1, attack)
envelope[-release:] = np.linspace(1, 0, release)
envelope[int(0.4 * sample_rate) : int(0.7 * sample_rate)] *= 0.5

signal = signal * envelope
signal = np.clip(signal, -1.0, 1.0)

# Downsample using min/max envelope for efficient rendering
num_bins = 2000
bin_size = num_samples // num_bins
time_binned = []
amp_min = []
amp_max = []

for i in range(num_bins):
    start = i * bin_size
    end = start + bin_size
    chunk = signal[start:end]
    time_binned.append(time[start + bin_size // 2])
    amp_min.append(float(chunk.min()))
    amp_max.append(float(chunk.max()))

df = pd.DataFrame({"time": time_binned, "amp_min": amp_min, "amp_max": amp_max})

# Plot - filled area between min and max envelope
waveform = (
    alt.Chart(df)
    .mark_area(
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color="rgba(48, 105, 152, 0.15)", offset=0),
                alt.GradientStop(color="rgba(48, 105, 152, 0.55)", offset=0.5),
                alt.GradientStop(color="rgba(48, 105, 152, 0.15)", offset=1),
            ],
            x1=0,
            x2=0,
            y1=0,
            y2=1,
        ),
        line=False,
    )
    .encode(
        x=alt.X("time:Q", title="Time (seconds)", axis=alt.Axis(format=".2f")),
        y=alt.Y("amp_min:Q", title="Amplitude", scale=alt.Scale(domain=[-1.05, 1.05])),
        y2="amp_max:Q",
        tooltip=[
            alt.Tooltip("time:Q", title="Time (s)", format=".3f"),
            alt.Tooltip("amp_max:Q", title="Peak", format=".3f"),
            alt.Tooltip("amp_min:Q", title="Trough", format=".3f"),
        ],
    )
)

# Zero baseline reference line
zero_line = (
    alt.Chart(pd.DataFrame({"y": [0]}))
    .mark_rule(color="#306998", strokeWidth=1.5, opacity=0.4, strokeDash=[6, 4])
    .encode(y="y:Q")
)

# Style
chart = (
    alt.layer(waveform, zero_line)
    .properties(width=1600, height=900, title=alt.Title("waveform-audio · altair · pyplots.ai", fontSize=28))
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.15)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.interactive().save("plot.html")
