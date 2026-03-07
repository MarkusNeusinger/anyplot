"""pyplots.ai
waveform-audio: Audio Waveform Plot
Library: plotly | Python 3.13
Quality: pending | Created: 2026-03-07
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)
sample_rate = 22050
duration = 1.5
num_samples = int(sample_rate * duration)
time = np.linspace(0, duration, num_samples)

# Synthesize audio: fundamental tone + harmonics with amplitude envelope
fundamental_freq = 220
signal = (
    0.6 * np.sin(2 * np.pi * fundamental_freq * time)
    + 0.25 * np.sin(2 * np.pi * fundamental_freq * 2 * time)
    + 0.1 * np.sin(2 * np.pi * fundamental_freq * 3 * time)
    + 0.05 * np.sin(2 * np.pi * fundamental_freq * 5 * time)
)

# Amplitude envelope: attack-sustain-decay shape
envelope = np.ones_like(time)
attack = int(0.05 * num_samples)
decay_start = int(0.7 * num_samples)
envelope[:attack] = np.linspace(0, 1, attack)
envelope[decay_start:] = np.linspace(1, 0.15, num_samples - decay_start)

# Add slight tremolo and noise for realism
tremolo = 1.0 + 0.08 * np.sin(2 * np.pi * 5.5 * time)
amplitude = signal * envelope * tremolo
amplitude += np.random.normal(0, 0.02, num_samples)
amplitude = np.clip(amplitude, -1.0, 1.0)

# Downsample for envelope rendering (min/max per block)
block_size = 32
num_blocks = num_samples // block_size
time_blocks = np.array([time[i * block_size] for i in range(num_blocks)])
amp_max = np.array([amplitude[i * block_size : (i + 1) * block_size].max() for i in range(num_blocks)])
amp_min = np.array([amplitude[i * block_size : (i + 1) * block_size].min() for i in range(num_blocks)])

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=np.concatenate([time_blocks, time_blocks[::-1]]),
        y=np.concatenate([amp_max, amp_min[::-1]]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.35)",
        line={"color": "#306998", "width": 1},
        name="Waveform",
        hovertemplate="Time: %{x:.3f}s<br>Amplitude: %{y:.3f}<extra></extra>",
    )
)

fig.add_hline(y=0, line_dash="solid", line_color="rgba(0, 0, 0, 0.3)", line_width=1)

# Style
fig.update_layout(
    title={"text": "waveform-audio \u00b7 plotly \u00b7 pyplots.ai", "font": {"size": 28}},
    xaxis={
        "title": {"text": "Time (seconds)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": False,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Amplitude", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [-1.05, 1.05],
        "showgrid": True,
        "gridcolor": "rgba(0, 0, 0, 0.08)",
        "gridwidth": 1,
        "zeroline": False,
    },
    template="plotly_white",
    showlegend=False,
    plot_bgcolor="white",
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
