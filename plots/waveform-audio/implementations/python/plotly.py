""" pyplots.ai
waveform-audio: Audio Waveform Plot
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-07
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
attack_end = int(0.05 * num_samples)
decay_start = int(0.7 * num_samples)
envelope[:attack_end] = np.linspace(0, 1, attack_end)
envelope[decay_start:] = np.linspace(1, 0.15, num_samples - decay_start)

# Add slight tremolo and noise for realism
tremolo = 1.0 + 0.08 * np.sin(2 * np.pi * 5.5 * time)
amplitude = signal * envelope * tremolo
amplitude += np.random.normal(0, 0.02, num_samples)
amplitude = np.clip(amplitude, -1.0, 1.0)

# Downsample for envelope rendering (min/max per block) - smaller blocks for smoother edges
block_size = 16
num_blocks = num_samples // block_size
time_blocks = np.array([(time[i * block_size] + time[(i + 1) * block_size - 1]) / 2 for i in range(num_blocks)])
amp_max = np.array([amplitude[i * block_size : (i + 1) * block_size].max() for i in range(num_blocks)])
amp_min = np.array([amplitude[i * block_size : (i + 1) * block_size].min() for i in range(num_blocks)])

# Phase boundaries for storytelling
attack_time = duration * 0.05
decay_time = duration * 0.7

# Plot
fig = go.Figure()

# Main waveform envelope with gradient-like layering for depth
fig.add_trace(
    go.Scatter(
        x=np.concatenate([time_blocks, time_blocks[::-1]]),
        y=np.concatenate([amp_max, amp_min[::-1]]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.18)",
        line={"color": "rgba(48, 105, 152, 0.6)", "width": 0.5, "shape": "spline"},
        name="Waveform",
        hovertemplate="Time: %{x:.3f}s<br>Amplitude: %{y:.3f}<extra></extra>",
    )
)

# Inner envelope (tighter) for visual depth
inner_scale = 0.65
fig.add_trace(
    go.Scatter(
        x=np.concatenate([time_blocks, time_blocks[::-1]]),
        y=np.concatenate([amp_max * inner_scale, amp_min[::-1] * inner_scale]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.30)",
        line={"width": 0, "shape": "spline"},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Peak envelope line on top for crisp definition
fig.add_trace(
    go.Scatter(
        x=time_blocks,
        y=amp_max,
        mode="lines",
        line={"color": "#306998", "width": 1.5, "shape": "spline"},
        showlegend=False,
        hoverinfo="skip",
    )
)
fig.add_trace(
    go.Scatter(
        x=time_blocks,
        y=amp_min,
        mode="lines",
        line={"color": "#306998", "width": 1.5, "shape": "spline"},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Zero-line
fig.add_hline(y=0, line_dash="solid", line_color="rgba(80, 80, 80, 0.25)", line_width=1)

# Phase region markers using vrects for visual storytelling
fig.add_vrect(x0=0, x1=attack_time, fillcolor="rgba(76, 175, 80, 0.07)", line_width=0)
fig.add_vrect(x0=decay_time, x1=duration, fillcolor="rgba(255, 152, 0, 0.07)", line_width=0)

# Phase labels as annotations for precise placement
fig.add_annotation(
    x=attack_time / 2,
    y=1.03,
    text="ATTACK",
    showarrow=False,
    font={"size": 16, "color": "rgba(76, 175, 80, 0.8)", "family": "Arial Black, sans-serif"},
    yref="y",
)
fig.add_annotation(
    x=(attack_time + decay_time) / 2,
    y=1.03,
    text="SUSTAIN",
    showarrow=False,
    font={"size": 16, "color": "rgba(100, 100, 100, 0.55)", "family": "Arial Black, sans-serif"},
    yref="y",
)
fig.add_annotation(
    x=(decay_time + duration) / 2,
    y=1.03,
    text="DECAY",
    showarrow=False,
    font={"size": 16, "color": "rgba(255, 140, 0, 0.8)", "family": "Arial Black, sans-serif"},
    yref="y",
)

# Phase boundary lines
for t_boundary in [attack_time, decay_time]:
    fig.add_vline(x=t_boundary, line_dash="dot", line_color="rgba(0, 0, 0, 0.15)", line_width=1)

# Style
fig.update_layout(
    title={
        "text": "waveform-audio · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#2c3e50", "family": "Arial Black, sans-serif"},
        "x": 0.02,
        "xanchor": "left",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Time (seconds)", "font": {"size": 22, "color": "#555"}},
        "tickfont": {"size": 18, "color": "#666"},
        "showgrid": False,
        "zeroline": False,
        "linecolor": "rgba(0, 0, 0, 0.15)",
        "linewidth": 1,
        "ticks": "outside",
        "tickcolor": "rgba(0, 0, 0, 0.15)",
        "ticklen": 6,
    },
    yaxis={
        "title": {"text": "Amplitude", "font": {"size": 22, "color": "#555"}},
        "tickfont": {"size": 18, "color": "#666"},
        "range": [-1.08, 1.08],
        "showgrid": True,
        "gridcolor": "rgba(0, 0, 0, 0.05)",
        "gridwidth": 1,
        "zeroline": False,
        "linecolor": "rgba(0, 0, 0, 0.15)",
        "linewidth": 1,
        "ticks": "outside",
        "tickcolor": "rgba(0, 0, 0, 0.15)",
        "ticklen": 6,
        "dtick": 0.5,
    },
    template="plotly_white",
    showlegend=False,
    plot_bgcolor="rgba(250, 251, 253, 1)",
    paper_bgcolor="white",
    margin={"l": 90, "r": 50, "t": 80, "b": 70},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
