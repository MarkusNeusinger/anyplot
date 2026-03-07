""" pyplots.ai
waveform-audio: Audio Waveform Plot
Library: altair 6.0.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-07
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

# Amplitude envelope: attack-sustain(with dip)-release with brief clipping section
envelope = np.ones_like(time)
attack = int(0.05 * sample_rate)
release = int(0.3 * sample_rate)
envelope[:attack] = np.linspace(0, 1, attack)
envelope[-release:] = np.linspace(1, 0, release)
envelope[int(0.4 * sample_rate) : int(0.7 * sample_rate)] *= 0.5
# Boost a short section to demonstrate clipping behavior
envelope[int(0.15 * sample_rate) : int(0.25 * sample_rate)] *= 1.35

signal = signal * envelope
signal = np.clip(signal, -1.0, 1.0)

# Vectorized min/max envelope binning for efficient rendering
num_bins = 2000
bin_size = num_samples // num_bins
usable = num_bins * bin_size
signal_trimmed = signal[:usable].reshape(num_bins, bin_size)
time_trimmed = time[:usable].reshape(num_bins, bin_size)

df = pd.DataFrame(
    {
        "time": time_trimmed[:, bin_size // 2],
        "amp_min": signal_trimmed.min(axis=1),
        "amp_max": signal_trimmed.max(axis=1),
    }
)
df["clipped"] = (df["amp_max"] >= 0.99) | (df["amp_min"] <= -0.99)

# Shared x/y encodings
x_enc = alt.X("time:Q", title="Time (seconds)", axis=alt.Axis(format=".2f", tickCount=8))
y_enc = alt.Y("amp_min:Q", title="Amplitude", scale=alt.Scale(domain=[-1.0, 1.0]))

# Nearest-point selection for interactive crosshair
nearest = alt.selection_point(nearest=True, on="pointerover", fields=["time"], empty=False)

# Main waveform fill with vertical gradient
waveform_gradient = (
    alt.Chart(df)
    .mark_area(
        interpolate="monotone",
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color="rgba(48, 105, 152, 0.10)", offset=0),
                alt.GradientStop(color="rgba(48, 105, 152, 0.60)", offset=0.45),
                alt.GradientStop(color="rgba(48, 105, 152, 0.60)", offset=0.55),
                alt.GradientStop(color="rgba(48, 105, 152, 0.10)", offset=1),
            ],
            x1=0,
            x2=0,
            y1=0,
            y2=1,
        ),
        line=False,
    )
    .encode(x=x_enc, y=y_enc, y2="amp_max:Q")
)

# Clipped regions overlay (filtered layer with red tint)
clipped_overlay = (
    alt.Chart(df)
    .mark_area(interpolate="monotone", color="rgba(180, 50, 50, 0.50)", line=False)
    .encode(x="time:Q", y=y_enc, y2="amp_max:Q")
    .transform_filter(alt.datum.clipped == True)  # noqa: E712
)

# Zero baseline reference line
zero_line = (
    alt.Chart(pd.DataFrame({"y": [0]}))
    .mark_rule(color="#306998", strokeWidth=1.5, opacity=0.35, strokeDash=[6, 4])
    .encode(y="y:Q")
)

# Clipping threshold lines at ±1.0
clip_lines = (
    alt.Chart(pd.DataFrame({"y": [-1.0, 1.0]}))
    .mark_rule(color="#b43232", strokeWidth=0.8, opacity=0.3, strokeDash=[3, 5])
    .encode(y="y:Q")
)

# Interactive vertical crosshair following the pointer
crosshair_rule = (
    alt.Chart(df).mark_rule(color="#306998", strokeWidth=1, opacity=0.5).encode(x="time:Q").transform_filter(nearest)
)

# Invisible selection trigger layer with tooltips
selection_layer = (
    alt.Chart(df)
    .mark_point(opacity=0)
    .encode(
        x="time:Q",
        y="amp_max:Q",
        tooltip=[
            alt.Tooltip("time:Q", title="Time (s)", format=".3f"),
            alt.Tooltip("amp_max:Q", title="Peak", format=".3f"),
            alt.Tooltip("amp_min:Q", title="Trough", format=".3f"),
        ],
    )
    .add_params(nearest)
)

# Compose layers and style
chart = (
    alt.layer(waveform_gradient, clipped_overlay, zero_line, clip_lines, crosshair_rule, selection_layer)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "waveform-audio · altair · pyplots.ai",
            fontSize=28,
            subtitle="440 Hz tone with harmonics · attack–sustain–release envelope · clipped region highlighted",
            subtitleFontSize=16,
            subtitleColor="#666666",
        ),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.12, domainColor="#aaaaaa", tickColor="#aaaaaa")
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.interactive().save("plot.html")
